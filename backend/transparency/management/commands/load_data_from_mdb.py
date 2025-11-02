import csv
import subprocess
from django.core.management.base import BaseCommand
from transparency.models import (
    Party,
    Race,
    Candidate,
    IECommittee,
    DonorEntity,
    Expenditure,
    Contribution,
    ContactLog,
    StatementOfInterest,
)

MDB_FILE = "2025 1020 CFS_Export_PRR.mdb"
BATCH_SIZE = 1000


def export_table(table_name):
    """Stream data from an MDB table as dictionaries."""
    process = subprocess.Popen(
        ["mdb-export", MDB_FILE, table_name],
        stdout=subprocess.PIPE,
        text=True,
    )
    return csv.DictReader(process.stdout)


class Command(BaseCommand):
    help = "Safely import all MDB tables into PostgreSQL without RAM overload."

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting MDB import...")

        # === PARTIES ===
        self.stdout.write("→ Loading Parties...")
        parties = []
        for row in export_table("Parties"):
            name = (row.get("PartyName") or "").strip()
            if not name:
                continue
            parties.append(Party(name=name))
            if len(parties) >= BATCH_SIZE:
                Party.objects.bulk_create(parties, ignore_conflicts=True)
                parties = []
        if parties:
            Party.objects.bulk_create(parties, ignore_conflicts=True)
        self.stdout.write(f"✅ Parties loaded: {Party.objects.count()}")

        # === OFFICES / RACES ===
        self.stdout.write("→ Loading Offices...")
        races = []
        for row in export_table("Offices"):
            name = (row.get("OfficeName") or "").strip()
            if not name:
                continue
            races.append(Race(name=name))
            if len(races) >= BATCH_SIZE:
                Race.objects.bulk_create(races, ignore_conflicts=True)
                races = []
        if races:
            Race.objects.bulk_create(races, ignore_conflicts=True)
        self.stdout.write(f"✅ Offices/Races loaded: {Race.objects.count()}")

        # === NAMES / DONORS ===
        self.stdout.write("→ Loading Names...")
        donors = []
        for row in export_table("Names"):
            name = (row.get("Name") or "").strip()
            if not name:
                continue
            donors.append(
                DonorEntity(
                    name=name,
                    entity_type=(row.get("EntityType") or "").strip() or None,
                )
            )
            if len(donors) >= BATCH_SIZE:
                DonorEntity.objects.bulk_create(donors, ignore_conflicts=True)
                donors = []
        if donors:
            DonorEntity.objects.bulk_create(donors, ignore_conflicts=True)
        self.stdout.write(f"✅ Donor Entities loaded: {DonorEntity.objects.count()}")

        # === COMMITTEES ===
        self.stdout.write("→ Loading Committees...")
        committees = []
        for row in export_table("Committees"):
            name_id = (row.get("NameID") or "").strip()
            committees.append(
                IECommittee(
                    name=f"Committee {name_id}" if name_id else "Unknown Committee",
                    committee_type="General",
                    ein=None,
                )
            )
            if len(committees) >= BATCH_SIZE:
                IECommittee.objects.bulk_create(committees, ignore_conflicts=True)
                committees = []
        if committees:
            IECommittee.objects.bulk_create(committees, ignore_conflicts=True)
        self.stdout.write(f"✅ Committees loaded: {IECommittee.objects.count()}")

        # === TRANSACTIONS → CONTRIBUTIONS / EXPENDITURES ===
        self.stdout.write("→ Loading Transactions...")
        contributions = []
        expenditures = []
        for row in export_table("Transactions"):
            try:
                amount = float(row.get("Amount", "0") or 0)
            except ValueError:
                continue

            date = (row.get("Date") or "").split(" ")[0].strip() or None
            committee_id = (row.get("CommitteeID") or "").strip()
            donor_id = (row.get("NameID") or "").strip()

            if amount > 0:
                contributions.append(
                    Contribution(
                        amount=amount,
                        date=date or None,
                        year=None,
                        raw=row,
                    )
                )
                if len(contributions) >= BATCH_SIZE:
                    Contribution.objects.bulk_create(contributions, ignore_conflicts=True)
                    contributions = []
            elif amount < 0:
                expenditures.append(
                    Expenditure(
                        amount=abs(amount),
                        date=date or None,
                        year=None,
                        purpose=row.get("Description", ""),
                        raw=row,
                    )
                )
                if len(expenditures) >= BATCH_SIZE:
                    Expenditure.objects.bulk_create(expenditures, ignore_conflicts=True)
                    expenditures = []

        if contributions:
            Contribution.objects.bulk_create(contributions, ignore_conflicts=True)
        if expenditures:
            Expenditure.objects.bulk_create(expenditures, ignore_conflicts=True)

        self.stdout.write(f"✅ Contributions loaded: {Contribution.objects.count()}")
        self.stdout.write(f"✅ Expenditures loaded: {Expenditure.objects.count()}")

        # === SUMMARY ===
        self.stdout.write("\n🎯 Import Summary")
        self.stdout.write(f"  • Parties: {Party.objects.count()}")
        self.stdout.write(f"  • Races: {Race.objects.count()}")
        self.stdout.write(f"  • Donors: {DonorEntity.objects.count()}")
        self.stdout.write(f"  • Committees: {IECommittee.objects.count()}")
        self.stdout.write(f"  • Contributions: {Contribution.objects.count()}")
        self.stdout.write(f"  • Expenditures: {Expenditure.objects.count()}")
        self.stdout.write("✅ Import complete — all tables loaded safely without RAM overflow.")
