import csv
import subprocess
import gc
import io
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from tqdm import tqdm

from transparency.models import (
    MDB_Name, MDB_Committee, MDB_Transaction,
    MDB_EntityType, MDB_TransactionType, MDB_Office, MDB_Category, MDB_Party
)

# CRITICAL: Even smaller batch size to prevent memory issues
BATCH_SIZE = 2000  # Reduced from 5000 to 2000


class Command(BaseCommand):
    help = 'Load RAW data from MDB file into database (no transformations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of records to load (for testing)',
        )
        parser.add_argument(
            '--skip-names',
            action='store_true',
            help='Skip loading names (use if already loaded)',
        )
        parser.add_argument(
            '--skip-transactions',
            action='store_true',
            help='Skip loading transactions (use if already loaded)',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        skip_names = options.get('skip_names')
        skip_transactions = options.get('skip_transactions')
        
        self.stdout.write(self.style.SUCCESS('\n🚀 Starting RAW MDB data import (no transformations)...\n'))
        
        try:
            # Load reference tables first (small)
            self.load_entity_types()
            self.load_transaction_types()
            self.load_offices()
            self.load_categories()
            self.load_parties()
            
            # Load committees (medium size)
            self.load_committees(limit)
            
            # Load names (HUGE - 2.3M records) - with memory management
            if not skip_names:
                self.load_names(limit)
            else:
                self.stdout.write('⏭️ Skipping Names (--skip-names flag)\n')
            
            # Load transactions (MASSIVE - 10M records) - with memory management
            if not skip_transactions:
                self.load_transactions(limit)
            else:
                self.stdout.write('⏭️ Skipping Transactions (--skip-transactions flag)\n')
            
            self.stdout.write(self.style.SUCCESS('\n✨ Import complete!\n'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during import: {str(e)}\n'))
            raise

    def export_table(self, table_name):
        """Export table from MDB file using mdb-export."""
        mdb_file = '/opt/az_sunshine/backend/2025 1020 CFS_Export_PRR.mdb'
        cmd = ['mdb-export', mdb_file, table_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def load_entity_types(self):
        """Load EntityTypes reference table."""
        self.stdout.write('→ Loading Entity Types...')
        
        csv_data = self.export_table('EntityTypes')
        reader = csv.DictReader(csv_data.splitlines())
        
        entity_types = []
        for row in tqdm(reader, desc="EntityTypes"):
            entity_types.append(MDB_EntityType(
                entity_type_id=int(row['EntityTypeID']),
                entity_type_name=row['EntityTypeName']
            ))
        
        MDB_EntityType.objects.bulk_create(entity_types, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(entity_types)} entity types\n'))

    def load_transaction_types(self):
        """Load TransactionTypes reference table."""
        self.stdout.write('→ Loading Transaction Types...')
        
        csv_data = self.export_table('TransactionTypes')
        reader = csv.DictReader(csv_data.splitlines())
        
        transaction_types = []
        for row in tqdm(reader, desc="TransactionTypes"):
            transaction_types.append(MDB_TransactionType(
                transaction_type_id=int(row['TransactionTypeID']),
                transaction_type_name=row['TransactionTypeName'],
                income_expense_neutral_id=int(row['IncomeExpenseNeutralID']) if row.get('IncomeExpenseNeutralID') else None
            ))
        
        MDB_TransactionType.objects.bulk_create(transaction_types, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(transaction_types)} transaction types\n'))

    def load_offices(self):
        """Load Offices reference table."""
        self.stdout.write('→ Loading Offices...')
        
        csv_data = self.export_table('Offices')
        reader = csv.DictReader(csv_data.splitlines())
        
        offices = []
        for row in tqdm(reader, desc="Offices"):
            # Build office data based on available fields in the model
            office_data = {
                'office_id': int(row['OfficeID']),
                'office_name': row['OfficeName']
            }
            
            offices.append(MDB_Office(**office_data))
        
        MDB_Office.objects.bulk_create(offices, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(offices)} offices\n'))

    def load_categories(self):
        """Load Categories reference table."""
        self.stdout.write('→ Loading Categories...')
        
        csv_data = self.export_table('Categories')
        reader = csv.DictReader(csv_data.splitlines())
        
        categories = []
        for row in tqdm(reader, desc="Categories"):
            categories.append(MDB_Category(
                category_id=int(row['CategoryID']),
                category_name=row['CategoryName']
            ))
        
        MDB_Category.objects.bulk_create(categories, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(categories)} categories\n'))

    def load_parties(self):
        """Load Parties reference table."""
        self.stdout.write('→ Loading Parties (RAW)...')
        
        csv_data = self.export_table('Parties')
        reader = csv.DictReader(csv_data.splitlines())
        
        parties = []
        for row in tqdm(reader, desc="Parties"):
            parties.append(MDB_Party(
                party_id=int(row['PartyID']),
                party_name=row['PartyName']
            ))
        
        MDB_Party.objects.bulk_create(parties, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(parties)} parties\n'))

    def load_committees(self, limit=None):
        """Load Committees table."""
        self.stdout.write('→ Loading Committees (RAW)...')
        
        csv_data = self.export_table('Committees')
        reader = csv.DictReader(csv_data.splitlines())
        
        committees = []
        count = 0
        
        for row in tqdm(reader, desc="Committees"):
            if limit and count >= limit:
                break
            
            # Only include fields that exist in both CSV and model
            committee_data = {
                'committee_id': int(row['CommitteeID']),
            }
            
            # Add optional fields if they exist
            if row.get('NameID'):
                committee_data['name_id'] = int(row['NameID'])
            if row.get('ChairpersonNameID'):
                committee_data['chairperson_name_id'] = int(row['ChairpersonNameID'])
            if row.get('TreasurerNameID'):
                committee_data['treasurer_name_id'] = int(row['TreasurerNameID'])
            if row.get('CandidateNameID'):
                committee_data['candidate_name_id'] = int(row['CandidateNameID'])
            if row.get('DesigneeNameID'):
                committee_data['designee_name_id'] = int(row['DesigneeNameID'])
            if row.get('SponsorNameID'):
                committee_data['sponsor_name_id'] = int(row['SponsorNameID'])
            if row.get('BallotMeasureID'):
                committee_data['ballot_measure_id'] = int(row['BallotMeasureID'])
            if row.get('PhysicalAddress1'):
                committee_data['physical_address1'] = row['PhysicalAddress1']
            if row.get('PhysicalAddress2'):
                committee_data['physical_address2'] = row['PhysicalAddress2']
            if row.get('PhysicalCity'):
                committee_data['physical_city'] = row['PhysicalCity']
            if row.get('PhysicalState'):
                committee_data['physical_state'] = row['PhysicalState']
            if row.get('PhysicalZipCode'):
                committee_data['physical_zip_code'] = row['PhysicalZipCode']
            if row.get('SponsorType'):
                committee_data['sponsor_type'] = row['SponsorType']
            if row.get('SponsorRelationship'):
                committee_data['sponsor_relationship'] = row['SponsorRelationship']
            if row.get('OrganizationDate'):
                committee_data['organization_date'] = row['OrganizationDate']
            if row.get('TerminationDate'):
                committee_data['termination_date'] = row['TerminationDate']
            if row.get('BenefitsBallotMeasure'):
                committee_data['benefits_ballot_measure'] = int(row['BenefitsBallotMeasure'])
            if row.get('FinancialInstitution1'):
                committee_data['financial_institution1'] = row['FinancialInstitution1']
            if row.get('FinancialInstitution2'):
                committee_data['financial_institution2'] = row['FinancialInstitution2']
            if row.get('FinancialInstitution3'):
                committee_data['financial_institution3'] = row['FinancialInstitution3']
            if row.get('CandidatePartyID'):
                committee_data['candidate_party_id'] = int(row['CandidatePartyID'])
            if row.get('CandidateOfficeID'):
                committee_data['candidate_office_id'] = int(row['CandidateOfficeID'])
            if row.get('CandidateCountyID'):
                committee_data['candidate_county_id'] = int(row['CandidateCountyID'])
            if row.get('CandidateIsIncumbent'):
                committee_data['candidate_is_incumbent'] = int(row['CandidateIsIncumbent'])
            if row.get('CandidateCycleID'):
                committee_data['candidate_cycle_id'] = int(row['CandidateCycleID'])
            if row.get('CandidateOtherPartyName'):
                committee_data['candidate_other_party_name'] = row['CandidateOtherPartyName']
            
            committees.append(MDB_Committee(**committee_data))
            count += 1
            
            if len(committees) >= BATCH_SIZE:
                MDB_Committee.objects.bulk_create(committees, ignore_conflicts=True)
                committees.clear()
                gc.collect()
        
        if committees:
            MDB_Committee.objects.bulk_create(committees, ignore_conflicts=True)
        
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {count} committees\n'))

    def load_names(self, limit=None):
        """Load Names table WITH MEMORY MANAGEMENT (2.3M records).
        
        This uses TRUE streaming, batching, and garbage collection to prevent OOM.
        Uses proper CSV parsing to handle quoted fields with commas.
        """
        self.stdout.write('→ Loading Names (RAW - 2.3M entities with memory management)...')
        
        # Use subprocess.Popen for streaming large output
        mdb_file = '/opt/az_sunshine/backend/2025 1020 CFS_Export_PRR.mdb'
        cmd = ['mdb-export', mdb_file, 'Names']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=8192)
        
        # Use csv.DictReader with proper text stream handling
        csv_reader = csv.DictReader(process.stdout)
        
        names = []
        count = 0
        batch_num = 0
        skipped = 0
        
        # Stream line by line with proper CSV parsing
        for row in csv_reader:
            if limit and count >= limit:
                break
            
            try:
                # Create Name object with proper error handling
                names.append(MDB_Name(
                    name_id=int(row.get('NameID', '0')),
                    name_group_id=int(row['NameGroupID']) if row.get('NameGroupID', '').strip() else None,
                    entity_type_id=int(row['EntityTypeID']) if row.get('EntityTypeID', '').strip() else None,
                    last_name=row.get('LastName', '').strip('"'),
                    first_name=row.get('FirstName', '').strip('"'),
                    middle_name=row.get('MiddleName', '').strip('"'),
                    suffix=row.get('Suffix', '').strip('"'),
                    address1=row.get('Address1', '').strip('"'),
                    address2=row.get('Address2', '').strip('"'),
                    city=row.get('City', '').strip('"'),
                    state=row.get('State', '').strip('"'),
                    zip_code=row.get('ZipCode', '').strip('"'),
                    county_id=int(row['CountyID']) if row.get('CountyID', '').strip() else None,
                    occupation=row.get('Occupation', '').strip('"'),
                    employer=row.get('Employer', '').strip('"')
                ))
                count += 1
                
            except (ValueError, KeyError) as e:
                skipped += 1
                if skipped <= 10:  # Log first 10 errors
                    self.stdout.write(f'   ⚠️  Skipped malformed row {count + skipped}: {str(e)}')
                continue
            
            # Commit in batches and free memory
            if len(names) >= BATCH_SIZE:
                MDB_Name.objects.bulk_create(names, ignore_conflicts=True)
                names.clear()
                batch_num += 1
                
                # Force garbage collection every 10 batches
                if batch_num % 10 == 0:
                    gc.collect()
                    connection.close()  # Close DB connection to free resources
                    self.stdout.write(f'   💾 Committed {count:,} names...')
        
        # Insert remaining
        if names:
            MDB_Name.objects.bulk_create(names, ignore_conflicts=True)
        
        # Cleanup
        process.wait()
        gc.collect()
        
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Skipped {skipped:,} malformed rows'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {count:,} names\n'))

    def load_transactions(self, limit=None):
        """Load Transactions table WITH MEMORY MANAGEMENT (10M records).
        
        This uses TRUE streaming, batching, and garbage collection to prevent OOM.
        Uses proper CSV parsing to handle quoted fields with commas.
        """
        self.stdout.write('→ Loading Transactions (RAW - 10M records with memory management)...')
        
        # Use subprocess.Popen for streaming large output
        mdb_file = '/opt/az_sunshine/backend/2025 1020 CFS_Export_PRR.mdb'
        cmd = ['mdb-export', mdb_file, 'Transactions']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=8192)
        
        # Use csv.DictReader with proper text stream handling
        csv_reader = csv.DictReader(process.stdout)
        
        transactions = []
        count = 0
        batch_num = 0
        skipped = 0
        
        # Stream line by line with proper CSV parsing
        for row in csv_reader:
            if limit and count >= limit:
                break
            
            try:
                # Parse amount
                amount = None
                if row.get('Amount'):
                    try:
                        amount = Decimal(row['Amount'].strip().strip('"'))
                    except:
                        amount = Decimal('0')
                
                # Create Transaction object with proper error handling
                transactions.append(MDB_Transaction(
                    transaction_id=int(row.get('TransactionID', '0')),
                    modifies_transaction_id=int(row['ModifiesTransactionID']) if row.get('ModifiesTransactionID', '').strip() else None,
                    transaction_type_id=int(row['TransactionTypeID']) if row.get('TransactionTypeID', '').strip() else None,
                    committee_id=int(row['CommitteeID']) if row.get('CommitteeID', '').strip() else None,
                    transaction_date=row.get('TransactionDate', '').strip('"'),
                    amount=amount,
                    name_id=int(row['NameID']) if row.get('NameID', '').strip() else None,
                    is_for_benefit=int(row['IsForBenefit']) if row.get('IsForBenefit', '').strip() else None,
                    subject_committee_id=int(row['SubjectCommitteeID']) if row.get('SubjectCommitteeID', '').strip() else None,
                    memo=row.get('Memo', '').strip('"'),
                    category_id=int(row['CategoryID']) if row.get('CategoryID', '').strip() else None,
                    account_type=row.get('AccountType', '').strip('"'),
                    deleted=int(row.get('Deleted', '0')) if row.get('Deleted', '').strip() else 0
                ))
                count += 1
                
            except (ValueError, KeyError) as e:
                skipped += 1
                if skipped <= 10:  # Log first 10 errors
                    self.stdout.write(f'   ⚠️  Skipped malformed row {count + skipped}: {str(e)}')
                continue
            
            # Commit in batches and free memory
            if len(transactions) >= BATCH_SIZE:
                MDB_Transaction.objects.bulk_create(transactions, ignore_conflicts=True)
                transactions.clear()
                batch_num += 1
                
                # Force garbage collection every 10 batches
                if batch_num % 10 == 0:
                    gc.collect()
                    connection.close()  # Close DB connection to free resources
                    self.stdout.write(f'   💾 Committed {count:,} transactions...')
        
        # Insert remaining
        if transactions:
            MDB_Transaction.objects.bulk_create(transactions, ignore_conflicts=True)
        
        # Cleanup
        process.wait()
        gc.collect()
        
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Skipped {skipped:,} malformed rows'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {count:,} transactions\n'))
