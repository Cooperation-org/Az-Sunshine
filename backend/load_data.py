#!/usr/bin/env python
"""
Simple script to load CSV data into the database.
Run this after migrations to populate the database with sample data.
"""
import os
import sys
import django
import csv
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from transparency.models import (
    Race, Candidate, Party, IECommittee, DonorEntity, 
    Expenditure, Contribution, ContactLog
)

def parse_date(date_str):
    """Parse date string, return None if empty or invalid."""
    if not date_str or date_str == '':
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None

def parse_datetime(dt_str):
    """Parse datetime string, return None if empty or invalid."""
    if not dt_str or dt_str == '':
        return None
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None

def parse_bool(val):
    """Parse boolean value."""
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ('true', '1', 'yes')

def load_races():
    """Load races from CSV."""
    print("Loading races...")
    csv_path = 'transparency/data/races.csv'
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} not found, skipping...")
        return
    
    Race.objects.all().delete()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        races = []
        for row in reader:
            races.append(Race(
                id=int(row['id']),
                name=row['name'],
                office=row.get('office', ''),
                district=row.get('district', ''),
                is_fake=parse_bool(row.get('is_fake', True))
            ))
        Race.objects.bulk_create(races, batch_size=500)
    print(f"  ✓ Loaded {len(races)} races")

def load_parties():
    """Load parties."""
    print("Loading parties...")
    parties_data = [
        {'id': 1, 'name': 'Democratic'},
        {'id': 2, 'name': 'Republican'},
        {'id': 3, 'name': 'Independent'},
        {'id': 4, 'name': 'Green'},
        {'id': 5, 'name': 'Libertarian'},
    ]
    Party.objects.all().delete()
    for p in parties_data:
        Party.objects.create(**p)
    print(f"  ✓ Loaded {len(parties_data)} parties")

def load_candidates():
    """Load candidates from CSV."""
    print("Loading candidates...")
    csv_path = 'transparency/data/candidates.csv'
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} not found, skipping...")
        return
    
    Candidate.objects.all().delete()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            race_id = row.get('race_id')
            race = Race.objects.filter(id=race_id).first() if race_id else None
            
            # Assign random party
            party = Party.objects.order_by('?').first()
            
            Candidate.objects.create(
                id=int(row['id']),
                name=row['name'],
                race=race,
                party=party,
                email=row.get('email', ''),
                filing_date=parse_date(row.get('filing_date')),
                source=row.get('source', 'AZ_SOS'),
                contacted=parse_bool(row.get('contacted', False)),
                contacted_at=parse_datetime(row.get('contacted_at')),
                notes=row.get('notes', ''),
                external_id=row.get('external_id', ''),
                is_fake=parse_bool(row.get('is_fake', True)),
            )
            count += 1
            if count % 100 == 0:
                print(f"    ... {count} candidates loaded")
    print(f"  ✓ Loaded {count} candidates")

def load_committees():
    """Load IE committees from CSV."""
    print("Loading IE Committees...")
    csv_path = 'transparency/data/iecommittees.csv'
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} not found, skipping...")
        return
    
    IECommittee.objects.all().delete()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        committees = []
        for row in reader:
            committees.append(IECommittee(
                id=int(row['id']),
                name=row['name'],
                committee_type=row.get('committee_type', ''),
                ein=row.get('ein', ''),
                is_fake=parse_bool(row.get('is_fake', True))
            ))
        IECommittee.objects.bulk_create(committees, batch_size=500)
    print(f"  ✓ Loaded {len(committees)} IE committees")

def load_donors():
    """Load donor entities from CSV."""
    print("Loading donors...")
    csv_path = 'transparency/data/donors.csv'
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} not found, skipping...")
        return
    
    DonorEntity.objects.all().delete()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        donors = []
        for row in reader:
            donors.append(DonorEntity(
                id=int(row['id']),
                name=row['name'],
                entity_type=row.get('entity_type', ''),
                total_contribution=float(row.get('total_contribution', 0)),
                is_fake=parse_bool(row.get('is_fake', True))
            ))
        DonorEntity.objects.bulk_create(donors, batch_size=500)
    print(f"  ✓ Loaded {len(donors)} donors")

