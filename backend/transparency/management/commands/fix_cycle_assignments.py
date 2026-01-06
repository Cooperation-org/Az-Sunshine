"""
Fix incorrect election cycle assignments for committees.

Committees should be assigned to cycles based on their organization_date
and actual election activity, not arbitrarily to the latest cycle.

Run with: python manage.py fix_cycle_assignments --dry-run
         python manage.py fix_cycle_assignments --apply
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from transparency.models import Committee, Cycle, Transaction
from datetime import datetime


class Command(BaseCommand):
    help = 'Fix incorrect election cycle assignments for committees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually apply the fixes'
        )

    def get_correct_cycle(self, org_date):
        """
        Determine the correct election cycle based on organization date.
        Arizona elections are in even years.
        """
        if not org_date:
            return None

        year = org_date.year

        # If organized in odd year, they're running in the next (even) year
        # If organized in even year before November, same year election
        # If organized in even year after November, next even year
        if year % 2 == 1:  # Odd year
            target_year = year + 1
        else:  # Even year
            # If after November, next election cycle
            if org_date.month >= 11:
                target_year = year + 2
            else:
                target_year = year

        # Find matching cycle
        try:
            return Cycle.objects.get(name=str(target_year))
        except Cycle.DoesNotExist:
            return None

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        apply = options['apply']

        if not dry_run and not apply:
            self.stdout.write(self.style.WARNING(
                'Please specify --dry-run or --apply'
            ))
            return

        self.stdout.write('Scanning for misassigned committees...\n')

        # Find committees where org_date suggests different cycle
        misassigned = []

        committees = Committee.objects.filter(
            organization_date__isnull=False,
            election_cycle__isnull=False,
            candidate__isnull=False
        ).select_related('election_cycle', 'candidate', 'candidate_office')

        for committee in committees:
            correct_cycle = self.get_correct_cycle(committee.organization_date)

            if correct_cycle and correct_cycle != committee.election_cycle:
                misassigned.append({
                    'committee': committee,
                    'current_cycle': committee.election_cycle,
                    'correct_cycle': correct_cycle
                })

        self.stdout.write(f'\nFound {len(misassigned)} misassigned committees\n')

        # Show details
        for item in misassigned[:20]:
            c = item['committee']
            candidate_name = f"{c.candidate.first_name} {c.candidate.last_name}" if c.candidate else "Unknown"
            office = c.candidate_office.name if c.candidate_office else "No office"

            self.stdout.write(
                f"  {candidate_name} | {office}\n"
                f"    Org Date: {c.organization_date}\n"
                f"    Current: {item['current_cycle'].name} -> Should be: {item['correct_cycle'].name}\n"
            )

        if len(misassigned) > 20:
            self.stdout.write(f'  ... and {len(misassigned) - 20} more\n')

        # Apply fixes if requested
        if apply and misassigned:
            self.stdout.write('\nApplying fixes...\n')
            fixed_count = 0

            for item in misassigned:
                committee = item['committee']
                committee.election_cycle = item['correct_cycle']
                committee.save(update_fields=['election_cycle'])
                fixed_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'\nFixed {fixed_count} committee cycle assignments'
            ))
        elif dry_run:
            self.stdout.write(self.style.WARNING(
                '\nDry run - no changes made. Use --apply to fix.'
            ))
