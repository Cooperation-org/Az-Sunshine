#!/usr/bin/env python3
import sys
import csv
import os
from decimal import Decimal
from datetime import datetime
import django

# ✅ Ensure project root is on the import path so 'config' is discoverable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# ✅ Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from transparency.models import IECommittee, DonorEntity, Expenditure, Contribution, Candidate, Race


def parse_decimal(value):
    """Safely parse a decimal number from string values."""
    try:
        return Decimal(value.replace(',', '').strip())
    except Exception:
        return Decimal('0')


def parse_date(date_str):
    """Try multiple date formats safely."""
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except Exception:
            continue
    return None


def ingest_ie_csv(path):
    """Load Independent Expenditure data (with races and candidates)."""
    created = 0
    updated = 0

    print(f"🔍 Loading CSV: {path}")

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            committee_name = (
                row.get('committee_name')
                or row.get('committee')
                or row.get('CommitteeName')
                or 'Unknown Committee'
            )
            donor_name = row.get('donor_name') or row.get('contributor') or 'Anonymous Donor'
            candidate_name = row.get('candidate') or row.get('candidate_name') or 'Unknown Candidate'
            race_name = row.get('race') or row.get('race_name') or 'General Election'
            amount = parse_decimal(row.get('amount') or row.get('Amount') or '0')
            date = parse_date(row.get('date') or row.get('Date') or row.get('expenditure_date'))

            # ✅ Create / get Race and Candidate
            race, _ = Race.objects.get_or_create(name=race_name.strip(), defaults={'is_fake': True})
            candidate, _ = Candidate.objects.get_or_create(
                name=candidate_name.strip(),
                defaults={'race': race, 'is_fake': True}
            )

            # ✅ Create / get Committee and Donor
            committee, _ = IECommittee.objects.get_or_create(
                name=committee_name.strip(),
                defaults={'is_fake': True}
            )
            donor, _ = DonorEntity.objects.get_or_create(
                name=donor_name.strip(),
                defaults={'is_fake': True}
            )

            # ✅ Record Contribution
            Contribution.objects.create(
                donor=donor,
                committee=committee,
                amount=amount,
                date=date,
                raw=row,
                is_fake=True
            )

            # ✅ Record Expenditure
            exp, created_flag = Expenditure.objects.get_or_create(
                ie_committee=committee,
                amount=amount,
                date=date,
                candidate_name=candidate_name,
                defaults={'raw': row, 'race': race, 'is_fake': True},
            )

            if created_flag:
                created += 1
            else:
                updated += 1

    print(f"✅ Ingest complete: created={created}, updated={updated}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python load_static_ie_db.py path/to/file.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)

    ingest_ie_csv(csv_path)
