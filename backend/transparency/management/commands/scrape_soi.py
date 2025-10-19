from django.core.management.base import BaseCommand
from transparency.models import Candidate, Race
from playwright.sync_api import sync_playwright
from datetime import datetime
import re
import time

SOS_LISTING_URL = 'https://azsos.gov/elections/candidates/statements-interest'

class Command(BaseCommand):
    help = 'Scrape AZ SOS Statements of Interest and populate Candidate records'

    def handle(self, *args, **options):
        self.stdout.write('Starting SOI scrape...')
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(SOS_LISTING_URL, timeout=60000)
                time.sleep(2)

                # This is a placeholder scraping strategy.
                # Inspect the page and adapt the CSS selectors for production.

                # Find links on page that likely contain SOI records
                anchors = page.query_selector_all('a')
                for a in anchors:
                    href = a.get_attribute('href')
                    if href and 'apps.arizona.vote' in href:
                        try:
                            page2 = browser.new_page()
                            page2.goto(href, timeout=60000)
                            content = page2.content()

                            # Try to pull a name (example: h1) and email pattern
                            name_el = page2.query_selector('h1')
                            name = name_el.inner_text().strip() if name_el else None
                            email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}', content)
                            email = email_match.group(0) if email_match else None

                            external_id = href
                            candidate, created = Candidate.objects.get_or_create(
                                external_id=external_id,
                                defaults={
                                    'name': name or 'Unknown',
                                    'email': email,
                                    'source': 'AZ_SOS'
                                }
                            )
                            if created:
                                self.stdout.write(f'Added candidate: {candidate.name}')
                            page2.close()
                        except Exception as e:
                            self.stdout.write(f'Error opening {href}: {e}')
                browser.close()
        except Exception as e:
            self.stdout.write(f'Playwright error: {e}')
        self.stdout.write('Done SOI scrape.')
