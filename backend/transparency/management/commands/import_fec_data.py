"""
Import federal election data (FEC) for Arizona races.

This command fetches independent expenditure data from the FEC API
(api.open.fec.gov) for Arizona federal races including US Senate
and US House races.

API Key:
    The FEC API requires an API key. Get a free one at:
    https://api.data.gov/signup/

    Set the key via:
    1. Environment variable: FEC_API_KEY=your_key_here
    2. Command line: --api-key YOUR_KEY
    3. Django settings: FEC_API_KEY = 'your_key_here'

Usage:
    # Dry run to preview data without saving
    python manage.py import_fec_data --dry-run

    # Import specific election cycle
    python manage.py import_fec_data --cycle 2024

    # Import multiple cycles
    python manage.py import_fec_data --cycle 2020 --cycle 2022 --cycle 2024

    # Save to JSON file for review
    python manage.py import_fec_data --cycle 2024 --output /tmp/fec_az_2024.json

    # Import all recent cycles (2018-2024)
    python manage.py import_fec_data --all-cycles

    # Specify API key on command line
    python manage.py import_fec_data --api-key YOUR_API_KEY --cycle 2024
"""

import json
import os
import time
import requests
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from pathlib import Path


# Arizona Congressional Districts (as of 2022 redistricting: 9 districts)
AZ_DISTRICTS = ['AZ-01', 'AZ-02', 'AZ-03', 'AZ-04', 'AZ-05', 'AZ-06', 'AZ-07', 'AZ-08', 'AZ-09']
AZ_SENATE = 'AZ-S1'  # Senate seat designation

# FEC API base URL
FEC_API_BASE = 'https://api.open.fec.gov/v1'

# Default cycles to fetch if --all-cycles is used
DEFAULT_CYCLES = [2018, 2020, 2022, 2024]

# Demo API key (for testing - limited rate)
# Get your own at https://api.data.gov/signup/
DEMO_API_KEY = 'DEMO_KEY'


