"""
Web scraper for FollowTheMoney.org to fetch Arizona IE data.

This scraper fetches independent expenditure data from FollowTheMoney.org
without requiring an API key.

Usage:
    python manage.py scrape_ftm --cycle 2022
    python manage.py scrape_ftm --cycle 2022 --office Governor
    python manage.py scrape_ftm --cycle 2022 --compare
"""

import json
import time
import re
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from django.db.models.functions import Abs

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from transparency.models import Transaction, Office, Cycle


class Command(BaseCommand):
    help = 'Scrape FollowTheMoney.org for Arizona IE data verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cycle',
            type=str,
            required=True,
            help='Election cycle year (e.g., "2022")'
        )
        parser.add_argument(
            '--office',
            type=str,
            help='Filter by office (e.g., "Governor")'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare scraped data with Az-Sunshine database'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON file path'
        )

    def handle(self, *args, **options):
        cycle_year = options['cycle']
        office_filter = options.get('office')
        do_compare = options.get('compare', False)
        output_path = options.get('output')

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 60 + '\n'
            '  FOLLOWTHEMONEY.ORG SCRAPER\n'
            '  Arizona IE Data Verification\n'
            '=' * 60 + '\n'
        ))

        # Set up headless Chrome
        self.stdout.write("Setting up headless Chrome browser...")
        driver = self._setup_driver()

        try:
            # Scrape IE data
            self.stdout.write(f"\nScraping IE data for Arizona {cycle_year}...")
            ftm_data = self._scrape_ie_data(driver, cycle_year, office_filter)

            if not ftm_data:
                self.stdout.write(self.style.ERROR("No data scraped from FollowTheMoney"))
                return

            self.stdout.write(self.style.SUCCESS(
                f"\nScraped {len(ftm_data)} candidates from FollowTheMoney"
            ))

            # Display scraped data
            self._display_scraped_data(ftm_data)

            # Save to file if requested
            if output_path:
                report = {
                    'source': 'followthemoney.org',
                    'scraped_at': datetime.now().isoformat(),
                    'cycle': cycle_year,
                    'office': office_filter,
                    'candidates': ftm_data
                }
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2)
                self.stdout.write(self.style.SUCCESS(f"\nSaved to: {output_path}"))

            # Compare with database if requested
            if do_compare:
                self._compare_with_database(ftm_data, cycle_year, office_filter)

        finally:
            driver.quit()
            self.stdout.write("\nBrowser closed.")

    def _setup_driver(self):
        """Set up headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def _scrape_ie_data(self, driver, cycle_year, office_filter=None):
        """Scrape IE data from FollowTheMoney"""
        candidates = []

        # Build URL for Arizona IE data
        # dt=2 means Independent Spending data type
        # c-exi=1 means include expenditures
        # gro=c-t-id means group by candidate
        base_url = "https://www.followthemoney.org/show-me"
        params = f"?s=AZ&y={cycle_year}&dt=2&c-exi=1&gro=c-t-id"

        if office_filter:
            # Map office names to FTM codes
            office_codes = {
                'Governor': 'G',
                'Attorney General': 'AG',
                'Secretary of State': 'SOS',
                'State Treasurer': 'ST',
                'Superintendent of Public Instruction': 'SPI',
            }
            code = office_codes.get(office_filter, '')
            if code:
                params += f"&c-r-ot={code}"

        url = base_url + params
        self.stdout.write(f"Loading: {url}")

        driver.get(url)

        # Wait for data to load (JavaScript rendering)
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, .data-table, #results"))
            )
            time.sleep(3)  # Extra wait for full data load
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Timeout waiting for data: {e}"))

        # Try multiple selectors to find data
        candidates = self._extract_table_data(driver)

        if not candidates:
            # Try alternative extraction method
            candidates = self._extract_from_page_source(driver)

        return candidates

    def _extract_table_data(self, driver):
        """Extract data from table elements"""
        candidates = []

        try:
            # Look for data tables
            tables = driver.find_elements(By.TAG_NAME, "table")

            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        # Try to extract candidate name and amount
                        name = cells[0].text.strip()
                        amount_text = cells[-1].text.strip()

                        if name and self._looks_like_candidate(name):
                            amount = self._parse_amount(amount_text)
                            if amount > 0:
                                candidates.append({
                                    'name': name,
                                    'total_ie': float(amount),
                                    'source': 'followthemoney.org'
                                })
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error extracting table data: {e}"))

        return candidates

    def _extract_from_page_source(self, driver):
        """Extract data from page source using regex"""
        candidates = []

        try:
            page_source = driver.page_source

            # Look for candidate data patterns in JavaScript
            # FTM often embeds data in JSON format
            json_pattern = r'\{[^{}]*"Candidate"[^{}]*\}'
            matches = re.findall(json_pattern, page_source)

            for match in matches:
                try:
                    data = json.loads(match)
                    if 'Candidate' in data:
                        candidates.append({
                            'name': data.get('Candidate', ''),
                            'total_ie': float(data.get('Total', 0)),
                            'source': 'followthemoney.org'
                        })
                except:
                    pass

            # Alternative: look for data in specific elements
            data_elements = driver.find_elements(By.CSS_SELECTOR, "[data-candidate], .candidate-row, .result-row")
            for elem in data_elements:
                name = elem.get_attribute('data-candidate') or elem.text.split('\n')[0]
                if name:
                    candidates.append({
                        'name': name.strip(),
                        'total_ie': 0,  # Would need to extract from element
                        'source': 'followthemoney.org'
                    })

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error extracting from page source: {e}"))

        return candidates

    def _looks_like_candidate(self, text):
        """Check if text looks like a candidate name"""
        if not text or len(text) < 3:
            return False
        # Skip common non-candidate strings
        skip_terms = ['total', 'amount', 'date', 'type', 'source', 'committee', 'pac']
        return not any(term in text.lower() for term in skip_terms)

    def _parse_amount(self, text):
        """Parse dollar amount from text"""
        try:
            # Remove $, commas, and other non-numeric chars
            clean = re.sub(r'[^\d.]', '', text)
            return Decimal(clean) if clean else Decimal('0')
        except:
            return Decimal('0')

    def _display_scraped_data(self, data):
        """Display scraped data summary"""
        self.stdout.write('\n' + '-' * 50)
        self.stdout.write('SCRAPED DATA FROM FOLLOWTHEMONEY:')
        self.stdout.write('-' * 50)

        total = Decimal('0')
        for cand in sorted(data, key=lambda x: x.get('total_ie', 0), reverse=True)[:20]:
            name = cand.get('name', 'Unknown')
            amount = cand.get('total_ie', 0)
            total += Decimal(str(amount))
            self.stdout.write(f"  {name}: ${amount:,.2f}")

        self.stdout.write(f"\nTotal IE (top 20): ${total:,.2f}")

    def _compare_with_database(self, ftm_data, cycle_year, office_filter):
        """Compare scraped data with Az-Sunshine database"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('COMPARISON WITH AZ-SUNSHINE DATABASE:')
        self.stdout.write('=' * 50)

        try:
            cycle = Cycle.objects.get(name=cycle_year)
        except Cycle.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Cycle {cycle_year} not found"))
            return

        filters = {
            'deleted': False,
            'subject_committee__isnull': False,
            'transaction_date__gte': cycle.begin_date,
            'transaction_date__lte': cycle.end_date,
            'transaction_type__income_expense_neutral': 2,
        }

        if office_filter:
            try:
                office = Office.objects.get(name=office_filter)
                filters['subject_committee__candidate_office'] = office
            except Office.DoesNotExist:
                pass

        # Get our totals
        our_total = Transaction.objects.filter(**filters).aggregate(
            total=Sum(Abs('amount'))
        )['total'] or Decimal('0')

        # FTM total
        ftm_total = sum(Decimal(str(c.get('total_ie', 0))) for c in ftm_data)

        self.stdout.write(f"\nAz-Sunshine Total IE: ${our_total:,.2f}")
        self.stdout.write(f"FollowTheMoney Total: ${ftm_total:,.2f}")

        variance = abs(our_total - ftm_total)
        if our_total > 0:
            variance_pct = float(variance / our_total * 100)
        else:
            variance_pct = 0

        if variance_pct <= 5:
            self.stdout.write(self.style.SUCCESS(
                f"Variance: ${variance:,.2f} ({variance_pct:.1f}%) - GOOD MATCH"
            ))
        elif variance_pct <= 15:
            self.stdout.write(self.style.WARNING(
                f"Variance: ${variance:,.2f} ({variance_pct:.1f}%) - ACCEPTABLE"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Variance: ${variance:,.2f} ({variance_pct:.1f}%) - NEEDS REVIEW"
            ))
