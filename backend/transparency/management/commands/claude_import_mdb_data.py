"""
Django management command that uses Claude to intelligently import MDB data
OPTIMIZED VERSION: Uses bulk operations for large tables with better error handling
FIXED: Handles missing committee references in transactions and null dates in reports
"""

from django.core.management.base import BaseCommand
import anthropic
import os
import csv
from decimal import Decimal
from datetime import datetime
import pytz
from django.conf import settings
from transparency.models import *
from django.db import transaction


class Command(BaseCommand):
    help = 'Import MDB data with Claude validation (optimized)'

    def __init__(self):
        super().__init__()
        self.claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.csv_dir = './transparency/utils/mdb_exports'
        self.test_mode = False
        self.test_limit = 100
        self.batch_size = 5000

    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', help='Test mode: only import 100 records per table')
        parser.add_argument('--csv-dir', type=str, default='/transparency/utils/mdb_exports', help='Directory containing exported CSV files')
        parser.add_argument('--batch-size', type=int, default=5000, help='Batch size for bulk operations (default: 5000)')
        parser.add_argument('--skip-claude', action='store_true', help='Skip Claude validation (faster for re-runs)')

    def handle(self, *args, **options):
        self.test_mode = options['test']
        self.csv_dir = options['csv_dir']
        self.batch_size = options['batch_size']
        skip_claude = options['skip_claude']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('CLAUDE-MANAGED MDB IMPORT (OPTIMIZED v3)'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if self.test_mode:
            self.stdout.write(self.style.WARNING(f'TEST MODE: Importing {self.test_limit} records per table'))

        import_sequence = [
            ('Counties', County, self.import_counties),
            ('Parties', Party, self.import_parties),
            ('Offices', Office, self.import_offices),
            ('Cycles', Cycle, self.import_cycles),
            ('EntityTypes', EntityType, self.import_entity_types),
            ('TransactionTypes', TransactionType, self.import_transaction_types),
            ('Categories', ExpenseCategory, self.import_categories),
            ('ReportTypes', ReportType, self.import_report_types),
            ('ReportNames', ReportName, self.import_report_names),
            ('BallotMeasures', BallotMeasure, self.import_ballot_measures_fixed),
            ('Names', Entity, self.import_entities_bulk),
            ('Committees', Committee, self.import_committees_bulk_fixed),
            ('Transactions', Transaction, self.import_transactions_bulk),
            ('Reports', Report, self.import_reports_bulk),
        ]

        for table_name, model, import_func in import_sequence:
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(self.style.SUCCESS(f'Importing: {table_name}'))
            self.stdout.write(f'{"=" * 60}')

            try:
                if not skip_claude:
                    validation = self.ask_claude_to_validate(table_name, model)
                    self.stdout.write(self.style.WARNING(f'Claude says: {validation[:200]}...'))

                count = import_func()

                if not skip_claude:
                    verification = self.ask_claude_to_verify(table_name, model, count)
                    self.stdout.write(self.style.SUCCESS(f'Claude verification: {verification}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'✓ Imported {count:,} records'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERROR importing {table_name}: {e}'))
                if not skip_claude:
                    help_text = self.ask_claude_for_help(table_name, str(e))
                    self.stdout.write(self.style.WARNING(f'Claude suggests: {help_text}'))
                raise

    def ask_claude_to_validate(self, table_name, model):
        prompt = f"""I'm about to import data from {table_name}.csv into Django model {model.__name__}.
Should I proceed? Any data quality issues I should watch for?
Give me a one-sentence validation check."""
        return self.ask_claude(prompt, max_tokens=150)

    def ask_claude_to_verify(self, table_name, model, count):
        sample = list(model.objects.all()[:3])
        prompt = f"""I just imported {count} records into {model.__name__}.
Sample records: {sample}
Does this look correct? Any red flags? One sentence verification."""
        return self.ask_claude(prompt, max_tokens=150)

    def ask_claude_for_help(self, table_name, error_message):
        prompt = f"""Import failed for {table_name} with error:
{error_message}
What's the likely cause and how do I fix it? Be specific."""
        return self.ask_claude(prompt, max_tokens=300)

    def ask_claude(self, prompt, max_tokens=1024):
        message = self.claude.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def read_csv(self, filename):
        filepath = os.path.join(self.csv_dir, filename)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if self.test_mode:
                rows = rows[:self.test_limit]
            return rows

    def parse_date(self, date_str):
        if not date_str or date_str.strip() == '':
            return None
        try:
            dt = datetime.strptime(date_str, '%m/%d/%y %H:%M:%S')
            if dt.year > 2050:
                dt = dt.replace(year=dt.year - 100)
            arizona_tz = pytz.timezone('America/Phoenix')
            dt = arizona_tz.localize(dt)
            return dt
        except:
            return None

    def parse_boolean(self, value):
        if value == '1':
            return True
        elif value == '0':
            return False
        return None

    def clean_empty_string(self, value):
        return None if value == '' else value

    def normalize_state(self, state_value):
        if not state_value or state_value.strip() == '':
            return ''

        state_value = state_value.strip().upper()
        if len(state_value) == 2:
            return state_value

        state_map = {
            'ARIZONA': 'AZ', 'CALIFORNIA': 'CA', 'TEXAS': 'TX',
            'NEW YORK': 'NY', 'FLORIDA': 'FL', 'ILLINOIS': 'IL',
            'PENNSYLVANIA': 'PA', 'OHIO': 'OH', 'GEORGIA': 'GA',
            'NORTH CAROLINA': 'NC', 'MICHIGAN': 'MI', 'NEW JERSEY': 'NJ',
            'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'MASSACHUSETTS': 'MA',
            'COLORADO': 'CO', 'NEVADA': 'NV', 'OREGON': 'OR',
            'UTAH': 'UT', 'NEW MEXICO': 'NM',
        }

        if state_value in state_map:
            return state_map[state_value]

        if len(state_value) > 2:
            return state_value[:2]

        return state_value

    def import_counties(self):
        rows = self.read_csv('Counties.csv')
        for row in rows:
            County.objects.update_or_create(
                county_id=int(row['CountyID']),
                defaults={'name': row['CountyName']}
            )
        return len(rows)

    def import_parties(self):
        rows = self.read_csv('Parties.csv')
        for row in rows:
            Party.objects.update_or_create(
                party_id=int(row['PartyID']),
                defaults={'name': row['PartyName']}
            )
        return len(rows)

    def import_offices(self):
        rows = self.read_csv('Offices.csv')
        for row in rows:
            Office.objects.update_or_create(
                office_id=int(row['OfficeID']),
                defaults={'name': row['OfficeName']}
            )
        return len(rows)

    def import_cycles(self):
        rows = self.read_csv('Cycles.csv')
        count = 0
        for row in rows:
            begin_date = self.parse_date(row['BeginDate'])
            end_date = self.parse_date(row['EndDate'])

            if not begin_date or not end_date:
                continue

            try:
                Cycle.objects.update_or_create(
                    cycle_id=int(row['CycleID']),
                    defaults={
                        'name': row['CycleName'],
                        'begin_date': begin_date,
                        'end_date': end_date,
                    }
                )
                count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing Cycle {row['CycleID']}: {e}"))
        return count

    def import_entity_types(self):
        rows = self.read_csv('EntityTypes.csv')
        for row in rows:
            EntityType.objects.update_or_create(
                entity_type_id=int(row['EntityTypeID']),
                defaults={'name': row['EntityTypeName']}
            )
        return len(rows)

    def import_transaction_types(self):
        rows = self.read_csv('TransactionTypes.csv')
        for row in rows:
            TransactionType.objects.update_or_create(
                transaction_type_id=int(row['TransactionTypeID']),
                defaults={
                    'name': row['TransactionTypeName'],
                    'income_expense_neutral': int(row['IncomeExpenseNeutralID']),
                }
            )
        return len(rows)

    def import_categories(self):
        rows = self.read_csv('Categories.csv')
        for row in rows:
            ExpenseCategory.objects.update_or_create(
                category_id=int(row['CategoryID']),
                defaults={'name': row['CategoryName']}
            )
        return len(rows)

    def import_report_types(self):
        rows = self.read_csv('ReportTypes.csv')
        for row in rows:
            ReportType.objects.update_or_create(
                report_type_id=int(row['ReportTypeID']),
                defaults={'name': row['ReportTypeName']}
            )
        return len(rows)

    def import_report_names(self):
        rows = self.read_csv('ReportNames.csv')
        for row in rows:
            ReportName.objects.update_or_create(
                report_name_id=int(row['ReportNameID']),
                defaults={'name': row['ReportName']}
            )
        return len(rows)

    def import_ballot_measures_fixed(self):
        rows = self.read_csv('BallotMeasures.csv')
        count = 0

        for row in rows:
            try:
                official_title = self.clean_empty_string(row['OfficialTitle'])
                if official_title is None:
                    official_title = row['ShortTitle']

                sos_identifier = row['SOSIdentifier'].strip() if row['SOSIdentifier'] else ''

                if sos_identifier in ('', 'N/A', 'None', 'NULL', 'None exists', 'None exists yet'):
                    sos_identifier = f"UNKNOWN-{row['BallotMeasureID']}"

                ballot_measure_id = int(row['BallotMeasureID'])

                ballot_measure, created = BallotMeasure.objects.get_or_create(
                    ballot_measure_id=ballot_measure_id,
                    defaults={
                        'sos_identifier': sos_identifier,
                        'measure_number': self.clean_empty_string(row['MeasureNumber']),
                        'short_title': row['ShortTitle'],
                        'official_title': official_title,
                    }
                )

                if not created:
                    try:
                        ballot_measure.measure_number = self.clean_empty_string(row['MeasureNumber'])
                        ballot_measure.short_title = row['ShortTitle']
                        ballot_measure.official_title = official_title
                        if ballot_measure.sos_identifier.startswith('UNKNOWN-'):
                            ballot_measure.sos_identifier = sos_identifier
                        ballot_measure.save()
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f"Could not update BallotMeasure {ballot_measure_id}: {e}"
                        ))

                count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error importing BallotMeasure {row.get('BallotMeasureID')}: {e}"
                ))

        return count

    def import_entities_bulk(self):
        rows = self.read_csv('Names.csv')
        total = len(rows)

        existing_ids = set(Entity.objects.values_list('name_id', flat=True))
        self.stdout.write(f"Found {len(existing_ids):,} existing entities")

        entities_to_create = []
        count = 0
        skipped = 0

        for i, row in enumerate(rows):
            if i % 10000 == 0:
                self.stdout.write(f"Processing: {i:,}/{total:,} ({i*100//total}%)")

            try:
                name_id = int(row['NameID'])

                if name_id in existing_ids:
                    skipped += 1
                    continue

                entity_type_id = int(row['EntityTypeID'])
                county_id = self.clean_empty_string(row['CountyID'])
                state_value = self.normalize_state(self.clean_empty_string(row['State']) or '')

                entity = Entity(
                    name_id=name_id,
                    name_group_id=int(row['NameGroupID']),
                    entity_type_id=entity_type_id,
                    last_name=row['LastName'] or '',
                    first_name=self.clean_empty_string(row['FirstName']) or '',
                    middle_name=self.clean_empty_string(row['MiddleName']) or '',
                    suffix=self.clean_empty_string(row['Suffix']) or '',
                    address1=self.clean_empty_string(row['Address1']) or '',
                    address2=self.clean_empty_string(row['Address2']) or '',
                    city=self.clean_empty_string(row['City']) or '',
                    state=state_value,
                    zip_code=self.clean_empty_string(row['ZipCode']) or '',
                    county_id=int(county_id) if county_id else None,
                    occupation=self.clean_empty_string(row['Occupation']) or '',
                    employer=self.clean_empty_string(row['Employer']) or '',
                )

                entities_to_create.append(entity)

                if len(entities_to_create) >= self.batch_size:
                    with transaction.atomic():
                        Entity.objects.bulk_create(entities_to_create, ignore_conflicts=True)
                    count += len(entities_to_create)
                    self.stdout.write(f"✓ Inserted {count:,} entities")
                    entities_to_create = []

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error at row {i} (NameID: {row.get("NameID", "?")}): {e}'))

        if entities_to_create:
            with transaction.atomic():
                Entity.objects.bulk_create(entities_to_create, ignore_conflicts=True)
            count += len(entities_to_create)

        self.stdout.write(self.style.SUCCESS(f"✓ Total inserted: {count:,}, Skipped: {skipped:,}"))
        return count

    def import_committees_bulk_fixed(self):
        rows = self.read_csv('Committees.csv')
        total = len(rows)

        existing_ids = set(Committee.objects.values_list('committee_id', flat=True))
        self.stdout.write(f"Found {len(existing_ids):,} existing committees")

        valid_ballot_measures = set(BallotMeasure.objects.values_list('ballot_measure_id', flat=True))
        valid_entities = set(Entity.objects.values_list('name_id', flat=True))
        valid_parties = set(Party.objects.values_list('party_id', flat=True))
        valid_offices = set(Office.objects.values_list('office_id', flat=True))
        valid_counties = set(County.objects.values_list('county_id', flat=True))
        valid_cycles = set(Cycle.objects.values_list('cycle_id', flat=True))

        self.stdout.write(f"Valid FKs: {len(valid_ballot_measures):,} ballot measures, {len(valid_entities):,} entities")

        committees_to_create = []
        count = 0
        skipped = 0
        fk_errors = 0

        for i, row in enumerate(rows):
            if i % 1000 == 0:
                self.stdout.write(f"Processing: {i:,}/{total:,}")

            try:
                committee_id = int(row['CommitteeID'])

                if committee_id in existing_ids:
                    skipped += 1
                    continue

                name_id = int(row['NameID'])
                if name_id not in valid_entities:
                    fk_errors += 1
                    if fk_errors <= 10:
                        self.stdout.write(self.style.WARNING(
                            f"Committee {committee_id}: Entity {name_id} not found - SKIPPING"
                        ))
                    continue

                chairperson_id = int(row['ChairpersonNameID']) if row['ChairpersonNameID'] else None
                if chairperson_id and chairperson_id not in valid_entities:
                    chairperson_id = None

                treasurer_id = int(row['TreasurerNameID']) if row['TreasurerNameID'] else None
                if treasurer_id and treasurer_id not in valid_entities:
                    treasurer_id = None

                candidate_id = int(row['CandidateNameID']) if row['CandidateNameID'] else None
                if candidate_id and candidate_id not in valid_entities:
                    candidate_id = None

                sponsor_id = int(row['SponsorNameID']) if row['SponsorNameID'] else None
                if sponsor_id and sponsor_id not in valid_entities:
                    sponsor_id = None

                ballot_measure_id = int(row['BallotMeasureID']) if row['BallotMeasureID'] else None
                if ballot_measure_id and ballot_measure_id not in valid_ballot_measures:
                    ballot_measure_id = None

                candidate_party_id = int(row['CandidatePartyID']) if row['CandidatePartyID'] else None
                if candidate_party_id and candidate_party_id not in valid_parties:
                    candidate_party_id = None
                
                candidate_office_id = int(row['CandidateOfficeID']) if row['CandidateOfficeID'] else None
                if candidate_office_id and candidate_office_id not in valid_offices:
                    candidate_office_id = None
                
                candidate_county_id = int(row['CandidateCountyID']) if row['CandidateCountyID'] and int(row['CandidateCountyID']) > 0 else None
                if candidate_county_id and candidate_county_id not in valid_counties:
                    candidate_county_id = None
                
                election_cycle_id = int(row['CandidateCycleID']) if row['CandidateCycleID'] else None
                if election_cycle_id and election_cycle_id not in valid_cycles:
                    election_cycle_id = None
                
                committee = Committee(
                    committee_id=committee_id,
                    name_id=name_id,
                    chairperson_id=chairperson_id,
                    treasurer_id=treasurer_id,
                    candidate_id=candidate_id,
                    sponsor_id=sponsor_id,
                    ballot_measure_id=ballot_measure_id,
                    candidate_party_id=candidate_party_id,
                    candidate_office_id=candidate_office_id,
                    candidate_county_id=candidate_county_id,
                    is_incumbent=self.parse_boolean(row['CandidateIsIncumbent']),
                    election_cycle_id=election_cycle_id,
                    sponsor_type=self.clean_empty_string(row['SponsorType']) or '',
                    sponsor_relationship=self.clean_empty_string(row['SponsorRelationship']) or '',
                    benefits_ballot_measure=self.parse_boolean(row['BenefitsBallotMeasure']),
                    organization_date=self.parse_date(row['OrganizationDate']),
                    termination_date=self.parse_date(row['TerminationDate']),
                    physical_address1=self.clean_empty_string(row['PhysicalAddress1']) or '',
                    physical_address2=self.clean_empty_string(row['PhysicalAddress2']) or '',
                    physical_city=self.clean_empty_string(row['PhysicalCity']) or '',
                    physical_state=self.clean_empty_string(row['PhysicalState']) or '',
                    physical_zip_code=self.clean_empty_string(row['PhysicalZipCode']) or '',
                    financial_institution1=self.clean_empty_string(row['FinancialInstitution1']) or '',
                    financial_institution2=self.clean_empty_string(row['FinancialInstitution2']) or '',
                    financial_institution3=self.clean_empty_string(row['FinancialInstitution3']) or '',
                )
                
                committees_to_create.append(committee)
                
                if len(committees_to_create) >= self.batch_size:
                    with transaction.atomic():
                        Committee.objects.bulk_create(committees_to_create, ignore_conflicts=True)
                    count += len(committees_to_create)
                    self.stdout.write(f"✓ Inserted {count:,} committees")
                    committees_to_create = []
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error at row {i} (CommitteeID: {row.get("CommitteeID", "?")}): {e}'))
        
        if committees_to_create:
            with transaction.atomic():
                Committee.objects.bulk_create(committees_to_create, ignore_conflicts=True)
            count += len(committees_to_create)
        
        if fk_errors > 10:
            self.stdout.write(self.style.WARNING(f"... and {fk_errors - 10} more FK errors (committees skipped)"))
        
        self.stdout.write(self.style.SUCCESS(f"✓ Total inserted: {count:,}, Skipped: {skipped:,}, FK Errors: {fk_errors:,}"))
        return count

    def import_transactions_bulk(self):
        rows = self.read_csv('Transactions.csv')
        total = len(rows)
        
        existing_ids = set(Transaction.objects.values_list('transaction_id', flat=True))
        self.stdout.write(f"Found {len(existing_ids):,} existing transactions")
        
        valid_committees = set(Committee.objects.values_list('committee_id', flat=True))
        self.stdout.write(f"Found {len(valid_committees):,} valid committees for FK validation")
        
        modifies_mapping = {}
        
        transactions_to_create = []
        count = 0
        skipped = 0
        committee_fk_errors = 0
        
        self.stdout.write(self.style.SUCCESS("PASS 1: Importing transactions (validating committee references)"))
        
        for i, row in enumerate(rows):
            if i % 10000 == 0:
                self.stdout.write(f"Processing: {i:,}/{total:,} ({i*100//total}%)")
            
            try:
                transaction_id = int(row['TransactionID'])
                
                if transaction_id in existing_ids:
                    skipped += 1
                    continue
                
                # CRITICAL FIX: Validate committee exists before proceeding
                committee_id = int(row['CommitteeID'])
                if committee_id not in valid_committees:
                    committee_fk_errors += 1
                    if committee_fk_errors <= 10:
                        self.stdout.write(self.style.WARNING(
                            f"Transaction {transaction_id}: Committee {committee_id} not found - SKIPPING"
                        ))
                    skipped += 1
                    continue
                
                modifies_raw = row['ModifiesTransactionID']
                if modifies_raw and modifies_raw.strip() and modifies_raw != str(transaction_id):
                    modifies_mapping[transaction_id] = int(modifies_raw)
                
                subject_committee_raw = row['SubjectCommitteeID']
                subject_committee_id = None
                if subject_committee_raw and subject_committee_raw.strip():
                    subject_committee_int = int(subject_committee_raw)
                    if subject_committee_int > 0 and subject_committee_int in valid_committees:
                        subject_committee_id = subject_committee_int
                
                category_raw = row['CategoryID']
                category_id = None
                if category_raw and category_raw.strip():
                    category_int = int(category_raw)
                    if category_int > 0:
                        category_id = category_int
                
                transaction_obj = Transaction(
                    transaction_id=transaction_id,
                    committee_id=committee_id,
                    transaction_type_id=int(row['TransactionTypeID']),
                    transaction_date=self.parse_date(row['TransactionDate']),
                    amount=Decimal(row['Amount']),
                    entity_id=int(row['NameID']),
                    subject_committee_id=subject_committee_id,
                    is_for_benefit=self.parse_boolean(row['IsForBenefit']),
                    category_id=category_id,
                    memo=self.clean_empty_string(row['Memo']) or '',
                    account_type=self.clean_empty_string(row['AccountType']) or '',
                    modifies_transaction_id=None,
                    deleted=self.parse_boolean(row['Deleted']),
                )
                
                transactions_to_create.append(transaction_obj)
                
                if len(transactions_to_create) >= self.batch_size:
                    with transaction.atomic():
                        Transaction.objects.bulk_create(transactions_to_create, ignore_conflicts=True)
                    count += len(transactions_to_create)
                    self.stdout.write(f"✓ Inserted {count:,} transactions")
                    transactions_to_create = []
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error at row {i}: {e}'))
        
        if transactions_to_create:
            with transaction.atomic():
                Transaction.objects.bulk_create(transactions_to_create, ignore_conflicts=True)
            count += len(transactions_to_create)
        
        if committee_fk_errors > 10:
            self.stdout.write(self.style.WARNING(
                f"... and {committee_fk_errors - 10} more transactions skipped (invalid committee references)"
            ))
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ PASS 1 Complete: {count:,} inserted, {skipped:,} skipped, {committee_fk_errors:,} committee FK errors"
        ))
        
        if modifies_mapping:
            self.stdout.write(self.style.SUCCESS(f"\nPASS 2: Updating {len(modifies_mapping):,} modifies_transaction_id references"))
            
            all_transaction_ids = set(Transaction.objects.values_list('transaction_id', flat=True))
            
            updates_to_make = []
            invalid_refs = 0
            
            for trans_id, modifies_id in modifies_mapping.items():
                if modifies_id in all_transaction_ids:
                    updates_to_make.append((trans_id, modifies_id))
                else:
                    invalid_refs += 1
                    if invalid_refs <= 5:
                        self.stdout.write(self.style.WARNING(
                            f"Transaction {trans_id} references non-existent transaction {modifies_id}"
                        ))
            
            batch_size = 1000
            updated_count = 0
            for i in range(0, len(updates_to_make), batch_size):
                batch = updates_to_make[i:i+batch_size]
                with transaction.atomic():
                    for trans_id, modifies_id in batch:
                        Transaction.objects.filter(transaction_id=trans_id).update(
                            modifies_transaction_id=modifies_id
                        )
                updated_count += len(batch)
                if (i // batch_size) % 10 == 0:
                    self.stdout.write(f"✓ Updated {updated_count:,}/{len(updates_to_make):,} references")
            
            if invalid_refs > 5:
                self.stdout.write(self.style.WARNING(f"... and {invalid_refs - 5} more invalid transaction references"))
            
            self.stdout.write(self.style.SUCCESS(f"✓ PASS 2 Complete: {updated_count:,} references updated"))
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ FINAL: Total={count:,}, Skipped={skipped:,}, Committee FK Errors={committee_fk_errors:,}"
        ))
        return count

    def import_reports_bulk(self):
        rows = self.read_csv('Reports.csv')
        total = len(rows)
        
        existing_ids = set(Report.objects.values_list('report_id', flat=True))
        self.stdout.write(f"Found {len(existing_ids):,} existing reports")
        
        # Validate committee IDs exist before trying to import
        valid_committees = set(Committee.objects.values_list('committee_id', flat=True))
        self.stdout.write(f"Found {len(valid_committees):,} valid committees for FK validation")
        
        # Separate original reports from amendments
        original_reports = []
        amended_reports = []
        amendment_mapping = {}  # report_id -> original_report_id
        
        committee_fk_errors = 0
        skipped = 0
        null_date_errors = 0
        
        self.stdout.write(self.style.SUCCESS("PASS 1: Separating original reports from amendments"))
        
        for i, row in enumerate(rows):
            if i % 10000 == 0:
                self.stdout.write(f"Processing: {i:,}/{total:,}")
            
            try:
                report_id = int(row['ReportID'])
                
                if report_id in existing_ids:
                    skipped += 1
                    continue
                
                # Check if committee exists
                committee_id = int(row['CommitteeID'])
                if committee_id not in valid_committees:
                    committee_fk_errors += 1
                    if committee_fk_errors <= 10:
                        self.stdout.write(self.style.WARNING(
                            f"Report {report_id}: Committee {committee_id} not found - SKIPPING"
                        ))
                    skipped += 1
                    continue
                
                # Parse dates with null checking
                report_period_begin = self.parse_date(row['ReportPeriodBeginDate'])
                report_period_end = self.parse_date(row['ReportPeriodEndDate'])
                filing_period_begin = self.parse_date(row['FilingPeriodBeginDate'])
                filing_period_end = self.parse_date(row['FilingPeriodEndDate'])
                filing_datetime = self.parse_date(row['FilingDateTime'])
                
                # Skip if required dates are missing
                if not report_period_end or not filing_datetime:
                    null_date_errors += 1
                    if null_date_errors <= 10:
                        self.stdout.write(self.style.WARNING(
                            f"Report {report_id}: Missing required dates (period_end={report_period_end}, filing={filing_datetime}) - SKIPPING"
                        ))
                    skipped += 1
                    continue
                
                # Parse all fields
                report_data = {
                    'report_id': report_id,
                    'committee_id': committee_id,
                    'cycle_id': int(row['CycleID']),
                    'report_type_id': int(row['ReportTypeID']),
                    'report_name_id': int(row['ReportNameID']),
                    'report_period_begin': report_period_begin,
                    'report_period_end': report_period_end,
                    'filing_period_begin': filing_period_begin,
                    'filing_period_end': filing_period_end,
                    'filing_datetime': filing_datetime,
                    'original_report_id': int(row['OriginalReportID']) if row['OriginalReportID'] else None,
                }
                
                # Separate into original vs amended
                if report_data['original_report_id']:
                    amended_reports.append(report_data)
                    amendment_mapping[report_id] = report_data['original_report_id']
                else:
                    original_reports.append(report_data)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error at row {i} (ReportID: {row.get("ReportID", "?")}): {e}'))
        
        if committee_fk_errors > 10:
            self.stdout.write(self.style.WARNING(
                f"... and {committee_fk_errors - 10} more reports skipped (invalid committee references)"
            ))
        
        if null_date_errors > 10:
            self.stdout.write(self.style.WARNING(
                f"... and {null_date_errors - 10} more reports skipped (missing required dates)"
            ))
        
        self.stdout.write(self.style.SUCCESS(
            f"✓ Sorted: {len(original_reports):,} original reports, {len(amended_reports):,} amendments"
        ))
        
        # PASS 2: Insert original reports first
        self.stdout.write(self.style.SUCCESS("\nPASS 2: Inserting original reports"))
        
        reports_to_create = []
        count = 0
        
        for i, report_data in enumerate(original_reports):
            if i % 5000 == 0 and i > 0:
                self.stdout.write(f"Processing: {i:,}/{len(original_reports):,}")
            
            report = Report(**report_data)
            reports_to_create.append(report)
            
            if len(reports_to_create) >= self.batch_size:
                with transaction.atomic():
                    Report.objects.bulk_create(reports_to_create, ignore_conflicts=True)
                count += len(reports_to_create)
                self.stdout.write(f"✓ Inserted {count:,} original reports")
                reports_to_create = []
        
        if reports_to_create:
            with transaction.atomic():
                Report.objects.bulk_create(reports_to_create, ignore_conflicts=True)
            count += len(reports_to_create)
        
        self.stdout.write(self.style.SUCCESS(f"✓ PASS 2 Complete: {count:,} original reports inserted"))
        
        # PASS 3: Insert amended reports (validating original_report_id exists)
        self.stdout.write(self.style.SUCCESS("\nPASS 3: Inserting amended reports"))
        
        all_report_ids = set(Report.objects.values_list('report_id', flat=True))
        
        reports_to_create = []
        amendment_count = 0
        invalid_refs = 0
        
        for i, report_data in enumerate(amended_reports):
            if i % 5000 == 0 and i > 0:
                self.stdout.write(f"Processing: {i:,}/{len(amended_reports):,}")
            
            # Validate original report exists
            if report_data['original_report_id'] not in all_report_ids:
                invalid_refs += 1
                if invalid_refs <= 10:
                    self.stdout.write(self.style.WARNING(
                        f"Report {report_data['report_id']} references non-existent original report {report_data['original_report_id']}"
                    ))
                continue
            
            report = Report(**report_data)
            reports_to_create.append(report)
            
            if len(reports_to_create) >= self.batch_size:
                with transaction.atomic():
                    Report.objects.bulk_create(reports_to_create, ignore_conflicts=True)
                amendment_count += len(reports_to_create)
                self.stdout.write(f"✓ Inserted {amendment_count:,} amended reports")
                reports_to_create = []
        
        if reports_to_create:
            with transaction.atomic():
                Report.objects.bulk_create(reports_to_create, ignore_conflicts=True)
            amendment_count += len(reports_to_create)
        
        if invalid_refs > 10:
            self.stdout.write(self.style.WARNING(f"... and {invalid_refs - 10} more invalid original report references"))
        
        self.stdout.write(self.style.SUCCESS(f"✓ PASS 3 Complete: {amendment_count:,} amended reports inserted"))
        
        total_inserted = count + amendment_count
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ FINAL: Total={total_inserted:,}, Skipped={skipped:,}, Committee FK Errors={committee_fk_errors:,}, Null Date Errors={null_date_errors:,}, Invalid Original Report Refs={invalid_refs:,}"
        ))
        return total_inserted