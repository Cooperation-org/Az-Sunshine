"""
Management command to load FEC Independent Expenditure data from JSON staging files.

Usage:
    python manage.py load_fec_staging
    python manage.py load_fec_staging --file /path/to/custom/file.json
"""

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from transparency.models import FECIndependentExpenditure


class Command(BaseCommand):
    help = 'Load FEC Independent Expenditure data from JSON staging file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/opt/az_sunshine/data/fec_staging/fec_ie_data_20260124_025013.json',
            help='Path to the JSON file to import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview import without saving to database'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        self.stdout.write(f"Loading FEC data from: {file_path}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}")

        # Extract metadata
        source = data.get('source', 'Unknown')
        fetched_at = data.get('fetched_at', 'Unknown')
        record_count = data.get('record_count', 0)
        expenditures = data.get('expenditures', [])

        self.stdout.write(f"Source: {source}")
        self.stdout.write(f"Fetched at: {fetched_at}")
        self.stdout.write(f"Records in file: {record_count}")
        self.stdout.write(f"Expenditures to process: {len(expenditures)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No data will be saved"))

        created_count = 0
        updated_count = 0
        error_count = 0

        for i, exp in enumerate(expenditures, 1):
            try:
                # Parse dates
                expenditure_date = self._parse_date(exp.get('expenditure_date'))
                filing_date = self._parse_date(exp.get('filing_date'))

                # Parse amount
                try:
                    amount = Decimal(str(exp.get('amount', 0)))
                except (InvalidOperation, ValueError):
                    amount = Decimal('0.00')

                # Prepare data
                fec_file_id = str(exp.get('fec_file_id', ''))
                if not fec_file_id:
                    self.stdout.write(
                        self.style.WARNING(f"Skipping record {i}: missing fec_file_id")
                    )
                    error_count += 1
                    continue

                record_data = {
                    'transaction_id': str(exp.get('transaction_id', '')),
                    'committee_id': str(exp.get('committee_id', '')),
                    'committee_name': str(exp.get('committee_name', ''))[:255],
                    'amount': amount,
                    'is_support': bool(exp.get('is_support', False)),
                    'candidate_id': str(exp.get('candidate_id', '')),
                    'candidate_name': str(exp.get('candidate_name', ''))[:255],
                    'candidate_first_name': str(exp.get('candidate_first_name', ''))[:100],
                    'candidate_last_name': str(exp.get('candidate_last_name', ''))[:100],
                    'candidate_party': str(exp.get('candidate_party', ''))[:10],
                    'candidate_office': str(exp.get('candidate_office', ''))[:10],
                    'candidate_office_district': exp.get('candidate_office_district') or None,
                    'race': str(exp.get('race', ''))[:20],
                    'cycle': int(exp.get('cycle', 0)),
                    'expenditure_date': expenditure_date,
                    'filing_date': filing_date,
                    'expenditure_description': str(exp.get('expenditure_description', '')),
                    'payee_name': str(exp.get('payee_name', ''))[:255],
                }

                if not dry_run:
                    obj, created = FECIndependentExpenditure.objects.update_or_create(
                        fec_file_id=fec_file_id,
                        defaults=record_data
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                else:
                    # In dry run, just count as if we'd create
                    created_count += 1

                # Progress output every 100 records
                if i % 100 == 0:
                    self.stdout.write(f"Processed {i}/{len(expenditures)} records...")

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error processing record {i}: {e}")
                )

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Import Summary"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"Total processed: {len(expenditures)}")
        self.stdout.write(self.style.SUCCESS(f"Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
        if error_count:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN COMPLETE - No data was saved"))

    def _parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            # Try ISO format first (YYYY-MM-DD)
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Try alternative formats
                return datetime.strptime(date_str, '%m/%d/%Y').date()
            except ValueError:
                return None
