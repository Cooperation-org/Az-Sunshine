import csv
import subprocess
import gc
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import connection
from tqdm import tqdm
from transparency.models import Party, IECommittee, Candidate, DonorEntity, Contribution

MDB_PATH = "/opt/az_sunshine/backend/2025 1020 CFS_Export_PRR.mdb"
BATCH_SIZE = 2000


class Command(BaseCommand):
    help = "Load data from the Arizona CFS Access MDB file into Django models (aligned and batched)"

    # --------------------------------------------------------------------------
    # Entry point
    # --------------------------------------------------------------------------
    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting MDB data import...\n")

        self.load_parties()
        self.load_committees()
        self.load_candidates()
        self.load_donors()
        self.load_contributions()

        self.stdout.write("🎉 All data imported successfully!\n")

    # --------------------------------------------------------------------------
    # Helper: stream MDB output line by line
    # --------------------------------------------------------------------------
    def run_mdb_export(self, table_name):
        """Stream MDB table rows line by line."""
        process = subprocess.Popen(
            ["mdb-export", "-H", MDB_PATH, table_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        for line in process.stdout:
            yield line.strip()

        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            err = process.stderr.read()
            self.stderr.write(f"❌ Error reading {table_name}: {err}")

    # --------------------------------------------------------------------------
    # Load Parties
    # --------------------------------------------------------------------------
    def load_parties(self):
        self.stdout.write("→ Loading Parties...")
        reader = csv.reader(self.run_mdb_export("Parties"))
        batch = []
        total = 0

        for row in tqdm(reader, desc="Parties", unit="rows"):
            try:
                if len(row) < 2:
                    continue
                party_id = int(row[0])
                name = row[1].strip()
                if name:
                    batch.append(Party(id=party_id, name=name))
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped Party row {row}: {e}")
                continue

        if batch:
            Party.objects.bulk_create(batch, ignore_conflicts=True)
            total = len(batch)

        self.stdout.write(f"✅ Parties loaded successfully! ({total} total)\n")

    # --------------------------------------------------------------------------
    # Load Committees (Fixed column index for name)
    # --------------------------------------------------------------------------
    def load_committees(self):
        self.stdout.write("→ Loading Committees...")
        reader = csv.reader(self.run_mdb_export("Committees"))
        batch, total = [], 0

        for row in tqdm(reader, desc="Committees", unit="rows"):
            try:
                if len(row) < 19:
                    continue
                ext_id = int(row[0])
                name = row[18].strip() if len(row) > 18 else ""
                if name:
                    batch.append(IECommittee(id=ext_id, name=name))
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped Committee row {row}: {e}")
                continue

            if len(batch) >= BATCH_SIZE:
                IECommittee.objects.bulk_create(batch, ignore_conflicts=True)
                total += len(batch)
                batch.clear()
                connection.close()
                gc.collect()

        if batch:
            IECommittee.objects.bulk_create(batch, ignore_conflicts=True)
            total += len(batch)

        self.stdout.write(f"✅ Committees loaded successfully! ({total} total)\n")

    # --------------------------------------------------------------------------
    # Load Candidates
    # --------------------------------------------------------------------------
    def load_candidates(self):
        self.stdout.write("→ Loading Candidates...")
        reader = csv.reader(self.run_mdb_export("Names"))
        batch, total = [], 0

        for row in tqdm(reader, desc="Candidates", unit="rows"):
            try:
                if len(row) < 4:
                    continue
                ext_id = row[0]
                name = row[3].strip().title()
                if name:
                    batch.append(Candidate(external_id=ext_id, name=name))
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped Candidate row {row}: {e}")
                continue

            if len(batch) >= BATCH_SIZE:
                Candidate.objects.bulk_create(batch, ignore_conflicts=True)
                total += len(batch)
                batch.clear()
                connection.close()
                gc.collect()

        if batch:
            Candidate.objects.bulk_create(batch, ignore_conflicts=True)
            total += len(batch)

        self.stdout.write(f"✅ Candidates loaded successfully! ({total} total)\n")

    # --------------------------------------------------------------------------
    # Load Donors
    # --------------------------------------------------------------------------
    def load_donors(self):
        self.stdout.write("→ Loading Donors...")
        reader = csv.reader(self.run_mdb_export("Names"))
        batch, total = [], 0

        for row in tqdm(reader, desc="Donors", unit="rows"):
            try:
                if len(row) < 4:
                    continue
                name = row[3].strip().title()
                if name:
                    batch.append(DonorEntity(name=name))
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped Donor row {row}: {e}")
                continue

            if len(batch) >= BATCH_SIZE:
                DonorEntity.objects.bulk_create(batch, ignore_conflicts=True)
                total += len(batch)
                batch.clear()
                connection.close()
                gc.collect()

        if batch:
            DonorEntity.objects.bulk_create(batch, ignore_conflicts=True)
            total += len(batch)

        self.stdout.write(f"✅ Donors loaded successfully! ({total} total)\n")

    # --------------------------------------------------------------------------
    # Load Contributions
    # --------------------------------------------------------------------------
    def load_contributions(self):
        self.stdout.write("→ Loading Contributions (Donor → Committee)...")
        reader = csv.reader(self.run_mdb_export("Transactions"))
        batch, total = [], 0

        for row in tqdm(reader, desc="Contributions", unit="rows"):
            try:
                if len(row) < 6:
                    continue

                donor_id = int(row[1]) if row[1] else None
                committee_id = int(row[2]) if row[2] else None
                amount = Decimal(row[5].replace(",", "")) if row[5] else Decimal(0)
                date_raw = row[4].replace('"', "").split(" ")[0] if row[4] else ""

                date = None
                for fmt in ("%m/%d/%y", "%m/%d/%Y"):
                    try:
                        if date_raw:
                            date = datetime.strptime(date_raw, fmt).date()
                            break
                    except ValueError:
                        continue

                donor = DonorEntity.objects.filter(id=donor_id).first() if donor_id else None
                committee = IECommittee.objects.filter(id=committee_id).first() if committee_id else None

                batch.append(
                    Contribution(
                        donor=donor,
                        committee=committee,
                        amount=amount,
                        date=date,
                        year=date.year if date else None,
                        raw={"source_row": row},
                    )
                )
            except Exception as e:
                self.stderr.write(f"⚠️ Skipped Transaction row {row}: {e}")
                continue

            if len(batch) >= BATCH_SIZE:
                Contribution.objects.bulk_create(batch, ignore_conflicts=True)
                total += len(batch)
                batch.clear()
                connection.close()
                gc.collect()

        if batch:
            Contribution.objects.bulk_create(batch, ignore_conflicts=True)
            total += len(batch)

        self.stdout.write(f"✅ Contributions loaded successfully! ({total} total)\n")
