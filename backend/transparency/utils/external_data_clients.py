"""
External Data Clients for Data Verification Layer
Fetches campaign finance data from:
1. FollowTheMoney.org API
2. SeeTheMoney.az.gov (Arizona Secretary of State)

Used to verify Az-Sunshine database accuracy.
"""

import requests
import logging
import time
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class FollowTheMoneyClient:
    """
    Client for FollowTheMoney.org API
    API Documentation: https://www.followthemoney.org/our-data/apis/documentation

    Requires API key from myFollowTheMoney account.
    Set FOLLOWTHEMONEY_API_KEY in Django settings or environment.
    """

    BASE_URL = "https://api.followthemoney.org"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'FOLLOWTHEMONEY_API_KEY', None)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Az-Sunshine-Verification/1.0',
            'Accept': 'application/json'
        })
        self._rate_limit_delay = 1.0  # seconds between requests
        self._last_request_time = 0

    def _rate_limit(self):
        """Respect rate limits"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling"""
        if not self.api_key:
            logger.warning("FollowTheMoney API key not configured")
            return None

        self._rate_limit()

        params = params or {}
        params['APIKey'] = self.api_key

        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"FollowTheMoney API error: {e}")
            return None

    def get_candidate_totals(self, state: str = 'AZ', year: int = None,
                             office: str = None) -> List[Dict]:
        """
        Get candidate fundraising totals

        Args:
            state: State abbreviation (default: AZ)
            year: Election year
            office: Office name filter

        Returns:
            List of candidate records with totals
        """
        params = {
            's': state,
            'y': year,
            'gro': 'c-t-id',  # Group by candidate
        }
        if office:
            params['f-fc'] = office

        data = self._make_request('candidates.php', params)
        if not data:
            return []

        return data.get('records', [])

    def get_independent_expenditures(self, state: str = 'AZ', year: int = None,
                                      candidate_id: str = None) -> List[Dict]:
        """
        Get independent expenditure data

        Args:
            state: State abbreviation
            year: Election year
            candidate_id: FollowTheMoney candidate/entity ID

        Returns:
            List of IE records
        """
        params = {
            's': state,
            'y': year,
            'gro': 'c-t-id',
        }
        if candidate_id:
            params['c-t-id'] = candidate_id

        data = self._make_request('independent_expenditures.php', params)
        if not data:
            return []

        return data.get('records', [])

    def get_arizona_races(self, year: int) -> List[Dict]:
        """Get all Arizona races for a given year"""
        params = {
            's': 'AZ',
            'y': year,
            'gro': 'f-fc',  # Group by office
        }
        data = self._make_request('candidates.php', params)
        if not data:
            return []

        return data.get('records', [])

    def search_candidate(self, name: str, state: str = 'AZ',
                        year: int = None) -> List[Dict]:
        """
        Search for a candidate by name

        Args:
            name: Candidate name to search
            state: State abbreviation
            year: Election year

        Returns:
            List of matching candidates
        """
        params = {
            's': state,
            'c-t-nm': name,
        }
        if year:
            params['y'] = year

        data = self._make_request('candidates.php', params)
        if not data:
            return []

        return data.get('records', [])


