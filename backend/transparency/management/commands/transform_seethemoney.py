"""
Transform SeeTheMoney CSV to format expected by import_csv command

QUICK FIX to get data importing NOW.
Later we'll implement proper staging/ETL architecture.

Usage:
    python manage.py transform_seethemoney path/to/seethemoney.csv
"""

from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
import csv
import hashlib
from datetime import datetime


class Command(BaseCommand):
    help = 'Transform SeeTheMoney CSV to importable format'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to SeeTheMoney CSV')

    def handle(self, *args, **options):
        input_path = Path(options['csv_file'])

        if not input_path.exists():
            raise CommandError(f'File not found: {input_path}')

        # Output to same directory with _transformed suffix
        output_path = input_path.with_stem(f"{input_path.stem}_transformed")

        self.stdout.write(f'\nTransforming: {input_path.name}')
        self.stdout.write(f'Output: {output_path.name}\n')

        stats = {'processed': 0, 'skipped': 0, 'errors': 0}

        with open(input_path, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)

            # Check for SeeTheMoney columns
            required_cols = ['TransactionDate', 'Amount']
            if not all(col in reader.fieldnames for col in required_cols):
                raise CommandError(
                    f'Not a SeeTheMoney CSV. Missing columns: {required_cols}'
                )

            with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
                # Write header for import_csv format
                fieldnames = [
                    'transaction_id', 'committee_id', 'transaction_type_id',
                    'transaction_date', 'amount', 'entity_id',
                    'filer_name', 'transaction_name', 'transaction_type_name',
                    'occupation', 'employer', 'city', 'state', 'zip_code'
                ]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                for row_num, row in enumerate(reader, start=1):
                    try:
                        # Generate IDs from data (consistent hash-based IDs)
                        tx_id = self._hash_to_int(
                            f"{row.get('TransactionDate', '')}"
                            f"{row.get('FilerName', '')}"
                            f"{row.get('TransactionName', '')}"
                            f"{row.get('Amount', '')}"
                        )

                        committee_id = self._hash_to_int(row.get('FilerName', 'Unknown'))
                        entity_id = self._hash_to_int(row.get('TransactionName', 'Unknown'))
                        tx_type_id = self._hash_to_int(row.get('TransactionType', 'Unknown'))

                        # Parse date
                        date_str = row.get('TransactionDate', '')
                        tx_date = self._parse_date(date_str)

                        # Parse amount
                        amount = row.get('Amount', '0').replace(',', '')

                        # Write transformed row
                        writer.writerow({
                            'transaction_id': tx_id,
                            'committee_id': committee_id,
                            'transaction_type_id': tx_type_id,
                            'transaction_date': tx_date,
                            'amount': amount,
                            'entity_id': entity_id,

                            # Keep original for reference
                            'filer_name': row.get('FilerName', ''),
                            'transaction_name': row.get('TransactionName', ''),
                            'transaction_type_name': row.get('TransactionType', ''),
                            'occupation': row.get('Occupation', ''),
                            'employer': row.get('Employer', ''),
                            'city': row.get('City', ''),
                            'state': row.get('State', ''),
                            'zip_code': row.get('ZipCode', ''),
                        })

                        stats['processed'] += 1

                        if stats['processed'] % 10000 == 0:
                            self.stdout.write(
                                f"Processed {stats['processed']:,} rows...",
                                ending='\r'
                            )

                    except Exception as e:
                        stats['errors'] += 1
                        if stats['errors'] <= 10:
                            self.stdout.write(
                                self.style.ERROR(f"Row {row_num}: {str(e)}")
                            )

        self.stdout.write(f'\n\n✅ Transformation complete:')
        self.stdout.write(f'  Processed: {stats["processed"]:,}')
        self.stdout.write(f'  Errors: {stats["errors"]:,}')
        self.stdout.write(f'\n📄 Output file: {output_path}')
        self.stdout.write(f'\n💡 Next step: python manage.py import_csv {output_path} --source "SeeTheMoney 2016 Q1"\n')

    def _hash_to_int(self, value: str) -> int:
        """Generate consistent integer ID from string"""
        if not value:
            value = "Unknown"
        # Get first 8 chars of hex hash and convert to int
        hash_hex = hashlib.md5(value.encode()).hexdigest()[:8]
        return int(hash_hex, 16) % 2147483647  # Keep within PostgreSQL INT range

    def _parse_date(self, date_str: str) -> str:
        """Parse SeeTheMoney date to YYYY-MM-DD format"""
        if not date_str:
            return '2016-01-01'  # Default

        formats = [
            '%m/%d/%Y %I:%M:%S %p',  # 11/8/2016 12:00:00 AM
            '%m/%d/%Y',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return '2016-01-01'  # Default fallback
