import gc
import traceback
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection, transaction
from tqdm import tqdm
from transparency.models import (
    # Application models
    Party, Race, Candidate, IECommittee, DonorEntity, Contribution, Expenditure,
    # Raw MDB models
    MDB_Name, MDB_Committee, MDB_Transaction, MDB_Party,
    MDB_EntityType, MDB_TransactionType, MDB_Office, MDB_Category
)


BATCH_SIZE = 500           # Minimum for efficiency
TRANSACTION_CHUNK_SIZE = 2000   # Still reasonable
DONOR_LOOKUP_CHUNK = 5000       # Don't go below this!
DONOR_CHUNK_SIZE = 10000
NAME_BATCH_SIZE = 1000  

# Email notification settings
NOTIFICATION_EMAIL = 'emosmwangi@gmail.com'

# Contribution Transaction Type IDs (Income)
CONTRIBUTION_TRANSACTION_TYPES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

# IE Transaction Type IDs (Independent Expenditures)
IE_TRANSACTION_TYPES = [33, 34, 76, 243, 274]


class Command(BaseCommand):
    help = "Map raw MDB data to application models with batch processing"

    def add_arguments(self, parser):
        parser.add_argument(
            '--step',
            type=str,
            help='Run specific step only (parties, candidates, ie_committees, donors, contributions, expenditures)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of records to process (for testing)',
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Disable email notifications',
        )

    def handle(self, *args, **options):
        step = options.get('step')
        limit = options.get('limit')
        send_email = not options.get('no_email', False)
        
        start_time = datetime.now()
        errors = []
        results = {}
        
        try:
            self.stdout.write("🚀 Starting MDB to Application mapping (batch optimized)...\n")
            
            if step:
                if step == 'parties':
                    results['parties'] = self.map_parties(limit)
                elif step == 'candidates':
                    results['candidates'] = self.map_candidates(limit)
                elif step == 'ie_committees':
                    results['ie_committees'] = self.map_ie_committees(limit)
                elif step == 'donors':
                    results['donors'] = self.map_donors(limit)
                elif step == 'contributions':
                    results['contributions'] = self.map_contributions(limit)
                elif step == 'expenditures':
                    results['expenditures'] = self.map_expenditures(limit)
                else:
                    error_msg = f"Unknown step: {step}"
                    self.stderr.write(error_msg)
                    errors.append(error_msg)
            else:
                # Run all steps in order
                results['parties'] = self.map_parties(limit)
                results['candidates'] = self.map_candidates(limit)
                results['ie_committees'] = self.map_ie_committees(limit)
                results['donors'] = self.map_donors(limit)
                results['contributions'] = self.map_contributions(limit)
                results['expenditures'] = self.map_expenditures(limit)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.stdout.write("🎉 Mapping complete!\n")
            
            # Send success email
            if send_email:
                self.send_success_email(results, start_time, end_time, duration)
                
        except Exception as e:
            end_time = datetime.now()
            duration = end_time - start_time
            error_msg = f"Critical error: {str(e)}\n{traceback.format_exc()}"
            self.stderr.write(error_msg)
            errors.append(error_msg)
            
            # Send error email
            if send_email:
                self.send_error_email(error_msg, results, start_time, end_time, duration)
            
            raise

    def send_success_email(self, results, start_time, end_time, duration):
        """Send success notification email."""
        subject = "✅ MDB Mapping Completed Successfully"
        
        message = f"""
MDB to Application Mapping has completed successfully!

Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}

Results:
--------
"""
        for step, count in results.items():
            message += f"• {step.replace('_', ' ').title()}: {count:,} records\n"
        
        message += f"\nServer: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'az-sunshine'}"
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [NOTIFICATION_EMAIL],
                fail_silently=False,
            )
            self.stdout.write(f"📧 Success email sent to {NOTIFICATION_EMAIL}")
        except Exception as e:
            self.stderr.write(f"⚠️ Failed to send success email: {e}")

    def send_error_email(self, error_msg, partial_results, start_time, end_time, duration):
        """Send error notification email."""
        subject = "❌ MDB Mapping Failed - Action Required"
        
        message = f"""
MDB to Application Mapping has FAILED!

Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
Failure Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}

ERROR DETAILS:
--------------
{error_msg}

Partial Results (before failure):
---------------------------------
"""
        if partial_results:
            for step, count in partial_results.items():
                message += f"• {step.replace('_', ' ').title()}: {count:,} records\n"
        else:
            message += "No steps completed before failure.\n"
        
        message += f"\nServer: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'az-sunshine'}"
        message += "\n\nPlease check the server logs for more details."
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [NOTIFICATION_EMAIL],
                fail_silently=False,
            )
            self.stdout.write(f"📧 Error email sent to {NOTIFICATION_EMAIL}")
        except Exception as e:
            self.stderr.write(f"⚠️ Failed to send error email: {e}")

    def parse_date(self, date_str):
        """Parse date from MDB format (MM/DD/YY or MM/DD/YYYY)."""
        if not date_str:
            return None
        
        date_str = date_str.strip().split(' ')[0]  # Remove time portion
        
        for fmt in ("%m/%d/%y", "%m/%d/%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def map_parties(self, limit=None):
        """Map MDB_Party to Party with source reference."""
        self.stdout.write("→ Mapping Parties...")
        
        mdb_parties = MDB_Party.objects.all()
        if limit:
            mdb_parties = mdb_parties[:limit]
        
        batch = []
        for mdb_party in tqdm(mdb_parties, desc="Parties"):
            batch.append(Party(
                id=mdb_party.party_id,
                name=mdb_party.party_name,
                source_mdb_party=mdb_party
            ))
            
            if len(batch) >= BATCH_SIZE:
                Party.objects.bulk_create(batch, ignore_conflicts=True)
                batch.clear()
        
        if batch:
            Party.objects.bulk_create(batch, ignore_conflicts=True)
        
        total = Party.objects.count()
        self.stdout.write(f"✅ Mapped {total} parties\n")
        return total

    def map_candidates(self, limit=None):
        """Map candidate committees to Candidate model."""
        self.stdout.write("→ Mapping Candidates from committees...")
        
        candidate_committees = MDB_Committee.objects.filter(
            candidate_name_id__isnull=False
        ).select_related()
        
        if limit:
            candidate_committees = candidate_committees[:limit]
        
        candidates_to_create = []
        total = 0
        
        for committee in tqdm(candidate_committees, desc="Candidates"):
            try:
                candidate_name = MDB_Name.objects.filter(
                    name_id=committee.candidate_name_id
                ).first()
                
                if not candidate_name:
                    continue
                
                name_parts = []
                if candidate_name.first_name:
                    name_parts.append(candidate_name.first_name)
                if candidate_name.middle_name:
                    name_parts.append(candidate_name.middle_name)
                if candidate_name.last_name:
                    name_parts.append(candidate_name.last_name)
                if candidate_name.suffix:
                    name_parts.append(candidate_name.suffix)
                
                full_name = ' '.join(name_parts).strip()
                if not full_name:
                    continue
                
                party = None
                if committee.candidate_party_id:
                    party = Party.objects.filter(id=committee.candidate_party_id).first()
                
                race = None
                if committee.candidate_office_id:
                    office = MDB_Office.objects.filter(
                        office_id=committee.candidate_office_id
                    ).first()
                    if office:
                        race, _ = Race.objects.get_or_create(
                            name=office.office_name,
                            defaults={
                                'office': office.office_name,
                                'source_mdb_office': office
                            }
                        )
                
                filing_date = self.parse_date(committee.organization_date)
                
                candidates_to_create.append(Candidate(
                    name=full_name,
                    race=race,
                    party=party,
                    filing_date=filing_date,
                    source="MDB",
                    external_id=f"committee_{committee.committee_id}",
                    source_mdb_committee=committee,
                    source_mdb_candidate_name=candidate_name,
                ))
                
                if len(candidates_to_create) >= BATCH_SIZE:
                    Candidate.objects.bulk_create(candidates_to_create, ignore_conflicts=True)
                    total += len(candidates_to_create)
                    candidates_to_create.clear()
                    gc.collect()
                    
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped candidate committee {committee.committee_id}: {e}")
                continue
        
        if candidates_to_create:
            Candidate.objects.bulk_create(candidates_to_create, ignore_conflicts=True)
            total += len(candidates_to_create)
        
        self.stdout.write(f"✅ Mapped {total} candidates\n")
        return total

    def map_ie_committees(self, limit=None):
        """Map IE committees to IECommittee model."""
        self.stdout.write("→ Mapping IE Committees...")
        
        ie_committees_query = MDB_Committee.objects.filter(
            candidate_name_id__isnull=True
        ).select_related()
        
        if limit:
            ie_committees_query = ie_committees_query[:limit]
        
        ie_committees_to_create = []
        total = 0
        
        for committee in tqdm(ie_committees_query, desc="IE Committees"):
            try:
                committee_name_obj = MDB_Name.objects.filter(
                    name_id=committee.name_id
                ).first()
                
                if not committee_name_obj:
                    continue
                
                name = committee_name_obj.last_name or f"Committee {committee.committee_id}"
                
                entity_type = None
                if committee_name_obj.entity_type_id:
                    entity_type_obj = MDB_EntityType.objects.filter(
                        entity_type_id=committee_name_obj.entity_type_id
                    ).first()
                    if entity_type_obj:
                        entity_type = entity_type_obj.entity_type_name
                
                ie_committees_to_create.append(IECommittee(
                    id=committee.committee_id,
                    name=name,
                    committee_type=entity_type,
                    source_mdb_committee=committee,
                    source_mdb_committee_name=committee_name_obj,
                ))
                
                if len(ie_committees_to_create) >= BATCH_SIZE:
                    IECommittee.objects.bulk_create(ie_committees_to_create, ignore_conflicts=True)
                    total += len(ie_committees_to_create)
                    ie_committees_to_create.clear()
                    gc.collect()
                    
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped IE committee {committee.committee_id}: {e}")
                continue
        
        if ie_committees_to_create:
            IECommittee.objects.bulk_create(ie_committees_to_create, ignore_conflicts=True)
            total += len(ie_committees_to_create)
        
        self.stdout.write(f"✅ Mapped {total} IE committees\n")
        return total

    def map_donors(self, limit=None):
        """Map donors by processing transactions in chunks (MUCH FASTER!)."""
        self.stdout.write("→ Mapping Donors (processing transactions in chunks)...")
        
        # Instead of SELECT DISTINCT on all transactions, process in chunks
        offset = 0
        chunk_size = DONOR_CHUNK_SIZE
        total_donors = 0
        seen_donor_ids = set()
        
        while True:
            self.stdout.write(f"   Processing transaction chunk starting at offset {offset:,}...")
            
            # Get chunk of transactions
            query = f'''
                SELECT DISTINCT t."NameID"
                FROM mdb_transactions t
                WHERE t."TransactionTypeID" IN ({','.join(map(str, CONTRIBUTION_TRANSACTION_TYPES))})
                  AND t."NameID" IS NOT NULL
                  AND t."Deleted" = 0
                ORDER BY t."NameID"
                LIMIT {chunk_size}
                OFFSET {offset}
            '''
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                donor_ids_chunk = [row[0] for row in cursor.fetchall()]
            
            if not donor_ids_chunk:
                break
            
            # Filter out already-processed donors
            new_donor_ids = [did for did in donor_ids_chunk if did not in seen_donor_ids]
            seen_donor_ids.update(new_donor_ids)
            
            if new_donor_ids:
                self.stdout.write(f"   Found {len(new_donor_ids):,} new donors in this chunk...")
                
                # Process these donors in sub-batches
                for i in range(0, len(new_donor_ids), 5000):
                    sub_batch = new_donor_ids[i:i+5000]
                    names = MDB_Name.objects.filter(name_id__in=sub_batch)
                    
                    donors_to_create = []
                    for name in names:
                        try:
                            name_parts = []
                            if name.first_name:
                                name_parts.append(name.first_name)
                            if name.middle_name:
                                name_parts.append(name.middle_name)
                            if name.last_name:
                                name_parts.append(name.last_name)
                            
                            full_name = ' '.join(name_parts).strip() or name.last_name or f"Donor {name.name_id}"
                            
                            entity_type = None
                            if name.entity_type_id:
                                entity_type_obj = MDB_EntityType.objects.filter(
                                    entity_type_id=name.entity_type_id
                                ).first()
                                if entity_type_obj:
                                    entity_type = entity_type_obj.entity_type_name
                            
                            donors_to_create.append(DonorEntity(
                                id=name.name_id,
                                name=full_name,
                                entity_type=entity_type,
                                source_mdb_name=name,
                            ))
                            
                        except Exception as e:
                            self.stderr.write(f"⚠️ Skipped donor {name.name_id}: {e}")
                            continue
                    
                    if donors_to_create:
                        DonorEntity.objects.bulk_create(donors_to_create, ignore_conflicts=True)
                        total_donors += len(donors_to_create)
                    
                    gc.collect()
            
            offset += chunk_size
            
            if limit and offset >= limit:
                break
            
            # Progress update
            self.stdout.write(f"   Total unique donors processed so far: {len(seen_donor_ids):,}")
        
        self.stdout.write(f"✅ Mapped {total_donors:,} donors\n")
        return total_donors

    def map_contributions(self, limit=None):
        """Map contribution transactions in batches."""
        self.stdout.write("→ Mapping Contributions (processing in batches)...")
        
        # Count total for progress
        with connection.cursor() as cursor:
            cursor.execute(f'''
                SELECT COUNT(*)
                FROM mdb_transactions t
                WHERE t."TransactionTypeID" IN ({','.join(map(str, CONTRIBUTION_TRANSACTION_TYPES))})
                  AND t."Deleted" = 0
            ''')
            total_count = cursor.fetchone()[0]
        
        self.stdout.write(f"   Total contributions to process: {total_count:,}")
        
        # Process in batches with offset/limit
        offset = 0
        batch_size = 10000
        total_mapped = 0
        
        while True:
            self.stdout.write(f"   Processing batch at offset {offset:,}...")
            
            query = f'''
                SELECT 
                    t."TransactionID",
                    t."NameID",
                    t."CommitteeID",
                    t."TransactionDate",
                    t."Amount",
                    t."Memo"
                FROM mdb_transactions t
                WHERE t."TransactionTypeID" IN ({','.join(map(str, CONTRIBUTION_TRANSACTION_TYPES))})
                  AND t."Deleted" = 0
                ORDER BY t."TransactionID"
                LIMIT {batch_size}
                OFFSET {offset}
            '''
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            if not rows:
                break
            
            contributions_to_create = []
            
            for row in rows:
                trans_id, name_id, committee_id, trans_date, amount, memo = row
                
                try:
                    donor = None
                    if name_id:
                        donor = DonorEntity.objects.filter(id=name_id).first()
                    
                    committee = None
                    if committee_id:
                        committee = IECommittee.objects.filter(id=committee_id).first()
                    
                    date = self.parse_date(trans_date)
                    year = date.year if date else None
                    amount_val = Decimal(str(amount)) if amount else Decimal(0)
                    
                    contributions_to_create.append(Contribution(
                        donor=donor,
                        committee=committee,
                        amount=amount_val,
                        date=date,
                        year=year,
                        raw={'transaction_id': trans_id, 'memo': memo},
                        source_mdb_transaction_id=trans_id,
                    ))
                    
                except Exception as e:
                    self.stderr.write(f"⚠️ Skipped contribution {trans_id}: {e}")
                    continue
            
            if contributions_to_create:
                Contribution.objects.bulk_create(contributions_to_create, ignore_conflicts=True)
                total_mapped += len(contributions_to_create)
            
            offset += batch_size
            progress_pct = int(100 * offset / total_count)
            self.stdout.write(f"   Progress: {offset:,}/{total_count:,} ({progress_pct}%) - Mapped {total_mapped:,} contributions")
            
            gc.collect()
            connection.close()
            
            if limit and offset >= limit:
                break
        
        self.stdout.write(f"✅ Mapped {total_mapped:,} contributions\n")
        return total_mapped

    def map_expenditures(self, limit=None):
        """Map IE expenditure transactions."""
        self.stdout.write("→ Mapping Independent Expenditures...")
        
        ie_transactions = MDB_Transaction.objects.filter(
            transaction_type_id__in=IE_TRANSACTION_TYPES,
            deleted=0
        ).select_related()
        
        if limit:
            ie_transactions = ie_transactions[:limit]
        
        expenditures_to_create = []
        total = 0
        
        for trans in tqdm(ie_transactions, desc="IE Expenditures"):
            try:
                ie_committee = None
                if trans.committee_id:
                    ie_committee = IECommittee.objects.filter(id=trans.committee_id).first()
                
                candidate = None
                if trans.subject_committee_id:
                    candidate = Candidate.objects.filter(
                        external_id=f"committee_{trans.subject_committee_id}"
                    ).first()
                
                date = self.parse_date(trans.transaction_date)
                year = date.year if date else None
                amount = trans.amount or Decimal(0)
                
                payee_name = None
                if trans.name_id:
                    payee = MDB_Name.objects.filter(name_id=trans.name_id).first()
                    if payee:
                        payee_name = f"{payee.first_name or ''} {payee.last_name or ''}".strip()
                
                expenditures_to_create.append(Expenditure(
                    ie_committee=ie_committee,
                    candidate=candidate,
                    amount=amount,
                    date=date,
                    year=year,
                    purpose=trans.memo,
                    candidate_name=payee_name,
                    raw={'transaction_id': trans.transaction_id},
                    source_mdb_transaction=trans,
                ))
                
                if len(expenditures_to_create) >= BATCH_SIZE:
                    Expenditure.objects.bulk_create(expenditures_to_create, ignore_conflicts=True)
                    total += len(expenditures_to_create)
                    expenditures_to_create.clear()
                    gc.collect()
                    
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped IE expenditure {trans.transaction_id}: {e}")
                continue
        
        if expenditures_to_create:
            Expenditure.objects.bulk_create(expenditures_to_create, ignore_conflicts=True)
            total += len(expenditures_to_create)
        
        self.stdout.write(f"✅ Mapped {total} IE expenditures\n")
        return total
