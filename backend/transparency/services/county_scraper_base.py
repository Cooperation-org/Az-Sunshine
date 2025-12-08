"""
Base class for county election website scrapers

Provides common functionality for scraping county election data including:
- Campaign finance filings
- Candidate information
- Election results
- Filing deadlines
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class CountyScraperBase(ABC):
    """
    Abstract base class for county election scrapers

    Each county implementation should override:
    - BASE_URL: County website URL
    - scrape_candidates(): Extract candidate data
    - scrape_filings(): Extract campaign finance filings
    """

    BASE_URL = None  # Must be set by subclass
    COUNTY_NAME = None  # Must be set by subclass

    def __init__(self, headless=True, data_dir=None):
        """
        Initialize scraper

        Args:
            headless: Run browser in headless mode
            data_dir: Directory to save scraped data
        """
        if not self.BASE_URL:
            raise NotImplementedError("Subclass must define BASE_URL")

        if not self.COUNTY_NAME:
            raise NotImplementedError("Subclass must define COUNTY_NAME")

        self.headless = headless

        # Setup data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent / "data" / "county_data"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized {self.COUNTY_NAME} scraper")

    def scrape(self, year=None, save_to_csv=True):
        """
        Main scrape method - coordinates all scraping tasks

        Args:
            year: Year to scrape (default: current year)
            save_to_csv: Save results to CSV file

        Returns:
            dict with scraped data
        """
        year = year or datetime.now().year
        logger.info(f"Starting {self.COUNTY_NAME} scrape for year {year}")

        results = {
            'county': self.COUNTY_NAME,
            'year': year,
            'scrape_date': datetime.now().isoformat(),
            'candidates': [],
            'filings': [],
            'errors': []
        }

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()

            try:
                # Navigate to base URL
                logger.info(f"Navigating to {self.BASE_URL}")
                page.goto(self.BASE_URL, wait_until="networkidle", timeout=30000)

                # Scrape candidates
                try:
                    logger.info("Scraping candidates...")
                    results['candidates'] = self.scrape_candidates(page, year)
                    logger.info(f"Found {len(results['candidates'])} candidates")
                except Exception as e:
                    error_msg = f"Error scraping candidates: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)

                # Scrape filings
                try:
                    logger.info("Scraping campaign finance filings...")
                    results['filings'] = self.scrape_filings(page, year)
                    logger.info(f"Found {len(results['filings'])} filings")
                except Exception as e:
                    error_msg = f"Error scraping filings: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)

            finally:
                browser.close()

        # Save to CSV if requested
        if save_to_csv:
            self._save_to_csv(results)

        return results

    @abstractmethod
    def scrape_candidates(self, page, year):
        """
        Scrape candidate information

        Args:
            page: Playwright page object
            year: Election year

        Returns:
            list of dicts with candidate data
        """
        pass

    @abstractmethod
    def scrape_filings(self, page, year):
        """
        Scrape campaign finance filings

        Args:
            page: Playwright page object
            year: Election year

        Returns:
            list of dicts with filing data
        """
        pass

    def _save_to_csv(self, results):
        """Save results to CSV files"""
        import csv

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save candidates
        if results['candidates']:
            candidates_file = (
                self.data_dir /
                f"{self.COUNTY_NAME.lower()}_candidates_{timestamp}.csv"
            )

            with open(candidates_file, 'w', newline='', encoding='utf-8') as f:
                if results['candidates']:
                    writer = csv.DictWriter(f, fieldnames=results['candidates'][0].keys())
                    writer.writeheader()
                    writer.writerows(results['candidates'])

            logger.info(f"Saved candidates to {candidates_file}")

        # Save filings
        if results['filings']:
            filings_file = (
                self.data_dir /
                f"{self.COUNTY_NAME.lower()}_filings_{timestamp}.csv"
            )

            with open(filings_file, 'w', newline='', encoding='utf-8') as f:
                if results['filings']:
                    writer = csv.DictWriter(f, fieldnames=results['filings'][0].keys())
                    writer.writeheader()
                    writer.writerows(results['filings'])

            logger.info(f"Saved filings to {filings_file}")

    def navigate_with_retry(self, page, url, retries=3):
        """Navigate to URL with retry logic"""
        for attempt in range(retries):
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                return True
            except PlaywrightTimeout:
                logger.warning(f"Timeout navigating to {url}, attempt {attempt + 1}/{retries}")
                if attempt == retries - 1:
                    raise

        return False

    def safe_get_text(self, locator, default=""):
        """Safely get text from locator"""
        try:
            return locator.inner_text().strip()
        except:
            return default

    def safe_get_attribute(self, locator, attribute, default=""):
        """Safely get attribute from locator"""
        try:
            return locator.get_attribute(attribute) or default
        except:
            return default
