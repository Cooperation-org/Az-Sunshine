"""
Management command to verify Az-Sunshine data against external sources.

Usage:
    # Verify all races for all cycles
    python manage.py verify_external_data

    # Verify specific cycle
    python manage.py verify_external_data --cycle 2022

    # Verify specific race
    python manage.py verify_external_data --office "Governor" --cycle 2022

    # Output JSON report
    python manage.py verify_external_data --output report.json

    # Only show critical issues
    python manage.py verify_external_data --critical-only
"""

import json
import logging
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from transparency.utils.data_verification import (
    DataVerificationEngine,
    VerificationResult,
    Severity
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verify Az-Sunshine data against external sources (FollowTheMoney, SeeTheMoney)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--office',
            type=str,
            help='Specific office to verify (e.g., "Governor", "Attorney General")'
        )
        parser.add_argument(
            '--cycle',
            type=str,
            help='Specific cycle year to verify (e.g., "2022")'
        )
        parser.add_argument(
            '--party',
            type=str,
            help='Filter by party (e.g., "Republican", "Democratic")'
        )
        parser.add_argument(
            '--cycles',
            type=str,
            nargs='+',
            default=['2016', '2018', '2020', '2022', '2024'],
            help='List of cycles to verify (default: 2016-2024)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON report to file'
        )
        parser.add_argument(
            '--critical-only',
            action='store_true',
            help='Only show critical and high severity issues'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 60 + '\n'
            '  AZ-SUNSHINE DATA VERIFICATION\n'
            '  External Source Comparison Tool\n'
            '=' * 60 + '\n'
        ))

        engine = DataVerificationEngine()

        # Check API key
        if not getattr(settings, 'FOLLOWTHEMONEY_API_KEY', None):
            self.stdout.write(self.style.WARNING(
                '\nNote: FOLLOWTHEMONEY_API_KEY not set.\n'
                'FollowTheMoney.org verification will be skipped.\n'
                'Set this in your Django settings to enable full verification.\n'
            ))

        results = []

        if options['office'] and options['cycle']:
            # Verify single race
            self.stdout.write(f"\nVerifying {options['office']} {options['cycle']}...")
            result = engine.verify_race(
                office_name=options['office'],
                cycle_year=options['cycle'],
                party_name=options.get('party')
            )
            results.append(result)
        elif options['cycle']:
            # Verify all races for a specific cycle
            self.stdout.write(f"\nVerifying all races for {options['cycle']}...")
            results = engine.verify_all_races(cycles=[options['cycle']])
        else:
            # Verify all races for all cycles
            cycles = options['cycles']
            self.stdout.write(f"\nVerifying all races for cycles: {', '.join(cycles)}...")
            results = engine.verify_all_races(cycles=cycles)

        # Generate report
        report = engine.generate_verification_report(results)

        # Display summary
        self._display_summary(report, options)

        # Display discrepancies
        self._display_discrepancies(results, options)

        # Output to file if requested
        if options['output']:
            with open(options['output'], 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(
                f"\nReport saved to: {options['output']}"
            ))

        # Exit with error code if critical issues found
        if report['summary']['critical_issues'] > 0:
            self.stdout.write(self.style.ERROR(
                f"\n{report['summary']['critical_issues']} CRITICAL issues found!"
            ))
            return

        self.stdout.write(self.style.SUCCESS('\nVerification complete.'))

    def _display_summary(self, report: dict, options: dict):
        """Display summary statistics"""
        summary = report['summary']

        self.stdout.write('\n' + '-' * 40)
        self.stdout.write(self.style.MIGRATE_HEADING('SUMMARY'))
        self.stdout.write('-' * 40)

        self.stdout.write(f"Races Verified:      {summary['races_verified']}")
        self.stdout.write(f"Total Discrepancies: {summary['total_discrepancies']}")

        # Color-coded severity counts
        if summary['critical_issues'] > 0:
            self.stdout.write(self.style.ERROR(
                f"Critical Issues:     {summary['critical_issues']}"
            ))
        else:
            self.stdout.write(f"Critical Issues:     {summary['critical_issues']}")

        if summary['high_issues'] > 0:
            self.stdout.write(self.style.WARNING(
                f"High Issues:         {summary['high_issues']}"
            ))
        else:
            self.stdout.write(f"High Issues:         {summary['high_issues']}")

        by_type = report['by_type']
        self.stdout.write(f"\nBy Type:")
        self.stdout.write(f"  Missing Candidates: {by_type['missing_candidate']}")
        self.stdout.write(f"  Amount Mismatches:  {by_type['amount_mismatch']}")
        self.stdout.write(f"  Extra Candidates:   {by_type['extra_candidate']}")

        # Overall health
        health = summary['overall_health']
        if health == 'good':
            self.stdout.write(self.style.SUCCESS(f"\nOverall Health: {health.upper()}"))
        elif health == 'warning':
            self.stdout.write(self.style.WARNING(f"\nOverall Health: {health.upper()}"))
        else:
            self.stdout.write(self.style.ERROR(f"\nOverall Health: {health.upper()}"))

    def _display_discrepancies(self, results: list, options: dict):
        """Display individual discrepancies"""
        critical_only = options.get('critical_only', False)
        verbose = options.get('verbose', False)

        # Collect all discrepancies
        all_discrepancies = []
        for result in results:
            for disc in result.discrepancies:
                disc_dict = disc.to_dict()
                disc_dict['race'] = f"{result.office} {result.cycle}"
                all_discrepancies.append(disc_dict)

        if not all_discrepancies:
            self.stdout.write(self.style.SUCCESS('\nNo discrepancies found!'))
            return

        # Filter if needed
        if critical_only:
            all_discrepancies = [
                d for d in all_discrepancies
                if d['severity'] in ['critical', 'high']
            ]

        if not all_discrepancies:
            self.stdout.write('\nNo critical/high issues found.')
            return

        self.stdout.write('\n' + '-' * 40)
        self.stdout.write(self.style.MIGRATE_HEADING('DISCREPANCIES'))
        self.stdout.write('-' * 40)

        # Group by severity
        for severity in ['critical', 'high', 'medium', 'low']:
            severity_discs = [d for d in all_discrepancies if d['severity'] == severity]
            if not severity_discs:
                continue

            if severity == 'critical':
                self.stdout.write(self.style.ERROR(f"\n{severity.upper()} ({len(severity_discs)}):"))
            elif severity == 'high':
                self.stdout.write(self.style.WARNING(f"\n{severity.upper()} ({len(severity_discs)}):"))
            else:
                self.stdout.write(f"\n{severity.upper()} ({len(severity_discs)}):")

            for disc in severity_discs[:10]:  # Limit display
                self.stdout.write(f"\n  [{disc['race']}] {disc['candidate_name'] or 'N/A'}")
                self.stdout.write(f"    Type: {disc['discrepancy_type']}")
                self.stdout.write(f"    {disc['description']}")
                if disc.get('variance_percent'):
                    self.stdout.write(f"    Variance: {disc['variance_percent']:.1f}%")
                if verbose:
                    self.stdout.write(f"    Az-Sunshine: {disc['az_sunshine_value']}")
                    self.stdout.write(f"    External: {disc['external_value']}")

            if len(severity_discs) > 10:
                self.stdout.write(f"\n  ... and {len(severity_discs) - 10} more {severity} issues")
