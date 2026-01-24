"""
Verification system that compares Az-Sunshine database against external data
sources (tucson.com scraped data).

This is our "second layer" to catch errors before Ben does.

Usage:
    # Run verification with default data file
    python manage.py verify_against_tucson

    # Specify custom data file
    python manage.py verify_against_tucson --data-file /path/to/data.json

    # Set custom discrepancy threshold (default 10%)
    python manage.py verify_against_tucson --threshold 5

    # Output to custom report file
    python manage.py verify_against_tucson --output /path/to/report.txt

    # Verbose mode with detailed matching info
    python manage.py verify_against_tucson --verbose
"""

import json
import os
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from django.db.models.functions import Abs

from transparency.models import Committee, Transaction, Office, Cycle, Entity


class Command(BaseCommand):
    help = 'Verify Az-Sunshine data against tucson.com scraped data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-file',
            type=str,
            default='/opt/az_sunshine/data/tucson_verification_data.json',
            help='Path to tucson.com verification data JSON file'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=10.0,
            help='Percentage threshold for flagging discrepancies (default: 10%%)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='/opt/az_sunshine/data/verification_report.txt',
            help='Output path for verification report'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed matching information'
        )

    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        self.threshold = options.get('threshold', 10.0)

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 60 + '\n'
            '  AZ-SUNSHINE vs TUCSON.COM VERIFICATION\n'
            '  Second Layer Data Integrity Check\n'
            '=' * 60 + '\n'
        ))

        # Load tucson.com data
        data_file = options['data_file']
        self.stdout.write(f"Loading tucson.com data from: {data_file}")

        tucson_data = self._load_tucson_data(data_file)
        if not tucson_data:
            self.stdout.write(self.style.ERROR("Failed to load tucson.com data!"))
            return

        # Run verification
        results = self._verify_data(tucson_data)

        # Generate and save report
        report_path = options['output']
        report_text = self._generate_report(results, tucson_data)

        self._save_report(report_text, report_path)

        # Display summary
        self._display_summary(results)

    def _load_tucson_data(self, data_file):
        """Load and parse tucson.com verification data JSON"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.stdout.write(self.style.SUCCESS(
                f"Loaded {len(data.get('candidates', []))} candidates, "
                f"{len(data.get('committees', []))} committees from tucson.com data"
            ))
            return data

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {data_file}"))
            self.stdout.write(self.style.WARNING(
                "\nTo create the verification data file, scrape tucson.com articles\n"
                "and save the data in the following JSON format:\n\n"
                '{\n'
                '  "source": "tucson.com",\n'
                '  "scraped_date": "2024-01-24",\n'
                '  "candidates": [\n'
                '    {\n'
                '      "name": "Katie Hobbs",\n'
                '      "office": "Governor",\n'
                '      "cycle": "2022",\n'
                '      "ie_total": 15000000,\n'
                '      "ie_for": 12000000,\n'
                '      "ie_against": 3000000,\n'
                '      "source_url": "https://tucson.com/..."\n'
                '    }\n'
                '  ],\n'
                '  "committees": [\n'
                '    {\n'
                '      "name": "Republican Governors Association",\n'
                '      "total_spending": 11000000,\n'
                '      "cycle": "2022",\n'
                '      "source_url": "https://tucson.com/..."\n'
                '    }\n'
                '  ]\n'
                '}'
            ))
            return None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON in {data_file}: {e}"))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading data: {e}"))
            return None

    def _verify_data(self, tucson_data):
        """Compare tucson.com data against our database"""
        results = {
            'missing_entities': [],
            'amount_discrepancies': [],
            'data_matches': [],
            'missing_races': [],
            'summary': {
                'total_checked': 0,
                'matches': 0,
                'discrepancies': 0,
                'missing': 0
            }
        }

        # Verify candidates
        candidates = tucson_data.get('candidates', [])
        for candidate in candidates:
            results['summary']['total_checked'] += 1
            self._verify_candidate(candidate, results)

        # Verify committees/outside spending groups
        committees = tucson_data.get('committees', [])
        for committee in committees:
            results['summary']['total_checked'] += 1
            self._verify_committee(committee, results)

        # Verify races/cycles
        races = tucson_data.get('races', [])
        for race in races:
            results['summary']['total_checked'] += 1
            self._verify_race(race, results)

        return results

    def _verify_candidate(self, tucson_candidate, results):
        """Verify a single candidate against our database"""
        name = tucson_candidate.get('name', '')
        office = tucson_candidate.get('office', '')
        cycle = tucson_candidate.get('cycle', '')
        expected_ie = Decimal(str(tucson_candidate.get('ie_total', 0)))
        expected_ie_for = Decimal(str(tucson_candidate.get('ie_for', 0)))
        expected_ie_against = Decimal(str(tucson_candidate.get('ie_against', 0)))
        source_url = tucson_candidate.get('source_url', '')

        if self.verbose:
            self.stdout.write(f"\nVerifying candidate: {name} ({office} {cycle})")

        # Parse name
        name_parts = name.strip().split()
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[-1] if len(name_parts) > 1 else name_parts[0] if name_parts else ''

        # Find candidate in our database
        db_candidate = self._find_candidate_in_db(first_name, last_name, office, cycle)

        if not db_candidate:
            results['missing_entities'].append({
                'type': 'candidate',
                'name': name,
                'office': office,
                'cycle': cycle,
                'expected_ie': float(expected_ie),
                'source_url': source_url
            })
            results['summary']['missing'] += 1
            return

        # Get IE spending from our database
        db_ie = self._get_candidate_ie_spending(db_candidate, cycle)
        db_ie_total = db_ie['total']
        db_ie_for = db_ie['for']
        db_ie_against = db_ie['against']

        # Calculate variance
        if expected_ie > 0:
            variance_pct = float((db_ie_total - expected_ie) / expected_ie * 100)
        else:
            variance_pct = 100 if db_ie_total > 0 else 0

        # Check if within threshold
        if abs(variance_pct) <= self.threshold:
            results['data_matches'].append({
                'name': name,
                'office': office,
                'cycle': cycle,
                'tucson_ie': float(expected_ie),
                'db_ie': float(db_ie_total),
                'variance_pct': variance_pct
            })
            results['summary']['matches'] += 1
        else:
            results['amount_discrepancies'].append({
                'type': 'candidate',
                'name': name,
                'office': office,
                'cycle': cycle,
                'tucson_ie': float(expected_ie),
                'tucson_ie_for': float(expected_ie_for),
                'tucson_ie_against': float(expected_ie_against),
                'db_ie': float(db_ie_total),
                'db_ie_for': float(db_ie_for),
                'db_ie_against': float(db_ie_against),
                'variance_pct': variance_pct,
                'source_url': source_url
            })
            results['summary']['discrepancies'] += 1

    def _verify_committee(self, tucson_committee, results):
        """Verify a single committee/PAC against our database"""
        name = tucson_committee.get('name', '')
        cycle = tucson_committee.get('cycle', '')
        expected_spending = Decimal(str(tucson_committee.get('total_spending', 0)))
        source_url = tucson_committee.get('source_url', '')

        if self.verbose:
            self.stdout.write(f"\nVerifying committee: {name} ({cycle})")

        # Find committee in our database
        db_committee = self._find_committee_in_db(name)

        if not db_committee:
            results['missing_entities'].append({
                'type': 'committee',
                'name': name,
                'cycle': cycle,
                'expected_spending': float(expected_spending),
                'source_url': source_url
            })
            results['summary']['missing'] += 1
            return

        # Get spending from our database
        db_spending = self._get_committee_spending(db_committee, cycle)

        # Calculate variance
        if expected_spending > 0:
            variance_pct = float((db_spending - expected_spending) / expected_spending * 100)
        else:
            variance_pct = 100 if db_spending > 0 else 0

        # Check if within threshold
        if abs(variance_pct) <= self.threshold:
            results['data_matches'].append({
                'name': name,
                'type': 'committee',
                'cycle': cycle,
                'tucson_spending': float(expected_spending),
                'db_spending': float(db_spending),
                'variance_pct': variance_pct
            })
            results['summary']['matches'] += 1
        else:
            results['amount_discrepancies'].append({
                'type': 'committee',
                'name': name,
                'cycle': cycle,
                'tucson_spending': float(expected_spending),
                'db_spending': float(db_spending),
                'variance_pct': variance_pct,
                'source_url': source_url
            })
            results['summary']['discrepancies'] += 1

    def _verify_race(self, tucson_race, results):
        """Verify race-level spending totals"""
        office = tucson_race.get('office', '')
        cycle = tucson_race.get('cycle', '')
        expected_total = Decimal(str(tucson_race.get('total_ie', 0)))
        source_url = tucson_race.get('source_url', '')

        if self.verbose:
            self.stdout.write(f"\nVerifying race: {office} {cycle}")

        # Get race total from our database
        db_total = self._get_race_ie_total(office, cycle)

        if db_total is None:
            results['missing_races'].append({
                'office': office,
                'cycle': cycle,
                'expected_total': float(expected_total),
                'source_url': source_url
            })
            results['summary']['missing'] += 1
            return

        # Calculate variance
        if expected_total > 0:
            variance_pct = float((db_total - expected_total) / expected_total * 100)
        else:
            variance_pct = 100 if db_total > 0 else 0

        # Check if within threshold
        if abs(variance_pct) <= self.threshold:
            results['data_matches'].append({
                'name': f"{office} {cycle}",
                'type': 'race',
                'tucson_total': float(expected_total),
                'db_total': float(db_total),
                'variance_pct': variance_pct
            })
            results['summary']['matches'] += 1
        else:
            results['amount_discrepancies'].append({
                'type': 'race',
                'name': f"{office} {cycle}",
                'office': office,
                'cycle': cycle,
                'tucson_total': float(expected_total),
                'db_total': float(db_total),
                'variance_pct': variance_pct,
                'source_url': source_url
            })
            results['summary']['discrepancies'] += 1

    def _find_candidate_in_db(self, first_name, last_name, office_name, cycle_year):
        """Find a candidate committee in our database"""
        # Try exact match first
        candidates = Committee.objects.filter(
            candidate__isnull=False
        ).filter(
            Q(candidate__last_name__iexact=last_name) |
            Q(name__last_name__iexact=last_name)
        )

        if first_name:
            candidates = candidates.filter(
                Q(candidate__first_name__iexact=first_name) |
                Q(candidate__first_name__istartswith=first_name[:1]) |
                Q(name__first_name__iexact=first_name) |
                Q(name__first_name__istartswith=first_name[:1])
            )

        # Filter by office if provided
        if office_name:
            office_candidates = candidates.filter(
                candidate_office__name__icontains=office_name
            )
            if office_candidates.exists():
                candidates = office_candidates

        # Filter by cycle if provided
        if cycle_year:
            try:
                cycle = Cycle.objects.get(name=str(cycle_year))
                cycle_candidates = candidates.filter(election_cycle=cycle)
                if cycle_candidates.exists():
                    candidates = cycle_candidates
            except Cycle.DoesNotExist:
                pass

        if self.verbose and candidates.exists():
            self.stdout.write(f"  Found in DB: {candidates.first()}")

        return candidates.first()

    def _find_committee_in_db(self, committee_name):
        """Find a committee/PAC in our database"""
        # Clean the name for matching
        search_terms = committee_name.lower().split()

        # Try various matching strategies
        committees = Committee.objects.filter(
            Q(name__last_name__icontains=committee_name) |
            Q(name__first_name__icontains=committee_name)
        )

        if not committees.exists():
            # Try matching individual words
            for term in search_terms:
                if len(term) > 3:  # Skip short words
                    partial_match = Committee.objects.filter(
                        Q(name__last_name__icontains=term) |
                        Q(name__first_name__icontains=term)
                    )
                    if partial_match.exists():
                        committees = partial_match
                        break

        if self.verbose and committees.exists():
            self.stdout.write(f"  Found in DB: {committees.first()}")

        return committees.first()

    def _get_candidate_ie_spending(self, committee, cycle_year):
        """Get IE spending totals for a candidate from our database"""
        filters = {
            'subject_committee': committee,
            'deleted': False,
            'transaction_type__income_expense_neutral': 2,
        }

        # Filter by cycle date range if provided
        if cycle_year:
            try:
                cycle = Cycle.objects.get(name=str(cycle_year))
                filters['transaction_date__gte'] = cycle.begin_date
                filters['transaction_date__lte'] = cycle.end_date
            except Cycle.DoesNotExist:
                pass

        totals = Transaction.objects.filter(**filters).aggregate(
            for_total=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            against_total=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
            total=Sum(Abs('amount'))
        )

        return {
            'for': totals['for_total'] or Decimal('0'),
            'against': totals['against_total'] or Decimal('0'),
            'total': totals['total'] or Decimal('0')
        }

    def _get_committee_spending(self, committee, cycle_year):
        """Get total spending by a committee"""
        filters = {
            'committee': committee,
            'deleted': False,
            'transaction_type__income_expense_neutral': 2,
        }

        # Filter by cycle date range if provided
        if cycle_year:
            try:
                cycle = Cycle.objects.get(name=str(cycle_year))
                filters['transaction_date__gte'] = cycle.begin_date
                filters['transaction_date__lte'] = cycle.end_date
            except Cycle.DoesNotExist:
                pass

        total = Transaction.objects.filter(**filters).aggregate(
            total=Sum(Abs('amount'))
        )['total']

        return total or Decimal('0')

    def _get_race_ie_total(self, office_name, cycle_year):
        """Get total IE spending for a race"""
        try:
            office = Office.objects.filter(name__icontains=office_name).first()
            if not office:
                return None

            cycle = Cycle.objects.get(name=str(cycle_year))
        except (Office.DoesNotExist, Cycle.DoesNotExist):
            return None

        total = Transaction.objects.filter(
            subject_committee__candidate_office=office,
            deleted=False,
            transaction_type__income_expense_neutral=2,
            transaction_date__gte=cycle.begin_date,
            transaction_date__lte=cycle.end_date
        ).aggregate(total=Sum(Abs('amount')))['total']

        return total or Decimal('0')

    def _generate_report(self, results, tucson_data):
        """Generate the verification report text"""
        lines = []
        now = datetime.now()

        lines.append("=" * 60)
        lines.append("=== VERIFICATION REPORT ===")
        lines.append("=" * 60)
        lines.append(f"Date: {now.strftime('%Y-%m-%d')}")
        lines.append(f"Time: {now.strftime('%H:%M:%S')}")
        lines.append(f"Source: {tucson_data.get('source', 'tucson.com')}")
        lines.append(f"Scraped Date: {tucson_data.get('scraped_date', 'Unknown')}")
        lines.append(f"Threshold: {self.threshold}%")
        lines.append("")

        # Missing entities section
        lines.append("-" * 60)
        lines.append("MISSING FROM DATABASE:")
        lines.append("-" * 60)

        if results['missing_entities']:
            for entity in results['missing_entities']:
                entity_type = entity.get('type', 'entity')
                name = entity.get('name', 'Unknown')

                if entity_type == 'candidate':
                    expected = entity.get('expected_ie', 0)
                    office = entity.get('office', '')
                    cycle = entity.get('cycle', '')
                    lines.append(f"- {name} ({office} {cycle}): Expected ${expected:,.0f} IE, Found: $0")
                elif entity_type == 'committee':
                    expected = entity.get('expected_spending', 0)
                    cycle = entity.get('cycle', '')
                    lines.append(f"- {name} ({cycle}): Expected ${expected:,.0f}, Found: $0")
        else:
            lines.append("- None (all entities found in database)")

        lines.append("")

        # Missing races section
        if results['missing_races']:
            lines.append("-" * 60)
            lines.append("MISSING RACES/CYCLES:")
            lines.append("-" * 60)
            for race in results['missing_races']:
                office = race.get('office', '')
                cycle = race.get('cycle', '')
                expected = race.get('expected_total', 0)
                lines.append(f"- {office} {cycle}: Expected ${expected:,.0f} total IE, Found: $0")
            lines.append("")

        # Amount discrepancies section
        lines.append("-" * 60)
        lines.append("AMOUNT DISCREPANCIES:")
        lines.append("-" * 60)

        if results['amount_discrepancies']:
            # Sort by variance percentage (absolute value, descending)
            sorted_discrepancies = sorted(
                results['amount_discrepancies'],
                key=lambda x: abs(x.get('variance_pct', 0)),
                reverse=True
            )

            for disc in sorted_discrepancies:
                name = disc.get('name', 'Unknown')
                disc_type = disc.get('type', '')
                variance_pct = disc.get('variance_pct', 0)

                if disc_type == 'candidate':
                    tucson_ie = disc.get('tucson_ie', 0)
                    db_ie = disc.get('db_ie', 0)
                    office = disc.get('office', '')
                    cycle = disc.get('cycle', '')
                    lines.append(f"- {name} {cycle}: Tucson says ${tucson_ie:,.0f} IE, "
                               f"We have ${db_ie:,.0f} ({variance_pct:+.1f}%)")
                elif disc_type == 'committee':
                    tucson_spending = disc.get('tucson_spending', 0)
                    db_spending = disc.get('db_spending', 0)
                    cycle = disc.get('cycle', '')
                    lines.append(f"- {name} {cycle}: Tucson says ${tucson_spending:,.0f}, "
                               f"We have ${db_spending:,.0f} ({variance_pct:+.1f}%)")
                elif disc_type == 'race':
                    tucson_total = disc.get('tucson_total', 0)
                    db_total = disc.get('db_total', 0)
                    lines.append(f"- {name}: Tucson says ${tucson_total:,.0f}, "
                               f"We have ${db_total:,.0f} ({variance_pct:+.1f}%)")
        else:
            lines.append("- None (all amounts match within threshold)")

        lines.append("")

        # Data matches section
        lines.append("-" * 60)
        lines.append("DATA MATCHES:")
        lines.append("-" * 60)

        if results['data_matches']:
            for match in results['data_matches']:
                name = match.get('name', 'Unknown')
                variance_pct = match.get('variance_pct', 0)
                match_type = match.get('type', '')

                if match_type == 'committee':
                    lines.append(f"- {name}: Match within {self.threshold}% (variance: {variance_pct:+.1f}%)")
                elif match_type == 'race':
                    lines.append(f"- {name}: Match within {self.threshold}% (variance: {variance_pct:+.1f}%)")
                else:
                    office = match.get('office', '')
                    cycle = match.get('cycle', '')
                    lines.append(f"- {name} {cycle}: Match within {self.threshold}% (variance: {variance_pct:+.1f}%)")
        else:
            lines.append("- No matches found")

        lines.append("")

        # Summary section
        lines.append("=" * 60)
        lines.append("SUMMARY:")
        lines.append("=" * 60)
        summary = results['summary']
        total = summary['total_checked']
        matches = summary['matches']
        discrepancies = summary['discrepancies']
        missing = summary['missing']

        match_pct = (matches / total * 100) if total > 0 else 0
        disc_pct = (discrepancies / total * 100) if total > 0 else 0
        missing_pct = (missing / total * 100) if total > 0 else 0

        lines.append(f"- Total entities checked: {total}")
        lines.append(f"- Matches: {matches} ({match_pct:.0f}%)")
        lines.append(f"- Discrepancies: {discrepancies} ({disc_pct:.0f}%)")
        lines.append(f"- Missing: {missing} ({missing_pct:.0f}%)")
        lines.append("")

        # Health assessment
        if match_pct >= 90:
            lines.append("HEALTH: EXCELLENT - Data matches external sources well")
        elif match_pct >= 75:
            lines.append("HEALTH: GOOD - Most data matches, review discrepancies")
        elif match_pct >= 50:
            lines.append("HEALTH: WARNING - Significant discrepancies detected")
        else:
            lines.append("HEALTH: CRITICAL - Major data integrity issues")

        lines.append("")
        lines.append("=" * 60)
        lines.append(f"Report generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        return '\n'.join(lines)

    def _save_report(self, report_text, report_path):
        """Save the report to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_text)

            self.stdout.write(self.style.SUCCESS(f"\nReport saved to: {report_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error saving report: {e}"))

    def _display_summary(self, results):
        """Display summary to console"""
        summary = results['summary']

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.MIGRATE_HEADING('VERIFICATION SUMMARY'))
        self.stdout.write('=' * 60)

        total = summary['total_checked']
        matches = summary['matches']
        discrepancies = summary['discrepancies']
        missing = summary['missing']

        match_pct = (matches / total * 100) if total > 0 else 0
        disc_pct = (discrepancies / total * 100) if total > 0 else 0
        missing_pct = (missing / total * 100) if total > 0 else 0

        self.stdout.write(f"\nTotal entities checked: {total}")

        if matches > 0:
            self.stdout.write(self.style.SUCCESS(f"Matches: {matches} ({match_pct:.0f}%)"))
        else:
            self.stdout.write(f"Matches: {matches} ({match_pct:.0f}%)")

        if discrepancies > 0:
            self.stdout.write(self.style.WARNING(f"Discrepancies (>{self.threshold}%): {discrepancies} ({disc_pct:.0f}%)"))
        else:
            self.stdout.write(f"Discrepancies (>{self.threshold}%): {discrepancies} ({disc_pct:.0f}%)")

        if missing > 0:
            self.stdout.write(self.style.ERROR(f"Missing: {missing} ({missing_pct:.0f}%)"))
        else:
            self.stdout.write(f"Missing: {missing} ({missing_pct:.0f}%)")

        # Show top discrepancies
        if results['amount_discrepancies']:
            self.stdout.write('\n' + '-' * 40)
            self.stdout.write(self.style.WARNING('TOP DISCREPANCIES:'))
            sorted_disc = sorted(
                results['amount_discrepancies'],
                key=lambda x: abs(x.get('variance_pct', 0)),
                reverse=True
            )[:5]
            for disc in sorted_disc:
                name = disc.get('name', 'Unknown')
                variance_pct = disc.get('variance_pct', 0)
                self.stdout.write(f"  - {name}: {variance_pct:+.1f}%")

        # Show missing entities
        if results['missing_entities']:
            self.stdout.write('\n' + '-' * 40)
            self.stdout.write(self.style.ERROR('MISSING ENTITIES:'))
            for entity in results['missing_entities'][:5]:
                name = entity.get('name', 'Unknown')
                expected = entity.get('expected_ie', entity.get('expected_spending', 0))
                self.stdout.write(f"  - {name}: ${expected:,.0f}")
            if len(results['missing_entities']) > 5:
                self.stdout.write(f"  ... and {len(results['missing_entities']) - 5} more")

        # Health assessment
        self.stdout.write('')
        if match_pct >= 90:
            self.stdout.write(self.style.SUCCESS('HEALTH: EXCELLENT - Ready for Ben\'s review'))
        elif match_pct >= 75:
            self.stdout.write(self.style.SUCCESS('HEALTH: GOOD - Minor discrepancies to review'))
        elif match_pct >= 50:
            self.stdout.write(self.style.WARNING('HEALTH: WARNING - Investigate before Ben sees this'))
        else:
            self.stdout.write(self.style.ERROR('HEALTH: CRITICAL - Do not publish until fixed'))
