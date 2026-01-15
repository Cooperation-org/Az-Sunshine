#!/usr/bin/env python3
"""
FollowTheMoney.org Data Fetcher

Fetches Arizona campaign finance data from FollowTheMoney.org for comparison
with our local database. Uses their public API endpoints.

Usage:
    python scripts/followthemoney_fetcher.py --api-key YOUR_KEY
    python scripts/followthemoney_fetcher.py --fetch-candidates --state AZ --year 2022
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path

# Add Django setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from transparency.models import Committee, Transaction, Office, Cycle
from django.db.models import Sum, Q
from django.db.models.functions import Abs


class FollowTheMoneyFetcher:
    """Fetches and compares data from FollowTheMoney.org"""

    BASE_URL = "https://api.followthemoney.org"

    # State codes
    STATES = {
        'AZ': 'Arizona',
        'CA': 'California',
        'TX': 'Texas',
        # Add more as needed
    }

    # Office type mappings
    OFFICE_TYPES = {
        'G': 'Governor',
        'AG': 'Attorney General',
        'SS': 'Secretary of State',
        'ST': 'State Treasurer',
        'SPI': 'Superintendent of Public Instruction',
        'CC': 'Corporation Commissioner',
    }

    def __init__(self, api_key=None, output_dir=None):
        self.api_key = api_key
        self.output_dir = Path(output_dir or '/opt/az_sunshine/backend/data/followthemoney')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AZ-Sunshine-DataVerification/1.0 (research project)',
            'Accept': 'application/json',
        })

    def _make_request(self, endpoint, params=None, delay=1.0):
        """Make a request with rate limiting"""
        url = f"{self.BASE_URL}/{endpoint}"
        if params is None:
            params = {}
        if self.api_key:
            params['APIKey'] = self.api_key
        params['mode'] = 'json'

        time.sleep(delay)  # Be respectful

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def fetch_entity(self, entity_id):
        """Fetch details for a specific entity"""
        return self._make_request('entity.php', {'eid': entity_id})

    def fetch_candidates_by_state_year(self, state, year):
        """
        Fetch candidate data for a state and year.
        Note: This requires proper API access.
        """
        params = {
            's': state,
            'y': year,
            'c-t-eid': 1,  # Candidate type
        }
        return self._make_request('candidates.php', params)

    def save_data(self, data, filename):
        """Save fetched data to JSON file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"Saved: {filepath}")
        return filepath


class LocalDataExporter:
    """Export our local database data for comparison"""

    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or '/opt/az_sunshine/backend/data/comparison')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_race_ie_data(self, office_name, cycle_year):
        """Export IE spending data for a specific race"""
        try:
            office = Office.objects.get(name=office_name)
            cycle = Cycle.objects.get(name=str(cycle_year))
        except (Office.DoesNotExist, Cycle.DoesNotExist) as e:
            print(f"Error: {e}")
            return None

        # Get IE spending data
        results = Transaction.objects.filter(
            subject_committee__candidate_office=office,
            transaction_date__gte=cycle.begin_date,
            transaction_date__lte=cycle.end_date,
            transaction_type__income_expense_neutral=2,
            deleted=False
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__last_name',
            'subject_committee__candidate_party__name',
        ).annotate(
            ie_for=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            ie_against=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
            total_ie=Sum(Abs('amount'))
        ).order_by('-total_ie')

        data = {
            'office': office_name,
            'cycle': cycle_year,
            'exported_at': datetime.now().isoformat(),
            'candidates': []
        }

        for r in results:
            data['candidates'].append({
                'committee_id': r['subject_committee__committee_id'],
                'name': r['subject_committee__name__last_name'],
                'party': r['subject_committee__candidate_party__name'],
                'ie_for': float(r['ie_for'] or 0),
                'ie_against': float(r['ie_against'] or 0),
                'total_ie': float(r['total_ie'] or 0),
            })

        # Save to file
        filename = f"local_{office_name.lower().replace(' ', '_')}_{cycle_year}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Exported: {filepath}")
        return data

    def export_all_2022_races(self):
        """Export all major 2022 races"""
        races = [
            ('Governor', 2022),
            ('Attorney General', 2022),
            ('Secretary of State', 2022),
            ('State Treasurer', 2022),
            ('Superintendent of Public Instruction', 2022),
        ]

        all_data = {}
        for office, year in races:
            data = self.export_race_ie_data(office, year)
            if data:
                all_data[f"{office}_{year}"] = data

        # Save combined file
        combined_path = self.output_dir / 'all_2022_races.json'
        with open(combined_path, 'w') as f:
            json.dump(all_data, f, indent=2)

        print(f"\nCombined export: {combined_path}")
        return all_data


