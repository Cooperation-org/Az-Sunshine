"""
Django Management Command: Arizona Statement of Interest (SOI) Scraper
VERSION 2.1: Fixed Cloudflare Turnstile solver (no multiple clicks)
Place in: transparency/management/commands/soi_scraper.py

Usage:
    python manage.py soi_scraper
    python manage.py soi_scraper --dry-run
"""

import asyncio
import json
import csv
import random
import os
import sys
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from playwright.async_api import async_playwright, Browser, Page
import logging

from transparency.models import CandidateStatementOfInterest, Office, Party

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressReporter:
    """Real-time progress reporting with visual feedback"""
    
    def __init__(self, stdout):
        self.stdout = stdout
        self.current_step = ""
        self.progress = 0
        
    def update(self, step, progress, message=""):
        """Update progress with visual indicator"""
        self.current_step = step
        self.progress = progress
        
        # Create progress bar
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Print with carriage return to update same line
        sys.stdout.write(f'\r{step}: [{bar}] {progress}% {message}')
        sys.stdout.flush()
        
        if progress >= 100:
            sys.stdout.write('\n')
            sys.stdout.flush()
    
    def log(self, message):
        """Log a message without disrupting progress bar"""
        sys.stdout.write('\n' + message + '\n')
        sys.stdout.flush()


