"""
Export IE data from Az-Sunshine for comparison with SeeTheMoney.

Usage:
    # Export 2022 IE data
    python manage.py export_ie_for_comparison --cycle 2022

    # Export Governor 2022 only
    python manage.py export_ie_for_comparison --cycle 2022 --office Governor

    # Output to specific file
    python manage.py export_ie_for_comparison --cycle 2022 --output /tmp/ie_2022.csv
"""

import csv
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q
from django.db.models.functions import Abs

from transparency.models import Transaction, Office, Cycle


class Command(BaseCommand):
    help = 'Export IE data for comparison with SeeTheMoney'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cycle',
            type=str,
            required=True,
            help='Election cycle year (e.g., "2022")'
        )
        parser.add_argument(
            '--office',
            type=str,
            help='Filter by office (e.g., "Governor")'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output CSV file path'
        )
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Output summary by candidate instead of transactions'
        )

    def handle(self, *args, **options):
        cycle_year = options['cycle']
        office_filter = options.get('office')
        output_path = options.get('output') or f'/opt/az_sunshine/backend/data/comparison/az_sunshine_ie_{cycle_year}.csv'
        summary_mode = options.get('summary', False)

        try:
            cycle = Cycle.objects.get(name=cycle_year)
        except Cycle.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Cycle {cycle_year} not found"))
            return

        self.stdout.write(f"Exporting IE data for {cycle_year}...")

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

        if summary_mode:
            self._export_summary(filters, output_path)
        else:
            self._export_transactions(filters, output_path)

        self.stdout.write(self.style.SUCCESS(f"\nExported to: {output_path}"))

    def _export_summary(self, filters, output_path):
        """Export summary by candidate/committee"""
        ie_data = Transaction.objects.filter(**filters).values(
            'subject_committee__committee_id',
            'subject_committee__name__last_name',
            'subject_committee__name__first_name',
            'subject_committee__candidate_office__name',
            'subject_committee__candidate_party__name',
        ).annotate(
            ie_for=Sum(Abs('amount'), filter=Q(is_for_benefit=True)),
            ie_against=Sum(Abs('amount'), filter=Q(is_for_benefit=False)),
            total_ie=Sum(Abs('amount')),
            tx_count=Count('transaction_id')
        ).order_by('-total_ie')

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Committee ID', 'Candidate/Committee Name', 'Office', 'Party',
                'IE For', 'IE Against', 'Total IE', 'Transaction Count'
            ])

            for row in ie_data:
                name = f"{row['subject_committee__name__first_name'] or ''} {row['subject_committee__name__last_name'] or ''}".strip()
                writer.writerow([
                    row['subject_committee__committee_id'],
                    name,
                    row['subject_committee__candidate_office__name'] or '',
                    row['subject_committee__candidate_party__name'] or '',
                    float(row['ie_for'] or 0),
                    float(row['ie_against'] or 0),
                    float(row['total_ie'] or 0),
                    row['tx_count'] or 0
                ])

        self.stdout.write(f"Exported {ie_data.count()} candidate summaries")

    def _export_transactions(self, filters, output_path):
        """Export individual IE transactions"""
        transactions = Transaction.objects.filter(**filters).select_related(
            'committee__name',
            'subject_committee__name',
            'subject_committee__candidate_office',
            'transaction_type'
        ).order_by('transaction_date')

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Transaction ID', 'Date', 'Spender Committee', 'Spender ID',
                'Subject Committee', 'Subject ID', 'Office',
                'Amount', 'For Benefit', 'Transaction Type'
            ])

            count = 0
            for tx in transactions:
                spender_name = ''
                if tx.committee and tx.committee.name:
                    spender_name = f"{tx.committee.name.first_name or ''} {tx.committee.name.last_name or ''}".strip()

                subject_name = ''
                if tx.subject_committee and tx.subject_committee.name:
                    subject_name = f"{tx.subject_committee.name.first_name or ''} {tx.subject_committee.name.last_name or ''}".strip()

                office = ''
                if tx.subject_committee and tx.subject_committee.candidate_office:
                    office = tx.subject_committee.candidate_office.name

                writer.writerow([
                    tx.transaction_id,
                    tx.transaction_date,
                    spender_name,
                    tx.committee_id,
                    subject_name,
                    tx.subject_committee_id,
                    office,
                    float(abs(tx.amount)),
                    'For Benefit' if tx.is_for_benefit else 'Not For Benefit',
                    tx.transaction_type.name if tx.transaction_type else ''
                ])
                count += 1

        self.stdout.write(f"Exported {count} transactions")
