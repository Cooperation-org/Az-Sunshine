"""
Merge Duplicate Candidate Entities

This command identifies and merges duplicate candidate entities that represent
the same person across multiple election cycles.

Matching Criteria:
- Same first name + last name (case insensitive)
- Optional: Same city (use --strict flag)

Safety Features:
- Dry run mode by default (use --execute to actually merge)
- Audit log of all merges
- Preserves the entity with most committees/transactions as primary
- Updates all related records (transactions, committees)

Usage:
    python manage.py merge_duplicate_candidates                  # Dry run
    python manage.py merge_duplicate_candidates --execute        # Actually merge
    python manage.py merge_duplicate_candidates --strict         # Require city match
"""

import json
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Q
from transparency.models import Entity, Committee, Transaction


class Command(BaseCommand):
    help = 'Merge duplicate candidate entities that represent the same person'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually perform merges (default is dry run)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of candidates to process (0 = all)'
        )
        parser.add_argument(
            '--candidate',
            type=str,
            help='Process only a specific candidate name (e.g., "ROBERT MEZA")'
        )
        parser.add_argument(
            '--min-entities',
            type=int,
            default=2,
            help='Minimum number of entities to consider as duplicate (default: 2)'
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Require city match for merge (default: merge by name only)'
        )

    def normalize_city(self, city):
        """Normalize city name for comparison"""
        if not city:
            return ''
        return city.upper().strip().replace('.', '').replace(',', '')

    def cities_match(self, city1, city2):
        """Check if two cities are the same or variations"""
        c1 = self.normalize_city(city1)
        c2 = self.normalize_city(city2)

        if not c1 or not c2:
            return False

        # Exact match
        if c1 == c2:
            return True

        # Known variations
        variations = {
            'SCOTTSDALE': ['SCOTTSDALE'],
            'PHOENIX': ['PHOENIX', 'PHX'],
            'TUCSON': ['TUCSON'],
            'MESA': ['MESA'],
            'CHANDLER': ['CHANDLER'],
            'GILBERT': ['GILBERT'],
            'TEMPE': ['TEMPE'],
            'GLENDALE': ['GLENDALE'],
            'PRESCOTT': ['PRESCOTT'],
            'FLAGSTAFF': ['FLAGSTAFF'],
            'SIERRA VISTA': ['SIERRA VISTA', 'SIERRAVISTA'],
            'ORO VALLEY': ['ORO VALLEY', 'OROVALLEY'],
            'SUN CITY WEST': ['SUN CITY WEST', 'SUNCITYWEST'],
            'SKULL VALLEY': ['SKULL VALLEY', 'SKULLVALLEY'],
            'APACHE JUNCTION': ['APACHE JUNCTION', 'APACHEJUNCTION'],
        }

        for canonical, vars in variations.items():
            if c1 in vars and c2 in vars:
                return True

        return False

    def get_entity_transaction_count(self, entity_id):
        """Get count of transactions for an entity"""
        return Transaction.objects.filter(entity_id=entity_id).count()

    def get_entity_committee_count(self, entity_id):
        """Get count of committees for an entity"""
        return Committee.objects.filter(candidate_id=entity_id).count()

    def handle(self, *args, **options):
        execute = options['execute']
        limit = options['limit']
        candidate_filter = options.get('candidate')
        min_entities = options['min_entities']
        strict = options.get('strict', False)

        mode = "EXECUTE MODE" if execute else "DRY RUN MODE"
        match_mode = "STRICT (city match required)" if strict else "NAME ONLY"
        self.stdout.write(self.style.WARNING(f'\n=== DUPLICATE CANDIDATE MERGER ({mode}) ==='))
        self.stdout.write(self.style.WARNING(f'Matching mode: {match_mode}\n'))

        # Find all candidate committees grouped by entity
        self.stdout.write('Analyzing candidate entities...')

        candidate_committees = Committee.objects.filter(
            candidate__isnull=False
        ).select_related('candidate', 'candidate_office').values(
            'candidate__name_id',
            'candidate__first_name',
            'candidate__last_name',
            'candidate__middle_name',
            'candidate__city',
            'candidate__state',
            'candidate_office__name',
            'committee_id'
        )

        # Group by normalized name
        name_groups = defaultdict(list)
        for c in candidate_committees:
            first = (c['candidate__first_name'] or '').strip().upper()
            last = (c['candidate__last_name'] or '').strip().upper()
            if first and last:
                key = f'{first} {last}'
                name_groups[key].append({
                    'entity_id': c['candidate__name_id'],
                    'first_name': c['candidate__first_name'],
                    'last_name': c['candidate__last_name'],
                    'middle_name': c['candidate__middle_name'],
                    'city': c['candidate__city'],
                    'state': c['candidate__state'],
                    'office': c['candidate_office__name'],
                    'committee_id': c['committee_id']
                })

        # Find candidates with multiple entities
        duplicates = []
        for name, entries in name_groups.items():
            entity_ids = set(e['entity_id'] for e in entries)
            if len(entity_ids) >= min_entities:
                if candidate_filter and name != candidate_filter.upper():
                    continue
                duplicates.append({
                    'name': name,
                    'entity_count': len(entity_ids),
                    'entries': entries
                })

        # Sort by entity count
        duplicates.sort(key=lambda x: -x['entity_count'])

        if limit > 0:
            duplicates = duplicates[:limit]

        self.stdout.write(f'Found {len(duplicates)} candidates with potential duplicates\n')

        total_merged = 0
        merge_log = []

        for dup in duplicates:
            name = dup['name']
            entries = dup['entries']

            # Group entries by entity_id
            entities_by_id = defaultdict(list)
            for e in entries:
                entities_by_id[e['entity_id']].append(e)

            # Get all unique cities for this candidate
            entity_cities = {}
            for eid, ent_entries in entities_by_id.items():
                cities = set(e['city'] for e in ent_entries if e['city'])
                entity_cities[eid] = list(cities)

            # Determine merge groups based on mode
            if strict:
                # STRICT MODE: Require city match
                merge_groups = []
                processed = set()

                for eid1, cities1 in entity_cities.items():
                    if eid1 in processed:
                        continue

                    group = {eid1}
                    processed.add(eid1)

                    for eid2, cities2 in entity_cities.items():
                        if eid2 in processed:
                            continue

                        # Check if cities match
                        should_merge = False
                        for c1 in cities1:
                            for c2 in cities2:
                                if self.cities_match(c1, c2):
                                    should_merge = True
                                    break
                            if should_merge:
                                break

                        if should_merge:
                            group.add(eid2)
                            processed.add(eid2)

                    if len(group) > 1:
                        merge_groups.append(group)
            else:
                # NAME ONLY MODE: Merge all entities with same name
                merge_groups = [set(entities_by_id.keys())]

            # Process merge groups
            for group in merge_groups:
                if len(group) < 2:
                    continue
                # Get transaction counts for each entity
                entity_scores = []
                for eid in group:
                    tx_count = self.get_entity_transaction_count(eid)
                    cm_count = self.get_entity_committee_count(eid)
                    entity_scores.append({
                        'id': eid,
                        'tx_count': tx_count,
                        'cm_count': cm_count,
                        'score': tx_count + cm_count * 10,
                        'cities': entity_cities.get(eid, [])
                    })

                # Sort by score descending - highest becomes primary
                entity_scores.sort(key=lambda x: -x['score'])
                primary = entity_scores[0]
                duplicates_to_merge = entity_scores[1:]

                if not duplicates_to_merge:
                    continue

                self.stdout.write(f'\n{name}:')
                self.stdout.write(f'  Primary Entity {primary["id"]}: {primary["cities"]} '
                                f'(tx: {primary["tx_count"]}, committees: {primary["cm_count"]})')

                for d in duplicates_to_merge:
                    self.stdout.write(f'  -> Merge Entity {d["id"]}: {d["cities"]} '
                                    f'(tx: {d["tx_count"]}, committees: {d["cm_count"]})')

                if execute:
                    try:
                        with transaction.atomic():
                            primary_entity = Entity.objects.get(name_id=primary['id'])

                            for d in duplicates_to_merge:
                                dup_entity = Entity.objects.get(name_id=d['id'])

                                # Move transactions
                                tx_moved = Transaction.objects.filter(entity=dup_entity).update(entity=primary_entity)

                                # Move committees (candidate reference)
                                cm_moved = Committee.objects.filter(candidate=dup_entity).update(candidate=primary_entity)

                                # Mark duplicate as merged
                                dup_entity.first_name = f"[MERGED->{primary['id']}] {dup_entity.first_name or ''}"
                                dup_entity.save()

                                merge_log.append({
                                    'name': name,
                                    'primary_id': primary['id'],
                                    'merged_id': d['id'],
                                    'transactions_moved': tx_moved,
                                    'committees_moved': cm_moved
                                })

                                total_merged += 1

                        self.stdout.write(self.style.SUCCESS(f'  Merged successfully'))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))
                else:
                    total_merged += len(duplicates_to_merge)

        self.stdout.write(f'\n{"=" * 50}')
        self.stdout.write(f'Total entities {"merged" if execute else "would be merged"}: {total_merged}')

        if execute and merge_log:
            # Save audit log
            log_file = '/tmp/candidate_merge_log.json'
            with open(log_file, 'w') as f:
                json.dump(merge_log, f, indent=2)
            self.stdout.write(f'Audit log saved to: {log_file}')

        if not execute:
            self.stdout.write(self.style.WARNING('\nThis was a DRY RUN. Use --execute to actually merge.'))
