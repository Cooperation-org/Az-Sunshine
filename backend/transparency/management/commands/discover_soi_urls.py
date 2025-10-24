import os
import time
import json
import traceback
from urllib.parse import urljoin
from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Constants - tweak paths as you like
BASE_URL = "https://apps.arizona.vote/electioninfo/"
OUTPUT_FILE = "soi_urls.txt"
LOG_FILE = "playwright_debug.log"
AUTH_JSON = "auth.json"  # storage state that Playwright can export for headless cron runs

# Where Playwright will store the persistent Chromium profile for this script.
# Default is ./chrome_profile inside backend. Set env var PROFILE_DIR to change.
PROFILE_DIR = os.environ.get("PROFILE_DIR", os.path.join(os.getcwd(), "chrome_profile"))


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Command(BaseCommand):
    help = "Discover SOI URLs using a persistent Chromium profile for better trust/fingerprint"

    def handle(self, *args, **options):
        def log(msg):
            line = f"[{now()}] {msg}"
            self.stdout.write(line)
            with open(LOG_FILE, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

        # ensure log
        with open(LOG_FILE, "w", encoding="utf-8") as fh:
            fh.write(f"=== discover_soi_urls start: {now()} ===\n")

        # Make sure the profile dir exists
        os.makedirs(PROFILE_DIR, exist_ok=True)
        log(f"Using persistent profile directory: {PROFILE_DIR}")
        log("Starting Playwright...")

        try:
            with sync_playwright() as p:
                # Launch a persistent context (behaves like a real Chrome profile)
                # NOTE: do not use your *daily* Chrome profile path directly while Chrome is running.
                log("Launching persistent Chromium context (visible). If this is the first run, a new profile will be created.")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=PROFILE_DIR,
                    headless=False,
                    viewport={"width": 1400, "height": 900},
                    slow_mo=100,
                    args=[
                        "--start-maximized",
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-extensions",
                        "--disable-gpu",
                    ],
                    # You can customize the user agent if you want: user_agent="..."
                )

                try:
                    page = context.new_page()
                except Exception:
                    # launch_persistent_context sometimes returns a context already with pages
                    pages = context.pages
                    page = pages[0] if pages else context.new_page()

                try:
                    log(f"Navigating to {BASE_URL} (timeout 3 min)...")
                    page.goto(BASE_URL, timeout=180000)
                    # wait a reasonable amount but avoid hanging forever on JS-challenges
                    try:
                        page.wait_for_load_state("networkidle", timeout=90000)
                    except Exception:
                        log("networkidle not reached (possible challenge or slow resources). Continuing...")

                    # Give the page a bit to settle
                    time.sleep(2)

                    # Detect text/iframe markers for challenge
                    challenge = False
                    try:
                        body_text = (page.text_content("body") or "").lower()
                        if "verify you are human" in body_text or "just a moment" in body_text or "private access token" in body_text:
                            challenge = True
                            log("Challenge text detected in page body.")
                        if page.query_selector("iframe[title*='recaptcha']") or page.query_selector("iframe[src*='captcha']"):
                            challenge = True
                            log("Captcha iframe detected.")
                    except Exception:
                        log("Error while checking challenge markers (ignored)")

                    if challenge:
                        log("Detected a bot-challenge. Please solve it manually in the opened browser window.")
                        log("After solving the challenge, press ENTER here to continue and save session for later automated runs.")
                        input("Press ENTER after solving the challenge in the browser...")
                        # Save storage_state after manual solve so headless cron can use auth.json
                        try:
                            context.storage_state(path=AUTH_JSON)
                            log(f"Saved storage state to {AUTH_JSON}")
                        except Exception:
                            log("Failed to save storage_state; continuing without writing auth.json.")
                    else:
                        # No challenge detected; save storage state proactively
                        try:
                            context.storage_state(path=AUTH_JSON)
                            log(f"No challenge detected. Saved storage state to {AUTH_JSON}")
                        except Exception:
                            log("Could not save storage_state (non-fatal).")

                    # Take final screenshot + HTML dump for debug
                    try:
                        page.screenshot(path="debug_final.png", full_page=True)
                        with open("debug_final.html", "w", encoding="utf-8") as fh:
                            fh.write(page.content())
                        log("Saved debug_final.png and debug_final.html")
                    except Exception:
                        log("Failed to save debug artifacts (ignored).")

                    # Extract links robustly
                    anchors = []
                    try:
                        locator = page.locator("a")
                        total = locator.count()
                        log(f"Found {total} <a> elements via locator.")
                        for i in range(total):
                            try:
                                href = locator.nth(i).get_attribute("href")
                                if href and "/SOI/" in href:
                                    anchors.append(urljoin(BASE_URL, href))
                            except Exception:
                                continue
                    except Exception:
                        # fallback JS evaluation
                        log("Locator approach failed; falling back to JS evaluation.")
                        try:
                            hrefs = page.evaluate("Array.from(document.querySelectorAll('a')).map(a => a.href)")
                            for h in hrefs:
                                if h and "/SOI/" in h:
                                    anchors.append(h)
                        except Exception:
                            log("JS fallback also failed.")

                    anchors = sorted(set(anchors))
                    if anchors:
                        with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
                            fh.write("\n".join(anchors))
                        log(f"Saved {len(anchors)} SOI URLs to {OUTPUT_FILE}")
                    else:
                        log("No SOI URLs found on the page.")

                except PlaywrightTimeoutError:
                    log("Timeout while loading the page (PlaywrightTimeoutError). See debug artifacts.")
                    log(traceback.format_exc())

                except Exception as e:
                    log(f"Unhandled error during page operations: {e}")
                    log(traceback.format_exc())

                finally:
                    log("Cleaning up: closing context in 3s...")
                    time.sleep(3)
                    try:
                        context.close()
                    except Exception:
                        log("Error closing context (ignored).")

        except Exception as e:
            log(f"Fatal Playwright error: {e}")
            log(traceback.format_exc())

        log("Done.")
