"""
Management command to compare Az-Sunshine data against SeeTheMoney CSV exports.

This is the 2nd layer verification - compares our database directly against
the official Arizona Secretary of State data.

Usage:
    # Download IE CSV from https://seethemoney.az.gov
    # Select "Independent Expenditures" tab, set filters, click "Export"
    # Save to /opt/az_sunshine/backend/data/seethemoney/

    # Compare Governor 2022
    python manage.py compare_seethemoney --csv ie_export.csv --office Governor --cycle 2022

    # Compare all statewide offices 2022
    python manage.py compare_seethemoney --csv ie_export.csv --cycle 2022

    # Full report with details
    python manage.py compare_seethemoney --csv ie_export.csv --cycle 2022 --verbose
"""

import csv
import json
from decimal import Decimal
from collections import defaultdict
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from django.db.models.functions import Abs

from transparency.models import Committee, Transaction, Office, Cycle


class Command(BaseCommand):
    help = 'Compare Az-Sunshine data against SeeTheMoney CSV exports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            required=True,
            help='Path to SeeTheMoney IE export CSV file'
        )
        parser.add_argument(
            '--office',
            type=str,
            help='Filter by office (e.g., "Governor", "Attorney General")'
        )
        parser.add_argument(
            '--cycle',
            type=str,
            required=True,
            help='Election cycle year (e.g., "2022")'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON report to file'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed comparison output'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=1.0,
            help='Percentage threshold for flagging discrepancies (default: 1.0%%)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 60 + '\n'
            '  AZ-SUNSHINE vs SEETHEMONEY COMPARISON\n'
            '  2nd Layer Verification\n'
            '=' * 60 + '\n'
        ))

        csv_path = options['csv']
        cycle_year = options['cycle']
        office_filter = options.get('office')
        verbose = options.get('verbose', False)
        threshold = options.get('threshold', 1.0)

        # Parse SeeTheMoney CSV
        self.stdout.write(f"Loading SeeTheMoney data from: {csv_path}")
        stm_data = self._parse_seethemoney_csv(csv_path, cycle_year)

        if not stm_data:
            self.stdout.write(self.style.ERROR("No data found in CSV!"))
            return

        self.stdout.write(f"Found {len(stm_data)} candidates in SeeTheMoney data\n")

        # Get Az-Sunshine data
        self.stdout.write(f"Loading Az-Sunshine data for cycle {cycle_year}...")
        az_data = self._get_az_sunshine_data(cycle_year, office_filter)
        self.stdout.write(f"Found {len(az_data)} candidates in Az-Sunshine\n")

        # Compare data
        results = self._compare_data(stm_data, az_data, threshold)

        # Display results
        self._display_results(results, verbose)

        # Save report if requested
        if options.get('output'):
            report = {
                'generated_at': datetime.now().isoformat(),
                'cycle': cycle_year,
                'office': office_filter,
                'seethemoney_candidates': len(stm_data),
                'az_sunshine_candidates': len(az_data),
                'matches': results['matches'],
                'discrepancies': results['discrepancies'],
                'missing_from_az': results['missing_from_az'],
                'extra_in_az': results['extra_in_az']
            }
            with open(options['output'], 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f"\nReport saved to: {options['output']}"))

    def _parse_seethemoney_csv(self, csv_path, cycle_year):
        """
        Parse SeeTheMoney IE export CSV

        Expected columns (adjust based on actual export format):
        - Candidate Name / Subject Committee
        - Support/Oppose / Position
        - Amount
        - Office
        - Date
        """
        candidates = defaultdict(lambda: {
            'ie_for': Decimal('0'),
            'ie_against': Decimal('0'),
            'total_ie': Decimal('0'),
            'transaction_count': 0,
            'office': None
        })

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                # Auto-detect column names
                fieldnames = reader.fieldnames
                self.stdout.write(f"CSV columns: {fieldnames[:10]}...")

                # Map common column name variations
                name_cols = ['Subject Committee', 'Candidate Name', 'Subject', 'Name',
                            'CandidateName', 'SubjectCommittee', 'Candidate']
                amount_cols = ['Amount', 'Transaction Amount', 'Expenditure Amount']
                position_cols = ['Position', 'Support/Oppose', 'SupportOppose', 'Type',
                                'For/Against', 'ForAgainst', 'Benefit']
                office_cols = ['Office', 'Office Sought', 'OfficeSought', 'Race']

                name_col = self._find_column(fieldnames, name_cols)
                amount_col = self._find_column(fieldnames, amount_cols)
                position_col = self._find_column(fieldnames, position_cols)
                office_col = self._find_column(fieldnames, office_cols)

                if not name_col or not amount_col:
                    self.stdout.write(self.style.ERROR(
                        f"Could not find required columns. Found: {fieldnames}"
                    ))
                    return {}

                self.stdout.write(f"Using columns: name={name_col}, amount={amount_col}, "
                                f"position={position_col}, office={office_col}")

                for row in reader:
                    candidate_name = row.get(name_col, '').strip()
                    if not candidate_name:
                        continue

                    try:
                        amount = Decimal(str(row.get(amount_col, '0')).replace(',', '').replace('$', ''))
                    except:
                        continue

                    position = row.get(position_col, '').lower() if position_col else ''
                    office = row.get(office_col, '') if office_col else ''

                    # Normalize name for matching
                    norm_name = self._normalize_name(candidate_name)

                    # Determine if support or oppose
                    is_support = self._is_support(position)

                    if is_support:
                        candidates[norm_name]['ie_for'] += abs(amount)
                    else:
                        candidates[norm_name]['ie_against'] += abs(amount)

                    candidates[norm_name]['total_ie'] += abs(amount)
                    candidates[norm_name]['transaction_count'] += 1
                    candidates[norm_name]['original_name'] = candidate_name
                    if office:
                        candidates[norm_name]['office'] = office

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_path}"))
            return {}
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error parsing CSV: {e}"))
            return {}

        return dict(candidates)

    def _find_column(self, fieldnames, possible_names):
        """Find matching column name from list of possibilities"""
        for name in possible_names:
            for field in fieldnames:
                if name.lower() == field.lower().strip():
                    return field
        return None

    def _normalize_name(self, name):
        """Normalize candidate/committee name for matching"""
        name = name.lower().strip()
        # Remove common suffixes
        for suffix in [' for governor', ' for attorney general', ' for state treasurer',
                       ' for secretary of state', ' for arizona', ' for az',
                       ' 2022', ' 2024', ' 2020', ' 2018', ' 2016',
                       ' committee', ' campaign']:
            name = name.replace(suffix, '')
        # Normalize whitespace
        return ' '.join(name.split())

    def _is_support(self, position):
        """Determine if position indicates support (True) or oppose (False)"""
        position = position.lower()
        support_terms = ['support', 'for', 'benefit', 'in support', 'supports']
        oppose_terms = ['oppose', 'against', 'not for benefit', 'opposes']

        for term in support_terms:
            if term in position:
                return True
        for term in oppose_terms:
            if term in position:
                return False

        # Default to support if unclear
        return True

    def _get_az_sunshine_data(self, cycle_year, office_filter=None):
        """Get IE data from Az-Sunshine database"""
        try:
            cycle = Cycle.objects.get(name=cycle_year)
        except Cycle.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Cycle {cycle_year} not found"))
            return {}

        filters = {
            'deleted': False,
            'subject_committee__isnull': False,
            'transaction_date__gte': cycle.begin_date,
            'transaction_date__lte': cycle.end_date,
            'transaction_type__income_expense_neutral': 2,
        }

        if office_filter:
            try:
                office = Office.objects.get(name=office_filter)
                filters['subject_committee__candidate_office'] = office
            except Office.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Office '{office_filter}' not found"))

        # Aggregate IE by subject committee
        ie_data = Transaction.objects.filter(**filters).values(
            'subject_committee__committee_id',
            'subject_committee__name__last_name',
            'subject_committee__name__first_name',
            'subject_committee__candidate_office__name',
        ).annotate(
            ie_for=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            ie_against=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
            total_ie=Sum(Abs('amount')),
        )

        candidates = {}
        for row in ie_data:
            name = f"{row['subject_committee__name__first_name'] or ''} {row['subject_committee__name__last_name'] or ''}".strip()
            norm_name = self._normalize_name(name)

            if norm_name in candidates:
                # Aggregate multiple committees for same candidate
                candidates[norm_name]['ie_for'] += row['ie_for'] or Decimal('0')
                candidates[norm_name]['ie_against'] += row['ie_against'] or Decimal('0')
                candidates[norm_name]['total_ie'] += row['total_ie'] or Decimal('0')
            else:
                candidates[norm_name] = {
                    'ie_for': row['ie_for'] or Decimal('0'),
                    'ie_against': row['ie_against'] or Decimal('0'),
                    'total_ie': row['total_ie'] or Decimal('0'),
                    'original_name': name,
                    'office': row['subject_committee__candidate_office__name'],
                    'committee_id': row['subject_committee__committee_id']
                }

        return candidates

    def _compare_data(self, stm_data, az_data, threshold):
        """Compare SeeTheMoney and Az-Sunshine data"""
        results = {
            'matches': [],
            'discrepancies': [],
            'missing_from_az': [],
            'extra_in_az': [],
            'total_stm_ie': Decimal('0'),
            'total_az_ie': Decimal('0')
        }

        # Track which Az-Sunshine candidates were matched
        az_matched = set()

        for stm_name, stm_cand in stm_data.items():
            results['total_stm_ie'] += stm_cand['total_ie']

            # Try to find match in Az-Sunshine
            az_cand = az_data.get(stm_name)

            if not az_cand:
                # Try fuzzy match
                az_cand, matched_name = self._fuzzy_match(stm_name, az_data, az_matched)
                if matched_name:
                    az_matched.add(matched_name)
            else:
                az_matched.add(stm_name)

            if az_cand:
                # Compare amounts
                stm_total = stm_cand['total_ie']
                az_total = az_cand['total_ie']

                if stm_total > 0:
                    variance_pct = abs(float(stm_total - az_total) / float(stm_total) * 100)
                else:
                    variance_pct = 100 if az_total > 0 else 0

                if variance_pct <= threshold:
                    results['matches'].append({
                        'name': stm_cand.get('original_name', stm_name),
                        'stm_total': float(stm_total),
                        'az_total': float(az_total),
                        'variance_pct': variance_pct
                    })
                else:
                    results['discrepancies'].append({
                        'name': stm_cand.get('original_name', stm_name),
                        'stm_ie_for': float(stm_cand['ie_for']),
                        'stm_ie_against': float(stm_cand['ie_against']),
                        'stm_total': float(stm_total),
                        'az_ie_for': float(az_cand['ie_for']),
                        'az_ie_against': float(az_cand['ie_against']),
                        'az_total': float(az_total),
                        'variance_pct': variance_pct,
                        'variance_amount': float(abs(stm_total - az_total))
                    })
            else:
                results['missing_from_az'].append({
                    'name': stm_cand.get('original_name', stm_name),
                    'stm_total': float(stm_cand['total_ie']),
                    'office': stm_cand.get('office')
                })

        # Find extra candidates in Az-Sunshine
        for az_name, az_cand in az_data.items():
            results['total_az_ie'] += az_cand['total_ie']
            if az_name not in az_matched:
                results['extra_in_az'].append({
                    'name': az_cand.get('original_name', az_name),
                    'az_total': float(az_cand['total_ie']),
                    'office': az_cand.get('office')
                })

        return results

    def _fuzzy_match(self, name, az_data, already_matched):
        """Try to find fuzzy match for candidate name"""
        name_parts = set(name.split())

        best_match = None
        best_score = 0

        for az_name, az_cand in az_data.items():
            if az_name in already_matched:
                continue

            az_parts = set(az_name.split())

            # Calculate Jaccard similarity
            intersection = len(name_parts & az_parts)
            union = len(name_parts | az_parts)

            if union > 0:
                score = intersection / union
                if score > best_score and score >= 0.5:  # 50% threshold
                    best_score = score
                    best_match = (az_cand, az_name)

        if best_match:
            return best_match
        return None, None

    def _display_results(self, results, verbose):
        """Display comparison results"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.MIGRATE_HEADING('COMPARISON RESULTS'))
        self.stdout.write('=' * 60)

        # Summary
        total_matches = len(results['matches'])
        total_discrepancies = len(results['discrepancies'])
        total_missing = len(results['missing_from_az'])
        total_extra = len(results['extra_in_az'])

        self.stdout.write(f"\nMatches (within threshold):    {total_matches}")

        if total_discrepancies > 0:
            self.stdout.write(self.style.WARNING(
                f"Discrepancies:                 {total_discrepancies}"
            ))
        else:
            self.stdout.write(f"Discrepancies:                 {total_discrepancies}")

        if total_missing > 0:
            self.stdout.write(self.style.ERROR(
                f"Missing from Az-Sunshine:      {total_missing}"
            ))
        else:
            self.stdout.write(f"Missing from Az-Sunshine:      {total_missing}")

        self.stdout.write(f"Extra in Az-Sunshine:          {total_extra}")

        # Total IE comparison
        self.stdout.write(f"\nTotal IE (SeeTheMoney):  ${results['total_stm_ie']:,.2f}")
        self.stdout.write(f"Total IE (Az-Sunshine):  ${results['total_az_ie']:,.2f}")

        variance = abs(results['total_stm_ie'] - results['total_az_ie'])
        if results['total_stm_ie'] > 0:
            variance_pct = float(variance / results['total_stm_ie'] * 100)
        else:
            variance_pct = 0

        if variance_pct <= 1:
            self.stdout.write(self.style.SUCCESS(
                f"Total Variance:          ${variance:,.2f} ({variance_pct:.2f}%)"
            ))
        elif variance_pct <= 5:
            self.stdout.write(self.style.WARNING(
                f"Total Variance:          ${variance:,.2f} ({variance_pct:.2f}%)"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Total Variance:          ${variance:,.2f} ({variance_pct:.2f}%)"
            ))

        # Detailed output
        if verbose:
            if results['discrepancies']:
                self.stdout.write('\n' + '-' * 40)
                self.stdout.write(self.style.WARNING('DISCREPANCIES:'))
                for disc in sorted(results['discrepancies'],
                                   key=lambda x: x['variance_amount'], reverse=True)[:10]:
                    self.stdout.write(f"\n  {disc['name']}")
                    self.stdout.write(f"    SeeTheMoney: ${disc['stm_total']:,.2f} "
                                    f"(For: ${disc['stm_ie_for']:,.2f}, Against: ${disc['stm_ie_against']:,.2f})")
                    self.stdout.write(f"    Az-Sunshine: ${disc['az_total']:,.2f} "
                                    f"(For: ${disc['az_ie_for']:,.2f}, Against: ${disc['az_ie_against']:,.2f})")
                    self.stdout.write(f"    Variance: ${disc['variance_amount']:,.2f} ({disc['variance_pct']:.1f}%)")

            if results['missing_from_az']:
                self.stdout.write('\n' + '-' * 40)
                self.stdout.write(self.style.ERROR('MISSING FROM AZ-SUNSHINE:'))
                for missing in sorted(results['missing_from_az'],
                                     key=lambda x: x['stm_total'], reverse=True)[:10]:
                    self.stdout.write(f"  {missing['name']}: ${missing['stm_total']:,.2f}")

        # Health assessment
        if total_discrepancies == 0 and total_missing == 0 and variance_pct <= 1:
            self.stdout.write(self.style.SUCCESS('\n*** DATA VERIFIED - MATCH ***'))
        elif variance_pct <= 5:
            self.stdout.write(self.style.WARNING('\n*** DATA MOSTLY MATCHES - REVIEW DISCREPANCIES ***'))
        else:
            self.stdout.write(self.style.ERROR('\n*** SIGNIFICANT DISCREPANCIES - INVESTIGATION NEEDED ***'))
