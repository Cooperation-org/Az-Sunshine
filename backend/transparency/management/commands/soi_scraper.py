"""
Django Management Command: Arizona Statement of Interest (SOI) Scraper
FIXED VERSION: Better database import with proper error handling
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
    """Stealth scraper using dedicated Chrome profile to bypass Cloudflare"""
    
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
        
    async def _wait_for_cloudflare(self, page: Page):
        """Wait for Cloudflare challenge to complete"""
        if self.progress:
            self.progress.log("🔍 Checking for Cloudflare challenge...")
        
        try:
            await page.wait_for_load_state('networkidle', timeout=60000)
            
            is_cloudflare = await page.evaluate("""
                () => {
                    const text = document.body.innerText.toLowerCase();
                    return text.includes('verify you are human') || 
                           text.includes('cloudflare') ||
                           document.querySelector('.cf-wrapper') !== null;
                }
            """)
            
            if is_cloudflare:
                if self.progress:
                    self.progress.log("⚠️  Cloudflare challenge detected - Please solve manually")
                
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
                            self.progress.log("✅ Cloudflare challenge passed!")
                        await asyncio.sleep(2)
                        return True
                    
                    if i % 10 == 0 and i > 0 and self.progress:
                        self.progress.log(f"⏳ Still waiting... ({i}s)")
                
                logger.error("Timeout waiting for Cloudflare challenge")
                return False
            else:
                if self.progress:
                    self.progress.log("✅ No Cloudflare challenge detected")
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
        base_progress = (page_num - 1) * (60 / total_pages)  # 0-60% for scraping
        
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
                    
                    // Try multiple selector patterns for table rows
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
                            
                            // Skip header rows
                            if (!allText || allText.length < 5) return;
                            if (allText.toLowerCase().includes('office') && 
                                allText.toLowerCase().includes('candidate')) {
                                return;
                            }
                            
                            // Extract email
                            const emailMatch = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
                            
                            // Get cells - Order: Office, Candidate Name, Party, Phone, Email
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
                            
                            // Fallback: try to parse from raw text
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
                
                if i < total_urls:  # Don't delay after last page
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
    """
    Django management command for SOI scraping and database loading
    Implements Phase 1, Requirement 1 from Ben's specs
    """
    help = 'Scrape Arizona SOS Statements of Interest and load into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database'
        )
        parser.add_argument(
            '--csv-output',
            type=str,
            default='data/soi_candidates.csv',
            help='Path to save CSV output'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        csv_path = options['csv_output']
        
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('🗳️  Arizona SOI Scraper + Database Loader'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')
        
        # Initialize progress reporter
        progress = ProgressReporter(self.stdout)
        
        # STEP 1: Scrape SOI pages
        progress.update("Starting", 0, "Initializing scraper...")
        scraper = SOIScraper(progress_reporter=progress)
        
        try:
            # Run async scraping
            results = asyncio.run(scraper.scrape_all())
            
            if not results:
                self.stdout.write(self.style.WARNING('\n⚠️  No candidates found in scrape'))
                return
            
            progress.update("Scraping", 60, f"✅ Found {len(results)} candidates")
            
            # Save to CSV
            progress.update("Saving", 65, "Writing CSV backup...")
            scraper.save_results_csv(csv_path)
            progress.update("Saving", 70, "✅ CSV saved")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Scraping failed: {e}'))
            import traceback
            traceback.print_exc()
            return
        
        # STEP 2: Load into database with FIXED logic
        progress.update("Loading", 70, "Processing candidates...")
        
        stats = {
            'total_rows': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        try:
            with transaction.atomic():
                for i, row in enumerate(results, 1):
                    stats['total_rows'] += 1
                    
                    try:
                        result = self.process_candidate_row(row, dry_run)
                        stats[result] += 1
                        
                        # Update progress every 10 candidates
                        if i % 10 == 0:
                            db_progress = 70 + int((i / len(results)) * 25)
                            progress.update("Loading", db_progress, 
                                          f"Processed {i}/{len(results)} candidates")
                            
                    except Exception as e:
                        stats['errors'] += 1
                        progress.log(f'⚠️  Error on row {i}: {str(e)}')
                        logger.error(f"Error processing candidate: {e}", exc_info=True)
                
                if dry_run:
                    progress.log('🔄 DRY RUN - Rolling back changes')
                    transaction.set_rollback(True)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Database loading failed: {str(e)}'))
            import traceback
            traceback.print_exc()
            return
        
        progress.update("Complete", 100, "✅ Done!")
        
        # Print summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ SCRAPING & LOADING COMPLETE!'))
        self.stdout.write('='*70)
        self.stdout.write(f'📊 Total candidates scraped: {stats["total_rows"]}')
        self.stdout.write(self.style.SUCCESS(f'✨ Created in DB: {stats["created"]}'))
        self.stdout.write(self.style.WARNING(f'🔄 Updated in DB: {stats["updated"]}'))
        self.stdout.write(f'⏭️  Skipped: {stats["skipped"]}')
        
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {stats["errors"]}'))
        
        # Show next steps
        self.stdout.write('\n' + '='*70)
        self.stdout.write('📋 NEXT STEPS (Phase 1 Workflow):')
        self.stdout.write('='*70)
        self.stdout.write('1️⃣  Review uncontacted candidates at /soi/')
        self.stdout.write('2️⃣  Send info packets to candidate emails')
        self.stdout.write('3️⃣  Mark as "contacted" after sending')
        self.stdout.write('4️⃣  Monitor pledge receipts')
        self.stdout.write('='*70)

    def process_candidate_row(self, row, dry_run=False):
        """
        FIXED: Process single candidate and create/update in database
        Better validation and error handling
        """
        name = row.get('name', '').strip()
        email = row.get('email', '').strip()
        office_name = row.get('office', '').strip()
        party_name = row.get('party', '').strip()
        phone = row.get('phone', '').strip()
        
        # Skip invalid entries
        if not name or name == 'Unknown' or len(name) < 2:
            logger.debug(f"Skipping invalid name: {name}")
            return 'skipped'
        
        # Get or create Office
        office = None
        if office_name and office_name != 'Unknown' and len(office_name) > 2:
            office, created = Office.objects.get_or_create(
                name=office_name,
                defaults={'office_type': 'STATE'}
            )
            if created:
                logger.info(f"Created new office: {office_name}")
        else:
            logger.debug(f"Skipping candidate with invalid office: {office_name}")
            return 'skipped'
        
        # Check if candidate SOI already exists
        try:
            soi = CandidateStatementOfInterest.objects.get(
                candidate_name=name,
                office=office
            )
            
            # Update fields if we have new data
            updated = False
            if email and not soi.email:
                soi.email = email
                updated = True
            if phone and not soi.phone:
                soi.phone = phone
                updated = True
            
            if updated and not dry_run:
                soi.save()
                logger.info(f"Updated candidate: {name}")
            
            return 'updated' if updated else 'skipped'
            
        except CandidateStatementOfInterest.DoesNotExist:
            # Create new SOI record
            if not dry_run:
                soi = CandidateStatementOfInterest.objects.create(
                    candidate_name=name,
                    office=office,
                    email=email,
                    phone=phone,
                    filing_date=datetime.now().date(),
                    contact_status='uncontacted',
                    pledge_received=False
                )
                logger.info(f"Created new candidate: {name} for {office_name}")
            
            return 'created'