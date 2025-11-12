"""
Enhanced SOI Scraper with Webhook Integration
File: transparency/management/commands/soi_scraper_webhook.py

This version supports:
1. Manual trigger from React frontend
2. Automated cron jobs
3. Webhook notifications to cloud VPS
4. Real-time progress updates
5. Proper office creation with auto-incrementing IDs
"""

import asyncio
import json
import csv
import random
import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max
from playwright.async_api import async_playwright, Browser, Page
import logging

from transparency.models import CandidateStatementOfInterest, Office

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Send real-time updates to cloud server via webhook"""

    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or os.getenv('SOI_WEBHOOK_URL')
        self.session_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def send_update(self, status, progress, message, data=None):
        """Send progress update to webhook endpoint"""
        if not self.webhook_url:
            logger.warning("No webhook URL configured")
            return

        payload = {
            'session_id': self.session_id,
            'status': status,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            logger.info(f"✅ Webhook sent: {message}")
        except Exception as e:
            logger.error(f"❌ Webhook failed: {e}")


class ProgressReporter:
    """Enhanced progress reporting with webhook support"""
    
    def __init__(self, stdout, webhook_notifier=None):
        self.stdout = stdout
        self.webhook = webhook_notifier
        self.current_step = ""
        self.progress = 0
        
    def update(self, step, progress, message="", data=None):
        """Update progress with visual indicator and webhook"""
        self.current_step = step
        self.progress = progress
        
        # Create progress bar for console
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Print to console
        sys.stdout.write(f'\r{step}: [{bar}] {progress}% {message}')
        sys.stdout.flush()
        
        if progress >= 100:
            sys.stdout.write('\n')
            sys.stdout.flush()
        
        # Send webhook notification
        if self.webhook:
            status = 'running' if progress < 100 else 'completed'
            self.webhook.send_update(status, progress, f"{step}: {message}", data)
    
    def log(self, message):
        """Log a message without disrupting progress bar"""
        sys.stdout.write('\n' + message + '\n')
        sys.stdout.flush()


class SOIScraper:
    """Stealth scraper with webhook notifications"""
    
    SOI_URLS = [
        "https://apps.arizona.vote/electioninfo/SOI/71",
        "https://apps.arizona.vote/electioninfo/SOI/69",
        "https://apps.arizona.vote/electioninfo/SOI/68"
    ]
    
    def __init__(self, progress_reporter=None):
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
        
        self.browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            executable_path=self.chrome_executable,
            headless=False,  # Visible browser to bypass Cloudflare
            channel=None,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-popup-blocking',
            ],
            viewport={'width': 1920, 'height': 1080},
            user_agent=None,
            ignore_default_args=['--enable-automation'],
        )
        
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
                    self.progress.log("⚠️  Cloudflare detected - waiting...")
                await asyncio.sleep(30)
                return True
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
        
    async def scrape_soi_page(self, url: str, page: Page, page_num: int, total_pages: int) -> list:
        """Scrape a single SOI page with progress updates"""
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
            
            if self.progress:
                self.progress.update("Scraping", int(base_progress + 15), "Extracting data...")
            
            # Extract candidate data
            candidates = await page.evaluate(r"""
                () => {
                    const results = [];
                    const selectors = ['table tbody tr', 'table tr', '.candidate-row'];
                    
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
                            
                            let office = '', name = '', party = '', phone = '';
                            
                            if (cells.length >= 2) {
                                office = cells[0]?.innerText?.trim() || '';
                                name = cells[1]?.innerText?.trim() || '';
                                if (cells.length >= 3) party = cells[2]?.innerText?.trim() || '';
                                if (cells.length >= 4) phone = cells[3]?.innerText?.trim() || '';
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
                self.progress.update(
                    "Scraping", 
                    int(base_progress + 20), 
                    f"Found {len(candidates)} candidates",
                    {'page': page_num, 'candidates_found': len(candidates)}
                )
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            if self.progress and self.progress.webhook:
                self.progress.webhook.send_update('error', 0, f"Scraping failed: {str(e)}")
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
                self.progress.update(
                    "Scraping", 
                    60, 
                    f"Complete - {len(self.results)} total candidates",
                    {'total_candidates': len(self.results)}
                )
            
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
    Django management command with webhook support
    
    Usage:
        python manage.py soi_scraper_webhook
        python manage.py soi_scraper_webhook --dry-run
        python manage.py soi_scraper_webhook --webhook-url https://your-vps.com/api/soi/webhook/
    """
    help = 'Scrape Arizona SOS Statements of Interest with webhook notifications'

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
        parser.add_argument(
            '--webhook-url',
            type=str,
            help='Webhook URL for real-time updates'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        csv_path = options['csv_output']
        webhook_url = options['webhook_url'] or os.getenv('SOI_WEBHOOK_URL')
        
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('🗳️  Arizona SOI Scraper + Webhook Integration'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('')
        
        # Initialize webhook notifier
        webhook = WebhookNotifier(webhook_url) if webhook_url else None
        if webhook:
            self.stdout.write(self.style.SUCCESS(f'📡 Webhook enabled: {webhook_url}'))
        
        # Initialize progress reporter
        progress = ProgressReporter(self.stdout, webhook)
        
        # STEP 1: Scrape SOI pages
        progress.update("Starting", 0, "Initializing scraper...")
        scraper = SOIScraper(progress_reporter=progress)
        
        try:
            # Run async scraping
            results = asyncio.run(scraper.scrape_all())
            
            if not results:
                self.stdout.write(self.style.WARNING('\n⚠️  No candidates found'))
                if webhook:
                    webhook.send_update('completed', 100, 'No candidates found', {'total': 0})
                return
            
            progress.update("Scraping", 60, f"✅ Found {len(results)} candidates")
            
            # Save to CSV
            progress.update("Saving", 65, "Writing CSV backup...")
            scraper.save_results_csv(csv_path)
            progress.update("Saving", 70, "✅ CSV saved")
            
        except Exception as e:
            error_msg = f'Scraping failed: {e}'
            self.stdout.write(self.style.ERROR(f'\n❌ {error_msg}'))
            if webhook:
                webhook.send_update('error', 0, error_msg)
            import traceback
            traceback.print_exc()
            return
        
        # STEP 2: Load into database
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
                        
                        if i % 10 == 0:
                            db_progress = 70 + int((i / len(results)) * 25)
                            progress.update(
                                "Loading", 
                                db_progress, 
                                f"Processed {i}/{len(results)}",
                                {'processed': i, 'total': len(results)}
                            )
                            
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"Error on row {i}: {e}")
                
                if dry_run:
                    progress.log('📄 DRY RUN - Rolling back')
                    transaction.set_rollback(True)
        
        except Exception as e:
            error_msg = f'Database loading failed: {str(e)}'
            self.stdout.write(self.style.ERROR(f'\n❌ {error_msg}'))
            if webhook:
                webhook.send_update('error', 0, error_msg)
            return
        
        progress.update("Complete", 100, "✅ Done!", stats)
        
        # Final webhook notification
        if webhook:
            webhook.send_update('completed', 100, 'Scraping completed successfully', stats)
        
        # Print summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ COMPLETE!'))
        self.stdout.write('='*70)
        self.stdout.write(f'📊 Total: {stats["total_rows"]}')
        self.stdout.write(self.style.SUCCESS(f'✨ Created: {stats["created"]}'))
        self.stdout.write(self.style.WARNING(f'🔄 Updated: {stats["updated"]}'))
        self.stdout.write(f'⭐ Skipped: {stats["skipped"]}')
        
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {stats["errors"]}'))

    def process_candidate_row(self, row, dry_run=False):
        """Process single candidate and create/update in database"""
        name = row.get('name', '').strip()
        email = row.get('email', '').strip()
        office_name = row.get('office', '').strip()
        phone = row.get('phone', '').strip()
        
        if not name or len(name) < 2:
            return 'skipped'
        
        # Get or create Office with proper ID
        office = None
        if office_name and len(office_name) > 2:
            # Try to get existing office first
            office = Office.objects.filter(name=office_name).first()
            
            if not office:
                # Get next office_id
                max_id = Office.objects.aggregate(Max('office_id'))['office_id__max'] or 0
                office = Office.objects.create(
                    office_id=max_id + 1,
                    name=office_name,
                    office_type='STATE'
                )
        else:
            return 'skipped'
        
        # Check if exists
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