class SeeTheMoneyClient:
    """
    Client for Arizona Secretary of State's SeeTheMoney.az.gov

    This is the official source for Arizona campaign finance data.
    Uses web scraping since there's no official API.
    """

    BASE_URL = "https://seethemoney.az.gov"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Az-Sunshine-Verification/1.0',
            'Accept': 'application/json, text/html'
        })
        self._rate_limit_delay = 2.0  # Be respectful to gov site
        self._last_request_time = 0

    def _rate_limit(self):
        """Respect rate limits"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[requests.Response]:
        """Make request with error handling"""
        self._rate_limit()

        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"SeeTheMoney request error: {e}")
            return None

    def get_independent_expenditures_csv(self, candidate_name: str = None,
                                         year: int = None,
                                         support_oppose: str = None) -> Optional[str]:
        """
        Download IE data as CSV from SeeTheMoney

        Args:
            candidate_name: Filter by candidate name
            year: Election year
            support_oppose: 'Benefits' or 'Opposes'

        Returns:
            CSV content as string, or None on error
        """
        # SeeTheMoney uses a specific URL pattern for CSV exports
        params = {
            'format': 'csv',
        }
        if candidate_name:
            params['candidate'] = candidate_name
        if year:
            params['year'] = year
        if support_oppose:
            params['position'] = support_oppose

        response = self._make_request('api/independent-expenditures/export', params)
        if response:
            return response.text
        return None

    def get_candidate_ie_summary(self, candidate_name: str,
                                  year: int = None) -> Dict[str, Any]:
        """
        Get IE spending summary for a specific candidate

        Args:
            candidate_name: Candidate name
            year: Election year

        Returns:
            Dict with ie_for, ie_against, total
        """
        # This would need to parse the actual page or use their internal API
        # For now, return structure that will be populated
        return {
            'candidate_name': candidate_name,
            'year': year,
            'ie_for': Decimal('0'),
            'ie_against': Decimal('0'),
            'total_ie': Decimal('0'),
            'transaction_count': 0,
            'source': 'seethemoney.az.gov',
            'fetched_at': datetime.now().isoformat()
        }

    def search_candidates(self, office: str = None, year: int = None) -> List[Dict]:
        """
        Search for candidates with IE spending

        Args:
            office: Office name filter
            year: Election year

        Returns:
            List of candidates with IE data
        """
        params = {}
        if office:
            params['office'] = office
        if year:
            params['year'] = year

        # Would need to parse the search results page
        # Return empty for now - will implement with actual scraping
        return []


class ExternalDataAggregator:
    """
    Aggregates data from multiple external sources for verification
    """

    def __init__(self):
        self.ftm_client = FollowTheMoneyClient()
        self.stm_client = SeeTheMoneyClient()

    def get_race_data(self, office: str, year: int,
                      party: str = None) -> Dict[str, Any]:
        """
        Get race data from all external sources

        Args:
            office: Office name (e.g., "Governor", "Attorney General")
            year: Election year
            party: Optional party filter

        Returns:
            Aggregated data from all sources
        """
        result = {
            'office': office,
            'year': year,
            'party': party,
            'sources': {},
            'fetched_at': datetime.now().isoformat()
        }

        # FollowTheMoney data
        ftm_data = self.ftm_client.get_arizona_races(year)
        if ftm_data:
            # Filter to specific office
            office_data = [r for r in ftm_data
                          if office.lower() in r.get('Office', '').lower()]
            result['sources']['followthemoney'] = {
                'status': 'success',
                'records': office_data,
                'count': len(office_data)
            }
        else:
            result['sources']['followthemoney'] = {
                'status': 'error' if self.ftm_client.api_key else 'no_api_key',
                'records': [],
                'count': 0
            }

        # SeeTheMoney data
        stm_candidates = self.stm_client.search_candidates(office=office, year=year)
        result['sources']['seethemoney'] = {
            'status': 'success' if stm_candidates else 'no_data',
            'records': stm_candidates,
            'count': len(stm_candidates)
        }

        return result

    def get_candidate_comparison(self, candidate_name: str,
                                  year: int) -> Dict[str, Any]:
        """
        Get candidate data from all sources for comparison

        Args:
            candidate_name: Candidate name
            year: Election year

        Returns:
            Data from all sources for this candidate
        """
        result = {
            'candidate_name': candidate_name,
            'year': year,
            'sources': {},
            'fetched_at': datetime.now().isoformat()
        }

        # FollowTheMoney
        ftm_results = self.ftm_client.search_candidate(candidate_name, year=year)
        result['sources']['followthemoney'] = {
            'status': 'success' if ftm_results else 'not_found',
            'data': ftm_results[0] if ftm_results else None
        }

        # SeeTheMoney
        stm_data = self.stm_client.get_candidate_ie_summary(candidate_name, year)
        result['sources']['seethemoney'] = {
            'status': 'success' if stm_data else 'not_found',
            'data': stm_data
        }

        return result
