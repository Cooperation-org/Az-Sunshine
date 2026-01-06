"""
Django management command to scrape county and city election data

Scrapes candidate and campaign finance data from:
- Maricopa County
- Pima County
- City of Tucson

Usage:
    # Scrape all counties
    python manage.py scrape_counties

    # Scrape specific county
    python manage.py scrape_counties --county maricopa
    python manage.py scrape_counties --county pima
    python manage.py scrape_counties --county tucson

    # Scrape specific year
    python manage.py scrape_counties --year 2024

    # Show browser (for debugging)
    python manage.py scrape_counties --no-headless
"""

from django.core.management.base import BaseCommand, CommandError
from transparency.services.maricopa_scraper import MaricopaScraper
from transparency.services.pima_scraper import PimaScraper
from transparency.services.tucson_scraper import TucsonScraper
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape county and city election data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--county',
            type=str,
            choices=['maricopa', 'pima', 'tucson', 'all'],
            default='all',
            help='County to scrape (default: all)'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Year to scrape (default: current year)'
        )
        parser.add_argument(
            '--no-headless',
            action='store_true',
            help='Show browser (useful for debugging)'
        )
        parser.add_argument(
            '--no-save',
            action='store_true',
            help='Do not save to CSV files'
        )

    def handle(self, *args, **options):
        county = options['county']
        year = options.get('year') or datetime.now().year
        headless = not options['no_headless']
        save_to_csv = not options['no_save']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('ARIZONA COUNTY ELECTION SCRAPER'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Year: {year}')
        self.stdout.write(f'Headless: {headless}')
        self.stdout.write(f'Save CSV: {save_to_csv}')
        self.stdout.write('')

        scrapers = self._get_scrapers(county, headless)
        results = {}

        for scraper_name, scraper in scrapers.items():
            self.stdout.write(f'\n📍 SCRAPING {scraper_name.upper()}')
            self.stdout.write('-' * 70)

            try:
                result = scraper.scrape(year=year, save_to_csv=save_to_csv)
                results[scraper_name] = result

                # Print summary
                self.stdout.write(self.style.SUCCESS(
                    f"{scraper_name}: "
                    f"{len(result['candidates'])} candidates, "
                    f"{len(result['filings'])} filings"
                ))

                if result['errors']:
                    self.stdout.write(self.style.WARNING(
                        f" {len(result['errors'])} errors encountered"
                    ))
                    for error in result['errors'][:3]:  # Show first 3 errors
                        self.stdout.write(f"   - {error}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"{scraper_name} failed: {str(e)}"
                ))
                logger.error(f"Scraping {scraper_name} failed", exc_info=True)
                results[scraper_name] = {'error': str(e)}

        # Final summary
        self._print_summary(results)

    def _get_scrapers(self, county, headless):
        """Get scrapers to run based on county selection"""
        all_scrapers = {
            'maricopa': MaricopaScraper(headless=headless),
            'pima': PimaScraper(headless=headless),
            'tucson': TucsonScraper(headless=headless),
        }

        if county == 'all':
            return all_scrapers
        else:
            return {county: all_scrapers[county]}

    def _print_summary(self, results):
        """Print final summary of all scraping"""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('SCRAPING COMPLETE'))
        self.stdout.write('=' * 70)

        total_candidates = 0
        total_filings = 0
        total_errors = 0

        for county, result in results.items():
            if 'error' in result:
                self.stdout.write(f"{county}: FAILED")
            else:
                candidates = len(result.get('candidates', []))
                filings = len(result.get('filings', []))
                errors = len(result.get('errors', []))

                total_candidates += candidates
                total_filings += filings
                total_errors += errors

                self.stdout.write(
                    f"{county}: {candidates} candidates, {filings} filings"
                )

        self.stdout.write('')
        self.stdout.write(f"Total candidates: {total_candidates}")
        self.stdout.write(f"Total filings: {total_filings}")

        if total_errors > 0:
            self.stdout.write(self.style.WARNING(f"Total errors: {total_errors}"))

        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  - Review CSV files in backend/data/county_data/')
        self.stdout.write('  - Import data to database if needed')
        self.stdout.write('  - Update selectors if scraping failed')
        self.stdout.write('=' * 70)
