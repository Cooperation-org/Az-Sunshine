from django.core.management.base import BaseCommand
from transparency.models import Candidate, Race
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

AZ_SOS_SOI = "https://azsos.gov/elections/candidates/statements-interest"
SOI_BASE = "https://apps.arizona.vote"

class Command(BaseCommand):
    help = "Scrape AZ SOS Statements of Interest and add new candidates"

    def handle(self, *args, **options):
        self.stdout.write("Fetching AZ SOS Statements of Interest...")
        resp = requests.get(AZ_SOS_SOI, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        names = set()
        for a in soup.select("a"):
            href = a.get("href") or ""
            text = (a.get_text() or "").strip()
            if text and "Statement of Interest" not in text:
                if href.startswith("/"):
                    try:
                        sub = requests.get(urljoin(AZ_SOS_SOI, href), timeout=20)
                        sub.raise_for_status()
                        sub_soup = BeautifulSoup(sub.text, "html.parser")
                        for li in sub_soup.select("li"):
                            t = li.get_text(separator=" ", strip=True)
                            if len(t) > 3:
                                names.add(t)
                    except Exception:
                        continue
                else:
                    if len(text.split()) <= 5:
                        names.add(text)

        if not names:
            for li in soup.select("li"):
                t = li.get_text(separator=" ", strip=True)
                if len(t) > 3:
                    names.add(t)

        created = 0
        for n in names:
            try:
                if Candidate.objects.filter(name__iexact=n).exists():
                    continue
                race, _ = Race.objects.get_or_create(name="Unknown", defaults={"year": 2024})
                Candidate.objects.create(name=n, race=race)
                created += 1
            except Exception as e:
                self.stderr.write(f"Failed to create candidate {n}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Done. New candidates created: {created}"))
