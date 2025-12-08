"""
Django management command to synchronize data from AZ Secretary of State

This command automates the entire workflow:
1. Download latest database from AZ SOS
2. Import data using CSV import command
3. Track sync history

Usage:
    # Download and import latest data
    python manage.py sync_sos_data

    # Download specific year/quarter
    python manage.py sync_sos_data --year 2024 --quarter 1

    # Download only (no import)
    python manage.py sync_sos_data --download-only

    # Import latest downloaded file
    python manage.py sync_sos_data --import-only
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from transparency.services.az_sos_scraper import AZSOSScraper, AZSOSDownloadError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Download and import campaign finance data from AZ Secretary of State'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Year to download (default: current year)'
        )
        parser.add_argument(
            '--quarter',
            type=int,
            choices=[1, 2, 3, 4],
            help='Quarter to download (1-4)'
        )
        parser.add_argument(
            '--download-only',
            action='store_true',
            help='Download only, skip import'
        )
        parser.add_argument(
            '--import-only',
            action='store_true',
            help='Import latest download, skip download step'
        )
        parser.add_argument(
            '--purchase',
            action='store_true',
            help='Complete purchase (requires payment on file)'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            default=True,
            help='Run browser in headless mode (default: True)'
        )
        parser.add_argument(
            '--no-headless',
            action='store_true',
            help='Show browser (useful for CAPTCHA solving)'
        )

    def handle(self, *args, **options):
        year = options.get('year')
        quarter = options.get('quarter')
        download_only = options['download_only']
        import_only = options['import_only']
        purchase = options['purchase']
        headless = not options['no_headless'] if options['no_headless'] else options['headless']

        if download_only and import_only:
            raise CommandError("Cannot use both --download-only and --import-only")

        self.stdout.write(self.style.SUCCESS(
            '=' * 70
        ))
        self.stdout.write(self.style.SUCCESS(
            'AZ SECRETARY OF STATE DATA SYNC'
        ))
        self.stdout.write(self.style.SUCCESS(
            '=' * 70
        ))

        csv_file = None

        # Step 1: Download (unless import-only)
        if not import_only:
            self.stdout.write('\n📥 STEP 1: DOWNLOADING FROM AZ SOS')
            self.stdout.write('-' * 70)

            if purchase:
                self.stdout.write(self.style.WARNING(
                    '⚠️  Purchase mode enabled ($25 will be charged)'
                ))
                confirm = input('Continue? (yes/no): ')
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.ERROR('Cancelled'))
                    return

            try:
                scraper = AZSOSScraper(headless=headless)

                self.stdout.write(f'Year: {year or "all"}')
                self.stdout.write(f'Quarter: {quarter or "all"}')
                self.stdout.write(f'Headless: {headless}')

                if not headless:
                    self.stdout.write(self.style.WARNING(
                        '\n⚠️  Browser will open. Solve any CAPTCHAs manually.'
                    ))

                csv_file = scraper.download_database(
                    year=year,
                    quarter=quarter,
                    purchase=purchase
                )

                self.stdout.write(self.style.SUCCESS(
                    f'✅ Download complete: {csv_file}'
                ))

            except AZSOSDownloadError as e:
                raise CommandError(f'Download failed: {str(e)}')
            except Exception as e:
                logger.error(f'Unexpected error during download: {str(e)}', exc_info=True)
                raise CommandError(f'Download failed: {str(e)}')

        # Step 2: Import (unless download-only)
        if not download_only:
            self.stdout.write('\n📊 STEP 2: IMPORTING DATA')
            self.stdout.write('-' * 70)

            # Get CSV file to import
            if import_only:
                # Use latest downloaded file
                scraper = AZSOSScraper()
                csv_file = scraper.get_latest_download()

                if not csv_file:
                    raise CommandError(
                        'No downloaded files found. Run without --import-only first.'
                    )

                self.stdout.write(f'Using latest download: {csv_file}')

            elif not csv_file:
                raise CommandError('No CSV file available for import')

            # Generate source identifier
            source = f"AZ_SOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if year:
                source += f"_Y{year}"
            if quarter:
                source += f"_Q{quarter}"

            # Call import_csv command
            try:
                self.stdout.write(f'Source: {source}')
                self.stdout.write('Starting import...\n')

                call_command(
                    'import_csv',
                    str(csv_file),
                    source=source,
                    verbosity=options.get('verbosity', 1)
                )

                self.stdout.write(self.style.SUCCESS(
                    '\n✅ Import complete'
                ))

            except Exception as e:
                logger.error(f'Import failed: {str(e)}', exc_info=True)
                raise CommandError(f'Import failed: {str(e)}')

        # Final summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ SYNC COMPLETE'))
        self.stdout.write('=' * 70)

        if csv_file:
            self.stdout.write(f'CSV File: {csv_file}')

        self.stdout.write('\nNext steps:')
        self.stdout.write('  - Review import statistics above')
        self.stdout.write('  - Check Django admin for new data')
        self.stdout.write('  - Run materialized view refresh if needed')
        self.stdout.write('    python manage.py refresh_dashboard_views')
