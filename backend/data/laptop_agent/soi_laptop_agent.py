#!/usr/bin/env python3
"""
Arizona SOI Laptop Scraper Agent
================================

This script runs on your laptop and receives scrape requests from the server
via SSH tunnel. It uses your laptop's residential IP to bypass Cloudflare.

SETUP:
------
1. Install dependencies:
   pip install fastapi uvicorn playwright requests

2. Install Playwright browsers:
   playwright install chromium

3. Set up SSH reverse tunnel (see instructions at bottom)

4. Run this agent:
   python soi_laptop_agent.py

The agent listens on port 5001 and accepts scrape requests from the server.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Optional
import threading
import requests

# FastAPI
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

# Playwright
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Configuration ==============

# SOI URLs to scrape
SOI_URLS = [
    "https://apps.arizona.vote/electioninfo/SOI/71",
    "https://apps.arizona.vote/electioninfo/SOI/69",
    "https://apps.arizona.vote/electioninfo/SOI/68"
]

# Server callback URL (set by trigger request)
SERVER_CALLBACK_URL = None

# ============== FastAPI App ==============

app = FastAPI(
    title="SOI Laptop Agent",
    description="Scrapes Arizona SOI pages using residential IP",
    version="1.0.0"
)


class ScrapeRequest(BaseModel):
    job_id: str
    callback_url: str


class HealthResponse(BaseModel):
    status: str
    agent_version: str
    timestamp: str


# ============== Scraper Class ==============

class SOIScraper:
    """Playwright-based SOI scraper"""

    def __init__(self):
        self.results: List[Dict] = []

    async def scrape_all(self) -> List[Dict]:
        """Scrape all SOI URLs"""
        self.results = []

        async with async_playwright() as p:
            # Launch browser (non-headless for best Cloudflare bypass)
            browser = await p.chromium.launch(
                headless=False,  # Visible browser helps bypass Cloudflare
                args=['--disable-blink-features=AutomationControlled']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = await context.new_page()

            # Remove webdriver detection
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)

            for url in SOI_URLS:
                try:
                    logger.info(f"Scraping {url}")
                    candidates = await self._scrape_page(page, url)
                    self.results.extend(candidates)
                    logger.info(f"Found {len(candidates)} candidates from {url}")

                    # Wait between pages
                    await asyncio.sleep(3)

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")

            await browser.close()

        return self.results

    async def _scrape_page(self, page, url: str) -> List[Dict]:
        """Scrape a single SOI page"""

        await page.goto(url, wait_until='domcontentloaded', timeout=60000)

        # Wait for page to load
        await asyncio.sleep(3)

        # Check for Cloudflare
        title = await page.title()
        if 'cloudflare' in title.lower() or 'blocked' in title.lower():
            logger.warning(f"Cloudflare detected on {url}, waiting...")
            await self._wait_for_cloudflare(page)

        # Extract candidates
        candidates = await page.evaluate("""
            () => {
                const results = [];
                const now = new Date().toISOString();

                // Find table rows
                document.querySelectorAll('table tbody tr, table tr').forEach((row, index) => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 2) return;

                    // Skip header rows
                    const text = row.innerText.toLowerCase();
                    if (text.includes('office') && text.includes('candidate')) return;

                    // Extract email
                    const emailMatch = row.innerText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/);

                    // Extract phone
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

                    if (candidate.name && candidate.name.length > 2) {
                        results.push(candidate);
                    }
                });

                return results;
            }
        """)

        return candidates

    async def _wait_for_cloudflare(self, page, timeout: int = 60):
        """Wait for Cloudflare challenge to complete"""

        for i in range(timeout):
            # Check if still on Cloudflare
            is_cloudflare = await page.evaluate("""
                () => {
                    const text = document.body.innerText.toLowerCase();
                    return text.includes('verify you are human') ||
                           text.includes('checking your browser') ||
                           text.includes('cloudflare');
                }
            """)

            if not is_cloudflare:
                logger.info("Cloudflare challenge passed!")
                return True

            # Try clicking Turnstile if present
            if i == 5:
                await self._try_solve_turnstile(page)

            await asyncio.sleep(1)

        logger.error("Cloudflare challenge timeout")
        return False

    async def _try_solve_turnstile(self, page):
        """Try to click Cloudflare Turnstile checkbox"""
        try:
            iframe = await page.query_selector('iframe[src*="turnstile"]')
            if iframe:
                box = await iframe.bounding_box()
                if box:
                    x = box['x'] + 30
                    y = box['y'] + box['height'] / 2
                    await page.mouse.click(x, y)
                    logger.info("Clicked Turnstile checkbox")
        except Exception as e:
            logger.debug(f"Turnstile click attempt: {e}")


# ============== Background Task ==============

def run_scrape_task(job_id: str, callback_url: str):
    """Run scrape in background and callback to server"""

    async def _scrape():
        logger.info(f"Starting scrape job {job_id}")

        try:
            scraper = SOIScraper()
            candidates = await scraper.scrape_all()

            logger.info(f"Scrape complete: {len(candidates)} candidates found")

            # Send results to server
            try:
                response = requests.post(
                    callback_url,
                    json={
                        'job_id': job_id,
                        'status': 'completed',
                        'candidates': candidates
                    },
                    timeout=30
                )
                logger.info(f"Callback response: {response.status_code}")
            except Exception as e:
                logger.error(f"Callback failed: {e}")

        except Exception as e:
            logger.error(f"Scrape failed: {e}")

            # Send error to server
            try:
                requests.post(
                    callback_url,
                    json={
                        'job_id': job_id,
                        'status': 'failed',
                        'error': str(e),
                        'candidates': []
                    },
                    timeout=30
                )
            except:
                pass

    # Run async scrape
    asyncio.run(_scrape())


# ============== API Endpoints ==============

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="online",
        agent_version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.post("/scrape")
def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Trigger SOI scrape.

    Called by server via SSH tunnel.
    Returns immediately, runs scrape in background.
    """
    logger.info(f"Received scrape request: job_id={request.job_id}")

    # Start background scrape
    background_tasks.add_task(
        run_scrape_task,
        request.job_id,
        request.callback_url
    )

    return {
        "status": "accepted",
        "job_id": request.job_id,
        "message": "Scrape started in background"
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "SOI Laptop Agent",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health check",
            "/scrape": "POST - Trigger scrape"
        }
    }


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn

    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                  SOI LAPTOP SCRAPER AGENT                         ║
╠═══════════════════════════════════════════════════════════════════╣
║  This agent receives scrape requests from the server via SSH      ║
║  tunnel and uses your laptop's residential IP to bypass           ║
║  Cloudflare protection.                                           ║
║                                                                   ║
║  SETUP:                                                           ║
║  1. Make sure Playwright is installed:                            ║
║     pip install playwright && playwright install chromium         ║
║                                                                   ║
║  2. Set up SSH reverse tunnel (run on laptop):                    ║
║     ssh -R 5001:localhost:5001 root@167.172.30.134               ║
║                                                                   ║
║  3. This agent is now running on port 5001                        ║
║                                                                   ║
║  The server can now trigger scrapes via the SSH tunnel!           ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=5001)
