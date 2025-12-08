"""
Arizona Secretary of State Database Purchase and Download Automation

This service automates the purchase and download of campaign finance data
from the Arizona Secretary of State website using Playwright.

Features:
- Automated login and navigation
- Database purchase workflow
- CSV download management
- Session persistence for faster subsequent runs
- Error handling and logging
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from django.conf import settings

logger = logging.getLogger(__name__)


class AZSOSScraper:
    """
    Automated scraper for AZ SOS campaign finance database

    Usage:
        scraper = AZSOSScraper()
        csv_path = scraper.download_database(year=2024, quarter=1)
    """

    # AZ SOS URLs (update these with actual URLs from the project spec)
    BASE_URL = "https://apps.azsos.gov/election/cfs/"
    LOGIN_URL = f"{BASE_URL}login"
    EXPORT_URL = f"{BASE_URL}data-export"

    def __init__(self, download_dir=None, headless=True):
        """
        Initialize the scraper

        Args:
            download_dir: Directory for downloaded files (default: backend/data/sos_downloads)
            headless: Run browser in headless mode (default: True, set False for CAPTCHA)
        """
        self.headless = headless

        # Setup download directory
        if download_dir:
            self.download_dir = Path(download_dir)
        else:
            backend_dir = Path(settings.BASE_DIR)
            self.download_dir = backend_dir / "data" / "sos_downloads"

        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Session file for persistent login
        self.session_file = self.download_dir / "session.json"

        logger.info(f"AZ SOS Scraper initialized. Download dir: {self.download_dir}")

    def download_database(self, year=None, quarter=None, purchase=False):
        """
        Download campaign finance database from AZ SOS

        Args:
            year: Year for data (default: current year)
            quarter: Quarter (1-4) for data (default: all)
            purchase: Whether to actually purchase ($25) or just download if already owned

        Returns:
            Path to downloaded CSV file
        """
        logger.info(f"Starting AZ SOS download - Year: {year}, Quarter: {quarter}")

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)

            # Create context with session persistence
            context_options = {
                "accept_downloads": True,
            }

            # Load previous session if exists
            if self.session_file.exists():
                context_options["storage_state"] = str(self.session_file)
                logger.info("Loaded previous session")

            context = browser.new_context(**context_options)
            page = context.new_page()

            try:
                # Step 1: Login
                if not self._is_logged_in(page):
                    logger.info("Logging in to AZ SOS...")
                    self._login(page)
                else:
                    logger.info("Already logged in (using saved session)")

                # Step 2: Navigate to data export section
                logger.info("Navigating to data export...")
                self._navigate_to_export(page)

                # Step 3: Select data parameters
                logger.info("Selecting data parameters...")
                self._select_parameters(page, year, quarter)

                # Step 4: Purchase or download
                if purchase:
                    logger.info("Initiating purchase...")
                    self._complete_purchase(page)

                # Step 5: Download CSV
                logger.info("Downloading CSV...")
                download_path = self._download_csv(page)

                # Save session for next time
                context.storage_state(path=str(self.session_file))
                logger.info("Session saved for future use")

                logger.info(f"Download complete: {download_path}")
                return download_path

            except Exception as e:
                logger.error(f"Error during download: {str(e)}", exc_info=True)
                raise

            finally:
                browser.close()

    def _is_logged_in(self, page):
        """Check if already logged in"""
        try:
            page.goto(self.BASE_URL, timeout=10000, wait_until="domcontentloaded")
            # Check for dashboard or logged-in indicator
            return "dashboard" in page.url.lower() or page.locator("text=Logout").count() > 0
        except:
            return False

    def _login(self, page):
        """
        Login to AZ SOS portal

        Requires environment variables:
        - AZ_SOS_USERNAME
        - AZ_SOS_PASSWORD
        """
        username = os.getenv('AZ_SOS_USERNAME')
        password = os.getenv('AZ_SOS_PASSWORD')

        if not username or not password:
            raise ValueError(
                "AZ SOS credentials not found. Set AZ_SOS_USERNAME and "
                "AZ_SOS_PASSWORD environment variables."
            )

        # Navigate to login page
        page.goto(self.LOGIN_URL, wait_until="networkidle")

        # Fill login form (update selectors based on actual website)
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)

        # Submit form
        page.click('button[type="submit"]')

        # Wait for navigation (may need manual CAPTCHA solving if headless=False)
        try:
            page.wait_for_url("**/dashboard**", timeout=60000)  # 60s for CAPTCHA
            logger.info("Login successful")
        except PlaywrightTimeout:
            # Check if CAPTCHA is present
            if page.locator("iframe[title*='reCAPTCHA']").count() > 0:
                logger.warning(
                    "CAPTCHA detected. Please solve CAPTCHA manually. "
                    "Waiting 120 seconds..."
                )
                page.wait_for_url("**/dashboard**", timeout=120000)
            else:
                raise Exception("Login failed - timeout waiting for dashboard")

    def _navigate_to_export(self, page):
        """Navigate to data export/download section"""
        # Update URL based on actual AZ SOS structure
        page.goto(self.EXPORT_URL, wait_until="networkidle")

        # Wait for export page to load
        page.wait_for_selector("text=Download", timeout=10000)

    def _select_parameters(self, page, year, quarter):
        """
        Select data parameters for export

        Args:
            year: Year to download
            quarter: Quarter (1-4) or None for all
        """
        # Select year if provided
        if year:
            page.select_option('select[name="year"]', str(year))
            logger.info(f"Selected year: {year}")

        # Select quarter if provided
        if quarter:
            page.select_option('select[name="quarter"]', str(quarter))
            logger.info(f"Selected quarter: {quarter}")

        # Select all data types (contributions, expenditures, etc.)
        # Update based on actual form structure
        if page.locator('input[type="checkbox"][value="all"]').count() > 0:
            page.check('input[type="checkbox"][value="all"]')
            logger.info("Selected all data types")

    def _complete_purchase(self, page):
        """
        Complete database purchase ($25)

        This assumes payment information is already on file.
        May require additional steps for first-time purchase.
        """
        logger.warning("Purchase functionality requires payment setup")

        # Click purchase button
        page.click('button:has-text("Purchase")')

        # Wait for payment confirmation
        page.wait_for_selector('text=Payment successful', timeout=30000)
        logger.info("Purchase completed successfully")

    def _download_csv(self, page):
        """
        Download CSV file

        Returns:
            Path to downloaded file
        """
        # Wait for and click download button
        with page.expect_download() as download_info:
            page.click('button:has-text("Download CSV")')

        download = download_info.value

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"az_sos_cfs_{timestamp}.csv"
        save_path = self.download_dir / filename

        # Save download
        download.save_as(save_path)
        logger.info(f"Downloaded to: {save_path}")

        return save_path

    def get_latest_download(self):
        """
        Get path to most recent download

        Returns:
            Path to latest CSV file or None
        """
        csv_files = list(self.download_dir.glob("az_sos_cfs_*.csv"))

        if not csv_files:
            return None

        # Sort by modification time
        latest = max(csv_files, key=lambda p: p.stat().st_mtime)
        return latest


class AZSOSDownloadError(Exception):
    """Custom exception for AZ SOS download errors"""
    pass
