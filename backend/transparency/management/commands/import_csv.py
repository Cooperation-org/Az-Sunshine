"""
Django management command to import campaign finance data from CSV files
with duplicate detection and data provenance tracking.

Usage:
    python manage.py import_csv path/to/file.csv --source "AZ SOS Q1 2024"
    python manage.py import_csv path/to/file.csv --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from transparency.models import (
    Committee, Entity, Transaction, TransactionType,
    EntityType, County, Party, Office, Cycle, ExpenseCategory
)
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
from pathlib import Path


class Command(BaseCommand):
    help = 'Import campaign finance data from CSV with duplicate detection'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--source',
            type=str,
            default='manual_import',
            help='Source identifier for data provenance tracking'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview import without committing to database'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        source = options['source']
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        # Validate file exists
        if not Path(csv_file).exists():
            raise CommandError(f'CSV file does not exist: {csv_file}')

        self.stdout.write(self.style.WARNING(
            f'Starting import from: {csv_file}'
        ))
        self.stdout.write(f'Source: {source}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate CSV headers
                self._validate_headers(reader.fieldnames)

                batch = []
                row_num = 0

                with transaction.atomic():
                    for row in reader:
                        row_num += 1

                        try:
                            result = self._process_row(row, source)
                            stats[result] += 1

                            # Progress indicator
                            if row_num % 100 == 0:
                                self.stdout.write(f'Processed {row_num} rows...', ending='\r')

                        except Exception as e:
                            stats['errors'] += 1
                            error_msg = f"Row {row_num}: {str(e)}"
                            stats['error_details'].append(error_msg)

                            if stats['errors'] <= 10:  # Only show first 10 errors
                                self.stdout.write(
                                    self.style.ERROR(error_msg)
                                )

                    if dry_run:
                        transaction.set_rollback(True)
                        self.stdout.write(
                            self.style.WARNING('\nDRY RUN - Rolling back all changes')
                        )

        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')

        # Print summary
        self._print_summary(stats, row_num)

    def _validate_headers(self, headers):
        """Validate that CSV has required columns"""
        required = [
            'committee_id', 'transaction_type_id', 'transaction_date',
            'amount', 'entity_id', 'transaction_id'
        ]

        missing = [h for h in required if h not in headers]
        if missing:
            raise CommandError(
                f'Missing required columns: {", ".join(missing)}'
            )

    def _process_row(self, row, source):
        """
        Process a single CSV row and create/update transaction.
        Returns: 'created', 'updated', or 'skipped'
        """
        # Generate natural key hash for duplicate detection
        record_hash = self._generate_record_hash(row)

        # Check if transaction already exists
        try:
            existing_txn = Transaction.objects.get(transaction_id=int(row['transaction_id']))

            # Check if data has changed using hash
            current_hash = self._generate_record_hash({
                'committee_id': existing_txn.committee_id,
                'transaction_type_id': existing_txn.transaction_type_id,
                'transaction_date': existing_txn.transaction_date.strftime('%Y-%m-%d'),
                'amount': str(existing_txn.amount),
                'entity_id': existing_txn.entity_id,
            })

            if current_hash == record_hash:
                return 'skipped'  # No changes
            else:
                # Update existing transaction
                self._update_transaction(existing_txn, row, source)
                return 'updated'

        except Transaction.DoesNotExist:
            # Create new transaction
            self._create_transaction(row, source, record_hash)
            return 'created'

    def _generate_record_hash(self, row):
        """
        Generate SHA256 hash from transaction natural key.
        Natural key: committee_id + transaction_date + amount + entity_id
        """
        natural_key = (
            f"{row['committee_id']}|"
            f"{row['transaction_date']}|"
            f"{row['amount']}|"
            f"{row['entity_id']}"
        )
        return hashlib.sha256(natural_key.encode()).hexdigest()

    def _create_transaction(self, row, source, record_hash):
        """Create new transaction from CSV row"""
        Transaction.objects.create(
            transaction_id=int(row['transaction_id']),
            committee_id=int(row['committee_id']),
            transaction_type_id=int(row['transaction_type_id']),
            transaction_date=self._parse_date(row['transaction_date']),
            amount=Decimal(row['amount']),
            entity_id=int(row['entity_id']),
            subject_committee_id=self._get_int_or_none(row.get('subject_committee_id')),
            is_for_benefit=self._get_bool_or_none(row.get('is_for_benefit')),
            category_id=self._get_int_or_none(row.get('category_id')),
            memo=row.get('memo', ''),
            account_type=row.get('account_type', ''),
            deleted=row.get('deleted', '0') == '1',
            # Note: record_hash and source fields need to be added to model
        )

    def _update_transaction(self, transaction, row, source):
        """Update existing transaction with new data"""
        transaction.amount = Decimal(row['amount'])
        transaction.transaction_date = self._parse_date(row['transaction_date'])
        transaction.memo = row.get('memo', '')
        transaction.deleted = row.get('deleted', '0') == '1'
        transaction.save()

    def _parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str:
            return None

        # Try common date formats
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%m-%d-%Y']

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(f'Unable to parse date: {date_str}')

    def _get_int_or_none(self, value):
        """Convert value to int or None"""
        if not value or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _get_bool_or_none(self, value):
        """Convert value to bool or None"""
        if value is None or value == '':
            return None
        if isinstance(value, bool):
            return value
        if str(value).lower() in ('true', '1', 't', 'yes'):
            return True
        if str(value).lower() in ('false', '0', 'f', 'no'):
            return False
        return None

    def _print_summary(self, stats, total_rows):
        """Print import summary statistics"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('IMPORT COMPLETE'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total rows processed: {total_rows}')
        self.stdout.write(self.style.SUCCESS(f'  Created:  {stats["created"]}'))
        self.stdout.write(self.style.WARNING(f'  Updated:  {stats["updated"]}'))
        self.stdout.write(f'  Skipped:  {stats["skipped"]} (no changes)')

        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'  Errors:   {stats["errors"]}'))

            if stats['error_details']:
                self.stdout.write('\nFirst errors:')
                for error in stats['error_details'][:10]:
                    self.stdout.write(self.style.ERROR(f'  - {error}'))

                if stats['errors'] > 10:
                    self.stdout.write(f'  ... and {stats["errors"] - 10} more errors')

        success_rate = ((stats['created'] + stats['updated'] + stats['skipped']) / total_rows * 100) if total_rows > 0 else 0
        self.stdout.write(f'\nSuccess rate: {success_rate:.1f}%')
        self.stdout.write('=' * 60)
