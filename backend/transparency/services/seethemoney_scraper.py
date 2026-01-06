"""
SeeTheMoney.az.gov Campaign Finance Data Scraper

FREE alternative to AZ SOS database purchase!

This service scrapes campaign finance data from Arizona's public
SeeTheMoney portal (seethemoney.az.gov) which provides free access
to all campaign finance data from 2002-present.

Features:
- No login required (public data)
- FREE - no $25 database fee
- CSV export functionality
- Covers all Arizona counties
- Data from 2002-2026
"""

import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from django.conf import settings

logger = logging.getLogger(__name__)


class SeeTheMoneyScraper:
    """
    FREE scraper for Arizona campaign finance data from SeeTheMoney.az.gov

    Usage:
        scraper = SeeTheMoneyScraper()
        csv_path = scraper.download_data(year=2024)
    """

    BASE_URL = "https://seethemoney.az.gov"
    ADVANCED_SEARCH_URL = f"{BASE_URL}/Reporting/AdvancedSearch/"

    def __init__(self, download_dir=None, headless=True):
        """
        Initialize the scraper

        Args:
            download_dir: Directory for downloaded files
            headless: Run browser in headless mode
        """
        self.headless = headless

        # Setup download directory
        if download_dir:
            self.download_dir = Path(download_dir)
        else:
            backend_dir = Path(settings.BASE_DIR)
            self.download_dir = backend_dir / "data" / "seethemoney_downloads"

        self.download_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SeeTheMoney Scraper initialized. Download dir: {self.download_dir}")

    def download_data(self, year=None, entity_type="Candidate", office_type=None, quarter=None):
        """
        Download campaign finance data from SeeTheMoney using quarterly chunks
        to avoid server timeouts on large datasets.

        Args:
            year: Year for data (default: current year)
            entity_type: Type of entity ("Candidate", "PAC", "Party", "All")
            office_type: Office type filter (optional)
            quarter: Specific quarter to download (1-4), or None for all quarters

        Returns:
            Path to downloaded CSV file (or list of paths if downloading all quarters)
        """
        if not year:
            year = datetime.now().year

        logger.info(f"Starting SeeTheMoney download - Year: {year}, Entity: {entity_type}")

        # CRITICAL FIX: Use quarterly date ranges to avoid 500K+ record timeouts
        all_quarters = [
            (f"{year}-01-01", f"{year}-03-31", "Q1"),
            (f"{year}-04-01", f"{year}-06-30", "Q2"),
            (f"{year}-07-01", f"{year}-09-30", "Q3"),
            (f"{year}-10-01", f"{year}-12-31", "Q4"),
        ]

        # FIXED: Download all quarters (or specific quarter if specified)
        if quarter and 1 <= quarter <= 4:
            quarters_to_download = [all_quarters[quarter - 1]]
            logger.info(f"Downloading single quarter: Q{quarter}")
        else:
            quarters_to_download = all_quarters
            logger.info(f"Downloading ALL quarters (Q1-Q4) for year {year}")

        downloaded_files = []

        for start_date, end_date, quarter_name in quarters_to_download:
            logger.info(f"Processing {quarter_name}: {start_date} to {end_date}")
            try:
                csv_path = self._download_quarter(year, entity_type, start_date, end_date, quarter_name)
                if csv_path:
                    downloaded_files.append(csv_path)
                    logger.info(f"{quarter_name} downloaded: {csv_path}")
            except Exception as e:
                logger.error(f"Failed to download {quarter_name}: {e}")
                # Continue with other quarters even if one fails
                continue

        if not downloaded_files:
            raise Exception(f"Failed to download any data for {year}")

        # If we downloaded multiple files, return the list
        # The caller can merge them if needed
        if len(downloaded_files) == 1:
            return downloaded_files[0]

        logger.info(f"Downloaded {len(downloaded_files)} quarterly files for {year}")
        return downloaded_files

    def _download_quarter(self, year, entity_type, start_date, end_date, quarter_name):
        """
        Download a single quarter of data.

        Returns:
            Path to downloaded CSV file
        """
        logger.info(f"Downloading {quarter_name} data: {start_date} to {end_date}")

        with sync_playwright() as p:
            # Launch browser with download settings
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                accept_downloads=True,
            )
            page = context.new_page()

            try:
                # Navigate to advanced search
                logger.info(f"Navigating to {self.ADVANCED_SEARCH_URL}")
                page.goto(self.ADVANCED_SEARCH_URL, wait_until="networkidle", timeout=30000)

                # Wait for page to load
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)

                # Set Election Cycle (year) - this is a dropdown
                try:
                    election_cycle = page.locator("#CycleId, select[name='CycleId'], select[name*='Election'], select[name*='Cycle']")
                    if election_cycle.count() > 0:
                        # Get available options
                        options = election_cycle.first.locator("option").all_inner_texts()
                        logger.info(f"Available election cycles: {options}")

                        # Try to select the requested year
                        try:
                            election_cycle.first.select_option(label=str(year))
                            logger.info(f"Selected election cycle by label: {year}")
                        except:
                            try:
                                election_cycle.first.select_option(value=str(year))
                                logger.info(f"Selected election cycle by value: {year}")
                            except:
                                available_years = [opt.strip() for opt in options if opt.strip() and opt.strip() != "Select..."]
                                if available_years:
                                    most_recent = available_years[0]
                                    election_cycle.first.select_option(label=most_recent)
                                    logger.info(f"Year {year} not available, selected most recent: {most_recent}")
                    else:
                        logger.warning("Election Cycle dropdown not found")
                except Exception as e:
                    logger.warning(f"Could not set election cycle: {e}")

                # Set date range for quarterly chunking (CRITICAL FIX for timeouts)
                try:
                    logger.info(f"Setting date range: {start_date} to {end_date}")
                    start_date_input = page.locator("input[name*='StartDate'], input[id*='StartDate'], input[placeholder*='Start']")
                    end_date_input = page.locator("input[name*='EndDate'], input[id*='EndDate'], input[placeholder*='End']")

                    if start_date_input.count() > 0:
                        start_date_input.first.fill(start_date)
                        logger.info(f"Set start date: {start_date}")

                    if end_date_input.count() > 0:
                        end_date_input.first.fill(end_date)
                        logger.info(f"Set end date: {end_date}")
                except Exception as e:
                    logger.warning(f"Could not set date range: {e}")

                # Set Filer Type (entity type) - checkboxes
                try:
                    if entity_type == "All":
                        # Check all filer types
                        for ftype in ["Candidate", "PAC", "Party"]:
                            checkbox = page.locator(f"input[type='checkbox'][value*='{ftype}'], label:has-text('{ftype}') input[type='checkbox']")
                            if checkbox.count() > 0:
                                checkbox.first.check()
                                logger.info(f"Checked: {ftype}")
                    else:
                        # Check specific entity type
                        checkbox = page.locator(f"input[type='checkbox'][value*='{entity_type}'], label:has-text('{entity_type}') input[type='checkbox']")
                        if checkbox.count() > 0:
                            checkbox.first.check()
                            logger.info(f"Checked entity type: {entity_type}")
                except Exception as e:
                    logger.warning(f"Could not set filer type: {e}")

                # THE KEY FIX: Fill amount range as the "additional search criteria"
                # This satisfies the "one more field" requirement without date validation issues
                logger.info("Filling amount range as additional search criteria...")
                try:
                    low_amount = page.locator("input[name*='LowAmount'], input[id*='LowAmount'], input[placeholder*='Low']")
                    high_amount = page.locator("input[name*='HighAmount'], input[id*='HighAmount'], input[placeholder*='High']")

                    if low_amount.count() > 0 and high_amount.count() > 0:
                        low_amount.first.fill("0")
                        high_amount.first.fill("999999999")
                        logger.info("Set amount range: 0 to 999999999 (captures all transactions)")
                    else:
                        logger.warning("Amount fields not found - trying alternative approach")
                        # Alternative: try any other simple field
                        try:
                            filer_name = page.locator("input[name*='Filer'], input[id*='Filer']")
                            if filer_name.count() > 0:
                                filer_name.first.fill("A")  # Just any letter
                                logger.info("Filled Filer Name with 'A' as fallback")
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Could not set amount range: {e}")

                page.wait_for_timeout(1000)

                # Look for and click search button
                # The button might be enabled now that we have search criteria
                search_button = page.locator(
                    "button:has-text('Search'):not([disabled]), "
                    "input[type='submit'][value*='Search']:not([disabled]), "
                    "button[type='submit']:not([disabled]), "
                    "#SearchButton:not([disabled])"
                )

                if search_button.count() > 0:
                    logger.info("Clicking search button...")
                    search_button.first.click()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(3000)  # Wait for results to load
                else:
                    logger.warning("Enabled search button not found, trying to trigger search via form submit...")
                    # Try submitting the form directly
                    form = page.locator("form")
                    if form.count() > 0:
                        form.first.evaluate("form => form.submit()")
                        page.wait_for_load_state("networkidle")
                        page.wait_for_timeout(3000)

                # Wait for results to load
                logger.info("Waiting for search results...")
                try:
                    page.wait_for_selector("table, .search-results, .results-grid", timeout=10000)
                    logger.info("Results table found")
                except:
                    logger.warning("No results table found, continuing anyway...")

                # CRITICAL: Multi-step wait for results to fully load
                logger.info("Waiting for search results to load...")

                # Step 1: Wait for results table to appear
                try:
                    page.wait_for_selector("table", state="visible", timeout=30000)
                    logger.info("Results table visible")
                except:
                    logger.warning("Results table not found")

                # Step 2: Wait for entry count to appear
                try:
                    page.wait_for_selector("text=/Showing.*entries/i", timeout=30000)
                    logger.info("Entry count displayed")
                except:
                    logger.warning("Entry count not displayed")

                # Step 3: Wait for Processing indicator to disappear (with stuck detection)
                logger.info("Waiting for data processing to complete...")
                try:
                    processing = page.locator("text=/Processing/i")
                    if processing.count() > 0:
                        logger.info("Data is loading... waiting up to 45 seconds")
                        page.wait_for_selector("text=/Processing/i", state="hidden", timeout=45000)
                        logger.info("Processing complete")
                except Exception as e:
                    logger.warning(f"Processing timeout: {e}")
                    logger.info("Attempting to force-remove stuck overlay...")

                    # Force remove overlay if stuck
                    try:
                        page.evaluate("document.querySelectorAll('.overlay').forEach(el => el.remove())")
                        logger.info("Forced removal of overlay")
                        page.wait_for_timeout(2000)
                    except:
                        pass

                # Check for "No records found" message
                no_results = page.locator("text=/no records found/i")
                if no_results.count() > 0:
                    logger.warning("Search returned no results for this date range")
                    raise Exception(f"No data found for {start_date} to {end_date}")

                # Step 4: Additional buffer for DataTables to stabilize
                logger.info("Allowing DataTables to stabilize...")
                page.wait_for_timeout(3000)

                # Take screenshot for debugging
                screenshot_path = self.download_dir / f"debug_seethemoney_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Debug screenshot saved to: {screenshot_path}")

                # Look for export/download button
                # Website has "Export Report" button with CSV option
                export_button = page.locator(
                    "button:has-text('Export Report'), "
                    "a:has-text('Export Report'), "
                    "button:has-text('Export'), "
                    "a:has-text('Export'), "
                    "button:has-text('CSV'), "
                    "a:has-text('CSV'), "
                    "a:has-text('Comma Separated Values')"
                )

                if export_button.count() > 0:
                    logger.info("Found export button, debugging its state...")

                    # DEBUG: Check button state thoroughly
                    try:
                        is_visible = export_button.first.is_visible()
                        is_enabled = export_button.first.is_enabled()
                        is_disabled_attr = export_button.first.get_attribute("disabled")

                        logger.info(f"Export button state:")
                        logger.info(f"  - Visible: {is_visible}")
                        logger.info(f"  - Enabled: {is_enabled}")
                        logger.info(f"  - Disabled attribute: {is_disabled_attr}")

                        # Check button classes and onclick
                        try:
                            classes = export_button.first.get_attribute("class")
                            onclick = export_button.first.get_attribute("onclick")
                            logger.info(f"  - Classes: {classes}")
                            logger.info(f"  - Onclick: {onclick}")
                        except:
                            pass
                    except Exception as e:
                        logger.warning(f"Could not check button state: {e}")

                    # If button is disabled, stop here
                    if is_disabled_attr:
                        logger.error("Export button is DISABLED - cannot proceed")
                        raise Exception("Export button is disabled. Data may still be loading or export feature unavailable.")

                    logger.info("Export button is enabled")

                    # Scroll button into view
                    try:
                        export_button.first.scroll_into_view_if_needed()
                        page.wait_for_timeout(500)
                        logger.info("Button scrolled into view")
                    except Exception as e:
                        logger.warning(f"Could not scroll button: {e}")

                    # STEP 1: Click Export Report button to open modal
                    logger.info("Clicking Export Report button to open modal...")
                    try:
                        export_button.first.click(force=True)
                        logger.info("Export Report button clicked")
                    except Exception as e:
                        logger.error(f"Failed to click export button: {e}")
                        # Try JavaScript click as fallback
                        logger.info("Trying JavaScript click as fallback...")
                        export_button.first.evaluate("button => button.click()")
                        logger.info("JavaScript click executed")

                    # STEP 2: Wait for modal to appear
                    logger.info("Waiting for Export Reports modal...")
                    try:
                        page.wait_for_selector("text=/Export Reports/i", state="visible", timeout=5000)
                        logger.info("Modal appeared")
                    except:
                        logger.warning("Modal title not found, continuing anyway...")

                    page.wait_for_timeout(1000)

                    # Capture screenshot after modal opens
                    after_export_screenshot = self.download_dir / f"after_export_click_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    page.screenshot(path=str(after_export_screenshot), full_page=True)
                    logger.info(f"Modal screenshot: {after_export_screenshot}")

                    # STEP 3: Select CSV format - BULLETPROOF METHOD
                    # Based on actual HTML: <select id="ExportFormatOptions"><option value="CSV">...
                    logger.info("Selecting CSV format from dropdown...")

                    # Wait for dropdown to be ready
                    page.wait_for_selector("#ExportFormatOptions", state="visible", timeout=5000)
                    page.wait_for_timeout(500)

                    # Method 1: Direct value selection (RECOMMENDED)
                    try:
                        logger.info("Attempting direct selection using value='CSV'...")
                        page.locator("#ExportFormatOptions").select_option(value="CSV")
                        logger.info("Selected CSV using select_option(value='CSV')")
                    except Exception as e:
                        logger.warning(f"Direct selection failed: {e}")
                        logger.info("Trying JavaScript fallback...")

                        # Fallback: JavaScript injection
                        page.evaluate("""
                            const select = document.getElementById('ExportFormatOptions');
                            if (!select) throw new Error('ExportFormatOptions select not found');
                            select.value = 'CSV';
                            select.dispatchEvent(new Event('change', { bubbles: true }));
                        """)
                        logger.info("Selected CSV using JavaScript fallback")

                    # VERIFY selection worked
                    selected_value = page.locator("#ExportFormatOptions").evaluate("el => el.value")
                    logger.info(f"Verification - Selected value: '{selected_value}'")

                    if selected_value != "CSV":
                        logger.error(f"Selection verification failed! Expected 'CSV', got '{selected_value}'")
                        raise Exception(f"Failed to select CSV format. Current value: '{selected_value}'")

                    logger.info("CSV format successfully selected and verified!")
                    page.wait_for_timeout(500)

                    # STEP 4: Set up download handler and click Export button
                    logger.info("Setting up download handler and clicking Export button...")

                    # The Export button has id="Export" per the actual HTML
                    export_button = page.locator("#Export")

                    if export_button.count() > 0:
                        logger.info("Found Export submit button (#Export)")

                        # Set up download expectation BEFORE clicking Export
                        with page.expect_download(timeout=60000) as download_info:
                            try:
                                export_button.click(timeout=10000)
                                logger.info("Export button clicked (form submitted)")
                            except Exception as e:
                                logger.warning(f"Normal click failed: {e}")
                                logger.info("Trying force click...")
                                export_button.click(force=True)
                                logger.info("Export button force-clicked")

                        download = download_info.value
                        logger.info("Download started!")
                    else:
                        logger.error("Export button (#Export) not found in modal")
                        logger.error(f"Check screenshot: {after_export_screenshot}")
                        raise Exception(
                            f"Export button not found in modal. "
                            f"Screenshot saved to {after_export_screenshot}"
                        )

                    # Save with descriptive filename including quarter
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"seethemoney_{entity_type.lower()}_{year}_{quarter_name}_{timestamp}.csv"
                    temp_path = self.download_dir / f"temp_{filename}"
                    save_path = self.download_dir / filename

                    # Save to temp location first
                    download.save_as(temp_path)
                    logger.info(f"Downloaded to temp location: {temp_path}")

                    # FIX UTF-16 ENCODING ISSUE
                    # Government sites export CSV as UTF-16, need to convert to UTF-8
                    logger.info("Converting UTF-16 to UTF-8...")
                    try:
                        # Try UTF-16 variants
                        encodings_to_try = ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-8']
                        content = None

                        for encoding in encodings_to_try:
                            try:
                                with open(temp_path, 'r', encoding=encoding) as f:
                                    content = f.read()

                                # Verify it looks correct (check first line doesn't have spaces between every char)
                                first_line = content.split('\n')[0]
                                # If we see normal CSV structure (commas without excessive spaces), it's good
                                if ',' in first_line and not all(c == ' ' for c in first_line[::2]):
                                    logger.info(f"Successfully decoded with {encoding}")
                                    break
                                else:
                                    content = None
                            except Exception as e:
                                logger.debug(f"Failed to decode with {encoding}: {e}")
                                continue

                        if content:
                            # Save as UTF-8
                            with open(save_path, 'w', encoding='utf-8', newline='') as f:
                                f.write(content)
                            logger.info(f"Converted to UTF-8: {save_path}")

                            # Remove temp file
                            temp_path.unlink()
                            logger.info("Removed temp file")
                        else:
                            logger.warning("Could not convert encoding, using original file")
                            temp_path.rename(save_path)

                    except Exception as e:
                        logger.error(f"Encoding conversion failed: {e}")
                        logger.info("Saving original file without conversion")
                        temp_path.rename(save_path)

                    logger.info(f"Downloaded successfully: {save_path}")

                    return save_path

                else:
                    # Try alternative: right-click on table and get data
                    logger.warning("Export button not found, trying alternative methods...")

                    # Look for data table
                    table = page.locator("table")
                    if table.count() > 0:
                        logger.info("Found data table, attempting to extract data...")

                        # Try to find a download link in the table header or toolbar
                        download_link = page.locator("a[href*='.csv'], a[href*='export']")
                        if download_link.count() > 0:
                            href = download_link.first.get_attribute("href")
                            logger.info(f"Found download link: {href}")

                            # Navigate to download URL
                            with page.expect_download() as download_info:
                                page.goto(href if href.startswith('http') else f"{self.BASE_URL}{href}")

                            download = download_info.value
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"seethemoney_{entity_type.lower()}_{year}_{timestamp}.csv"
                            save_path = self.download_dir / filename
                            download.save_as(save_path)

                            logger.info(f"Downloaded successfully: {save_path}")
                            return save_path

                    raise Exception(
                        "Could not find export button or download link. "
                        "The page structure may have changed. "
                        "Try manual download from seethemoney.az.gov"
                    )

            except Exception as e:
                logger.error(f"Error downloading from SeeTheMoney: {str(e)}")
                raise

            finally:
                browser.close()

    def get_available_years(self):
        """
        Get list of available years in the database

        Returns:
            List of years (2002-2026)
        """
        # SeeTheMoney typically has data from 2002 to current year + 2
        current_year = datetime.now().year
        return list(range(2002, current_year + 3))


# Convenience function
def download_seethemoney_data(year=None, entity_type="Candidate", headless=True, quarter=None):
    """
    Download campaign finance data from SeeTheMoney (FREE!)

    Args:
        year: Year for data
        entity_type: Type of entity ("Candidate", "PAC", "Party", "All")
        headless: Run browser in headless mode
        quarter: Specific quarter (1-4), or None to download all quarters

    Returns:
        Path to downloaded CSV file (or list of paths if downloading all quarters)
    """
    scraper = SeeTheMoneyScraper(headless=headless)
    return scraper.download_data(year=year, entity_type=entity_type, quarter=quarter)
