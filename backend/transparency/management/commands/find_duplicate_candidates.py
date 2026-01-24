"""
Find potential duplicate candidates for manual review.

This script identifies candidates with similar names who may be the same person
running for different offices or appearing multiple times in the database.

Usage:
    python manage.py find_duplicate_candidates
    python manage.py find_duplicate_candidates --output candidates_duplicates.json
"""

import json
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Count
from transparency.models import Committee, Entity


class Command(BaseCommand):
    help = 'Find potential duplicate candidates for manual review'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='duplicate_candidates.json',
            help='Output file path (default: duplicate_candidates.json)'
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=2,
            help='Minimum occurrences to flag as potential duplicate (default: 2)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        threshold = options['threshold']

        self.stdout.write(self.style.SUCCESS('Searching for potential duplicate candidates...'))

        # Get all candidate committees with their names
        candidates = Committee.objects.filter(
            candidate__isnull=False
        ).select_related(
            'candidate', 'candidate_office', 'candidate_party', 'election_cycle', 'name'
        )

        # Group by normalized name (first_name + last_name, lowercased)
        name_groups = defaultdict(list)

        for c in candidates:
            candidate_entity = c.candidate or c.name
            if not candidate_entity:
                continue

            first_name = (candidate_entity.first_name or '').strip().lower()
            last_name = (candidate_entity.last_name or '').strip().lower()

            # Skip if no name
            if not last_name and not first_name:
                continue

            # Normalize: remove common suffixes, titles
            last_name = last_name.replace('jr', '').replace('sr', '').replace('iii', '').replace('ii', '').strip()

            # Create normalized key
            normalized_key = f"{first_name} {last_name}".strip()

            if normalized_key:
                name_groups[normalized_key].append({
                    'committee_id': c.committee_id,
                    'full_name': candidate_entity.full_name if hasattr(candidate_entity, 'full_name') else f"{first_name} {last_name}",
                    'first_name': candidate_entity.first_name,
                    'last_name': candidate_entity.last_name,
                    'office': c.candidate_office.name if c.candidate_office else 'Unknown',
                    'party': c.candidate_party.name if c.candidate_party else 'Unknown',
                    'cycle': c.election_cycle.name if c.election_cycle else 'Unknown',
                    'entity_id': candidate_entity.name_id if hasattr(candidate_entity, 'name_id') else None
                })

        # Filter to groups with potential duplicates
        duplicates = {
            name: entries
            for name, entries in name_groups.items()
            if len(entries) >= threshold
        }

        # Sort by number of occurrences (descending)
        sorted_duplicates = dict(
            sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
        )

        # Generate report
        report = {
            'summary': {
                'total_candidates': candidates.count(),
                'potential_duplicate_names': len(sorted_duplicates),
                'total_duplicate_entries': sum(len(v) for v in sorted_duplicates.values()),
                'threshold': threshold
            },
            'duplicates': []
        }

        for normalized_name, entries in sorted_duplicates.items():
            # Check if entries have different entity_ids (true duplicates)
            unique_entity_ids = set(e['entity_id'] for e in entries if e['entity_id'])
            unique_offices = set(e['office'] for e in entries)

            duplicate_entry = {
                'normalized_name': normalized_name,
                'occurrences': len(entries),
                'unique_entity_ids': len(unique_entity_ids),
                'unique_offices': len(unique_offices),
                'likely_duplicate': len(unique_entity_ids) > 1,  # Multiple entity IDs = likely duplicate
                'same_name_different_offices': len(unique_offices) > 1,
                'entries': entries
            }
            report['duplicates'].append(duplicate_entry)

        # Write to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        self.stdout.write(self.style.SUCCESS(f'\nDuplicate Candidates Report'))
        self.stdout.write(f'=' * 50)
        self.stdout.write(f"Total candidates analyzed: {report['summary']['total_candidates']}")
        self.stdout.write(f"Potential duplicate names: {report['summary']['potential_duplicate_names']}")
        self.stdout.write(f"Total duplicate entries: {report['summary']['total_duplicate_entries']}")
        self.stdout.write('')

        # Show top 10 duplicates
        self.stdout.write(self.style.WARNING('Top 10 Potential Duplicates:'))
        for i, dup in enumerate(report['duplicates'][:10], 1):
            likely = " [LIKELY DUPLICATE]" if dup['likely_duplicate'] else ""
            diff_offices = " [DIFFERENT OFFICES]" if dup['same_name_different_offices'] else ""
            self.stdout.write(
                f"  {i}. {dup['normalized_name']} - {dup['occurrences']} occurrences{likely}{diff_offices}"
            )
            for entry in dup['entries'][:3]:
                self.stdout.write(f"      - {entry['office']} ({entry['cycle']}) - {entry['party']}")
            if len(dup['entries']) > 3:
                self.stdout.write(f"      ... and {len(dup['entries']) - 3} more")

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Full report saved to: {output_file}'))
        self.stdout.write('Review this file to identify candidates that should be merged.')
