"""
Arizona Statement of Interest (SOI) Scraper Service
VERSION 3.0: Ready for proxy integration

Scrapes candidate SOI data from:
- https://apps.arizona.vote/electioninfo/SOI/71
- https://apps.arizona.vote/electioninfo/SOI/69
- https://apps.arizona.vote/electioninfo/SOI/68

Usage:
    from transparency.services.soi_scraper_service import SOIScraperService

    # With proxy (required for Cloudflare bypass)
    scraper = SOIScraperService(proxy_url="http://user:pass@proxy.example.com:12321")
    candidates = scraper.scrape_all()

    # Or set proxy via environment variable
    # export SOI_PROXY_URL="http://user:pass@proxy.example.com:12321"
    scraper = SOIScraperService()
    candidates = scraper.scrape_all()
"""

import os
import logging
import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SOIScraperService:
    """
    Service class for scraping Arizona SOI pages.

    Attributes:
        SOI_URLS: List of SOI page URLs to scrape
        proxy_url: Residential proxy URL (required for Cloudflare bypass)
    """

    SOI_URLS = [
        "https://apps.arizona.vote/electioninfo/SOI/71",
        "https://apps.arizona.vote/electioninfo/SOI/69",
        "https://apps.arizona.vote/electioninfo/SOI/68"
    ]

    def __init__(self, proxy_url: Optional[str] = None, headless: bool = True):
        """
        Initialize the SOI scraper service.

        Args:
            proxy_url: Residential proxy URL. If not provided, will check
                       SOI_PROXY_URL environment variable.
            headless: Run browser in headless mode (default True)
        """
        self.proxy_url = proxy_url or os.environ.get('SOI_PROXY_URL')
        self.headless = headless
        self.results: List[Dict] = []

        # Data storage directory
        self.data_dir = Path(__file__).parent.parent.parent / 'data'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.proxy_url:
            logger.warning(
                "No proxy configured. Cloudflare will likely block requests. "
                "Set proxy_url or SOI_PROXY_URL environment variable."
            )

    def scrape_all(self) -> List[Dict]:
        """
        Scrape all SOI URLs and return candidate data.

        Returns:
            List of dictionaries containing candidate information:
            [
                {
                    'name': 'John Doe',
                    'office': 'State Senator District 1',
                    'party': 'Republican',
                    'phone': '555-123-4567',
                    'email': 'john@example.com',
                    'source_url': 'https://...',
                    'scraped_at': '2025-01-14T12:00:00'
                },
                ...
            ]
        """
        return asyncio.run(self._async_scrape_all())

    async def _async_scrape_all(self) -> List[Dict]:
        """Async implementation of scrape_all"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright")
            return []

        async with async_playwright() as p:
            browser = await self._setup_browser(p)

            if not browser:
                return []

            page = browser.pages[0] if browser.pages else await browser.new_page()

            for url in self.SOI_URLS:
                try:
                    candidates = await self._scrape_page(page, url)
                    self.results.extend(candidates)
                    logger.info(f"Scraped {len(candidates)} candidates from {url}")

                    # Human-like delay between pages
                    await asyncio.sleep(random.uniform(3, 6))

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")

            await browser.close()

        return self.results

    async def _setup_browser(self, playwright):
        """Setup browser with proxy and stealth settings"""

        launch_options = {
            'headless': self.headless,
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ],
        }

        # Add proxy if configured
        if self.proxy_url:
            launch_options['proxy'] = {'server': self.proxy_url}
            logger.info(f"Using proxy: {self.proxy_url.split('@')[-1] if '@' in self.proxy_url else 'configured'}")

        try:
            browser = await playwright.chromium.launch(**launch_options)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/Phoenix',
            )

            # Remove automation detection
            page = await context.new_page()
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)

            return context

        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return None

    async def _scrape_page(self, page, url: str) -> List[Dict]:
        """Scrape a single SOI page"""

        logger.info(f"Navigating to {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)

        # Wait for page to load
        await asyncio.sleep(3)

        # Check for Cloudflare block
        title = await page.title()
        if 'cloudflare' in title.lower() or 'blocked' in title.lower():
            logger.error(f"Blocked by Cloudflare on {url}")

            # Save screenshot for debugging
            screenshot_path = self.data_dir / f"soi_blocked_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Saved debug screenshot: {screenshot_path}")

            return []

        # Wait for possible Turnstile challenge
        await self._wait_for_cloudflare(page)

        # Extract candidate data
        candidates = await page.evaluate("""
            () => {
                const results = [];
                const now = new Date().toISOString();

                // Find all table rows
                document.querySelectorAll('table tbody tr, table tr').forEach((row, index) => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 2) return;

                    // Skip header rows
                    const text = row.innerText.toLowerCase();
                    if (text.includes('office') && text.includes('candidate')) return;

                    // Extract email if present
                    const emailMatch = row.innerText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/);

                    // Extract phone if present
                    const phoneMatch = row.innerText.match(/\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}/);

                    const candidate = {
                        office: cells[0]?.innerText?.trim() || '',
                        name: cells[1]?.innerText?.trim() || '',
                        party: cells[2]?.innerText?.trim() || '',
                        phone: phoneMatch ? phoneMatch[0] : (cells[3]?.innerText?.trim() || ''),
                        email: emailMatch ? emailMatch[0] : '',
                        source_url: window.location.href,
                        scraped_at: now
                    };

                    // Only add if we have a valid name
                    if (candidate.name && candidate.name.length > 2) {
                        results.push(candidate);
                    }
                });

                return results;
            }
        """)

        logger.info(f"Found {len(candidates)} candidates on {url}")

        # Save screenshot for verification
        screenshot_path = self.data_dir / f"soi_page_{url.split('/')[-1]}_{datetime.now().strftime('%H%M%S')}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)

        return candidates

    async def _wait_for_cloudflare(self, page, timeout: int = 30):
        """Wait for Cloudflare challenge to complete"""

        for i in range(timeout):
            is_cloudflare = await page.evaluate("""
                () => {
                    const text = document.body.innerText.toLowerCase();
                    return text.includes('verify you are human') ||
                           text.includes('checking your browser') ||
                           document.querySelector('iframe[src*="turnstile"]') !== null;
                }
            """)

            if not is_cloudflare:
                return True

            # Try to click Turnstile checkbox
            if i == 5:
                await self._solve_turnstile(page)

            await asyncio.sleep(1)

        logger.warning("Cloudflare challenge timeout")
        return False

    async def _solve_turnstile(self, page):
        """Attempt to solve Cloudflare Turnstile challenge"""
        try:
            iframe = await page.query_selector('iframe[src*="turnstile"]')
            if iframe:
                box = await iframe.bounding_box()
                if box:
                    x = box['x'] + 30
                    y = box['y'] + box['height'] / 2
                    await page.mouse.click(x, y)
                    logger.info("Clicked Turnstile checkbox")
                    await asyncio.sleep(3)
        except Exception as e:
            logger.debug(f"Turnstile solve attempt: {e}")

    def save_to_csv(self, output_path: Optional[str] = None) -> str:
        """Save scraped results to CSV file"""
        import csv

        if not self.results:
            logger.warning("No results to save")
            return ""

        if not output_path:
            output_path = str(self.data_dir / f"soi_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        fieldnames = ['name', 'office', 'party', 'phone', 'email', 'source_url', 'scraped_at']

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow({k: result.get(k, '') for k in fieldnames})

        logger.info(f"Saved {len(self.results)} candidates to {output_path}")
        return output_path


def test_scraper(proxy_url: Optional[str] = None):
    """
    Test the SOI scraper.

    Usage:
        # Without proxy (will likely fail due to Cloudflare)
        python -c "from transparency.services.soi_scraper_service import test_scraper; test_scraper()"

        # With proxy
        python -c "from transparency.services.soi_scraper_service import test_scraper; test_scraper('http://user:pass@proxy:port')"
    """
    logging.basicConfig(level=logging.INFO)

    scraper = SOIScraperService(proxy_url=proxy_url)
    candidates = scraper.scrape_all()

    print(f"\n{'='*60}")
    print(f"RESULTS: {len(candidates)} candidates found")
    print('='*60)

    for i, c in enumerate(candidates[:10], 1):
        print(f"{i}. {c['name']} - {c['office']} ({c['party']})")

    if candidates:
        csv_path = scraper.save_to_csv()
        print(f"\nSaved to: {csv_path}")

    return candidates


if __name__ == '__main__':
    test_scraper()
