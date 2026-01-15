#!/usr/bin/env python3
"""
SeeTheMoney.az.gov Data Comparator

Compares our local database with CSV exports from Arizona's official
campaign finance disclosure system.

USAGE:
1. Export local data:
   python scripts/seethemoney_comparator.py --export-local

2. Download CSV from SeeTheMoney.az.gov:
   - Go to: https://seethemoney.az.gov/Reporting/AdvancedSearch/
   - Select: "Independent Expenditures"
   - Set Election Cycle: 2022
   - Click Search, then Export as CSV
   - Save to: /opt/az_sunshine/backend/data/seethemoney/

3. Compare:
   python scripts/seethemoney_comparator.py --compare ie_2022.csv
"""

import os
import sys
import csv
import json
import argparse
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Django setup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from transparency.models import Committee, Transaction, Office, Cycle
from django.db.models import Sum, Q, Count
from django.db.models.functions import Abs


class SeeTheMoneyComparator:
    """Compare local data with SeeTheMoney CSV exports"""

    def __init__(self):
        self.local_dir = Path('/opt/az_sunshine/backend/data/comparison')
        self.external_dir = Path('/opt/az_sunshine/backend/data/seethemoney')
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self.external_dir.mkdir(parents=True, exist_ok=True)

    def export_local_ie_data(self, year=2022):
        """Export all IE data from our database for a given year"""
        try:
            cycle = Cycle.objects.get(name=str(year))
        except Cycle.DoesNotExist:
            print(f"Cycle {year} not found")
            return None

        # Get ALL IE transactions for the year
        transactions = Transaction.objects.filter(
            transaction_date__gte=cycle.begin_date,
            transaction_date__lte=cycle.end_date,
            transaction_type__income_expense_neutral=2,
            deleted=False,
            subject_committee__isnull=False
        ).select_related(
            'committee', 'committee__name',
            'subject_committee', 'subject_committee__name',
            'subject_committee__candidate_office',
            'subject_committee__candidate_party'
        )

        data = {
            'year': year,
            'exported_at': datetime.now().isoformat(),
            'total_transactions': transactions.count(),
            'by_candidate': defaultdict(lambda: {
                'ie_for': 0, 'ie_against': 0, 'total': 0,
                'transactions': 0, 'office': None, 'party': None
            }),
            'by_office': defaultdict(lambda: {'total': 0, 'candidates': set()}),
            'transactions': []
        }

        for t in transactions:
            subject_name = t.subject_committee.name.last_name if t.subject_committee and t.subject_committee.name else 'Unknown'
            filer_name = t.committee.name.last_name if t.committee and t.committee.name else 'Unknown'
            office = t.subject_committee.candidate_office.name if t.subject_committee and t.subject_committee.candidate_office else 'Unknown'
            party = t.subject_committee.candidate_party.name if t.subject_committee and t.subject_committee.candidate_party else None
            amount = abs(float(t.amount))

            # Aggregate by candidate
            data['by_candidate'][subject_name]['transactions'] += 1
            data['by_candidate'][subject_name]['office'] = office
            data['by_candidate'][subject_name]['party'] = party
            data['by_candidate'][subject_name]['total'] += amount

            if t.is_for_benefit:
                data['by_candidate'][subject_name]['ie_for'] += amount
            else:
                data['by_candidate'][subject_name]['ie_against'] += amount

            # Aggregate by office
            data['by_office'][office]['total'] += amount
            data['by_office'][office]['candidates'].add(subject_name)

            # Individual transaction (for detailed comparison)
            data['transactions'].append({
                'date': str(t.transaction_date),
                'filer': filer_name,
                'subject': subject_name,
                'amount': amount,
                'is_for_benefit': t.is_for_benefit,
                'office': office
            })

        # Convert defaultdicts and sets for JSON serialization
        data['by_candidate'] = dict(data['by_candidate'])
        data['by_office'] = {k: {'total': v['total'], 'candidates': list(v['candidates'])}
                            for k, v in data['by_office'].items()}

        # Save to file
        filepath = self.local_dir / f'local_ie_{year}.json'
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"Exported {len(data['transactions'])} transactions to {filepath}")
        self._print_summary(data)

        return data

    def _print_summary(self, data):
        """Print a summary of exported data"""
        print(f"\n{'='*70}")
        print(f"LOCAL DATABASE SUMMARY - {data['year']}")
        print(f"{'='*70}")
        print(f"Total IE transactions: {data['total_transactions']}")

        print(f"\nBY OFFICE:")
        for office, info in sorted(data['by_office'].items(), key=lambda x: -x[1]['total']):
            print(f"  {office}: ${info['total']:,.2f} ({len(info['candidates'])} candidates)")

        print(f"\nTOP 15 CANDIDATES BY IE SPENDING:")
        sorted_candidates = sorted(data['by_candidate'].items(), key=lambda x: -x[1]['total'])[:15]
        for name, info in sorted_candidates:
            party = f"({info['party']})" if info['party'] else ""
            print(f"  {name} {party}")
            print(f"    Office: {info['office']}")
            print(f"    For: ${info['ie_for']:,.2f} | Against: ${info['ie_against']:,.2f} | Total: ${info['total']:,.2f}")

    def parse_seethemoney_csv(self, csv_path):
        """Parse a CSV export from SeeTheMoney.az.gov"""
        filepath = self.external_dir / csv_path if not Path(csv_path).is_absolute() else Path(csv_path)

        if not filepath.exists():
            print(f"File not found: {filepath}")
            print(f"\nTo get this file:")
            print(f"  1. Go to: https://seethemoney.az.gov/Reporting/AdvancedSearch/")
            print(f"  2. Select 'Independent Expenditures'")
            print(f"  3. Set Election Cycle to desired year")
            print(f"  4. Click Search, then Export as CSV")
            print(f"  5. Save to: {self.external_dir}/")
            return None

        data = {
            'source': str(filepath),
            'parsed_at': datetime.now().isoformat(),
            'by_candidate': defaultdict(lambda: {'ie_for': 0, 'ie_against': 0, 'total': 0, 'transactions': 0}),
            'transactions': []
        }

        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # Print available columns for debugging
            print(f"CSV columns: {reader.fieldnames}")

            for row in reader:
                # SeeTheMoney CSV column names (may vary)
                # Common columns: Candidate/Committee, Amount, Support/Oppose, Date, Filer
                candidate = row.get('Candidate', row.get('Subject', row.get('Committee', 'Unknown')))
                amount_str = row.get('Amount', '0').replace('$', '').replace(',', '')
                try:
                    amount = abs(float(amount_str))
                except ValueError:
                    amount = 0

                support_oppose = row.get('Support/Oppose', row.get('Position', '')).upper()
                is_support = 'SUPPORT' in support_oppose or 'FOR' in support_oppose or 'BENEFIT' in support_oppose

                data['by_candidate'][candidate]['transactions'] += 1
                data['by_candidate'][candidate]['total'] += amount
                if is_support:
                    data['by_candidate'][candidate]['ie_for'] += amount
                else:
                    data['by_candidate'][candidate]['ie_against'] += amount

                data['transactions'].append({
                    'candidate': candidate,
                    'amount': amount,
                    'is_support': is_support,
                    'raw_row': dict(row)
                })

        data['by_candidate'] = dict(data['by_candidate'])
        print(f"Parsed {len(data['transactions'])} transactions from SeeTheMoney")

        return data

    def compare(self, local_year, csv_path):
        """Compare local data with SeeTheMoney CSV"""
        # Load local data
        local_file = self.local_dir / f'local_ie_{local_year}.json'
        if not local_file.exists():
            print(f"Local data not found. Run --export-local first.")
            return None

        with open(local_file) as f:
            local_data = json.load(f)

        # Parse external CSV
        external_data = self.parse_seethemoney_csv(csv_path)
        if not external_data:
            return None

        print(f"\n{'='*80}")
        print(f"COMPARISON: Local DB vs SeeTheMoney.az.gov")
        print(f"{'='*80}")

        # Find matching candidates
        local_candidates = set(local_data['by_candidate'].keys())
        external_candidates = set(external_data['by_candidate'].keys())

        matched = local_candidates & external_candidates
        local_only = local_candidates - external_candidates
        external_only = external_candidates - local_candidates

        print(f"\nMatched candidates: {len(matched)}")
        print(f"Local only: {len(local_only)}")
        print(f"External only: {len(external_only)}")

        # Compare matched candidates
        print(f"\n{'='*80}")
        print("MATCHED CANDIDATES COMPARISON")
        print(f"{'='*80}")

        results = []
        for candidate in sorted(matched):
            local = local_data['by_candidate'][candidate]
            external = external_data['by_candidate'][candidate]

            diff_total = local['total'] - external['total']
            diff_pct = (diff_total / external['total'] * 100) if external['total'] else 0

            result = {
                'candidate': candidate,
                'local_total': local['total'],
                'external_total': external['total'],
                'diff': diff_total,
                'diff_pct': diff_pct,
                'local_for': local['ie_for'],
                'external_for': external['ie_for'],
                'local_against': local['ie_against'],
                'external_against': external['ie_against'],
            }
            results.append(result)

            # Only print if there's a significant difference (>1%)
            if abs(diff_pct) > 1:
                print(f"\n{candidate}")
                print(f"  Local:    Total=${local['total']:>12,.2f}  For=${local['ie_for']:>12,.2f}  Against=${local['ie_against']:>12,.2f}")
                print(f"  External: Total=${external['total']:>12,.2f}  For=${external['ie_for']:>12,.2f}  Against=${external['ie_against']:>12,.2f}")
                print(f"  DIFF:     ${diff_total:>+12,.2f} ({diff_pct:+.1f}%)")

        # Save comparison report
        report = {
            'compared_at': datetime.now().isoformat(),
            'local_file': str(local_file),
            'external_file': csv_path,
            'matched_count': len(matched),
            'local_only_count': len(local_only),
            'external_only_count': len(external_only),
            'local_only': list(local_only),
            'external_only': list(external_only),
            'comparison_results': results
        }

        report_path = self.local_dir / f'comparison_report_{local_year}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n\nReport saved: {report_path}")

        return report


