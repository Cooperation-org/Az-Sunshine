"""
City of Tucson Elections Scraper

Scrapes candidate and campaign finance data from City of Tucson Clerk's Office
Website: https://www.tucsonaz.gov/clerks/elections

Tucson is Arizona's second-largest city (in Pima County).
"""

import logging
from .county_scraper_base import CountyScraperBase

logger = logging.getLogger(__name__)


class TucsonScraper(CountyScraperBase):
    """
    Scraper for City of Tucson election data

    City of Tucson Clerk: https://www.tucsonaz.gov/clerks
    Elections: https://www.tucsonaz.gov/clerks/elections
    """

    BASE_URL = "https://www.tucsonaz.gov/clerks/elections"
    COUNTY_NAME = "Tucson City"

    def scrape_candidates(self, page, year):
        """
        Scrape candidate information from City of Tucson

        Structure: Simple semantic HTML with h2 (ward) > strong (name) > em (party)

        Returns:
            list of candidate dicts
        """
        candidates = []

        try:
            # Navigate to candidates page
            candidates_url = "https://www.tucsonaz.gov/Departments/Clerks/Elections/Candidates"
            page.goto(candidates_url, wait_until="domcontentloaded", timeout=30000)

            # Wait for content to load (h2 elements contain ward info)
            page.wait_for_selector("h2", timeout=10000)

            # Get all ward sections (h2 tags contain "Ward 3", "Ward 5", etc.)
            ward_headings = page.locator("h2").all()

            # Process each ward section
            for heading in ward_headings:
                ward_text = self.safe_get_text(heading)

                # Only process ward headings
                if not ward_text or 'Ward' not in ward_text:
                    continue

                # Get all strong tags (candidate names) after this heading until next h2
                # Structure: <strong>LASTNAME, FIRSTNAME</strong> followed by <em>PARTY</em>
                next_element = heading
                try:
                    # Navigate through siblings to find candidates
                    siblings = page.evaluate("""
                        (heading) => {
                            const candidates = [];
                            let current = heading.nextElementSibling;

                            while (current && current.tagName !== 'H2') {
                                if (current.tagName === 'STRONG') {
                                    const name = current.textContent.trim();
                                    const party = current.nextElementSibling?.tagName === 'EM'
                                        ? current.nextElementSibling.textContent.trim()
                                        : '';

                                    candidates.push({
                                        name: name,
                                        party: party
                                    });
                                }
                                current = current.nextElementSibling;
                            }

                            return candidates;
                        }
                    """, heading.element_handle())

                    # Add each candidate found in this ward
                    for candidate_data in siblings:
                        if candidate_data.get('name'):
                            candidate = {
                                'name': candidate_data['name'],
                                'office': f'City Council {ward_text}',
                                'party': candidate_data.get('party', ''),
                                'ward': ward_text,
                                'filing_date': '',
                                'status': 'Active',
                                'county': self.COUNTY_NAME,
                                'jurisdiction': 'City of Tucson',
                                'year': year,
                                'email': '',
                                'phone': ''
                            }
                            candidates.append(candidate)
                            logger.info(f"Found candidate: {candidate['name']} - {ward_text}")

                except Exception as e:
                    logger.warning(f"Error parsing ward {ward_text}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Tucson candidates: {str(e)}")
            raise

        return candidates

    def scrape_filings(self, page, year):
        """
        Scrape campaign finance filings from City of Tucson

        NOTE: Tucson publishes campaign finance as PDF reports, not structured data.
        This method will try to find PDF links or structured data if available.

        Returns:
            list of filing dicts
        """
        filings = []

        try:
            # Navigate to campaign finance page
            finance_url = "https://www.tucsonaz.gov/Departments/Clerks/Elections/Campaign-Finance"

            if self.navigate_with_retry(page, finance_url):
                # Try to find PDF links or structured data
                # Tucson typically provides PDFs rather than tables
                try:
                    page.wait_for_selector("a[href*='.pdf'], table", timeout=5000)
                except Exception:
                    logger.warning("No campaign finance data found on Tucson site - may be PDF-only")
                    return filings

                # Filter by year
                year_select = page.locator("select[name='year'], #yearFilter")
                if year_select.count() > 0:
                    year_select.select_option(str(year))
                    page.wait_for_load_state("networkidle")

                # Extract filing records
                filing_elements = page.locator("table.reports tbody tr, div.filing").all()

                for element in filing_elements:
                    try:
                        filing = {
                            'candidate_name': self.safe_get_text(element.locator(".candidate, td.candidate-name")),
                            'committee_name': self.safe_get_text(element.locator(".committee, td.committee")),
                            'office': self.safe_get_text(element.locator(".office, td.office")),
                            'ward': self.safe_get_text(element.locator(".ward, td.ward")),
                            'filing_type': self.safe_get_text(element.locator(".type, td.report-type")),
                            'filing_date': self.safe_get_text(element.locator(".date, td.filed")),
                            'period_start': self.safe_get_text(element.locator(".start, td.period-start")),
                            'period_end': self.safe_get_text(element.locator(".end, td.period-end")),
                            'total_contributions': self._parse_amount(
                                self.safe_get_text(element.locator(".contributions, td.total-in"))
                            ),
                            'total_expenditures': self._parse_amount(
                                self.safe_get_text(element.locator(".expenditures, td.total-out"))
                            ),
                            'cash_on_hand': self._parse_amount(
                                self.safe_get_text(element.locator(".cash, td.balance"))
                            ),
                            'county': self.COUNTY_NAME,
                            'jurisdiction': 'City of Tucson',
                            'year': year
                        }

                        if filing['candidate_name'] or filing['committee_name']:
                            filings.append(filing)

                    except Exception as e:
                        logger.warning(f"Error parsing Tucson filing: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping Tucson filings: {str(e)}")
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
def scrape_tucson(year=None, headless=True):
    """
    Scrape City of Tucson election data

    Args:
        year: Year to scrape
        headless: Run headless browser

    Returns:
        dict with scraped data
    """
    scraper = TucsonScraper(headless=headless)
    return scraper.scrape(year=year)
