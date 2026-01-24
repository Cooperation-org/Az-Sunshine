"""
Import FEC independent expenditure data from bulk CSV download for Arizona CD-2 2018 race.

This command reads the FEC bulk data CSV file and imports AZ-02 (CD-2) 2018 records
into the FECIndependentExpenditure model.

Usage:
    python manage.py import_fec_bulk_az02
    python manage.py import_fec_bulk_az02 --dry-run
    python manage.py import_fec_bulk_az02 --csv /path/to/custom/file.csv
"""

import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime
from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from transparency.models import FECIndependentExpenditure


class Command(BaseCommand):
    help = 'Import FEC bulk independent expenditure data for Arizona CD-2 2018 race'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default='/opt/az_sunshine/data/fec_bulk/independent_expenditure_2017_2018.csv',
            help='Path to the FEC bulk CSV file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview data without saving to database'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each expenditure'
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)

        self.stdout.write(
            '\n' + '=' * 70 + '\n' +
            '  FEC BULK DATA IMPORTER\n' +
            '  Arizona Congressional District 2 (CD-2) - 2018 Race\n' +
            '=' * 70 + '\n'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved\n'))

        self.stdout.write(f'Reading CSV file: {csv_path}\n')

        # Read and filter AZ-02 records
        try:
            az02_records = self._read_az02_records(csv_path)
        except FileNotFoundError:
            raise CommandError(f"CSV file not found: {csv_path}")
        except Exception as e:
            raise CommandError(f"Error reading CSV file: {e}")

        self.stdout.write(f'Total AZ-02 2018 records found: {len(az02_records)}\n')

        if not az02_records:
            self.stdout.write(self.style.WARNING('No AZ-02 2018 records found'))
            return

        # Display summary
        self._display_summary(az02_records)

        # Save to database (unless dry run)
        if not dry_run:
            self._save_to_database(az02_records, verbose)
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN complete. {len(az02_records)} expenditures would be saved.'
            ))

    def _read_az02_records(self, csv_path):
        """Read CSV file and filter for Arizona CD-2 records"""
        az02_records = []

        with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter for Arizona CD-2 House races
                state = row.get('can_office_state', '').strip()
                district = row.get('can_office_dis', '').strip()
                office = row.get('can_office', '').strip()

                if state == 'AZ' and district == '02' and office == 'H':
                    az02_records.append(row)

        return az02_records

    def _display_summary(self, records):
        """Display summary of expenditures"""
        self.stdout.write('=' * 70)
        self.stdout.write('  SUMMARY: AZ-02 (CD-2) 2018 Independent Expenditures')
        self.stdout.write('=' * 70)

        total_amount = Decimal('0')
        support_amount = Decimal('0')
        oppose_amount = Decimal('0')
        committee_totals = defaultdict(lambda: {'total': Decimal('0'), 'count': 0})
        candidate_totals = defaultdict(lambda: {'support': Decimal('0'), 'oppose': Decimal('0'), 'party': ''})

        for row in records:
            try:
                amount = Decimal(row.get('exp_amo', '0').replace(',', ''))
            except (InvalidOperation, ValueError):
                amount = Decimal('0')

            total_amount += amount

            sup_opp = row.get('sup_opp', '').strip()
            is_support = sup_opp == 'S'

            if is_support:
                support_amount += amount
            else:
                oppose_amount += amount

            comm_name = row.get('spe_nam', 'Unknown')
            committee_totals[comm_name]['total'] += amount
            committee_totals[comm_name]['count'] += 1

            cand_name = row.get('cand_name', 'Unknown')
            if is_support:
                candidate_totals[cand_name]['support'] += amount
            else:
                candidate_totals[cand_name]['oppose'] += amount
            candidate_totals[cand_name]['party'] = row.get('cand_pty_aff', '')

        self.stdout.write(f'\nTotal Expenditures: {len(records)}')
        self.stdout.write(f'Total Amount: ${total_amount:,.2f}')
        self.stdout.write(f'  Support: ${support_amount:,.2f}')
        self.stdout.write(f'  Oppose: ${oppose_amount:,.2f}')

        self.stdout.write('\nTOP SPENDING COMMITTEES:')
        sorted_comms = sorted(committee_totals.items(), key=lambda x: x[1]['total'], reverse=True)
        for i, (name, data) in enumerate(sorted_comms[:15], 1):
            self.stdout.write(
                f"  {i:2}. {name[:50]:50} ${data['total']:>12,.2f} ({data['count']} txns)"
            )

        self.stdout.write('\nBY CANDIDATE:')
        for cand, data in sorted(candidate_totals.items(),
                                  key=lambda x: x[1]['support'] + x[1]['oppose'],
                                  reverse=True)[:10]:
            net = data['support'] - data['oppose']
            net_str = f"+${net:,.2f}" if net >= 0 else f"-${abs(net):,.2f}"
            party = f"({data['party']})" if data['party'] else ""
            self.stdout.write(f"  {cand} {party}")
            self.stdout.write(f"    Support: ${data['support']:,.2f} | Oppose: ${data['oppose']:,.2f} | Net: {net_str}")

    def _save_to_database(self, records, verbose):
        """Save expenditures to the database"""
        self.stdout.write('\nSaving to database...')

        created_count = 0
        updated_count = 0
        error_count = 0

        for i, row in enumerate(records, 1):
            try:
                # Generate unique file ID
                file_num = row.get('file_num', '')
                tran_id = row.get('tran_id', '')
                image_num = row.get('image_num', '')

                if file_num and tran_id:
                    fec_file_id = f"{file_num}_{tran_id}"
                elif image_num:
                    fec_file_id = str(image_num)
                else:
                    # Fallback using committee + date + amount
                    fec_file_id = f"AZ02_2018_{row.get('spe_id', '')}_{row.get('exp_date', '')}_{row.get('exp_amo', '')}"

                # Parse amount
                try:
                    amount = Decimal(row.get('exp_amo', '0').replace(',', ''))
                except (InvalidOperation, ValueError):
                    amount = Decimal('0')

                # Parse dates
                expenditure_date = self._parse_date(row.get('exp_date'))
                filing_date = self._parse_date(row.get('receipt_dat'))

                # Support/Oppose
                sup_opp = row.get('sup_opp', '').strip()
                is_support = sup_opp == 'S'

                # Parse candidate name into first/last
                cand_name = row.get('cand_name', '')
                candidate_first_name = ''
                candidate_last_name = ''
                if ',' in cand_name:
                    parts = cand_name.split(',', 1)
                    candidate_last_name = parts[0].strip()
                    candidate_first_name = parts[1].strip() if len(parts) > 1 else ''
                else:
                    candidate_last_name = cand_name

                record_data = {
                    'transaction_id': str(tran_id)[:100],
                    'committee_id': str(row.get('spe_id', ''))[:20],
                    'committee_name': str(row.get('spe_nam', ''))[:255],
                    'amount': amount,
                    'is_support': is_support,
                    'candidate_id': str(row.get('cand_id', ''))[:20],
                    'candidate_name': cand_name[:255],
                    'candidate_first_name': candidate_first_name[:100],
                    'candidate_last_name': candidate_last_name[:100],
                    'candidate_party': str(row.get('cand_pty_aff', ''))[:10],
                    'candidate_office': str(row.get('can_office', ''))[:10],
                    'candidate_office_district': row.get('can_office_dis') or '02',
                    'race': 'AZ-02',
                    'cycle': 2018,
                    'expenditure_date': expenditure_date,
                    'filing_date': filing_date,
                    'expenditure_description': str(row.get('pur', ''))[:500],
                    'payee_name': str(row.get('pay', ''))[:255],
                }

                obj, created = FECIndependentExpenditure.objects.update_or_create(
                    fec_file_id=fec_file_id,
                    defaults=record_data
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                if verbose:
                    action = 'SUPPORT' if is_support else 'OPPOSE'
                    self.stdout.write(
                        f"  [{action}] ${amount:,.2f} - {row.get('spe_nam', '')[:40]} -> {cand_name}"
                    )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error saving record {i}: {e}")
                )

            # Progress output every 50 records
            if i % 50 == 0:
                self.stdout.write(f"Processed {i}/{len(records)} records...")

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Import Complete'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f"Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
        if error_count:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))

    def _parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str:
            return None

        # Try various date formats
        formats = [
            '%d-%b-%y',  # 18-OCT-18
            '%d-%b-%Y',  # 18-OCT-2018
            '%Y-%m-%d',  # 2018-10-18
            '%m/%d/%Y',  # 10/18/2018
            '%m/%d/%y',  # 10/18/18
        ]

        date_str = date_str.strip()
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None
