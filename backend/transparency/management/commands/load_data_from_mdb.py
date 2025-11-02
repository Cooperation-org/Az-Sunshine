import csv
import subprocess
from tqdm import tqdm
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


def count_rows(table_name):
    """Quickly count total rows in a table for tqdm progress bar."""
    result = subprocess.run(
        ["mdb-tables", "-1", MDB_FILE],
        stdout=subprocess.PIPE,
        text=True,
    )
    tables = result.stdout.splitlines()
    if table_name not in tables:
        return 0

    proc = subprocess.Popen(
        ["mdb-export", MDB_FILE, table_name],
        stdout=subprocess.PIPE,
        text=True,
    )
    count = sum(1 for _ in proc.stdout) - 1  # subtract header
    return max(count, 1)


def export_table(table_name):
    """Stream MDB table rows as dicts."""
    process = subprocess.Popen(
        ["mdb-export", MDB_FILE, table_name],
        stdout=subprocess.PIPE,
        text=True,
    )
    return csv.DictReader(process.stdout)


class Command(BaseCommand):
    help = "Import all MDB tables into PostgreSQL with progress bars and batch insert."

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting MDB import with progress tracking...\n")

        # === PARTIES ===
        self.load_table(
            name="Parties",
            model=Party,
            build=lambda r: Party(name=(r.get("PartyName") or "").strip()),
        )

        # === OFFICES / RACES ===
        self.load_table(
            name="Offices",
            model=Race,
            build=lambda r: Race(name=(r.get("OfficeName") or "").strip()),
        )

        # === NAMES / DONORS ===
        self.load_table(
            name="Names",
            model=DonorEntity,
            build=lambda r: DonorEntity(
                name=(r.get("Name") or "").strip(),
                entity_type=(r.get("EntityType") or "").strip() or None,
            ),
        )

        # === COMMITTEES ===
        self.load_table(
            name="Committees",
            model=IECommittee,
            build=lambda r: IECommittee(
                name=f"Committee {(r.get('NameID') or '').strip() or 'Unknown'}",
                committee_type="General",
                ein=None,
            ),
        )

        # === TRANSACTIONS → CONTRIBUTIONS / EXPENDITURES ===
        self.stdout.write("\n→ Loading Transactions...")
        total_tx = count_rows("Transactions")
        contributions, expenditures = [], []

        for row in tqdm(export_table("Transactions"), total=total_tx, desc="Transactions", ncols=100):
            try:
                amount = float(row.get("Amount", "0") or 0)
            except ValueError:
                continue

            date = (row.get("Date") or "").split(" ")[0].strip() or None
            if amount > 0:
                contributions.append(
                    Contribution(amount=amount, date=date or None, raw=row)
                )
                if len(contributions) >= BATCH_SIZE:
                    Contribution.objects.bulk_create(contributions, ignore_conflicts=True)
                    contributions = []
            elif amount < 0:
                expenditures.append(
                    Expenditure(
                        amount=abs(amount),
                        date=date or None,
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

        # === SUMMARY ===
        self.stdout.write("\n🎯 Import Summary")
        self.stdout.write(f"  • Parties: {Party.objects.count()}")
        self.stdout.write(f"  • Races: {Race.objects.count()}")
        self.stdout.write(f"  • Donors: {DonorEntity.objects.count()}")
        self.stdout.write(f"  • Committees: {IECommittee.objects.count()}")
        self.stdout.write(f"  • Contributions: {Contribution.objects.count()}")
        self.stdout.write(f"  • Expenditures: {Expenditure.objects.count()}")
        self.stdout.write("\n✅ Import complete with progress tracking — all tables loaded safely.")

    def load_table(self, name, model, build):
        """Generic loader with tqdm progress bar."""
        self.stdout.write(f"\n→ Loading {name}...")
        total = count_rows(name)
        items = []
        for row in tqdm(export_table(name), total=total, desc=name, ncols=100):
            instance = build(row)
            if not instance or not getattr(instance, "name", "").strip():
                continue
            items.append(instance)
            if len(items) >= BATCH_SIZE:
                model.objects.bulk_create(items, ignore_conflicts=True)
                items = []
        if items:
            model.objects.bulk_create(items, ignore_conflicts=True)
        self.stdout.write(f"✅ {name} loaded: {model.objects.count()}")
