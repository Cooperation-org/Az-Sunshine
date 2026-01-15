"""
Management command to fix missing candidate links on committees.

This script:
1. Finds all committees with IE spending but no candidate linked
2. Extracts candidate name from committee name
3. Finds or creates matching Entity
4. Links the entity to the committee

Usage:
    # Dry run (preview changes)
    python manage.py fix_candidate_links --dry-run

    # Apply fixes
    python manage.py fix_candidate_links

    # Fix specific committee
    python manage.py fix_candidate_links --committee-id -445
"""

import re
import logging
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from django.db.models.functions import Abs
from django.db import transaction

from transparency.models import Committee, Transaction, Entity

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix missing candidate links on committees with IE spending'

    # Common patterns to extract candidate name from committee name
    NAME_PATTERNS = [
        # "John Smith for Governor" -> "John Smith"
        r'^(.+?)\s+for\s+',
        # "Elect John Smith" -> "John Smith"
        r'^Elect\s+(.+?)(?:\s+\d{4})?$',
        # "Vote John Smith" -> "John Smith"
        r'^Vote\s+(.+?)(?:\s+(?:for|LD|District|\d))',
        # "Committee to Elect John Smith" -> "John Smith"
        r'^Committee\s+to\s+Elect\s+(.+?)(?:\s+\d{4})?$',
        # "John Smith 2022" -> "John Smith"
        r'^(.+?)\s+\d{4}$',
        # "JOHN SMITH" (all caps, just use as-is)
        r'^([A-Z][A-Z\s]+)$',
    ]

    # Common suffixes to remove
    SUFFIXES_TO_REMOVE = [
        r'\s+\d{4}$',  # Year
        r'\s+for\s+.+$',  # "for Governor", "for Senate", etc.
        r'\s+-\s+.+$',  # "- District 10", etc.
        r'\s+LD\d+.*$',  # "LD22 Senate", etc.
        r'\s+District\s+\d+.*$',
        r'\s+Campaign.*$',
        r'\s+Committee.*$',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them'
        )
        parser.add_argument(
            '--committee-id',
            type=int,
            help='Fix specific committee by ID'
        )
        parser.add_argument(
            '--min-ie',
            type=float,
            default=0,
            help='Minimum IE amount to consider (default: 0)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        committee_id = options.get('committee_id')
        min_ie = options.get('min_ie', 0)

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '=' * 60 + '\n'
            '  FIX MISSING CANDIDATE LINKS\n'
            '=' * 60 + '\n'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))

        # Find committees to fix
        if committee_id:
            committees_to_fix = self._get_committee_by_id(committee_id)
        else:
            committees_to_fix = self._get_committees_without_candidates(min_ie)

        self.stdout.write(f'Found {len(committees_to_fix)} committees to fix\n')

        fixed_count = 0
        failed_count = 0
        skipped_count = 0

        for comm_data in committees_to_fix:
            result = self._fix_committee(comm_data, dry_run)
            if result == 'fixed':
                fixed_count += 1
            elif result == 'failed':
                failed_count += 1
            else:
                skipped_count += 1

        # Summary
        self.stdout.write('\n' + '-' * 40)
        self.stdout.write(self.style.MIGRATE_HEADING('SUMMARY'))
        self.stdout.write('-' * 40)
        self.stdout.write(f'Fixed:   {fixed_count}')
        self.stdout.write(f'Failed:  {failed_count}')
        self.stdout.write(f'Skipped: {skipped_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - Run without --dry-run to apply changes'))

    def _get_committees_without_candidates(self, min_ie=0):
        """Get all committees with IE spending but no candidate linked"""
        return Transaction.objects.filter(
            subject_committee__isnull=False,
            subject_committee__candidate__isnull=True,
            subject_committee__candidate_office__isnull=False,
            deleted=False,
            transaction_type__income_expense_neutral=2,
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__first_name',
            'subject_committee__name__last_name',
            'subject_committee__candidate_office__name',
            'subject_committee__election_cycle__name',
        ).annotate(
            total_ie=Sum(Abs('amount')),
        ).filter(total_ie__gte=min_ie).order_by('-total_ie')

    def _get_committee_by_id(self, committee_id):
        """Get specific committee data"""
        return Transaction.objects.filter(
            subject_committee__committee_id=committee_id,
            deleted=False,
            transaction_type__income_expense_neutral=2,
        ).values(
            'subject_committee__committee_id',
            'subject_committee__name__first_name',
            'subject_committee__name__last_name',
            'subject_committee__candidate_office__name',
            'subject_committee__election_cycle__name',
        ).annotate(
            total_ie=Sum(Abs('amount')),
        )

    def _extract_candidate_name(self, committee_name):
        """Extract candidate name from committee name"""
        if not committee_name:
            return None, None

        name = committee_name.strip()

        # Try each pattern
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Clean up the extracted name
                for suffix_pattern in self.SUFFIXES_TO_REMOVE:
                    extracted = re.sub(suffix_pattern, '', extracted, flags=re.IGNORECASE).strip()

                if extracted:
                    # Split into first/last name
                    parts = extracted.split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name = ' '.join(parts[1:])
                        return first_name, last_name
                    elif len(parts) == 1:
                        return None, parts[0]

        # Fallback: try to split the name directly
        # Remove common prefixes/suffixes
        cleaned = name
        for suffix_pattern in self.SUFFIXES_TO_REMOVE:
            cleaned = re.sub(suffix_pattern, '', cleaned, flags=re.IGNORECASE).strip()

        # Remove common prefixes
        cleaned = re.sub(r'^(Elect|Vote|Committee\s+to\s+Elect|Re-Elect)\s+', '', cleaned, flags=re.IGNORECASE).strip()

        parts = cleaned.split()
        if len(parts) >= 2:
            # Assume first word is first name, rest is last name
            return parts[0], ' '.join(parts[1:])

        return None, None

    def _find_matching_entity(self, first_name, last_name):
        """Find an existing entity matching the name"""
        if not last_name:
            return None

        # Try exact match first
        query = Entity.objects.filter(last_name__iexact=last_name)
        if first_name:
            query = query.filter(first_name__iexact=first_name)

        entities = list(query[:5])
        if entities:
            return entities[0]

        # Try partial match on last name
        query = Entity.objects.filter(last_name__icontains=last_name)
        if first_name:
            query = query.filter(first_name__icontains=first_name)

        entities = list(query[:5])
        if entities:
            return entities[0]

        # Try with first initial only
        if first_name:
            query = Entity.objects.filter(
                last_name__iexact=last_name,
                first_name__istartswith=first_name[0]
            )
            entities = list(query[:5])
            if entities:
                return entities[0]

        return None

    def _create_entity(self, first_name, last_name):
        """Create a new entity for the candidate"""
        from django.db.models import Max

        # Get the next available name_id (Entity uses name_id as primary key, not auto-increment)
        max_id = Entity.objects.aggregate(Max('name_id'))['name_id__max'] or 0
        next_id = max_id + 1

        entity = Entity.objects.create(
            name_id=next_id,
            first_name=first_name.upper() if first_name else '',
            last_name=last_name.upper() if last_name else ''
        )
        return entity

    def _fix_committee(self, comm_data, dry_run=False):
        """Fix a single committee's candidate link"""
        committee_id = comm_data['subject_committee__committee_id']
        comm_first = comm_data['subject_committee__name__first_name'] or ''
        comm_last = comm_data['subject_committee__name__last_name'] or ''
        committee_name = f"{comm_first} {comm_last}".strip()
        total_ie = comm_data['total_ie']
        office = comm_data['subject_committee__candidate_office__name']
        cycle = comm_data['subject_committee__election_cycle__name']

        self.stdout.write(f'\n[{committee_id}] {committee_name} ({cycle})')
        self.stdout.write(f'  Office: {office}, IE: ${total_ie:,.2f}')

        # Extract candidate name
        first_name, last_name = self._extract_candidate_name(committee_name)

        if not last_name:
            self.stdout.write(self.style.WARNING(f'  Could not extract candidate name'))
            return 'failed'

        self.stdout.write(f'  Extracted name: {first_name} {last_name}')

        # Find matching entity
        entity = self._find_matching_entity(first_name, last_name)

        if entity:
            self.stdout.write(f'  Found entity: {entity.first_name} {entity.last_name} (ID: {entity.name_id})')
        else:
            self.stdout.write(f'  No matching entity found, will create new one')

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'  [DRY RUN] Would link candidate'))
            return 'fixed'

        # Apply the fix
        try:
            with transaction.atomic():
                committee = Committee.objects.get(committee_id=committee_id)

                if not entity:
                    entity = self._create_entity(first_name, last_name)
                    self.stdout.write(f'  Created entity: {entity.first_name} {entity.last_name} (ID: {entity.name_id})')

                committee.candidate = entity
                committee.save()

                self.stdout.write(self.style.SUCCESS(f'  FIXED: Linked to {entity.first_name} {entity.last_name}'))
                return 'fixed'

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ERROR: {e}'))
            return 'failed'
