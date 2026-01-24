"""
Import FEC independent expenditure data for Arizona Senate 2020 race.
Mark Kelly vs Martha McSally - the most expensive Senate race in AZ history.
"""
from django.core.management.base import BaseCommand
from transparency.models import FECIndependentExpenditure
from django.db import transaction
from datetime import datetime
from decimal import Decimal
import csv


class Command(BaseCommand):
    help = 'Import FEC 2020 independent expenditure data for AZ Senate race (Kelly vs McSally)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/opt/az_sunshine/data/fec_bulk/independent_expenditure_2019_2020.csv',
            help='Path to the FEC bulk CSV file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without saving'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING('Importing AZ Senate 2020 FEC Data...'))
        self.stdout.write(f'Source file: {file_path}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no data will be saved'))

        # Track statistics
        stats = {
            'kelly_records': 0,
            'mcsally_records': 0,
            'kelly_total': Decimal('0'),
            'mcsally_total': Decimal('0'),
            'skipped_duplicates': 0,
            'errors': 0,
        }

        records_to_create = []
        # Get existing file IDs (primary key)
        existing_file_ids = set(
            FECIndependentExpenditure.objects.filter(cycle=2020).values_list('fec_file_id', flat=True)
        )

        self.stdout.write(f'Existing 2020 file IDs in DB: {len(existing_file_ids)}')

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    cand_name = row.get('cand_name', '').upper()
                    state = row.get('can_office_state', '').upper()
                    office = row.get('can_office', '').upper()

                    # Filter for AZ Senate candidates
                    is_kelly = 'KELLY' in cand_name and 'MARK' in cand_name and state == 'AZ'
                    is_mcsally = 'MCSALLY' in cand_name and state == 'AZ'

                    # Also check for Kelly for Senate committee entries
                    spe_nam = row.get('spe_nam', '').upper()
                    if 'MARK KELLY' in spe_nam and 'SENATE' in spe_nam:
                        is_kelly = True

                    if not (is_kelly or is_mcsally):
                        continue

                    # Create unique file ID (primary key) from file_num + transaction_id
                    file_num = row.get('file_num', '')
                    trans_id = row.get('tran_id', '')
                    if trans_id:
                        unique_file_id = f"{file_num}-{trans_id}"[:50]
                    else:
                        unique_file_id = f"FEC2020-{file_num}-{stats['kelly_records'] + stats['mcsally_records']}"[:50]

                    # Skip duplicates
                    if unique_file_id in existing_file_ids:
                        stats['skipped_duplicates'] += 1
                        continue

                    # Parse amount
                    try:
                        amount = Decimal(row.get('exp_amo', '0').replace(',', ''))
                    except:
                        amount = Decimal('0')

                    if amount == 0:
                        continue

                    # Parse date
                    exp_date = None
                    date_str = row.get('exp_date', '')
                    if date_str:
                        try:
                            exp_date = datetime.strptime(date_str, '%d-%b-%y').date()
                        except:
                            try:
                                exp_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except:
                                pass

                    # Determine support/oppose
                    sup_opp = row.get('sup_opp', 'S').upper()
                    is_support = sup_opp == 'S'

                    # Parse candidate name
                    cand_name_parts = row.get('cand_name', '').split(',')
                    last_name = cand_name_parts[0].strip() if cand_name_parts else ''
                    first_name = cand_name_parts[1].strip() if len(cand_name_parts) > 1 else ''

                    # Create record
                    record = FECIndependentExpenditure(
                        fec_file_id=unique_file_id,
                        transaction_id=trans_id[:100] if trans_id else '',
                        committee_id=row.get('spe_id', '')[:20],
                        committee_name=row.get('spe_nam', '')[:255],
                        candidate_id=row.get('cand_id', '')[:20],
                        candidate_name=row.get('cand_name', '')[:255],
                        candidate_first_name=first_name[:100],
                        candidate_last_name=last_name[:100],
                        candidate_office='S',
                        candidate_office_district='00',
                        candidate_party=row.get('cand_pty_aff', '')[:10],
                        amount=amount,
                        expenditure_date=exp_date,
                        expenditure_description=row.get('pur', '')[:500],
                        payee_name=row.get('pay', '')[:255],
                        is_support=is_support,
                        filing_date=None,
                        cycle=2020,
                        race='AZ-SEN',
                    )

                    records_to_create.append(record)
                    existing_file_ids.add(unique_file_id)

                    if is_kelly:
                        stats['kelly_records'] += 1
                        stats['kelly_total'] += abs(amount)
                    else:
                        stats['mcsally_records'] += 1
                        stats['mcsally_total'] += abs(amount)

                except Exception as e:
                    stats['errors'] += 1
                    if stats['errors'] <= 5:
                        self.stdout.write(self.style.WARNING(f'Error processing row: {e}'))

        # Summary before save
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== IMPORT SUMMARY ==='))
        self.stdout.write(f'Mark Kelly records: {stats["kelly_records"]:,}')
        self.stdout.write(f'Mark Kelly total: ${stats["kelly_total"]:,.2f}')
        self.stdout.write(f'Martha McSally records: {stats["mcsally_records"]:,}')
        self.stdout.write(f'Martha McSally total: ${stats["mcsally_total"]:,.2f}')
        self.stdout.write(f'Skipped duplicates: {stats["skipped_duplicates"]:,}')
        self.stdout.write(f'Errors: {stats["errors"]:,}')
        self.stdout.write(f'Total to import: {len(records_to_create):,}')

        if not dry_run and records_to_create:
            self.stdout.write('')
            self.stdout.write('Saving to database...')
            with transaction.atomic():
                FECIndependentExpenditure.objects.bulk_create(
                    records_to_create,
                    batch_size=500,
                    ignore_conflicts=True
                )
            self.stdout.write(self.style.SUCCESS(f'Imported {len(records_to_create):,} records'))
        elif dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN complete - no data saved'))
        else:
            self.stdout.write('No new records to import')

        # Show top spenders
        self.stdout.write('')
        self.stdout.write('Top spending committees (from import):')
        committee_totals = {}
        for r in records_to_create:
            name = r.committee_name
            committee_totals[name] = committee_totals.get(name, Decimal('0')) + abs(r.amount)

        for name, total in sorted(committee_totals.items(), key=lambda x: x[1], reverse=True)[:15]:
            self.stdout.write(f'  {name[:50]}: ${total:,.2f}')