def load_expenditures():
    """Load expenditures from CSV."""
    print("Loading expenditures...")
    csv_path = 'transparency/data/expenditures.csv'
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} not found, skipping...")
        return
    
    import random
    Expenditure.objects.all().delete()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            committee_id = row.get('ie_committee_id')
            race_id = row.get('race_id')
            
            committee = IECommittee.objects.filter(id=committee_id).first() if committee_id else None
            race = Race.objects.filter(id=race_id).first() if race_id else None
            
            # Get support_oppose from CSV or assign randomly (60% Support, 40% Oppose)
            support_oppose = row.get('support_oppose', '')
            if not support_oppose:
                support_oppose = random.choice(['Support'] * 6 + ['Oppose'] * 4)
            
            Expenditure.objects.create(
                id=int(row['id']),
                ie_committee=committee,
                race=race,
                amount=float(row['amount']),
                date=parse_date(row.get('date')),
                candidate_name=row.get('candidate_name', ''),
                purpose=row.get('purpose', ''),
                support_oppose=support_oppose,
                is_fake=parse_bool(row.get('is_fake', True))
            )
            count += 1
            if count % 100 == 0:
                print(f"    ... {count} expenditures loaded")
    print(f"  ✓ Loaded {count} expenditures")

def load_contributions():
    """Load contributions from CSV."""
    print("Loading contributions...")
    csv_path = 'transparency/data/contributions.csv'
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} not found, skipping...")
        return
    
    Contribution.objects.all().delete()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            donor_id = row.get('donor_id')
            committee_id = row.get('committee_id')
            
            donor = DonorEntity.objects.filter(id=donor_id).first()
            committee = IECommittee.objects.filter(id=committee_id).first()
            
            if donor and committee:
                Contribution.objects.create(
                    id=int(row['id']),
                    donor=donor,
                    committee=committee,
                    amount=float(row['amount']),
                    date=parse_date(row.get('date')),
                    is_fake=parse_bool(row.get('is_fake', True))
                )
                count += 1
                if count % 100 == 0:
                    print(f"    ... {count} contributions loaded")
    print(f"  ✓ Loaded {count} contributions")

def load_contact_logs():
    """Load contact logs from CSV."""
    print("Loading contact logs...")
    csv_path = 'transparency/data/contactlogs.csv'
    if not os.path.exists(csv_path):
        print(f"  ⚠ {csv_path} not found, skipping...")
        return
    
    ContactLog.objects.all().delete()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            candidate_id = row.get('candidate_id')
            candidate = Candidate.objects.filter(id=candidate_id).first()
            
            if candidate:
                ContactLog.objects.create(
                    id=int(row['id']),
                    candidate=candidate,
                    contacted_by=row.get('contacted_by', ''),
                    method=row.get('method', 'email'),
                    status=row.get('status', 'not_contacted'),
                    note=row.get('note', ''),
                    is_fake=parse_bool(row.get('is_fake', True))
                )
                count += 1
    print(f"  ✓ Loaded {count} contact logs")

if __name__ == '__main__':
    print("\n🚀 Loading campaign finance data...\n")
    
    load_races()
    load_parties()
    load_candidates()
    load_committees()
    load_donors()
    load_expenditures()
    load_contributions()
    load_contact_logs()
    
    print("\n✅ Data loading complete!\n")
    print(f"📊 Summary:")
    print(f"   Races: {Race.objects.count()}")
    print(f"   Parties: {Party.objects.count()}")
    print(f"   Candidates: {Candidate.objects.count()}")
    print(f"   IE Committees: {IECommittee.objects.count()}")
    print(f"   Donors: {DonorEntity.objects.count()}")
    print(f"   Expenditures: {Expenditure.objects.count()}")
    print(f"   Contributions: {Contribution.objects.count()}")
    print(f"   Contact Logs: {ContactLog.objects.count()}")
    print()

