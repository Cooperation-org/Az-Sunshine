import csv
import subprocess
import tempfile
from datetime import datetime
from tqdm import tqdm
from django.core.management.base import BaseCommand
from transparency.models import Contribution, Expenditure, DonorEntity, IECommittee


class Command(BaseCommand):
    help = "Load transactions directly from an MDB file into the PostgreSQL database."

    def add_arguments(self, parser):
        parser.add_argument("--mdb", type=str, required=True, help="Path to the MDB file.")
        parser.add_argument("--limit", type=int, default=5000, help="Maximum number of rows to import.")
        parser.add_argument("--table", type=str, default="Transactions", help="MDB table name to export (default: Transactions).")

    def handle(self, *args, **options):
        mdb_path = options["mdb"]
        table_name = options["table"]
        limit = options["limit"]

        self.stdout.write(f"📂 Reading data from {mdb_path} (table: {table_name})")

        # Step 1: Extract MDB to temporary CSV
        csv_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        csv_path = csv_temp.name

        cmd = f'mdb-export -H "{mdb_path}" "{table_name}" | head -n {limit}'
        self.stdout.write(f"⚙️ Running: {cmd}")
        subprocess.run(cmd, shell=True, check=True, stdout=open(csv_path, "w"))
        self.stdout.write(f"✅ Exported to CSV: {csv_path}")

        # Step 2: Read CSV file
        with open(csv_path, newline="", encoding="utf-8", errors="ignore") as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

        self.stdout.write(f"💾 Found approx {len(rows):,} rows to process.")

        contributions_created = 0
        expenditures_created = 0
        errors = 0

        # Step 3: Process each transaction
        for row in tqdm(rows, desc="💸 Importing Transactions"):
            if not row or len(row) < 6:
                continue

            try:
                date_str = (
                    row[4]
                    .replace("“", "")
                    .replace("”", "")
                    .replace('"', "")
                    .strip()
                    if len(row) > 4
                    else ""
                )

                parsed_date = self._parse_date(date_str)
                amount = float(row[5])
                description = row[9] if len(row) > 9 else ""
                donor_id = row[6] if len(row) > 6 and row[6] else None
                committee_id = row[3] if len(row) > 3 and row[3] else None

                # Ensure donor and committee exist
                donor, _ = DonorEntity.objects.get_or_create(
                    name=f"Donor {donor_id or 'Unknown'}"
                )
                committee, _ = IECommittee.objects.get_or_create(
                    name=f"Committee {committee_id or 'Unknown'}"
                )

                # Positive = contribution, Negative = expenditure
                if amount > 0:
                    Contribution.objects.create(
                        donor=donor,
                        committee=committee,
                        amount=amount,
                        date=parsed_date,
                        year=parsed_date.year if parsed_date else None,
                        raw=row,
                    )
                    contributions_created += 1
                elif amount < 0:
                    Expenditure.objects.create(
                        ie_committee=committee,
                        amount=abs(amount),
                        date=parsed_date,
                        year=parsed_date.year if parsed_date else None,
                        purpose=description,
                        raw=row,
                    )
                    expenditures_created += 1

            except Exception as e:
                errors += 1
                self.stdout.write(f"❗ Error on row {rows.index(row)}: {e}")

        # Step 4: Summary
        self.stdout.write("\n✅ Import Summary")
        self.stdout.write(f"  • Contributions: {contributions_created:,}")
        self.stdout.write(f"  • Expenditures:  {expenditures_created:,}")
        if errors:
            self.stdout.write(f"  ⚠️ Skipped {errors:,} rows due to errors.")

    def _parse_date(self, date_str):
        """Parse multiple date formats safely."""
        if not date_str:
            return None
        date_str = date_str.split(" ")[0].strip()
        patterns = ["%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"]
        for fmt in patterns:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.year < 1920:
                    dt = dt.replace(year=dt.year + 2000)
                return dt.date()
            except ValueError:
                continue
        return None
