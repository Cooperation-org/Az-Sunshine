"""
Management command to download FREE campaign finance data from SeeTheMoney.az.gov

Usage:
    python manage.py download_seethemoney --year 2024
    python manage.py download_seethemoney --year 2024 --entity-type PAC
    python manage.py download_seethemoney --year 2024 --import
"""

from django.core.management.base import BaseCommand
from transparency.services.seethemoney_scraper import download_seethemoney_data
import subprocess
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Download FREE campaign finance data from SeeTheMoney.az.gov'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=None,
            help='Year to download (default: current year)'
        )
        parser.add_argument(
            '--entity-type',
            type=str,
            default='Candidate',
            choices=['Candidate', 'PAC', 'Party', 'All'],
            help='Type of entity to download'
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            default=True,
            help='Run browser in headless mode (default: True)'
        )
        parser.add_argument(
            '--no-headless',
            action='store_false',
            dest='headless',
            help='Run browser with UI visible'
        )
        parser.add_argument(
            '--import',
            action='store_true',
            dest='auto_import',
            help='Automatically import CSV to database after download'
        )

    def handle(self, *args, **options):
        year = options['year']
        entity_type = options['entity_type']
        headless = options['headless']
        auto_import = options['auto_import']

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*70}\n"
            f"SEETHEMONEY.AZ.GOV - FREE CAMPAIGN FINANCE DATA\n"
            f"{'='*70}\n"
        ))

        self.stdout.write(f"Year: {year or 'current'}")
        self.stdout.write(f"Entity Type: {entity_type}")
        self.stdout.write(f"Headless: {headless}")
        self.stdout.write("")

        try:
            # Download data
            self.stdout.write(self.style.WARNING("Downloading data from SeeTheMoney..."))

            csv_path = download_seethemoney_data(
                year=year,
                entity_type=entity_type,
                headless=headless
            )

            self.stdout.write(self.style.SUCCESS(
                f"\nDownload completed successfully!\n"
                f"   File: {csv_path}\n"
            ))

            # Auto-import if requested
            if auto_import:
                # STEP 1: Transform SeeTheMoney CSV to importable format
                self.stdout.write(self.style.WARNING("\nTransforming CSV format..."))

                transform_result = subprocess.run(
                    [
                        'python', 'manage.py', 'transform_seethemoney',
                        str(csv_path),
                    ],
                    capture_output=True,
                    text=True
                )

                if transform_result.returncode != 0:
                    self.stdout.write(self.style.ERROR("\nTransform failed:"))
                    self.stdout.write(transform_result.stderr)
                    return

                # The transformed file has _transformed suffix
                from pathlib import Path
                transformed_path = Path(csv_path).with_stem(f"{Path(csv_path).stem}_transformed")

                self.stdout.write(self.style.SUCCESS(f"Transformed: {transformed_path.name}"))

                # STEP 2: Import transformed CSV
                self.stdout.write(self.style.WARNING("\nImporting CSV to database..."))

                import_result = subprocess.run(
                    [
                        'python', 'manage.py', 'import_csv',
                        str(transformed_path),
                        '--source', f'SeeTheMoney {entity_type} {year or "current"}',
                    ],
                    capture_output=True,
                    text=True
                )

                if import_result.returncode == 0:
                    self.stdout.write(self.style.SUCCESS("\nImport completed!"))
                    self.stdout.write(import_result.stdout)
                else:
                    self.stdout.write(self.style.ERROR("\nImport failed:"))
                    self.stdout.write(import_result.stderr)

            if not auto_import:
                year_str = year if year else "current"
                self.stdout.write(self.style.SUCCESS(
                    f"\n{'='*70}\n"
                    f"NEXT STEPS:\n"
                    f"{'='*70}\n"
                    f"1. Review CSV file: {csv_path}\n"
                    f"2. Import to database:\n"
                    f"   python manage.py transform_seethemoney {csv_path}\n"
                    f"   python manage.py import_csv {csv_path.replace('.csv', '_transformed.csv')}\n"
                    f"      --source 'SeeTheMoney {entity_type} {year_str}'\n"
                    f"\n"
                    f"Or use the Data Import Dashboard in the frontend!\n"
                    f"{'='*70}\n"
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nError: {str(e)}"))
            logger.error(f"SeeTheMoney download failed: {str(e)}", exc_info=True)
            return

        self.stdout.write(self.style.SUCCESS("Done!"))
