"""
Import FEC independent expenditure data for Arizona CD-2 (2nd Congressional District) 2018 race.

According to tucson.com, this race had about $800K+ in outside spending from groups like
Women Vote! and DCCC (Democratic Congressional Campaign Committee).

Usage:
    python manage.py import_fec_cd2_2018
    python manage.py import_fec_cd2_2018 --dry-run
    python manage.py import_fec_cd2_2018 --verbose
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
from transparency.models import FECIndependentExpenditure


# FEC API base URL
FEC_API_BASE = 'https://api.open.fec.gov/v1'

# Demo API key (for testing - limited rate)
DEMO_API_KEY = 'DEMO_KEY'


class Command(BaseCommand):
    help = 'Import FEC independent expenditure data for Arizona CD-2 2018 race'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='FEC API key (or set FEC_API_KEY env var)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview data without saving to database'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each expenditure'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Save data to JSON file for review'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)
        output_path = options.get('output')

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
            ))

        self.stdout.write(
            '\n' + '=' * 70 + '\n' +
            '  FEC INDEPENDENT EXPENDITURE IMPORTER\n' +
            '  Arizona Congressional District 2 (CD-2) - 2018 Race\n' +
            '=' * 70 + '\n'
        )

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved\n'))

        # Test API connection
        if not self._test_api_connection():
            self.stdout.write(self.style.ERROR('Failed to connect to FEC API'))
            return

        # Fetch CD-2 2018 data
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\nFetching AZ-02 (CD-2) 2018 Independent Expenditures...'
        ))

        expenditures = self._fetch_az02_2018_data(verbose)

        self.stdout.write(f'\nTotal expenditures found: {len(expenditures)}')

        if not expenditures:
            self.stdout.write(self.style.WARNING('No expenditures found'))
            return

        # Display summary
        self._display_summary(expenditures)

        # Save to JSON file if requested
        if output_path:
            self._save_to_json(output_path, expenditures)

        # Save to database (unless dry run)
        if not dry_run:
            self._save_to_database(expenditures)
        else:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN complete. {len(expenditures)} expenditures would be saved.'
            ))

    def _test_api_connection(self):
        """Test connection to FEC API with retry on rate limit"""
        self.stdout.write("Testing FEC API connection...")
        max_retries = 10
        retry_delay = 60  # seconds - start with 1 minute

        for attempt in range(max_retries):
            try:
                url = f"{FEC_API_BASE}/schedules/schedule_e/"
                params = {
                    'api_key': self.api_key,
                    'candidate_office_state': 'AZ',
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
                elif response.status_code == 403:
                    self.stdout.write(self.style.ERROR("  API key error"))
                    return False
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = min(retry_delay * (2 ** attempt), 600)  # Max 10 minutes
                        self.stdout.write(self.style.WARNING(
                            f"  Rate limited, waiting {wait_time}s before retry ({attempt + 1}/{max_retries})..."
                        ))
                        time.sleep(wait_time)
                        continue
                    else:
                        self.stdout.write(self.style.ERROR("  Rate limited, max retries exceeded"))
                        return False
                else:
                    self.stdout.write(self.style.ERROR(
                        f"  HTTP {response.status_code}: {response.text[:200]}"
                    ))
                    return False

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  Connection error: {e}"))
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False

        return False

    def _fetch_az02_2018_data(self, verbose):
        """
        Fetch all IE data for Arizona CD-2 in 2018

        Uses FEC API endpoint: /schedules/schedule_e/
        Filters:
        - candidate_office_state: AZ
        - candidate_office_district: 02
        - two_year_transaction_period: 2018
        """
        expenditures = []
        url = f"{FEC_API_BASE}/schedules/schedule_e/"

        # Parameters for AZ-02 2018
        params = {
            'api_key': self.api_key,
            'candidate_office_state': 'AZ',
            'candidate_office_district': '02',
            'two_year_transaction_period': 2018,
            'per_page': 100,
            'sort': '-expenditure_amount',
        }

        page = 1
        last_index = None
        max_pages = 100  # Safety limit

        while page <= max_pages:
            try:
                if last_index:
                    params['last_index'] = last_index

                self.stdout.write(f"  Fetching page {page}...", ending='')
                response = requests.get(url, params=params, timeout=60)

                if response.status_code == 429:
                    self.stdout.write(self.style.WARNING(" Rate limited, waiting 60s..."))
                    time.sleep(60)
                    continue

                if response.status_code == 422:
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
                    expenditure = self._parse_expenditure(item)
                    if expenditure:
                        expenditures.append(expenditure)
                        if verbose:
                            self._display_expenditure(expenditure)

                # Get pagination info
                pagination = data.get('pagination', {})
                last_index = pagination.get('last_indexes', {}).get('last_index')

                if not last_index or len(results) < 100:
                    break

                page += 1
                time.sleep(0.5)  # Be nice to the API

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f" Request error: {e}"))
                break

        return expenditures

    def _parse_expenditure(self, item):
        """Parse an expenditure item from FEC API response"""
        try:
            # Generate a unique file ID from sub_id or other fields
            sub_id = item.get('sub_id')
            file_number = item.get('file_number')
            transaction_id = item.get('transaction_id', '')

            # Create a unique identifier
            if sub_id:
                fec_file_id = str(sub_id)
            elif file_number and transaction_id:
                fec_file_id = f"{file_number}_{transaction_id}"
            else:
                # Fallback: create from committee_id + date + amount
                fec_file_id = f"AZ02_2018_{item.get('committee_id', 'UNK')}_{item.get('expenditure_date', '')}_{item.get('expenditure_amount', 0)}"

            expenditure = {
                'fec_file_id': fec_file_id,
                'transaction_id': transaction_id,
                'sub_id': sub_id,

                # Committee info
                'committee_id': item.get('committee_id', ''),
                'committee_name': item.get('committee', {}).get('name') or item.get('committee_name', ''),

                # Amount
                'amount': Decimal(str(item.get('expenditure_amount', 0))),

                # Support/Oppose
                'support_oppose': item.get('support_oppose_indicator', ''),
                'is_support': item.get('support_oppose_indicator') == 'S',

                # Candidate info
                'candidate_id': item.get('candidate_id', ''),
                'candidate_name': item.get('candidate_name', ''),
                'candidate_first_name': item.get('candidate_first_name', ''),
                'candidate_last_name': item.get('candidate_last_name', ''),
                'candidate_office': item.get('candidate_office', ''),
                'candidate_office_state': item.get('candidate_office_state', ''),
                'candidate_office_district': item.get('candidate_office_district', ''),
                'candidate_party': item.get('candidate_party', ''),

                # Race
                'race': 'AZ-02',
                'cycle': 2018,

                # Dates
                'expenditure_date': item.get('expenditure_date'),
                'dissemination_date': item.get('dissemination_date'),
                'filing_date': item.get('filing_date'),

                # Details
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
            }

            return expenditure

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"    Error parsing expenditure: {e}"))
            return None

    def _display_expenditure(self, exp):
        """Display a single expenditure (verbose mode)"""
        support_oppose = 'SUPPORT' if exp['is_support'] else 'OPPOSE'
        self.stdout.write(
            f"    [{support_oppose}] ${exp['amount']:,.2f} - "
            f"{exp['committee_name'][:50]} -> {exp['candidate_name']}"
        )

    def _display_summary(self, expenditures):
        """Display summary of expenditures"""
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('  SUMMARY: AZ-02 (CD-2) 2018 Independent Expenditures')
        self.stdout.write('=' * 70)

        total_amount = sum(exp['amount'] for exp in expenditures)
        support_amount = sum(exp['amount'] for exp in expenditures if exp['is_support'])
        oppose_amount = sum(exp['amount'] for exp in expenditures if not exp['is_support'])

        self.stdout.write(f'\nTotal Expenditures: {len(expenditures)}')
        self.stdout.write(f'Total Amount: ${total_amount:,.2f}')
        self.stdout.write(f'  Support: ${support_amount:,.2f}')
        self.stdout.write(f'  Oppose: ${oppose_amount:,.2f}')

        # By committee
        self.stdout.write('\nTOP SPENDING COMMITTEES:')
        committee_totals = defaultdict(lambda: {'total': Decimal('0'), 'count': 0})
        for exp in expenditures:
            committee_totals[exp['committee_name']]['total'] += exp['amount']
            committee_totals[exp['committee_name']]['count'] += 1

        sorted_committees = sorted(
            committee_totals.items(),
            key=lambda x: x[1]['total'],
            reverse=True
        )

        for i, (name, data) in enumerate(sorted_committees[:15], 1):
            self.stdout.write(
                f"  {i:2}. {name[:55]:55} ${data['total']:>12,.2f} ({data['count']} txns)"
            )

        # By candidate
        self.stdout.write('\nBY CANDIDATE:')
        candidate_totals = defaultdict(lambda: {
            'support': Decimal('0'),
            'oppose': Decimal('0'),
            'party': ''
        })
        for exp in expenditures:
            cand = exp['candidate_name']
            if exp['is_support']:
                candidate_totals[cand]['support'] += exp['amount']
            else:
                candidate_totals[cand]['oppose'] += exp['amount']
            if exp['candidate_party']:
                candidate_totals[cand]['party'] = exp['candidate_party']

        for cand, data in sorted(candidate_totals.items(),
                                  key=lambda x: x[1]['support'] + x[1]['oppose'],
                                  reverse=True):
            party = f"({data['party']})" if data['party'] else ""
            net = data['support'] - data['oppose']
            net_str = f"+${net:,.2f}" if net >= 0 else f"-${abs(net):,.2f}"
            self.stdout.write(
                f"  {cand} {party}:"
            )
            self.stdout.write(
                f"    Support: ${data['support']:,.2f}  |  Oppose: ${data['oppose']:,.2f}  |  Net: {net_str}"
            )

    def _save_to_json(self, output_path, expenditures):
        """Save data to JSON file for review"""
        self.stdout.write(f"\nSaving to JSON: {output_path}")

        output = {
            'source': 'FEC API (api.open.fec.gov)',
            'race': 'AZ-02',
            'cycle': 2018,
            'fetched_at': datetime.now().isoformat(),
            'record_count': len(expenditures),
            'total_amount': float(sum(exp['amount'] for exp in expenditures)),
            'expenditures': [
                {
                    'fec_file_id': exp['fec_file_id'],
                    'transaction_id': exp['transaction_id'],
                    'committee_id': exp['committee_id'],
                    'committee_name': exp['committee_name'],
                    'amount': float(exp['amount']),
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
                    'expenditure_date': exp['expenditure_date'],
                    'filing_date': exp['filing_date'],
                    'expenditure_description': exp['expenditure_description'],
                    'payee_name': exp['payee_name'],
                }
                for exp in expenditures
            ]
        }

        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        self.stdout.write(self.style.SUCCESS(f"  Saved {len(expenditures)} expenditures to {output_path}"))

    def _save_to_database(self, expenditures):
        """Save expenditures to the database"""
        self.stdout.write('\nSaving to database...')

        created_count = 0
        updated_count = 0
        error_count = 0

        for exp in expenditures:
            try:
                # Parse dates
                expenditure_date = self._parse_date(exp.get('expenditure_date'))
                filing_date = self._parse_date(exp.get('filing_date'))

                record_data = {
                    'transaction_id': str(exp.get('transaction_id', '')),
                    'committee_id': str(exp.get('committee_id', '')),
                    'committee_name': str(exp.get('committee_name', ''))[:255],
                    'amount': exp['amount'],
                    'is_support': exp['is_support'],
                    'candidate_id': str(exp.get('candidate_id', '')),
                    'candidate_name': str(exp.get('candidate_name', ''))[:255],
                    'candidate_first_name': str(exp.get('candidate_first_name', ''))[:100],
                    'candidate_last_name': str(exp.get('candidate_last_name', ''))[:100],
                    'candidate_party': str(exp.get('candidate_party', ''))[:10],
                    'candidate_office': str(exp.get('candidate_office', ''))[:10],
                    'candidate_office_district': exp.get('candidate_office_district') or None,
                    'race': exp['race'],
                    'cycle': exp['cycle'],
                    'expenditure_date': expenditure_date,
                    'filing_date': filing_date,
                    'expenditure_description': str(exp.get('expenditure_description', '')),
                    'payee_name': str(exp.get('payee_name', ''))[:255],
                }

                obj, created = FECIndependentExpenditure.objects.update_or_create(
                    fec_file_id=exp['fec_file_id'],
                    defaults=record_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error saving record: {e}")
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Import Complete'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f"Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
        if error_count:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))

    def _parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%m/%d/%Y').date()
            except ValueError:
                return None
