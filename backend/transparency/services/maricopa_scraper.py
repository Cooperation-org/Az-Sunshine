"""
Maricopa County Elections Department Scraper

Scrapes candidate and campaign finance data from Maricopa County Recorder's Office
Website: https://recorder.maricopa.gov/

Maricopa County is Arizona's largest county (Phoenix area) with the most election data.
"""

import logging
from .county_scraper_base import CountyScraperBase

logger = logging.getLogger(__name__)


class MaricopaScraper(CountyScraperBase):
    """
    Scraper for Maricopa County election data

    Maricopa County Recorder: https://recorder.maricopa.gov/
    Elections: https://recorder.maricopa.gov/elections/
    """

    BASE_URL = "https://recorder.maricopa.gov/elections/"
    COUNTY_NAME = "Maricopa"

    def scrape_candidates(self, page, year):
        """
        Scrape candidate information from Maricopa County

        NOTE: Maricopa County uses anti-bot protection and ASP.NET forms.
        Recommended alternative: Use AZ SOS database which includes all counties.

        Returns:
            list of candidate dicts with fields:
            - name
            - office
            - party
            - filing_date
            - status
            - county
        """
        candidates = []

        logger.warning(
            "⚠️  Maricopa County website uses anti-bot protection. "
            "Recommended: Use AZ SOS Automation instead (covers all counties including Maricopa)."
        )

        try:
            # Navigate to candidates page - may fail due to anti-bot measures
            candidates_url = f"{self.BASE_URL}candidate-listing"
            page.goto(candidates_url, wait_until="load", timeout=45000)

            # Wait for candidate table/list to load
            page.wait_for_selector("table.candidates, .candidate-list, div.candidate", timeout=10000)

            # Extract candidate rows (update selectors based on actual website structure)
            # These are example selectors - need to be updated based on actual Maricopa County website
            candidate_rows = page.locator("table.candidates tbody tr, div.candidate-item").all()

            for row in candidate_rows:
                try:
                    candidate = {
                        'name': self.safe_get_text(row.locator(".candidate-name, td:nth-child(1)")),
                        'office': self.safe_get_text(row.locator(".office, td:nth-child(2)")),
                        'party': self.safe_get_text(row.locator(".party, td:nth-child(3)")),
                        'filing_date': self.safe_get_text(row.locator(".filing-date, td:nth-child(4)")),
                        'status': self.safe_get_text(row.locator(".status, td:nth-child(5)"), "Active"),
                        'county': self.COUNTY_NAME,
                        'year': year
                    }

                    # Only add if we got at least a name
                    if candidate['name']:
                        candidates.append(candidate)

                except Exception as e:
                    logger.warning(f"Error parsing candidate row: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Maricopa candidates: {str(e)}")
            raise

        return candidates

    def scrape_filings(self, page, year):
        """
        Scrape campaign finance filings from Maricopa County

        Returns:
            list of filing dicts with fields:
            - candidate_name
            - committee_name
            - filing_type
            - filing_date
            - period_start
            - period_end
            - total_contributions
            - total_expenditures
            - cash_on_hand
            - county
        """
        filings = []

        try:
            # Navigate to campaign finance page
            finance_url = f"{self.BASE_URL}campaign-finance"

            if self.navigate_with_retry(page, finance_url):
                # Wait for filings table
                page.wait_for_selector("table.filings, .filing-list", timeout=10000)

                # Select year if dropdown exists
                year_selector = page.locator("select[name='year'], select#year")
                if year_selector.count() > 0:
                    year_selector.select_option(str(year))
                    page.wait_for_load_state("networkidle")

                # Extract filing rows
                filing_rows = page.locator("table.filings tbody tr, div.filing-item").all()

                for row in filing_rows:
                    try:
                        filing = {
                            'candidate_name': self.safe_get_text(row.locator(".candidate, td:nth-child(1)")),
                            'committee_name': self.safe_get_text(row.locator(".committee, td:nth-child(2)")),
                            'filing_type': self.safe_get_text(row.locator(".type, td:nth-child(3)")),
                            'filing_date': self.safe_get_text(row.locator(".date, td:nth-child(4)")),
                            'period_start': self.safe_get_text(row.locator(".period-start, td:nth-child(5)")),
                            'period_end': self.safe_get_text(row.locator(".period-end, td:nth-child(6)")),
                            'total_contributions': self._parse_amount(
                                self.safe_get_text(row.locator(".contributions, td:nth-child(7)"))
                            ),
                            'total_expenditures': self._parse_amount(
                                self.safe_get_text(row.locator(".expenditures, td:nth-child(8)"))
                            ),
                            'cash_on_hand': self._parse_amount(
                                self.safe_get_text(row.locator(".cash, td:nth-child(9)"))
                            ),
                            'county': self.COUNTY_NAME,
                            'year': year
                        }

                        if filing['candidate_name'] or filing['committee_name']:
                            filings.append(filing)

                    except Exception as e:
                        logger.warning(f"Error parsing filing row: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping Maricopa filings: {str(e)}")
            raise

        return filings

    def _parse_amount(self, amount_str):
        """Parse dollar amount from string"""
        if not amount_str:
            return "0.00"

        # Remove $ and commas
        amount_str = amount_str.replace('$', '').replace(',', '').strip()

        try:
            return f"{float(amount_str):.2f}"
        except ValueError:
            return "0.00"


# Convenience function for direct usage
def scrape_maricopa(year=None, headless=True):
    """
    Scrape Maricopa County election data

    Args:
        year: Year to scrape (default: current year)
        headless: Run browser in headless mode

    Returns:
        dict with scraped data
    """
    scraper = MaricopaScraper(headless=headless)
    return scraper.scrape(year=year)