class Command(BaseCommand):
    help = 'Import FEC independent expenditure data for Arizona federal races'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='FEC API key (or set FEC_API_KEY env var). Get free key at https://api.data.gov/signup/'
        )
        parser.add_argument(
            '--cycle',
            type=int,
            action='append',
            dest='cycles',
            help='Election cycle year(s) to fetch (e.g., --cycle 2020 --cycle 2024)'
        )
        parser.add_argument(
            '--all-cycles',
            action='store_true',
            help='Fetch all recent cycles (2018-2024)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview data without saving to database'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Save data to JSON file for review'
        )
        parser.add_argument(
            '--per-page',
            type=int,
            default=100,
            help='Results per API page (default: 100, max: 100)'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=50,
            help='Maximum pages to fetch per query (default: 50)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each expenditure'
        )

    def handle(self, *args, **options):
        cycles = options.get('cycles') or []
        all_cycles = options.get('all_cycles', False)
        dry_run = options.get('dry_run', False)
        output_path = options.get('output')
        per_page = min(options.get('per_page', 100), 100)  # FEC max is 100
        max_pages = options.get('max_pages', 50)
        verbose = options.get('verbose', False)

        # Get API key from various sources
        self.api_key = (
            options.get('api_key') or
            os.environ.get('FEC_API_KEY') or
            getattr(settings, 'FEC_API_KEY', None) or
            DEMO_API_KEY
        )

        if self.api_key == DEMO_API_KEY:
            self.stdout.write(self.style.WARNING(
                '\nUsing DEMO_KEY - limited to 1000 requests/hour.\n'
                'Get a free API key at: https://api.data.gov/signup/\n'
                'Set via: --api-key KEY, FEC_API_KEY env var, or settings.FEC_API_KEY\n'
            ))

        # Determine which cycles to fetch
        if all_cycles:
            cycles = DEFAULT_CYCLES
        elif not cycles:
            # Default to current and previous cycle
            current_year = datetime.now().year
            if current_year % 2 == 0:
                cycles = [current_year]
            else:
                cycles = [current_year - 1]

        self.stdout.write(
            '\n' + '=' * 70 + '\n' +
            '  FEC INDEPENDENT EXPENDITURE IMPORTER\n' +
            '  Arizona Federal Races (US Senate & House)\n' +
            '=' * 70 + '\n'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved\n'))

        self.stdout.write(f"Cycles to fetch: {', '.join(str(c) for c in cycles)}")
        self.stdout.write(f"Per page: {per_page}, Max pages: {max_pages}\n")

        # Test API connection
        if not self._test_api_connection():
            self.stdout.write(self.style.ERROR('Failed to connect to FEC API'))
            return

        # Fetch data for all cycles
        all_data = []
        summary_by_cycle = {}

        for cycle in sorted(cycles):
            self.stdout.write(self.style.MIGRATE_HEADING(
                f'\n{"=" * 50}\n  CYCLE {cycle}\n{"=" * 50}'
            ))

            cycle_data = self._fetch_cycle_data(cycle, per_page, max_pages, verbose)
            all_data.extend(cycle_data)

            # Summarize this cycle
            summary_by_cycle[cycle] = self._summarize_cycle_data(cycle_data)
            self._display_cycle_summary(cycle, summary_by_cycle[cycle])

        # Display overall summary
        self._display_overall_summary(summary_by_cycle)

        # Save to JSON file if requested
        if output_path:
            self._save_to_json(output_path, all_data, summary_by_cycle)

        # Save to database (unless dry run)
        if not dry_run and all_data:
            self._save_to_database(all_data)
        elif dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN complete. {len(all_data)} expenditures would be saved.'
            ))

    def _test_api_connection(self):
        """Test connection to FEC API"""
        self.stdout.write("Testing FEC API connection...")
        try:
            # Simple test query
            url = f"{FEC_API_BASE}/schedules/schedule_e/"
            params = {
                'api_key': self.api_key,
                'state': 'AZ',
                'per_page': 1,
            }
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    self.stdout.write(self.style.SUCCESS(
                        f"  Connected successfully. API version: {data.get('api_version', 'unknown')}"
                    ))
                    return True
                else:
                    self.stdout.write(self.style.ERROR(f"  Unexpected response format"))
                    return False
            elif response.status_code == 403:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                self.stdout.write(self.style.ERROR(
                    f"  API key error: {error_msg}"
                ))
                self.stdout.write(self.style.NOTICE(
                    "  Get a free API key at: https://api.data.gov/signup/"
                ))
                return False
            elif response.status_code == 429:
                self.stdout.write(self.style.ERROR(
                    "  Rate limited. Wait a moment and try again."
                ))
                return False
            else:
                self.stdout.write(self.style.ERROR(
                    f"  HTTP {response.status_code}: {response.text[:200]}"
                ))
                return False

        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR("  Connection timeout"))
            return False
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"  Connection error: {e}"))
            return False

    def _fetch_cycle_data(self, cycle, per_page, max_pages, verbose):
        """Fetch all IE data for a specific election cycle"""
        all_expenditures = []

        # Fetch Senate race IEs
        self.stdout.write(f"\nFetching US Senate IEs...")
        senate_data = self._fetch_schedule_e(
            cycle=cycle,
            office='S',  # Senate
            state='AZ',
            per_page=per_page,
            max_pages=max_pages,
            verbose=verbose
        )
        all_expenditures.extend(senate_data)
        self.stdout.write(f"  Found {len(senate_data)} Senate expenditures")

        # Fetch House race IEs
        self.stdout.write(f"\nFetching US House IEs...")
        house_data = self._fetch_schedule_e(
            cycle=cycle,
            office='H',  # House
            state='AZ',
            per_page=per_page,
            max_pages=max_pages,
            verbose=verbose
        )
        all_expenditures.extend(house_data)
        self.stdout.write(f"  Found {len(house_data)} House expenditures")

        return all_expenditures

    def _fetch_schedule_e(self, cycle, office, state, per_page, max_pages, verbose):
        """
        Fetch Schedule E (Independent Expenditure) data from FEC API

        API Docs: https://api.open.fec.gov/developers/
        Endpoint: /schedules/schedule_e/
        """
        expenditures = []
        url = f"{FEC_API_BASE}/schedules/schedule_e/"

        # Base parameters
        params = {
            'api_key': self.api_key,
            'state': state,
            'cycle': cycle,
            'per_page': per_page,
            'sort': '-expenditure_amount',  # Largest first
            'is_notice': False,  # Exclude 24/48 hour notices (they'll be in full reports)
        }

        # Filter by office type if specified
        if office:
            params['candidate_office'] = office

        page = 1
        last_index = None

        while page <= max_pages:
            try:
                # FEC uses cursor-based pagination
                if last_index:
                    params['last_index'] = last_index

                self.stdout.write(f"    Fetching page {page}...", ending='')
                response = requests.get(url, params=params, timeout=60)

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    self.stdout.write(self.style.WARNING(" Rate limited, waiting 60s..."))
                    time.sleep(60)
                    continue

                if response.status_code == 422:
                    # Validation error - likely pagination issue, try without last_index
                    self.stdout.write(self.style.WARNING(" Pagination limit reached"))
                    break

                if response.status_code != 200:
                    self.stdout.write(self.style.ERROR(
                        f" Error: HTTP {response.status_code}"
                    ))
                    break

                data = response.json()
                results = data.get('results', [])

                if not results:
                    self.stdout.write(" No more results")
                    break

                self.stdout.write(f" {len(results)} results")

                for item in results:
                    expenditure = self._parse_expenditure(item, cycle, office)
                    if expenditure:
                        expenditures.append(expenditure)
                        if verbose:
                            self._display_expenditure(expenditure)

                # Get pagination info
                pagination = data.get('pagination', {})
                last_index = pagination.get('last_indexes', {}).get('last_index')

                if not last_index or len(results) < per_page:
                    break

                page += 1
                time.sleep(0.5)  # Be nice to the API

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f" Request error: {e}"))
                break

        return expenditures

    def _parse_expenditure(self, item, cycle, office_type):
        """Parse an expenditure item from FEC API response"""
        try:
            # Extract key fields
            expenditure = {
                # Identifiers
                'fec_file_id': item.get('file_number'),
                'line_number': item.get('line_number'),
                'transaction_id': item.get('transaction_id'),
                'sub_id': item.get('sub_id'),

                # Committee (spender) info
                'committee_id': item.get('committee_id'),
                'committee_name': item.get('committee', {}).get('name') or item.get('committee_name', ''),

                # Amount
                'amount': Decimal(str(item.get('expenditure_amount', 0))),

                # Support/Oppose
                'support_oppose': item.get('support_oppose_indicator', ''),  # 'S' or 'O'
                'is_support': item.get('support_oppose_indicator') == 'S',

                # Candidate info
                'candidate_id': item.get('candidate_id'),
                'candidate_name': item.get('candidate_name', ''),
                'candidate_first_name': item.get('candidate_first_name', ''),
                'candidate_last_name': item.get('candidate_last_name', ''),
                'candidate_office': item.get('candidate_office', ''),  # H, S, P
                'candidate_office_state': item.get('candidate_office_state', ''),
                'candidate_office_district': item.get('candidate_office_district', ''),
                'candidate_party': item.get('candidate_party', ''),

                # Election info
                'cycle': cycle,
                'election_type': item.get('election_type', ''),

                # Dates
                'expenditure_date': item.get('expenditure_date'),
                'dissemination_date': item.get('dissemination_date'),
                'filing_date': item.get('filing_date'),
                'receipt_date': item.get('receipt_date'),

                # Expenditure details
                'expenditure_description': item.get('expenditure_description', ''),
                'payee_name': item.get('payee_name', ''),
                'payee_city': item.get('payee_city', ''),
                'payee_state': item.get('payee_state', ''),

                # Category
                'category': item.get('category', ''),
                'category_code': item.get('category_code', ''),

                # Report info
                'report_type': item.get('report_type', ''),
                'report_year': item.get('report_year'),

                # Memo and notes
                'memo_code': item.get('memo_code'),
                'memo_text': item.get('memo_text', ''),

                # Raw data for debugging
                '_raw': item,
            }

            # Build race identifier (e.g., "AZ-S1", "AZ-01")
            if expenditure['candidate_office'] == 'S':
                expenditure['race'] = f"{expenditure['candidate_office_state']}-S1"
            elif expenditure['candidate_office'] == 'H':
                district = expenditure['candidate_office_district'] or '00'
                expenditure['race'] = f"{expenditure['candidate_office_state']}-{district.zfill(2)}"
            else:
                expenditure['race'] = 'Unknown'

            return expenditure

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"    Error parsing expenditure: {e}"))
            return None

    def _display_expenditure(self, exp):
        """Display a single expenditure (verbose mode)"""
        support_oppose = 'SUPPORT' if exp['is_support'] else 'OPPOSE'
        self.stdout.write(
            f"      [{support_oppose}] ${exp['amount']:,.2f} - "
            f"{exp['committee_name'][:40]} -> {exp['candidate_name']} ({exp['race']})"
        )

    def _summarize_cycle_data(self, data):
        """Summarize expenditure data for a cycle"""
        summary = {
            'total_expenditures': len(data),
            'total_amount': sum(exp['amount'] for exp in data),
            'support_amount': sum(exp['amount'] for exp in data if exp['is_support']),
            'oppose_amount': sum(exp['amount'] for exp in data if not exp['is_support']),
            'by_race': defaultdict(lambda: {
                'count': 0,
                'total': Decimal('0'),
                'support': Decimal('0'),
                'oppose': Decimal('0'),
                'candidates': defaultdict(lambda: {
                    'support': Decimal('0'),
                    'oppose': Decimal('0'),
                    'party': ''
                })
            }),
            'by_committee': defaultdict(lambda: {
                'count': 0,
                'total': Decimal('0'),
                'support': Decimal('0'),
                'oppose': Decimal('0')
            }),
            'top_spenders': [],
            'top_candidates': [],
        }

        for exp in data:
            race = exp['race']
            committee = exp['committee_name']
            candidate = exp['candidate_name']
            amount = exp['amount']

            # By race
            summary['by_race'][race]['count'] += 1
            summary['by_race'][race]['total'] += amount
            if exp['is_support']:
                summary['by_race'][race]['support'] += amount
                summary['by_race'][race]['candidates'][candidate]['support'] += amount
            else:
                summary['by_race'][race]['oppose'] += amount
                summary['by_race'][race]['candidates'][candidate]['oppose'] += amount
            summary['by_race'][race]['candidates'][candidate]['party'] = exp['candidate_party']

            # By committee
            summary['by_committee'][committee]['count'] += 1
            summary['by_committee'][committee]['total'] += amount
            if exp['is_support']:
                summary['by_committee'][committee]['support'] += amount
            else:
                summary['by_committee'][committee]['oppose'] += amount

        # Calculate top spenders
        summary['top_spenders'] = sorted(
            [{'name': k, **v} for k, v in summary['by_committee'].items()],
            key=lambda x: x['total'],
            reverse=True
        )[:10]

        return summary

    def _display_cycle_summary(self, cycle, summary):
        """Display summary for a cycle"""
        self.stdout.write(f"\n{'-' * 50}")
        self.stdout.write(f"CYCLE {cycle} SUMMARY:")
        self.stdout.write(f"{'-' * 50}")

        self.stdout.write(f"\nTotal Expenditures: {summary['total_expenditures']:,}")
        self.stdout.write(f"Total Amount:       ${summary['total_amount']:,.2f}")
        self.stdout.write(f"  Support:          ${summary['support_amount']:,.2f}")
        self.stdout.write(f"  Oppose:           ${summary['oppose_amount']:,.2f}")

        # By race
        self.stdout.write(f"\nBY RACE:")
        for race in sorted(summary['by_race'].keys()):
            race_data = summary['by_race'][race]
            self.stdout.write(
                f"  {race}: ${race_data['total']:,.2f} "
                f"({race_data['count']} transactions)"
            )

            # Top candidates in this race
            candidates = sorted(
                race_data['candidates'].items(),
                key=lambda x: x[1]['support'] + x[1]['oppose'],
                reverse=True
            )[:5]
            for cand_name, cand_data in candidates:
                party = f"({cand_data['party']})" if cand_data['party'] else ""
                total = cand_data['support'] + cand_data['oppose']
                self.stdout.write(
                    f"    {cand_name} {party}: "
                    f"Support: ${cand_data['support']:,.2f}, "
                    f"Oppose: ${cand_data['oppose']:,.2f}"
                )

        # Top spenders
        self.stdout.write(f"\nTOP SPENDERS:")
        for i, spender in enumerate(summary['top_spenders'][:10], 1):
            self.stdout.write(
                f"  {i}. {spender['name'][:50]}: ${spender['total']:,.2f}"
            )

    def _display_overall_summary(self, summary_by_cycle):
        """Display overall summary across all cycles"""
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n{"=" * 70}\n  OVERALL SUMMARY\n{"=" * 70}'
        ))

        total_exp = sum(s['total_expenditures'] for s in summary_by_cycle.values())
        total_amt = sum(s['total_amount'] for s in summary_by_cycle.values())
        total_support = sum(s['support_amount'] for s in summary_by_cycle.values())
        total_oppose = sum(s['oppose_amount'] for s in summary_by_cycle.values())

        self.stdout.write(f"\nTotal across all cycles:")
        self.stdout.write(f"  Expenditures: {total_exp:,}")
        self.stdout.write(f"  Amount:       ${total_amt:,.2f}")
        self.stdout.write(f"  Support:      ${total_support:,.2f}")
        self.stdout.write(f"  Oppose:       ${total_oppose:,.2f}")

        self.stdout.write(f"\nBy cycle:")
        for cycle in sorted(summary_by_cycle.keys()):
            s = summary_by_cycle[cycle]
            self.stdout.write(
                f"  {cycle}: {s['total_expenditures']:,} expenditures, "
                f"${s['total_amount']:,.2f}"
            )

    def _save_to_json(self, output_path, data, summary_by_cycle):
        """Save data to JSON file for review"""
        self.stdout.write(f"\nSaving to JSON: {output_path}")

        output = {
            'source': 'FEC API (api.open.fec.gov)',
            'fetched_at': datetime.now().isoformat(),
            'state': 'AZ',
            'summary_by_cycle': {
                str(k): {
                    'total_expenditures': v['total_expenditures'],
                    'total_amount': float(v['total_amount']),
                    'support_amount': float(v['support_amount']),
                    'oppose_amount': float(v['oppose_amount']),
                    'by_race': {
                        race: {
                            'count': rd['count'],
                            'total': float(rd['total']),
                            'support': float(rd['support']),
                            'oppose': float(rd['oppose']),
                        }
                        for race, rd in v['by_race'].items()
                    },
                    'top_spenders': [
                        {
                            'name': s['name'],
                            'total': float(s['total']),
                            'count': s['count']
                        }
                        for s in v['top_spenders']
                    ]
                }
                for k, v in summary_by_cycle.items()
            },
            'expenditures': [
                {
                    'committee_id': exp['committee_id'],
                    'committee_name': exp['committee_name'],
                    'amount': float(exp['amount']),
                    'support_oppose': exp['support_oppose'],
                    'is_support': exp['is_support'],
                    'candidate_id': exp['candidate_id'],
                    'candidate_name': exp['candidate_name'],
                    'candidate_party': exp['candidate_party'],
                    'race': exp['race'],
                    'cycle': exp['cycle'],
                    'expenditure_date': exp['expenditure_date'],
                    'filing_date': exp['filing_date'],
                    'expenditure_description': exp['expenditure_description'],
                    'payee_name': exp['payee_name'],
                }
                for exp in data
            ]
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        self.stdout.write(self.style.SUCCESS(f"  Saved {len(data)} expenditures to {output_path}"))

    def _save_to_database(self, data):
        """Save data to database - initially to JSON file for review"""
        # For initial implementation, save to a staging file
        # This allows review before full database integration
        staging_path = Path('/opt/az_sunshine/data/fec_staging')
        staging_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        staging_file = staging_path / f'fec_ie_data_{timestamp}.json'

        self.stdout.write(f"\nSaving to staging file: {staging_file}")

        staging_data = {
            'source': 'FEC API',
            'fetched_at': datetime.now().isoformat(),
            'record_count': len(data),
            'expenditures': [
                {
                    'fec_file_id': exp['fec_file_id'],
                    'transaction_id': exp['transaction_id'],
                    'sub_id': exp['sub_id'],
                    'committee_id': exp['committee_id'],
                    'committee_name': exp['committee_name'],
                    'amount': float(exp['amount']),
                    'support_oppose': exp['support_oppose'],
                    'is_support': exp['is_support'],
                    'candidate_id': exp['candidate_id'],
                    'candidate_name': exp['candidate_name'],
                    'candidate_first_name': exp['candidate_first_name'],
                    'candidate_last_name': exp['candidate_last_name'],
                    'candidate_party': exp['candidate_party'],
                    'candidate_office': exp['candidate_office'],
                    'candidate_office_district': exp['candidate_office_district'],
                    'race': exp['race'],
                    'cycle': exp['cycle'],
                    'election_type': exp['election_type'],
                    'expenditure_date': exp['expenditure_date'],
                    'dissemination_date': exp['dissemination_date'],
                    'filing_date': exp['filing_date'],
                    'receipt_date': exp['receipt_date'],
                    'expenditure_description': exp['expenditure_description'],
                    'payee_name': exp['payee_name'],
                    'payee_city': exp['payee_city'],
                    'payee_state': exp['payee_state'],
                    'category': exp['category'],
                    'category_code': exp['category_code'],
                    'report_type': exp['report_type'],
                    'report_year': exp['report_year'],
                    'memo_code': exp['memo_code'],
                    'memo_text': exp['memo_text'],
                }
                for exp in data
            ]
        }

        with open(staging_file, 'w') as f:
            json.dump(staging_data, f, indent=2, default=str)

        self.stdout.write(self.style.SUCCESS(
            f"  Saved {len(data)} expenditures to staging file"
        ))
        self.stdout.write(self.style.NOTICE(
            f"\nNote: Data saved to staging file for review.\n"
            f"To integrate into database, create a FEC-specific model or\n"
            f"modify the Transaction model to include FEC data.\n"
            f"\nStaging file: {staging_file}"
        ))
