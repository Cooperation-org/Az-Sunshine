"""
Web scraper for SeeTheMoney.az.gov to fetch Arizona IE data.

This scraper fetches independent expenditure data directly from the
Arizona Secretary of State's official database.

Usage:
    python manage.py scrape_seethemoney --year 2022
    python manage.py scrape_seethemoney --year 2022 --compare
    python manage.py scrape_seethemoney --year 2022 --output /tmp/ie_2022.json
"""

import json
import time
import re
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from django.db.models.functions import Abs

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from transparency.models import Transaction, Office, Cycle


class Command(BaseCommand):
    help = 'Scrape SeeTheMoney.az.gov for Arizona IE data verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=str,
            required=True,
            help='Election year (e.g., "2022")'
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
        year = options['year']
        do_compare = options.get('compare', False)
        output_path = options.get('output')

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 60 + '\n'
            '  SEETHEMONEY.AZ.GOV SCRAPER\n'
            '  Official Arizona IE Data\n'
            '=' * 60 + '\n'
        ))

        # Set up headless Chrome
        self.stdout.write("Setting up headless Chrome browser...")
        driver = self._setup_driver()

        try:
            # Scrape IE data
            self.stdout.write(f"\nScraping IE data for {year}...")
            ie_data = self._scrape_ie_data(driver, year)

            if not ie_data:
                self.stdout.write(self.style.ERROR("No data scraped"))
                return

            self.stdout.write(self.style.SUCCESS(
                f"\nScraped {len(ie_data)} candidates from SeeTheMoney"
            ))

            # Display scraped data
            self._display_data(ie_data)

            # Calculate totals
            total_for = sum(c['ie_for'] for c in ie_data.values())
            total_against = sum(c['ie_against'] for c in ie_data.values())
            self.stdout.write(f"\nSeeTheMoney Totals:")
            self.stdout.write(f"  IE For:     ${total_for:,.2f}")
            self.stdout.write(f"  IE Against: ${total_against:,.2f}")
            self.stdout.write(f"  Total IE:   ${total_for + total_against:,.2f}")

            # Save to file if requested
            if output_path:
                report = {
                    'source': 'seethemoney.az.gov',
                    'scraped_at': datetime.now().isoformat(),
                    'year': year,
                    'total_ie_for': float(total_for),
                    'total_ie_against': float(total_against),
                    'total_ie': float(total_for + total_against),
                    'candidates': {k: {
                        'ie_for': float(v['ie_for']),
                        'ie_against': float(v['ie_against']),
                        'total_ie': float(v['ie_for'] + v['ie_against'])
                    } for k, v in ie_data.items()}
                }
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2)
                self.stdout.write(self.style.SUCCESS(f"\nSaved to: {output_path}"))

            # Compare with database if requested
            if do_compare:
                self._compare_with_database(ie_data, year)

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

    def _scrape_ie_data(self, driver, year):
        """Scrape IE data from SeeTheMoney"""
        candidates = defaultdict(lambda: {'ie_for': Decimal('0'), 'ie_against': Decimal('0')})

        try:
            # Load main page
            url = 'https://seethemoney.az.gov'
            self.stdout.write(f"Loading: {url}")
            driver.get(url)
            time.sleep(3)

            # Click on Independent Expenditures tab (page 5) using JavaScript
            self.stdout.write("Clicking Independent Expenditures tab...")
            driver.execute_script("document.querySelector('li[page=\"5\"] a').click()")
            time.sleep(3)

            # Set year filters
            self.stdout.write(f"Setting year filter to {year}...")

            # Find and set start year dropdown (class="StartFilter years")
            try:
                start_selects = driver.find_elements(By.CSS_SELECTOR, "select.StartFilter.years")
                if start_selects:
                    Select(start_selects[0]).select_by_visible_text(year)
                    self.stdout.write(f"  Set start year to {year}")
                    time.sleep(1)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not set start year: {e}"))

            # Find and set end year dropdown (class="EndFilter years")
            try:
                end_selects = driver.find_elements(By.CSS_SELECTOR, "select.EndFilter.years")
                if end_selects:
                    Select(end_selects[0]).select_by_visible_text(year)
                    self.stdout.write(f"  Set end year to {year}")
                    time.sleep(1)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not set end year: {e}"))

            # Wait for data to load
            time.sleep(3)

            # Try to show all entries (100 per page)
            try:
                show_select = driver.find_element(By.NAME, "IndependentExpenditureInformationTable_length")
                Select(show_select).select_by_visible_text("100")
                self.stdout.write("  Set to show 100 entries per page")
                time.sleep(3)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not set page size: {e}"))

            # Extract data from table
            page_num = 1
            while True:
                self.stdout.write(f"  Extracting page {page_num}...")

                # Find the IE table
                try:
                    table = driver.find_element(By.ID, "IndependentExpenditureInformationTable")
                    rows = table.find_elements(By.TAG_NAME, "tr")

                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            candidate_name = cells[0].text.strip()
                            ie_for_text = cells[1].text.strip()
                            ie_against_text = cells[2].text.strip()

                            if candidate_name and candidate_name != 'Affected Candidate Committee':
                                ie_for = self._parse_amount(ie_for_text)
                                ie_against = self._parse_amount(ie_against_text)

                                candidates[candidate_name]['ie_for'] += ie_for
                                candidates[candidate_name]['ie_against'] += ie_against

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error extracting table: {e}"))
                    break

                # Try to go to next page
                try:
                    # Find next button for IE table specifically
                    next_btns = driver.find_elements(By.CSS_SELECTOR, "#IndependentExpenditureInformation .paginate_button.next:not(.disabled)")
                    if next_btns and 'disabled' not in next_btns[0].get_attribute('class'):
                        next_btns[0].click()
                        time.sleep(2)
                        page_num += 1
                    else:
                        self.stdout.write(f"  No more pages (total: {page_num})")
                        break
                except Exception as e:
                    self.stdout.write(f"  Pagination ended: {e}")
                    break

                if page_num > 100:  # Safety limit
                    self.stdout.write("  Reached page limit")
                    break

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Scraping error: {e}"))

        return dict(candidates)

    def _parse_amount(self, text):
        """Parse dollar amount from text"""
        try:
            clean = re.sub(r'[^\d.]', '', text)
            return Decimal(clean) if clean else Decimal('0')
        except:
            return Decimal('0')

    def _display_data(self, data):
        """Display scraped data"""
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write('SCRAPED IE DATA FROM SEETHEMONEY:')
        self.stdout.write('-' * 60)

        sorted_data = sorted(
            data.items(),
            key=lambda x: x[1]['ie_for'] + x[1]['ie_against'],
            reverse=True
        )

        for name, amounts in sorted_data[:25]:
            total = amounts['ie_for'] + amounts['ie_against']
            self.stdout.write(
                f"  {name[:40]:<40} "
                f"For: ${amounts['ie_for']:>12,.2f}  "
                f"Against: ${amounts['ie_against']:>12,.2f}  "
                f"Total: ${total:>12,.2f}"
            )

        if len(sorted_data) > 25:
            self.stdout.write(f"\n  ... and {len(sorted_data) - 25} more candidates")

    def _compare_with_database(self, stm_data, year):
        """Compare scraped data with Az-Sunshine database"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('COMPARISON WITH AZ-SUNSHINE DATABASE:')
        self.stdout.write('=' * 60)

        try:
            cycle = Cycle.objects.get(name=year)
        except Cycle.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Cycle {year} not found"))
            return

        # Get our data
        our_data = Transaction.objects.filter(
            deleted=False,
            subject_committee__isnull=False,
            transaction_date__gte=cycle.begin_date,
            transaction_date__lte=cycle.end_date,
            transaction_type__income_expense_neutral=2,
        ).values(
            'subject_committee__name__last_name',
            'subject_committee__name__first_name',
        ).annotate(
            ie_for=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            ie_against=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
        )

        # Build lookup dict
        our_lookup = {}
        for row in our_data:
            name = f"{row['subject_committee__name__first_name'] or ''} {row['subject_committee__name__last_name'] or ''}".strip()
            norm_name = self._normalize_name(name)
            our_lookup[norm_name] = {
                'ie_for': row['ie_for'] or Decimal('0'),
                'ie_against': row['ie_against'] or Decimal('0'),
                'original_name': name
            }

        # Compare totals
        stm_total_for = sum(c['ie_for'] for c in stm_data.values())
        stm_total_against = sum(c['ie_against'] for c in stm_data.values())
        stm_total = stm_total_for + stm_total_against

        our_total_for = sum(c['ie_for'] for c in our_lookup.values())
        our_total_against = sum(c['ie_against'] for c in our_lookup.values())
        our_total = our_total_for + our_total_against

        self.stdout.write(f"\n{'Metric':<20} {'SeeTheMoney':>15} {'Az-Sunshine':>15} {'Variance':>15}")
        self.stdout.write('-' * 70)
        self.stdout.write(f"{'IE For':<20} ${stm_total_for:>13,.2f} ${our_total_for:>13,.2f} ${abs(stm_total_for - our_total_for):>13,.2f}")
        self.stdout.write(f"{'IE Against':<20} ${stm_total_against:>13,.2f} ${our_total_against:>13,.2f} ${abs(stm_total_against - our_total_against):>13,.2f}")
        self.stdout.write(f"{'Total IE':<20} ${stm_total:>13,.2f} ${our_total:>13,.2f} ${abs(stm_total - our_total):>13,.2f}")

        # Calculate variance percentage
        if stm_total > 0:
            variance_pct = abs(float(stm_total - our_total) / float(stm_total) * 100)
        else:
            variance_pct = 0

        self.stdout.write('')
        if variance_pct <= 1:
            self.stdout.write(self.style.SUCCESS(f"Variance: {variance_pct:.2f}% - EXCELLENT MATCH!"))
        elif variance_pct <= 5:
            self.stdout.write(self.style.SUCCESS(f"Variance: {variance_pct:.2f}% - GOOD MATCH"))
        elif variance_pct <= 10:
            self.stdout.write(self.style.WARNING(f"Variance: {variance_pct:.2f}% - ACCEPTABLE"))
        else:
            self.stdout.write(self.style.ERROR(f"Variance: {variance_pct:.2f}% - NEEDS REVIEW"))

        # Find discrepancies by candidate
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write('TOP DISCREPANCIES BY CANDIDATE:')
        self.stdout.write('-' * 60)

        discrepancies = []
        for stm_name, stm_amounts in stm_data.items():
            norm_name = self._normalize_name(stm_name)
            our_amounts = our_lookup.get(norm_name, {'ie_for': Decimal('0'), 'ie_against': Decimal('0')})

            stm_total_cand = stm_amounts['ie_for'] + stm_amounts['ie_against']
            our_total_cand = our_amounts['ie_for'] + our_amounts['ie_against']
            variance = abs(stm_total_cand - our_total_cand)

            if variance > 1000:  # Only show significant variances
                discrepancies.append({
                    'name': stm_name,
                    'stm_total': stm_total_cand,
                    'our_total': our_total_cand,
                    'variance': variance
                })

        discrepancies.sort(key=lambda x: x['variance'], reverse=True)

        for disc in discrepancies[:10]:
            self.stdout.write(f"\n  {disc['name']}")
            self.stdout.write(f"    SeeTheMoney: ${disc['stm_total']:,.2f}")
            self.stdout.write(f"    Az-Sunshine: ${disc['our_total']:,.2f}")
            self.stdout.write(f"    Variance:    ${disc['variance']:,.2f}")

    def _normalize_name(self, name):
        """Normalize name for comparison"""
        name = name.lower().strip()
        # Remove common suffixes
        for suffix in [' for governor', ' for arizona', ' for az', ' 2022', ' 2024',
                       ' for attorney general', ' for secretary of state']:
            name = name.replace(suffix, '')
        return ' '.join(name.split())