def main():
    parser = argparse.ArgumentParser(description='SeeTheMoney.az.gov Data Comparator')
    parser.add_argument('--export-local', action='store_true', help='Export local database IE data')
    parser.add_argument('--year', type=int, default=2022, help='Election year (default: 2022)')
    parser.add_argument('--compare', metavar='CSV_FILE', help='Compare with SeeTheMoney CSV export')
    parser.add_argument('--instructions', action='store_true', help='Show download instructions')

    args = parser.parse_args()

    comparator = SeeTheMoneyComparator()

    if args.instructions:
        print("""
HOW TO DOWNLOAD DATA FROM SEETHEMONEY.AZ.GOV
============================================

1. Open: https://seethemoney.az.gov/Reporting/AdvancedSearch/

2. In the search form:
   - Click "Independent Expenditures" tab
   - Set "Election Cycle" to 2022 (or desired year)
   - Leave other fields blank for all data

3. Click "Search"

4. On results page, click "Export Report" dropdown
   - Select "Comma Separated Values (CSV)"

5. Save the file to:
   /opt/az_sunshine/backend/data/seethemoney/ie_2022.csv

6. Run comparison:
   python scripts/seethemoney_comparator.py --compare ie_2022.csv
""")
        return

    if args.export_local:
        comparator.export_local_ie_data(args.year)

    if args.compare:
        comparator.compare(args.year, args.compare)

    if not any([args.export_local, args.compare, args.instructions]):
        # Default: export local and show instructions
        print("Exporting local data...")
        comparator.export_local_ie_data(args.year)
        print("\n" + "="*70)
        print("NEXT STEP: Download data from SeeTheMoney.az.gov")
        print("="*70)
        print("Run: python scripts/seethemoney_comparator.py --instructions")


if __name__ == '__main__':
    main()
