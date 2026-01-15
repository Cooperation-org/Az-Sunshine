"""
Comprehensive multi-year verification against SeeTheMoney.az.gov

This is the FULL 2nd layer verification - compares ALL years of IE data
against the official Arizona Secretary of State database.

Usage:
    python manage.py verify_all_years
    python manage.py verify_all_years --start 2018 --end 2024
    python manage.py verify_all_years --output /tmp/full_report.json
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

from transparency.models import Transaction, Cycle


class Command(BaseCommand):
    help = 'Comprehensive multi-year verification against SeeTheMoney.az.gov'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            type=int,
            default=2016,
            help='Start year (default: 2016)'
        )
        parser.add_argument(
            '--end',
            type=int,
            default=2026,
            help='End year (default: 2026)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON report file'
        )

    def handle(self, *args, **options):
        start_year = options['start']
        end_year = options['end']
        output_path = options.get('output') or f'/opt/az_sunshine/backend/data/comparison/full_verification_{start_year}_{end_year}.json'

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 70 + '\n'
            '  AZ-SUNSHINE FULL VERIFICATION\n'
            '  Comparing ALL years against SeeTheMoney.az.gov\n'
            '=' * 70 + '\n'
        ))

        # Setup browser once for all years
        self.stdout.write("Setting up browser...")
        driver = self._setup_driver()

        results = {}
        all_years_data = {
            'seethemoney': {},
            'az_sunshine': {}
        }

        try:
            # First, get all SeeTheMoney data
            self.stdout.write(f"\n{'=' * 70}")
            self.stdout.write("PHASE 1: SCRAPING SEETHEMONEY.AZ.GOV")
            self.stdout.write('=' * 70)

            for year in range(start_year, end_year + 1):
                self.stdout.write(f"\n[{year}] Scraping SeeTheMoney...")
                stm_data = self._scrape_year(driver, str(year))
                all_years_data['seethemoney'][year] = stm_data

                total_for = sum(c['ie_for'] for c in stm_data.values())
                total_against = sum(c['ie_against'] for c in stm_data.values())
                total = total_for + total_against

                self.stdout.write(f"  Candidates: {len(stm_data)}")
                self.stdout.write(f"  Total IE: ${total:,.2f}")

            driver.quit()
            self.stdout.write("\nBrowser closed.")

            # Get Az-Sunshine data for all years
            self.stdout.write(f"\n{'=' * 70}")
            self.stdout.write("PHASE 2: QUERYING AZ-SUNSHINE DATABASE")
            self.stdout.write('=' * 70)

            for year in range(start_year, end_year + 1):
                self.stdout.write(f"\n[{year}] Querying database...")
                az_data = self._get_az_sunshine_data(str(year))
                all_years_data['az_sunshine'][year] = az_data

                total_for = sum(c['ie_for'] for c in az_data.values())
                total_against = sum(c['ie_against'] for c in az_data.values())
                total = total_for + total_against

                self.stdout.write(f"  Candidates: {len(az_data)}")
                self.stdout.write(f"  Total IE: ${total:,.2f}")

            # Compare all years
            self.stdout.write(f"\n{'=' * 70}")
            self.stdout.write("PHASE 3: COMPARISON RESULTS")
            self.stdout.write('=' * 70)

            overall_stm_total = Decimal('0')
            overall_az_total = Decimal('0')
            year_results = []

            for year in range(start_year, end_year + 1):
                stm_data = all_years_data['seethemoney'].get(year, {})
                az_data = all_years_data['az_sunshine'].get(year, {})

                stm_total = sum(c['ie_for'] + c['ie_against'] for c in stm_data.values())
                az_total = sum(c['ie_for'] + c['ie_against'] for c in az_data.values())

                overall_stm_total += stm_total
                overall_az_total += az_total

                variance = abs(stm_total - az_total)
                if stm_total > 0:
                    variance_pct = float(variance / stm_total * 100)
                else:
                    variance_pct = 0 if az_total == 0 else 100

                # Determine status
                if stm_total == 0 and az_total == 0:
                    status = "NO DATA"
                    status_style = ""
                elif variance_pct <= 5:
                    status = "EXCELLENT"
                    status_style = "SUCCESS"
                elif variance_pct <= 10:
                    status = "GOOD"
                    status_style = "SUCCESS"
                elif variance_pct <= 20:
                    status = "ACCEPTABLE"
                    status_style = "WARNING"
                else:
                    status = "REVIEW NEEDED"
                    status_style = "ERROR"

                year_result = {
                    'year': year,
                    'seethemoney_total': float(stm_total),
                    'az_sunshine_total': float(az_total),
                    'variance': float(variance),
                    'variance_pct': variance_pct,
                    'status': status,
                    'stm_candidates': len(stm_data),
                    'az_candidates': len(az_data)
                }
                year_results.append(year_result)

                # Display result
                if status_style == "SUCCESS":
                    self.stdout.write(self.style.SUCCESS(
                        f"\n[{year}] {status} - Variance: {variance_pct:.2f}%"
                    ))
                elif status_style == "WARNING":
                    self.stdout.write(self.style.WARNING(
                        f"\n[{year}] {status} - Variance: {variance_pct:.2f}%"
                    ))
                elif status_style == "ERROR":
                    self.stdout.write(self.style.ERROR(
                        f"\n[{year}] {status} - Variance: {variance_pct:.2f}%"
                    ))
                else:
                    self.stdout.write(f"\n[{year}] {status}")

                self.stdout.write(f"  SeeTheMoney: ${stm_total:>15,.2f} ({len(stm_data)} candidates)")
                self.stdout.write(f"  Az-Sunshine: ${az_total:>15,.2f} ({len(az_data)} candidates)")
                self.stdout.write(f"  Variance:    ${variance:>15,.2f}")

            # Overall summary
            self.stdout.write(f"\n{'=' * 70}")
            self.stdout.write("OVERALL SUMMARY")
            self.stdout.write('=' * 70)

            overall_variance = abs(overall_stm_total - overall_az_total)
            if overall_stm_total > 0:
                overall_variance_pct = float(overall_variance / overall_stm_total * 100)
            else:
                overall_variance_pct = 0

            self.stdout.write(f"\nTotal SeeTheMoney IE ({start_year}-{end_year}): ${overall_stm_total:,.2f}")
            self.stdout.write(f"Total Az-Sunshine IE ({start_year}-{end_year}): ${overall_az_total:,.2f}")
            self.stdout.write(f"Overall Variance: ${overall_variance:,.2f} ({overall_variance_pct:.2f}%)")

            # Count statuses
            excellent = sum(1 for r in year_results if r['status'] == 'EXCELLENT')
            good = sum(1 for r in year_results if r['status'] == 'GOOD')
            acceptable = sum(1 for r in year_results if r['status'] == 'ACCEPTABLE')
            needs_review = sum(1 for r in year_results if r['status'] == 'REVIEW NEEDED')
            no_data = sum(1 for r in year_results if r['status'] == 'NO DATA')

            self.stdout.write(f"\nYear Status Summary:")
            self.stdout.write(self.style.SUCCESS(f"  EXCELLENT (≤5%):    {excellent}"))
            self.stdout.write(self.style.SUCCESS(f"  GOOD (≤10%):        {good}"))
            self.stdout.write(self.style.WARNING(f"  ACCEPTABLE (≤20%):  {acceptable}"))
            self.stdout.write(self.style.ERROR(f"  REVIEW NEEDED:      {needs_review}"))
            self.stdout.write(f"  NO DATA:            {no_data}")

            # Final verdict
            self.stdout.write(f"\n{'=' * 70}")
            if overall_variance_pct <= 5:
                self.stdout.write(self.style.SUCCESS(
                    "FINAL VERDICT: DATA VERIFIED - EXCELLENT MATCH"
                ))
            elif overall_variance_pct <= 10:
                self.stdout.write(self.style.SUCCESS(
                    "FINAL VERDICT: DATA VERIFIED - GOOD MATCH"
                ))
            elif overall_variance_pct <= 15:
                self.stdout.write(self.style.WARNING(
                    "FINAL VERDICT: DATA ACCEPTABLE - MINOR REVIEW RECOMMENDED"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    "FINAL VERDICT: SIGNIFICANT VARIANCE - INVESTIGATION NEEDED"
                ))
            self.stdout.write('=' * 70)

            # Save report
            report = {
                'generated_at': datetime.now().isoformat(),
                'period': f"{start_year}-{end_year}",
                'overall': {
                    'seethemoney_total': float(overall_stm_total),
                    'az_sunshine_total': float(overall_az_total),
                    'variance': float(overall_variance),
                    'variance_pct': overall_variance_pct
                },
                'by_year': year_results,
                'status_counts': {
                    'excellent': excellent,
                    'good': good,
                    'acceptable': acceptable,
                    'review_needed': needs_review,
                    'no_data': no_data
                }
            }

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.stdout.write(self.style.SUCCESS(f"\nReport saved to: {output_path}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            driver.quit()

    def _setup_driver(self):
        """Set up headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def _scrape_year(self, driver, year):
        """Scrape IE data for a specific year from SeeTheMoney"""
        candidates = defaultdict(lambda: {'ie_for': Decimal('0'), 'ie_against': Decimal('0')})

        try:
            # Load page
            driver.get('https://seethemoney.az.gov')
            time.sleep(3)

            # Click IE tab
            driver.execute_script("document.querySelector('li[page=\"5\"] a').click()")
            time.sleep(3)

            # Set year filters
            try:
                start_selects = driver.find_elements(By.CSS_SELECTOR, "select.StartFilter.years")
                if start_selects:
                    Select(start_selects[0]).select_by_visible_text(year)
                    time.sleep(1)
            except:
                pass

            try:
                end_selects = driver.find_elements(By.CSS_SELECTOR, "select.EndFilter.years")
                if end_selects:
                    Select(end_selects[0]).select_by_visible_text(year)
                    time.sleep(1)
            except:
                pass

            # Wait for data
            time.sleep(3)

            # Show 100 entries
            try:
                show_select = driver.find_element(By.NAME, "IndependentExpenditureInformationTable_length")
                Select(show_select).select_by_visible_text("100")
                time.sleep(3)
            except:
                pass

            # Extract data with pagination
            page_num = 1
            max_pages = 50

            while page_num <= max_pages:
                try:
                    table = driver.find_element(By.ID, "IndependentExpenditureInformationTable")
                    rows = table.find_elements(By.TAG_NAME, "tr")

                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            name = cells[0].text.strip()
                            ie_for = self._parse_amount(cells[1].text)
                            ie_against = self._parse_amount(cells[2].text)

                            if name and name != 'Affected Candidate Committee':
                                candidates[name]['ie_for'] += ie_for
                                candidates[name]['ie_against'] += ie_against

                except:
                    break

                # Try next page
                try:
                    next_btns = driver.find_elements(By.CSS_SELECTOR, "#IndependentExpenditureInformation .paginate_button.next:not(.disabled)")
                    if next_btns and 'disabled' not in next_btns[0].get_attribute('class'):
                        next_btns[0].click()
                        time.sleep(2)
                        page_num += 1
                    else:
                        break
                except:
                    break

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Scraping error for {year}: {e}"))

        return dict(candidates)

    def _get_az_sunshine_data(self, year):
        """Get IE data from Az-Sunshine database for a year"""
        candidates = defaultdict(lambda: {'ie_for': Decimal('0'), 'ie_against': Decimal('0')})

        try:
            cycle = Cycle.objects.get(name=year)
        except Cycle.DoesNotExist:
            return dict(candidates)

        data = Transaction.objects.filter(
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

        for row in data:
            name = f"{row['subject_committee__name__first_name'] or ''} {row['subject_committee__name__last_name'] or ''}".strip()
            if name:
                candidates[name]['ie_for'] = row['ie_for'] or Decimal('0')
                candidates[name]['ie_against'] = row['ie_against'] or Decimal('0')

        return dict(candidates)

    def _parse_amount(self, text):
        """Parse dollar amount"""
        try:
            clean = re.sub(r'[^\d.]', '', text)
            return Decimal(clean) if clean else Decimal('0')
        except:
            return Decimal('0')
