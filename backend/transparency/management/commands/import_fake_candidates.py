import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from transparency.models import (
    Race,
    Candidate,
    IECommittee,
    DonorEntity,
    Expenditure,
    Contribution,
    ContactLog,
)


class Command(BaseCommand):
    help = "Import fake CSV data for testing (10,000 rows simulated)"

    def handle(self, *args, **kwargs):
        # ✅ Use absolute path so Django finds your files correctly
        base_dir = os.path.join(settings.BASE_DIR, "transparency", "data")

        self.stdout.write(self.style.NOTICE("🚀 Starting fake data import..."))
        self.stdout.write(f"📂 Looking in: {base_dir}")

        # --- Import Races ---
        races_file = os.path.join(base_dir, "races.csv")
        if os.path.exists(races_file):
            with open(races_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    Race.objects.get_or_create(
                        name=row["name"],
                        defaults={
                            "office": row.get("office"),
                            "district": row.get("district"),
                            "is_fake": True,
                        },
                    )
            self.stdout.write(self.style.SUCCESS("✅ Races imported."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ race.csv not found, skipping."))

        # --- Import Candidates ---
        candidates_file = os.path.join(base_dir, "candidate.csv")
        if os.path.exists(candidates_file):
            with open(candidates_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    race = Race.objects.filter(name=row.get("race")).first()
                    Candidate.objects.get_or_create(
                        name=row["name"],
                        defaults={
                            "race": race,
                            "email": row.get("email"),
                            "filing_date": row.get("filing_date") or None,
                            "source": row.get("source", "AZ_SOS"),
                            "contacted": str(row.get("contacted")).lower() == "true",
                            "notes": row.get("notes"),
                            "is_fake": True,
                        },
                    )
            self.stdout.write(self.style.SUCCESS("✅ Candidates imported."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ candidate.csv not found, skipping."))

        # --- Import IE Committees ---
        committees_file = os.path.join(base_dir, "iecommittees.csv")
        if os.path.exists(committees_file):
            with open(committees_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    IECommittee.objects.get_or_create(
                        name=row["name"],
                        defaults={
                            "committee_type": row.get("committee_type"),
                            "ein": row.get("ein"),
                            "is_fake": True,
                        },
                    )
            self.stdout.write(self.style.SUCCESS("✅ IE Committees imported."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ iecommittee.csv not found, skipping."))

        # --- Import Donors ---
        donors_file = os.path.join(base_dir, "donors.csv")
        if os.path.exists(donors_file):
            with open(donors_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    DonorEntity.objects.get_or_create(
                        name=row["name"],
                        defaults={
                            "entity_type": row.get("entity_type"),
                            "total_contribution": row.get("total_contribution", 0),
                            "is_fake": True,
                        },
                    )
            self.stdout.write(self.style.SUCCESS("✅ Donor Entities imported."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ donorentity.csv not found, skipping."))

        # --- Import Expenditures ---
        expenditures_file = os.path.join(base_dir, "expenditures.csv")
        if os.path.exists(expenditures_file):
            with open(expenditures_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    committee = IECommittee.objects.filter(name=row.get("ie_committee")).first()
                    race = Race.objects.filter(name=row.get("race")).first()
                    Expenditure.objects.get_or_create(
                        ie_committee=committee,
                        amount=row.get("amount", 0),
                        date=row.get("date") or None,
                        race=race,
                        candidate_name=row.get("candidate_name"),
                        purpose=row.get("purpose"),
                        is_fake=True,
                    )
            self.stdout.write(self.style.SUCCESS("✅ Expenditures imported."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ expenditure.csv not found, skipping."))

        # --- Import Contributions ---
        contributions_file = os.path.join(base_dir, "contributions.csv")
        if os.path.exists(contributions_file):
            with open(contributions_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    donor = DonorEntity.objects.filter(name=row.get("donor")).first()
                    committee = IECommittee.objects.filter(name=row.get("committee")).first()

                    # Skip if missing donor or committee
                    if not donor or not committee:
                        continue

                    Contribution.objects.get_or_create(
                        donor=donor,
                        committee=committee,
                        defaults={
                            "amount": row.get("amount", 0),
                            "date": row.get("date") or None,
                            "is_fake": True,
                        },
                    )
            self.stdout.write(self.style.SUCCESS("✅ Contributions imported."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ contribution.csv not found, skipping."))

        # --- Import Contact Logs ---
        contactlogs_file = os.path.join(base_dir, "contactlogs.csv")
        if os.path.exists(contactlogs_file):
            with open(contactlogs_file, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    candidate = Candidate.objects.filter(name=row.get("candidate")).first()
                    if not candidate:
                        continue
                    ContactLog.objects.get_or_create(
                        candidate=candidate,
                        defaults={
                            "contacted_by": row.get("contacted_by"),
                            "method": row.get("method", "email"),
                            "status": row.get("status", "contacted"),
                            "note": row.get("note"),
                            "pledged_at": timezone.now()
                            if row.get("status") == "pledged"
                            else None,
                            "is_fake": True,
                        },
                    )
            self.stdout.write(self.style.SUCCESS("✅ Contact Logs imported."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ contactlog.csv not found, skipping."))

        self.stdout.write(self.style.SUCCESS("🎉 All fake data imported successfully!"))