class DataComparator:
    """Compare local data with external sources"""

    def __init__(self, local_dir=None, external_dir=None):
        self.local_dir = Path(local_dir or '/opt/az_sunshine/backend/data/comparison')
        self.external_dir = Path(external_dir or '/opt/az_sunshine/backend/data/followthemoney')

    def compare_race(self, office, year, external_data):
        """
        Compare local race data with external data.

        external_data should be a dict with candidate names as keys
        and IE totals as values.
        """
        local_file = self.local_dir / f"local_{office.lower().replace(' ', '_')}_{year}.json"

        if not local_file.exists():
            print(f"Local file not found: {local_file}")
            return None

        with open(local_file) as f:
            local_data = json.load(f)

        print(f"\n{'='*70}")
        print(f"COMPARISON: {office} {year}")
        print(f"{'='*70}")

        comparison = []
        for candidate in local_data['candidates']:
            name = candidate['name']
            local_total = candidate['total_ie']
            local_for = candidate['ie_for']
            local_against = candidate['ie_against']

            # Try to find matching external data
            external_total = external_data.get(name, {}).get('total', 'N/A')
            external_for = external_data.get(name, {}).get('for', 'N/A')
            external_against = external_data.get(name, {}).get('against', 'N/A')

            comparison.append({
                'name': name,
                'local_total': local_total,
                'external_total': external_total,
                'local_for': local_for,
                'external_for': external_for,
                'local_against': local_against,
                'external_against': external_against,
            })

            print(f"\n{name}:")
            print(f"  Local:    Total=${local_total:>12,.2f}  For=${local_for:>12,.2f}  Against=${local_against:>12,.2f}")
            if external_total != 'N/A':
                print(f"  External: Total=${external_total:>12,.2f}  For=${external_for:>12,.2f}  Against=${external_against:>12,.2f}")
                diff = local_total - external_total
                print(f"  Diff:     ${diff:>+12,.2f} ({diff/external_total*100:+.1f}%)" if external_total else "")
            else:
                print(f"  External: No matching data found")

        return comparison

    def generate_report(self):
        """Generate a full comparison report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'races': {}
        }

        # Load all local data
        for f in self.local_dir.glob('local_*.json'):
            with open(f) as file:
                data = json.load(file)
                key = f"{data['office']}_{data['cycle']}"
                report['races'][key] = {
                    'local_data': data,
                    'external_data': None,  # To be filled when external data is available
                    'comparison': None
                }

        report_path = self.local_dir / 'comparison_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved: {report_path}")
        return report


def main():
    parser = argparse.ArgumentParser(description='FollowTheMoney Data Fetcher & Comparator')
    parser.add_argument('--api-key', help='FollowTheMoney API key')
    parser.add_argument('--export-local', action='store_true', help='Export local database data')
    parser.add_argument('--fetch-external', action='store_true', help='Fetch from FollowTheMoney')
    parser.add_argument('--compare', action='store_true', help='Compare local vs external')
    parser.add_argument('--state', default='AZ', help='State code (default: AZ)')
    parser.add_argument('--year', type=int, default=2022, help='Election year (default: 2022)')
    parser.add_argument('--office', help='Specific office to process')

    args = parser.parse_args()

    if args.export_local:
        print("Exporting local database data...")
        exporter = LocalDataExporter()
        if args.office:
            exporter.export_race_ie_data(args.office, args.year)
        else:
            exporter.export_all_2022_races()

    if args.fetch_external:
        if not args.api_key:
            print("Note: API key not provided. Some features may be limited.")
            print("Get a free API key at: https://www.followthemoney.org/")

        fetcher = FollowTheMoneyFetcher(api_key=args.api_key)
        print(f"Fetching data for {args.state} {args.year}...")
        # API calls would go here

    if args.compare:
        comparator = DataComparator()
        comparator.generate_report()

    # Default: export local data if no args
    if not any([args.export_local, args.fetch_external, args.compare]):
        print("Exporting local database data (default action)...")
        exporter = LocalDataExporter()
        exporter.export_all_2022_races()


if __name__ == '__main__':
    main()
