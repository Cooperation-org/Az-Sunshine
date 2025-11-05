import gc
import time
import traceback
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection, transaction
from tqdm import tqdm
from transparency.models import (
    Party, Race, Candidate, IECommittee, DonorEntity, Contribution, Expenditure,
    MDB_Name, MDB_Committee, MDB_Transaction, MDB_Party,
    MDB_EntityType, MDB_TransactionType, MDB_Office, MDB_Category
)

# CRITICAL: Aggressive batch sizes for speed
BATCH_SIZE = 10000           # Large batches = fewer DB round trips
CHUNK_SIZE = 100000          # Process 100k at a time
CACHE_REFRESH_INTERVAL = 50000  # Refresh caches periodically
SLEEP_INTERVAL = 0.5         # Sleep after each batch to let PostgreSQL flush cache

NOTIFICATION_EMAIL = 'emosmwangi@gmail.com'
CONTRIBUTION_TRANSACTION_TYPES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
IE_TRANSACTION_TYPES = [33, 34, 76, 243, 274]


class Command(BaseCommand):
    help = "PRODUCTION-OPTIMIZED: Map MDB data with maximum speed and reliability"

    def __init__(self):
        super().__init__()
        # Pre-load lookup caches - THIS IS THE KEY TO SPEED
        self.party_cache = {}
        self.office_cache = {}
        self.entity_type_cache = {}
        self.race_cache = {}
        self.race_by_office_id = {}
        self.donor_cache = {}
        self.committee_cache = {}
        self.candidate_cache = {}

    def add_arguments(self, parser):
        parser.add_argument('--step', type=str, help='Run specific step')
        parser.add_argument('--limit', type=int, help='Limit records (testing only)')
        parser.add_argument('--no-email', action='store_true', help='Disable email')

    def handle(self, *args, **options):
        step = options.get('step')
        limit = options.get('limit')
        send_email = not options.get('no_email', False)
        
        start_time = datetime.now()
        results = {}
        
        try:
            self.stdout.write("=" * 60)
            self.stdout.write("🚀 PRODUCTION MDB MAPPING - OPTIMIZED FOR SPEED")
            self.stdout.write("=" * 60 + "\n")
            
            # CRITICAL: Load all lookups into memory ONCE
            self.stdout.write("📦 Loading lookup caches (this makes everything fast)...")
            self.load_all_caches()
            self.stdout.write("✅ Caches loaded\n")
            
            if step:
                results[step] = getattr(self, f'map_{step}')(limit)
            else:
                # Run in optimal order
                results['parties'] = self.map_parties(limit)
                results['races'] = self.ensure_races_exist()
                self.refresh_race_cache()  # Reload after creating races
                
                results['candidates'] = self.map_candidates(limit)
                results['ie_committees'] = self.map_ie_committees(limit)
                results['donors'] = self.map_donors(limit)
                
                # Refresh caches before large operations
                self.stdout.write("🔄 Refreshing caches before transactions...\n")
                self.refresh_donor_cache()
                self.refresh_committee_cache()
                self.refresh_candidate_cache()
                
                results['contributions'] = self.map_contributions(limit)
                results['expenditures'] = self.map_expenditures(limit)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(f"🎉 COMPLETE! Duration: {duration}")
            self.stdout.write("=" * 60)
            self.print_results(results)
            
            if send_email:
                self.send_success_email(results, start_time, end_time, duration)
                
        except Exception as e:
            end_time = datetime.now()
            duration = end_time - start_time
            error_msg = f"CRITICAL ERROR:\n{str(e)}\n{traceback.format_exc()}"
            self.stderr.write(self.style.ERROR(error_msg))
            
            if send_email:
                self.send_error_email(error_msg, results, start_time, end_time, duration)
            raise

    def load_all_caches(self):
        """Load ALL lookups into memory - THE KEY OPTIMIZATION"""
        # Parties
        for p in Party.objects.all().iterator(chunk_size=5000):
            self.party_cache[p.id] = p
        self.stdout.write(f"  ✓ Parties: {len(self.party_cache):,}")
        
        # Offices
        for o in MDB_Office.objects.all().iterator(chunk_size=5000):
            self.office_cache[o.office_id] = o
        self.stdout.write(f"  ✓ Offices: {len(self.office_cache):,}")
        
        # Entity types
        for et in MDB_EntityType.objects.all().iterator(chunk_size=5000):
            self.entity_type_cache[et.entity_type_id] = et
        self.stdout.write(f"  ✓ Entity Types: {len(self.entity_type_cache):,}")
        
        # Races
        self.refresh_race_cache()

    def refresh_race_cache(self):
        """Reload race cache"""
        self.race_cache.clear()
        self.race_by_office_id.clear()
        for r in Race.objects.all().iterator(chunk_size=5000):
            self.race_cache[r.name] = r
            if r.source_mdb_office_id:
                self.race_by_office_id[r.source_mdb_office_id] = r
        self.stdout.write(f"  ✓ Races: {len(self.race_cache):,}")

    def refresh_donor_cache(self):
        """Reload donor cache"""
        self.donor_cache.clear()
        for d in DonorEntity.objects.all().iterator(chunk_size=10000):
            self.donor_cache[d.id] = d
        self.stdout.write(f"  ✓ Donors: {len(self.donor_cache):,}")

    def refresh_committee_cache(self):
        """Reload committee cache"""
        self.committee_cache.clear()
        for c in IECommittee.objects.all().iterator(chunk_size=10000):
            self.committee_cache[c.id] = c
        self.stdout.write(f"  ✓ Committees: {len(self.committee_cache):,}")

    def refresh_candidate_cache(self):
        """Reload candidate cache"""
        self.candidate_cache.clear()
        for cand in Candidate.objects.all().iterator(chunk_size=10000):
            if cand.external_id:
                self.candidate_cache[cand.external_id] = cand
        self.stdout.write(f"  ✓ Candidates: {len(self.candidate_cache):,}")

    def parse_date(self, date_str):
        """Fast date parser"""
        if not date_str:
            return None
        date_str = date_str.strip().split(' ')[0]
        for fmt in ("%m/%d/%y", "%m/%d/%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def map_parties(self, limit=None):
        """Map parties - fast and simple"""
        self.stdout.write("→ Mapping Parties...")
        
        query = 'SELECT "PartyID", "PartyName" FROM mdb_parties ORDER BY "PartyID"'
        if limit:
            query += f' LIMIT {limit}'
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        
        parties = [
            Party(id=row[0], name=row[1], source_mdb_party_id=row[0])
            for row in rows
        ]
        
        Party.objects.bulk_create(parties, batch_size=BATCH_SIZE, ignore_conflicts=True)
        time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
        
        # Reload cache
        self.party_cache = {p.id: p for p in Party.objects.all()}
        
        total = Party.objects.count()
        self.stdout.write(f"✅ Parties: {total:,}\n")
        return total

    def ensure_races_exist(self):
        """Create Race records for all offices"""
        self.stdout.write("→ Ensuring races exist for all offices...")
        
        existing_office_ids = set(
            Race.objects.filter(source_mdb_office__isnull=False)
            .values_list('source_mdb_office_id', flat=True)
        )
        
        races_to_create = []
        for office_id, office in self.office_cache.items():
            if office_id not in existing_office_ids:
                races_to_create.append(Race(
                    name=office.office_name,
                    office=office.office_name,
                    source_mdb_office_id=office_id
                ))
        
        if races_to_create:
            Race.objects.bulk_create(races_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
            time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
            self.stdout.write(f"  Created {len(races_to_create):,} new races")
        
        total = Race.objects.count()
        self.stdout.write(f"✅ Races: {total:,}\n")
        return total

    def map_candidates(self, limit=None):
        """Map candidates with raw SQL + bulk operations"""
        self.stdout.write("→ Mapping Candidates...")
        
        query = """
            SELECT 
                c."CommitteeID",
                c."CandidateNameID",
                c."CandidatePartyID",
                c."CandidateOfficeID",
                c."OrganizationDate",
                n."FirstName",
                n."MiddleName",
                n."LastName",
                n."Suffix"
            FROM mdb_committees c
            LEFT JOIN mdb_names n ON n."NameID" = c."CandidateNameID"
            WHERE c."CandidateNameID" IS NOT NULL
            ORDER BY c."CommitteeID"
        """
        if limit:
            query += f' LIMIT {limit}'
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        
        self.stdout.write(f"  Processing {len(rows):,} candidate committees...")
        
        candidates_to_create = []
        now = datetime.now()
        
        for row in rows:
            comm_id, name_id, party_id, office_id, org_date, first, middle, last, suffix = row
            
            # Build name
            name_parts = [p for p in [first, middle, last, suffix] if p]
            full_name = ' '.join(name_parts).strip()
            if not full_name:
                continue
            
            # Get party from cache
            party = self.party_cache.get(party_id) if party_id else None
            
            # Get race from cache
            race = self.race_by_office_id.get(office_id) if office_id else None
            
            # Parse date
            filing_date = self.parse_date(org_date) if org_date else None
            
            candidates_to_create.append(Candidate(
                name=full_name,
                race=race,
                party=party,
                filing_date=filing_date,
                source="MDB",
                external_id=f"committee_{comm_id}",
                source_mdb_committee_id=comm_id,
                source_mdb_candidate_name_id=name_id,
                created_at=now,
                updated_at=now
            ))
            
            if len(candidates_to_create) >= BATCH_SIZE:
                Candidate.objects.bulk_create(candidates_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
                time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
                candidates_to_create.clear()
                gc.collect()
        
        if candidates_to_create:
            Candidate.objects.bulk_create(candidates_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)
            time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
        
        total = Candidate.objects.count()
        self.stdout.write(f"✅ Candidates: {total:,}\n")
        return total

    def map_ie_committees(self, limit=None):
        """Map IE committees"""
        self.stdout.write("→ Mapping IE Committees...")
        
        query = """
            SELECT 
                c."CommitteeID",
                c."NameID",
                n."LastName",
                n."EntityTypeID"
            FROM mdb_committees c
            LEFT JOIN mdb_names n ON n."NameID" = c."NameID"
            WHERE c."CandidateNameID" IS NULL
            ORDER BY c."CommitteeID"
        """
        if limit:
            query += f' LIMIT {limit}'
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        
        self.stdout.write(f"  Processing {len(rows):,} IE committees...")
        
        ie_committees = []
        for comm_id, name_id, last_name, entity_type_id in rows:
            if not name_id:
                continue
            
            name = last_name or f"Committee {comm_id}"
            
            entity_type = None
            if entity_type_id and entity_type_id in self.entity_type_cache:
                entity_type = self.entity_type_cache[entity_type_id].entity_type_name
            
            ie_committees.append(IECommittee(
                id=comm_id,
                name=name,
                committee_type=entity_type,
                source_mdb_committee_id=comm_id,
                source_mdb_committee_name_id=name_id
            ))
            
            if len(ie_committees) >= BATCH_SIZE:
                IECommittee.objects.bulk_create(ie_committees, batch_size=BATCH_SIZE, ignore_conflicts=True)
                time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
                ie_committees.clear()
                gc.collect()
        
        if ie_committees:
            IECommittee.objects.bulk_create(ie_committees, batch_size=BATCH_SIZE, ignore_conflicts=True)
            time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
        
        total = IECommittee.objects.count()
        self.stdout.write(f"✅ IE Committees: {total:,}\n")
        return total

    def map_donors(self, limit=None):
        """Map donors - FAST with raw SQL"""
        self.stdout.write("→ Mapping Donors...")
        
        # Get unique donor IDs in one query
        query = f"""
            SELECT DISTINCT t."NameID"
            FROM mdb_transactions t
            WHERE t."TransactionTypeID" IN ({','.join(map(str, CONTRIBUTION_TRANSACTION_TYPES))})
              AND t."NameID" IS NOT NULL
              AND t."Deleted" = 0
        """
        if limit:
            query += f' LIMIT {limit}'
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            donor_ids = [row[0] for row in cursor.fetchall()]
        
        self.stdout.write(f"  Found {len(donor_ids):,} unique donors")
        
        # Process in chunks
        total = 0
        for i in range(0, len(donor_ids), CHUNK_SIZE):
            chunk = donor_ids[i:i+CHUNK_SIZE]
            
            # Bulk fetch names with entity types
            query = """
                SELECT 
                    n."NameID",
                    n."FirstName",
                    n."MiddleName",
                    n."LastName",
                    n."EntityTypeID"
                FROM mdb_names n
                WHERE n."NameID" = ANY(%s)
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, [chunk])
                rows = cursor.fetchall()
            
            donors = []
            for name_id, first, middle, last, entity_type_id in rows:
                name_parts = [p for p in [first, middle, last] if p]
                full_name = ' '.join(name_parts).strip() or last or f"Donor {name_id}"
                
                entity_type = None
                if entity_type_id and entity_type_id in self.entity_type_cache:
                    entity_type = self.entity_type_cache[entity_type_id].entity_type_name
                
                donors.append(DonorEntity(
                    id=name_id,
                    name=full_name,
                    entity_type=entity_type,
                    source_mdb_name_id=name_id
                ))
            
            DonorEntity.objects.bulk_create(donors, batch_size=BATCH_SIZE, ignore_conflicts=True)
            time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
            total += len(donors)
            
            self.stdout.write(f"  Progress: {i+len(chunk):,}/{len(donor_ids):,}")
            gc.collect()
        
        self.stdout.write(f"✅ Donors: {total:,}\n")
        return total

    def map_contributions(self, limit=None):
        """Map contributions - MAXIMUM SPEED"""
        self.stdout.write("→ Mapping Contributions...")
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*)
            FROM mdb_transactions t
            WHERE t."TransactionTypeID" IN ({','.join(map(str, CONTRIBUTION_TRANSACTION_TYPES))})
              AND t."Deleted" = 0
        """
        
        with connection.cursor() as cursor:
            cursor.execute(count_query)
            total_count = cursor.fetchone()[0]
        
        self.stdout.write(f"  Total: {total_count:,} contributions to process")
        
        # Process in large chunks
        offset = 0
        total_mapped = 0
        
        while True:
            query = f"""
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
                LIMIT {CHUNK_SIZE} OFFSET {offset}
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            
            if not rows:
                break
            
            contributions = []
            for trans_id, name_id, comm_id, trans_date, amount, memo in rows:
                donor = self.donor_cache.get(name_id) if name_id else None
                committee = self.committee_cache.get(comm_id) if comm_id else None
                
                date = self.parse_date(trans_date) if trans_date else None
                year = date.year if date else None
                amount_val = Decimal(str(amount)) if amount else Decimal(0)
                
                contributions.append(Contribution(
                    donor=donor,
                    committee=committee,
                    amount=amount_val,
                    date=date,
                    year=year,
                    raw={'transaction_id': trans_id, 'memo': memo},
                    source_mdb_transaction_id=trans_id
                ))
            
            Contribution.objects.bulk_create(contributions, batch_size=BATCH_SIZE, ignore_conflicts=True)
            time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache - CRITICAL for large operations
            total_mapped += len(contributions)
            
            offset += CHUNK_SIZE
            progress = int(100 * offset / total_count) if total_count else 0
            self.stdout.write(f"  Progress: {progress}% ({total_mapped:,}/{total_count:,})")
            
            gc.collect()
            connection.close()  # Refresh connection
            
            if limit and offset >= limit:
                break
        
        self.stdout.write(f"✅ Contributions: {total_mapped:,}\n")
        return total_mapped

    def map_expenditures(self, limit=None):
        """Map expenditures"""
        self.stdout.write("→ Mapping Expenditures...")
        
        query = f"""
            SELECT 
                t."TransactionID",
                t."CommitteeID",
                t."SubjectCommitteeID",
                t."NameID",
                t."TransactionDate",
                t."Amount",
                t."Memo",
                n."FirstName",
                n."LastName"
            FROM mdb_transactions t
            LEFT JOIN mdb_names n ON n."NameID" = t."NameID"
            WHERE t."TransactionTypeID" IN ({','.join(map(str, IE_TRANSACTION_TYPES))})
              AND t."Deleted" = 0
            ORDER BY t."TransactionID"
        """
        if limit:
            query += f' LIMIT {limit}'
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        
        self.stdout.write(f"  Processing {len(rows):,} expenditures...")
        
        expenditures = []
        total = 0
        
        for trans_id, comm_id, subj_comm_id, name_id, trans_date, amount, memo, first, last in rows:
            ie_committee = self.committee_cache.get(comm_id) if comm_id else None
            candidate = self.candidate_cache.get(f"committee_{subj_comm_id}") if subj_comm_id else None
            
            date = self.parse_date(trans_date) if trans_date else None
            year = date.year if date else None
            amount_val = Decimal(str(amount)) if amount else Decimal(0)
            
            payee_name = None
            if first or last:
                payee_name = f"{first or ''} {last or ''}".strip()
            
            expenditures.append(Expenditure(
                ie_committee=ie_committee,
                candidate=candidate,
                amount=amount_val,
                date=date,
                year=year,
                purpose=memo,
                candidate_name=payee_name,
                raw={'transaction_id': trans_id},
                source_mdb_transaction_id=trans_id
            ))
            
            if len(expenditures) >= BATCH_SIZE:
                Expenditure.objects.bulk_create(expenditures, batch_size=BATCH_SIZE, ignore_conflicts=True)
                time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
                total += len(expenditures)
                expenditures.clear()
                gc.collect()
        
        if expenditures:
            Expenditure.objects.bulk_create(expenditures, batch_size=BATCH_SIZE, ignore_conflicts=True)
            time.sleep(SLEEP_INTERVAL)  # Let PostgreSQL flush cache
            total += len(expenditures)
        
        self.stdout.write(f"✅ Expenditures: {total:,}\n")
        return total

    def print_results(self, results):
        """Print summary"""
        self.stdout.write("\nResults Summary:")
        self.stdout.write("-" * 40)
        for step, count in results.items():
            self.stdout.write(f"  • {step.replace('_', ' ').title()}: {count:,} records")
        self.stdout.write("-" * 40)

    def send_success_email(self, results, start_time, end_time, duration):
        subject = "✅ MDB Mapping Complete - SUCCESS"
        message = f"""
MDB to Application Mapping completed successfully!

Duration: {duration}
Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}

Results:
--------
{chr(10).join(f'• {k.replace("_", " ").title()}: {v:,} records' for k, v in results.items())}

Server: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'az-sunshine'}
"""
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [NOTIFICATION_EMAIL])
            self.stdout.write(f"📧 Email sent to {NOTIFICATION_EMAIL}")
        except Exception as e:
            self.stderr.write(f"⚠️ Email failed: {e}")

    def send_error_email(self, error_msg, partial_results, start_time, end_time, duration):
        subject = "❌ MDB Mapping FAILED - Immediate Action Required"
        message = f"""
MDB Mapping has FAILED!

Duration: {duration}
Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
Failure: {end_time.strftime('%Y-%m-%d %H:%M:%S')}

ERROR:
------
{error_msg}

Partial Results:
----------------
{chr(10).join(f'• {k}: {v:,}' for k, v in partial_results.items()) if partial_results else 'No steps completed'}

Server: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'az-sunshine'}

Check server logs immediately!
"""
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [NOTIFICATION_EMAIL])
        except Exception as e:
            self.stderr.write(f"⚠️ Email failed: {e}")