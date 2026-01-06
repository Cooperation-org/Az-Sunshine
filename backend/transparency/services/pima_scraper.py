"""
Pima County Elections Department Scraper

Scrapes candidate and campaign finance data from Pima County Recorder's Office
Website: https://www.recorder.pima.gov/

Pima County is Arizona's second-largest county (Tucson area).
"""

import logging
from .county_scraper_base import CountyScraperBase

logger = logging.getLogger(__name__)


class PimaScraper(CountyScraperBase):
    """
    Scraper for Pima County election data

    Pima County Recorder: https://www.recorder.pima.gov/
    Elections: https://www.recorder.pima.gov/elections
    """

    BASE_URL = "https://www.recorder.pima.gov/elections"
    COUNTY_NAME = "Pima"

    def scrape_candidates(self, page, year):
        """
        Scrape candidate information from Pima County

        NOTE: Pima County may use anti-bot protection.
        Recommended alternative: Use AZ SOS database which includes all counties.

        Returns:
            list of candidate dicts
        """
        candidates = []

        logger.warning(
            " Pima County website may use anti-bot protection. "
            "Recommended: Use AZ SOS Automation instead (covers all counties including Pima)."
        )

        try:
            # Navigate to candidates section
            candidates_url = f"{self.BASE_URL}/candidates"
            page.goto(candidates_url, wait_until="load", timeout=45000)

            # Wait for content to load
            page.wait_for_selector("table, .candidate-list, div.candidate", timeout=10000)

            # Extract candidate information
            # Update selectors based on actual Pima County website structure
            candidate_elements = page.locator("table tr.candidate-row, div.candidate-entry").all()

            for element in candidate_elements:
                try:
                    candidate = {
                        'name': self.safe_get_text(element.locator(".name, td.candidate-name")),
                        'office': self.safe_get_text(element.locator(".office, td.office")),
                        'party': self.safe_get_text(element.locator(".party, td.party")),
                        'filing_date': self.safe_get_text(element.locator(".filed-date, td.date")),
                        'status': self.safe_get_text(element.locator(".status, td.status"), "Active"),
                        'county': self.COUNTY_NAME,
                        'year': year,
                        'email': self.safe_get_text(element.locator(".email, td.email")),
                        'phone': self.safe_get_text(element.locator(".phone, td.phone"))
                    }

                    if candidate['name']:
                        candidates.append(candidate)

                except Exception as e:
                    logger.warning(f"Error parsing Pima candidate: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Pima candidates: {str(e)}")
            raise

        return candidates

    def scrape_filings(self, page, year):
        """
        Scrape campaign finance filings from Pima County

        Returns:
            list of filing dicts
        """
        filings = []

        try:
            # Navigate to campaign finance section
            finance_url = f"{self.BASE_URL}/campaign-finance"

            if self.navigate_with_retry(page, finance_url):
                # Wait for filings table
                page.wait_for_selector("table.filings, .finance-reports", timeout=10000)

                # Filter by year if available
                year_filter = page.locator("select#year, select[name='year']")
                if year_filter.count() > 0:
                    year_filter.select_option(str(year))
                    page.wait_for_timeout(2000)  # Wait for filter to apply

                # Extract filing data
                filing_elements = page.locator("table.filings tbody tr, div.filing-record").all()

                for element in filing_elements:
                    try:
                        filing = {
                            'candidate_name': self.safe_get_text(element.locator(".candidate-name, td:nth-child(1)")),
                            'committee_name': self.safe_get_text(element.locator(".committee-name, td:nth-child(2)")),
                            'filing_type': self.safe_get_text(element.locator(".report-type, td:nth-child(3)")),
                            'filing_date': self.safe_get_text(element.locator(".filed, td:nth-child(4)")),
                            'period_start': self.safe_get_text(element.locator(".period-from, td:nth-child(5)")),
                            'period_end': self.safe_get_text(element.locator(".period-to, td:nth-child(6)")),
                            'total_contributions': self._parse_amount(
                                self.safe_get_text(element.locator(".contributions, td:nth-child(7)"))
                            ),
                            'total_expenditures': self._parse_amount(
                                self.safe_get_text(element.locator(".expenditures, td:nth-child(8)"))
                            ),
                            'cash_on_hand': self._parse_amount(
                                self.safe_get_text(element.locator(".balance, td:nth-child(9)"))
                            ),
                            'county': self.COUNTY_NAME,
                            'year': year
                        }

                        if filing['candidate_name'] or filing['committee_name']:
                            filings.append(filing)

                    except Exception as e:
                        logger.warning(f"Error parsing Pima filing: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping Pima filings: {str(e)}")
            raise

        return filings

    def _parse_amount(self, amount_str):
        """Parse dollar amount from string"""
        if not amount_str:
            return "0.00"

        amount_str = amount_str.replace('$', '').replace(',', '').strip()

        try:
            return f"{float(amount_str):.2f}"
        except ValueError:
            return "0.00"


# Convenience function
def scrape_pima(year=None, headless=True):
    """
    Scrape Pima County election data

    Args:
        year: Year to scrape
        headless: Run headless browser

    Returns:
        dict with scraped data
    """
    scraper = PimaScraper(headless=headless)
    return scraper.scrape(year=year)
