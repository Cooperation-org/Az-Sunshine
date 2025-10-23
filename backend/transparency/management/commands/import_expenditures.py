from django.core.management.base import BaseCommand
from transparency.models import IECommittee, DonorEntity, Candidate, Expenditure
import csv
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = "Import independent expenditures from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csvfile", type=str)

    def handle(self, *args, **options):
        path = options["csvfile"]
        count = 0
        self.stdout.write(f"Importing expenditures from {path} ...")

        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    committee_name = row.get("committee_name") or row.get("Committee")
                    candidate_name = row.get("candidate_name") or row.get("Candidate")
                    donor_name = row.get("donor_name") or row.get("Donor")
                    amount_raw = row.get("amount") or row.get("Amount")
                    date_raw = row.get("date") or row.get("Date")

                    if not (committee_name and candidate_name and amount_raw):
                        continue

                    committee, _ = IECommittee.objects.get_or_create(name=committee_name)
                    donor = None
                    if donor_name:
                        donor, _ = DonorEntity.objects.get_or_create(name=donor_name)

                    candidate, _ = Candidate.objects.get_or_create(
                        name=candidate_name, defaults={"race": None}
                    )

                    try:
                        amount = Decimal(amount_raw.replace(",", "").replace("$", ""))
                    except Exception:
                        continue

                    try:
                        date = datetime.strptime(date_raw, "%Y-%m-%d").date()
                    except Exception:
                        date = None

                    exists = Expenditure.objects.filter(
                        committee=committee, candidate=candidate, amount=amount, date=date
                    ).exists()

                    if not exists:
                        Expenditure.objects.create(
                            committee=committee,
                            candidate=candidate,
                            donor=donor,
                            amount=amount,
                            date=date,
                            purpose=row.get("purpose") or row.get("Purpose"),
                            support_oppose=row.get("support_oppose")
                            or row.get("SupportOppose")
                            or "Support",
                        )
                        count += 1

            self.stdout.write(self.style.SUCCESS(f"Imported {count} expenditures successfully."))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error importing data: {e}"))