class SOIScraper:
    """Stealth scraper with automatic Cloudflare Turnstile solver"""
    
    # Target URLs per Ben's requirements
    SOI_URLS = [
        "https://apps.arizona.vote/electioninfo/SOI/71",  # Primary source (most current)
        "https://apps.arizona.vote/electioninfo/SOI/69",
        "https://apps.arizona.vote/electioninfo/SOI/68"
    ]
    
    def __init__(self, progress_reporter=None):
        """Initialize scraper with progress reporting"""
        self.chrome_executable = "/usr/bin/google-chrome"
        self.user_data_dir = str(Path.home() / ".config/chrome-scraper-profile")
        self.browser: Browser = None
        self.results = []
        self.progress = progress_reporter
        
    async def _setup_browser(self, playwright):
        """Setup browser with real Chrome and dedicated profile"""
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        
        if self.progress:
            self.progress.log(f"🌐 Using Chrome from: {self.chrome_executable}")
        
        try:
            self.browser = await playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=self.chrome_executable,
                headless=False,
                channel=None,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-popup-blocking',
                    '--start-maximized',
                ],
                viewport={'width': 1920, 'height': 1080},
                user_agent=None,
                ignore_default_args=['--enable-automation'],
            )
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    async def _solve_cloudflare_turnstile(self, page: Page) -> bool:
        """
        🤖 AUTOMATIC CLOUDFLARE TURNSTILE SOLVER (FIXED)
        Automatically clicks the "Verify you are human" checkbox
        Now prevents multiple clicks!
        """
        try:
            if self.progress:
                self.progress.log("🤖 Checking Turnstile status...")
            
            # First check if already verified
            await asyncio.sleep(2)
            is_already_verified = await page.evaluate("""
                () => {
                    const text = document.body.innerText.toLowerCase();
                    return !text.includes('verify you are human');
                }
            """)
            
            if is_already_verified:
                if self.progress:
                    self.progress.log("✅ Already verified, skipping click")
                return True
            
            if self.progress:
                self.progress.log("🤖 Attempting to solve Turnstile challenge...")
            
            # Wait for Turnstile iframe to load
            await asyncio.sleep(random.uniform(2, 4))
            
            clicked = False  # Track if we successfully clicked
            
            # Strategy 1: Click the iframe directly at checkbox position
            if not clicked:
                try:
                    iframe_element = await page.query_selector('iframe[src*="turnstile"]')
                    if iframe_element:
                        box = await iframe_element.bounding_box()
                        if box:
                            # Add randomness to appear more human-like
                            x = box['x'] + random.randint(25, 35)
                            y = box['y'] + box['height'] / 2 + random.randint(-3, 3)
                            
                            if self.progress:
                                self.progress.log(f"🎯 Clicking Turnstile at ({int(x)}, {int(y)})")
                            
                            # Human-like mouse movement
                            await page.mouse.move(x, y)
                            await asyncio.sleep(random.uniform(0.2, 0.5))
                            await page.mouse.click(x, y)
                            await asyncio.sleep(2)
                            
                            if self.progress:
                                self.progress.log("✅ Clicked Turnstile checkbox (Strategy 1)")
                            clicked = True
                        else:
                            if self.progress:
                                self.progress.log("⚠️ Could not get iframe bounding box")
                    else:
                        if self.progress:
                            self.progress.log("⚠️ Turnstile iframe not found")
                except Exception as e:
                    if self.progress:
                        self.progress.log(f"⚠️ Strategy 1 failed: {str(e)[:50]}")
            
            # Strategy 2: Try to access iframe content directly
            if not clicked:
                try:
                    frames = page.frames
                    for frame in frames:
                        frame_url = frame.url
                        if 'turnstile' in frame_url or 'cloudflare' in frame_url:
                            try:
                                await frame.click('input[type="checkbox"]', timeout=2000)
                                if self.progress:
                                    self.progress.log("✅ Clicked checkbox via frame access (Strategy 2)")
                                await asyncio.sleep(2)
                                clicked = True
                                break
                            except:
                                pass
                except Exception as e:
                    if self.progress:
                        self.progress.log(f"⚠️ Strategy 2 failed: {str(e)[:50]}")
            
            # Strategy 3: Click by visible text
            if not clicked:
                try:
                    await page.click('text="Verify you are human"', timeout=3000)
                    if self.progress:
                        self.progress.log("✅ Clicked via text selector (Strategy 3)")
                    await asyncio.sleep(2)
                    clicked = True
                except Exception as e:
                    if self.progress:
                        self.progress.log(f"⚠️ Strategy 3 failed: {str(e)[:50]}")
            
            # If none of the strategies worked, return False early
            if not clicked:
                if self.progress:
                    self.progress.log("❌ All click strategies failed")
                return False
            
            # Wait for verification to complete
            if self.progress:
                self.progress.log("⏳ Waiting for Turnstile verification...")
            
            max_wait = 30
            for i in range(max_wait):
                await asyncio.sleep(1)
                
                # Check if we've passed the challenge
                is_verified = await page.evaluate("""
                    () => {
                        const text = document.body.innerText.toLowerCase();
                        // If "verify you are human" is gone, we passed
                        return !text.includes('verify you are human');
                    }
                """)
                
                if is_verified:
                    if self.progress:
                        self.progress.log("✅ Turnstile verification successful!")
                    await asyncio.sleep(3)  # Extra wait for page to fully load
                    return True
                
                if i % 5 == 0 and i > 0 and self.progress:
                    self.progress.log(f"⏳ Verifying... ({i}s)")
            
            if self.progress:
                self.progress.log("⚠️ Verification timeout - challenge may have failed")
            return False
            
        except Exception as e:
            logger.error(f"Turnstile solver error: {e}")
            return False
    
    async def _wait_for_cloudflare(self, page: Page):
        """
        UPDATED: Wait for and auto-solve Cloudflare challenge
        """
        if self.progress:
            self.progress.log("🔍 Checking for Cloudflare challenge...")
        
        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
            
            # Check if Cloudflare challenge is present
            is_cloudflare = await page.evaluate("""
                () => {
                    const text = document.body.innerText.toLowerCase();
                    return text.includes('verify you are human') || 
                           text.includes('cloudflare') ||
                           document.querySelector('.cf-wrapper') !== null ||
                           document.querySelector('iframe[src*="turnstile"]') !== null;
                }
            """)
            
            if is_cloudflare:
                if self.progress:
                    self.progress.log("⚠️ Cloudflare Turnstile detected!")
                
                # Try automatic solution
                success = await self._solve_cloudflare_turnstile(page)
                
                if success:
                    return True
                
                # If auto-solve failed, wait for manual intervention
                if self.progress:
                    self.progress.log("⚠️ Auto-solve incomplete - waiting for manual help...")
                
                max_wait = 120
                for i in range(max_wait):
                    await asyncio.sleep(1)
                    
                    is_still_cloudflare = await page.evaluate("""
                        () => {
                            const text = document.body.innerText.toLowerCase();
                            return text.includes('verify you are human') || 
                                   text.includes('cloudflare');
                        }
                    """)
                    
                    if not is_still_cloudflare:
                        if self.progress:
                            self.progress.log("✅ Challenge passed!")
                        await asyncio.sleep(2)
                        return True
                    
                    if i % 10 == 0 and i > 0 and self.progress:
                        self.progress.log(f"⏳ Still waiting... ({i}s)")
                
                logger.error("Timeout waiting for Cloudflare challenge")
                return False
            else:
                if self.progress:
                    self.progress.log("✅ No Cloudflare challenge")
                return True
                
        except Exception as e:
            logger.error(f"Error checking Cloudflare: {e}")
            return False
        
    async def _human_like_delay(self, min_ms: int = 1000, max_ms: int = 3000):
        """Random delay to mimic human behavior"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
        
    async def _scroll_page(self, page: Page):
        """Scroll page naturally like a human"""
        try:
            await page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if(totalHeight >= scrollHeight - window.innerHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
        except Exception as e:
            logger.warning(f"Scroll error (non-critical): {e}")
        
    async def scrape_soi_page(self, url: str, page: Page, page_num: int, total_pages: int) -> list:
        """
        Scrape a single SOI page with progress updates
        """
        base_progress = (page_num - 1) * (60 / total_pages)
        
        if self.progress:
            self.progress.update("Scraping", int(base_progress), f"Page {page_num}/{total_pages}")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            if not await self._wait_for_cloudflare(page):
                logger.error(f"Failed to bypass Cloudflare for {url}")
                return []
            
            if self.progress:
                self.progress.update("Scraping", int(base_progress + 10), "Loading page...")
            
            await self._human_like_delay(2000, 4000)
            await self._scroll_page(page)
            await self._human_like_delay(1000, 2000)
            
            if self.progress:
                self.progress.update("Scraping", int(base_progress + 15), "Extracting data...")
            
            # Extract candidate data
            candidates = await page.evaluate(r"""
                () => {
                    const results = [];
                    
                    const selectors = [
                        'table tbody tr',
                        'table tr',
                        '.candidate-row',
                    ];
                    
                    let rows = [];
                    for (const selector of selectors) {
                        rows = document.querySelectorAll(selector);
                        if (rows.length > 0) break;
                    }
                    
                    rows.forEach((row, index) => {
                        try {
                            const allText = row.innerText?.trim();
                            
                            if (!allText || allText.length < 5) return;
                            if (allText.toLowerCase().includes('office') && 
                                allText.toLowerCase().includes('candidate')) {
                                return;
                            }
                            
                            const emailMatch = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
                            
                            const cells = row.querySelectorAll('td');
                            let office = '';
                            let name = '';
                            let party = '';
                            let phone = '';
                            
                            if (cells.length >= 2) {
                                office = cells[0]?.innerText?.trim() || '';
                                name = cells[1]?.innerText?.trim() || '';
                                if (cells.length >= 3) party = cells[2]?.innerText?.trim() || '';
                                if (cells.length >= 4) phone = cells[3]?.innerText?.trim() || '';
                            }
                            
                            if (!name && allText.includes('\t')) {
                                const parts = allText.split('\t');
                                if (parts.length >= 2) {
                                    office = parts[0]?.trim() || '';
                                    name = parts[1]?.trim() || '';
                                }
                            }
                            
                            if (name && name.length > 2) {
                                results.push({
                                    name: name,
                                    office: office,
                                    party: party,
                                    phone: phone,
                                    email: emailMatch ? emailMatch[0] : '',
                                    raw_text: allText,
                                    source_url: window.location.href,
                                    row_index: index
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing row:', e);
                        }
                    });
                    
                    return results;
                }
            """)
            
            if self.progress:
                self.progress.update("Scraping", int(base_progress + 20), 
                                   f"Found {len(candidates)} candidates")
            
            if candidates:
                logger.info(f"Sample from page {page_num}: {json.dumps(candidates[0], indent=2)}")
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []
            
    async def scrape_all(self) -> list:
        """Scrape all SOI URLs with progress tracking"""
        async with async_playwright() as p:
            if self.progress:
                self.progress.update("Initializing", 5, "Setting up browser...")
            
            await self._setup_browser(p)
            
            page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()
            
            total_urls = len(self.SOI_URLS)
            for i, url in enumerate(self.SOI_URLS, 1):
                candidates = await self.scrape_soi_page(url, page, i, total_urls)
                self.results.extend(candidates)
                
                if i < total_urls:
                    await self._human_like_delay(5000, 8000)
            
            if self.progress:
                self.progress.update("Scraping", 60, "Complete")
            
            await self.browser.close()
            
        return self.results
    
    def save_results_csv(self, output_path: str):
        """Save results to CSV for backup"""
        if not self.results:
            logger.warning("No results to save")
            return None
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        fieldnames = ['name', 'office', 'party', 'phone', 'email', 'raw_text', 'source_url']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow({k: result.get(k, '') for k in fieldnames})
        
        logger.info(f"CSV saved to {output_path}")
        return output_path


class Command(BaseCommand):
    """Django management command for SOI scraping"""
    help = 'Scrape Arizona SOS Statements of Interest with auto Cloudflare solver'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--csv-output', type=str, default='data/soi_candidates.csv')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        csv_path = options['csv_output']
        
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('🗳️ Arizona SOI Scraper v2.1 (Fixed Cloudflare Solver)'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        progress = ProgressReporter(self.stdout)
        scraper = SOIScraper(progress_reporter=progress)
        
        try:
            results = asyncio.run(scraper.scrape_all())
            
            if not results:
                self.stdout.write(self.style.WARNING('\n⚠️ No candidates found'))
                return
            
            progress.update("Scraping", 60, f"✅ Found {len(results)} candidates")
            
            progress.update("Saving", 65, "Writing CSV...")
            scraper.save_results_csv(csv_path)
            progress.update("Saving", 70, "✅ CSV saved")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Scraping failed: {e}'))
            import traceback
            traceback.print_exc()
            return
        
        # Database loading logic
        progress.update("Loading", 70, "Processing candidates...")
        
        stats = {'total_rows': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        try:
            with transaction.atomic():
                for i, row in enumerate(results, 1):
                    stats['total_rows'] += 1
                    
                    try:
                        result = self.process_candidate_row(row, dry_run)
                        stats[result] += 1
                        
                        if i % 10 == 0:
                            db_progress = 70 + int((i / len(results)) * 25)
                            progress.update("Loading", db_progress, f"{i}/{len(results)}")
                            
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"Row {i} error: {e}")
                
                if dry_run:
                    transaction.set_rollback(True)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ DB loading failed: {e}'))
            return
        
        progress.update("Complete", 100, "✅ Done!")
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ COMPLETE!'))
        self.stdout.write('='*70)
        self.stdout.write(f'📊 Total: {stats["total_rows"]}')
        self.stdout.write(self.style.SUCCESS(f'✨ Created: {stats["created"]}'))
        self.stdout.write(self.style.WARNING(f'🔄 Updated: {stats["updated"]}'))
        self.stdout.write(f'⏭ Skipped: {stats["skipped"]}')
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {stats["errors"]}'))

    def process_candidate_row(self, row, dry_run=False):
        """Process candidate and create/update in database"""
        name = row.get('name', '').strip()
        email = row.get('email', '').strip()
        office_name = row.get('office', '').strip()
        phone = row.get('phone', '').strip()
        
        if not name or len(name) < 2:
            return 'skipped'
        
        office = None
        if office_name and len(office_name) > 2:
            office, _ = Office.objects.get_or_create(
                name=office_name,
                defaults={'office_type': 'STATE'}
            )
        else:
            return 'skipped'
        
        try:
            soi = CandidateStatementOfInterest.objects.get(
                candidate_name=name,
                office=office
            )
            
            updated = False
            if email and not soi.email:
                soi.email = email
                updated = True
            if phone and not soi.phone:
                soi.phone = phone
                updated = True
            
            if updated and not dry_run:
                soi.save()
            
            return 'updated' if updated else 'skipped'
            
        except CandidateStatementOfInterest.DoesNotExist:
            if not dry_run:
                CandidateStatementOfInterest.objects.create(
                    candidate_name=name,
                    office=office,
                    email=email,
                    phone=phone,
                    filing_date=datetime.now().date(),
                    contact_status='uncontacted',
                    pledge_received=False
                )
            
            return 'created'