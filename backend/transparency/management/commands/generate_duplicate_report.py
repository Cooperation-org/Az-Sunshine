"""
Generate a report of potential duplicate records for manual review.
Outputs a CSV file that can be used by editors to identify and merge duplicates.
"""
from django.core.management.base import BaseCommand
from django.db import connection
import csv
from datetime import datetime


class Command(BaseCommand):
    help = 'Generate CSV report of potential duplicate candidates and committees for manual review'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=f'duplicate_review_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            help='Output CSV filename'
        )
        parser.add_argument(
            '--min-occurrences',
            type=int,
            default=2,
            help='Minimum occurrences to be considered a duplicate (default: 2)'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        min_occurrences = options['min_occurrences']

        self.stdout.write(self.style.MIGRATE_HEADING('Generating Duplicate Report...'))

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Type', 'Name', 'Occurrence_Count', 'IDs', 'Offices_Seats',
                'Cities', 'Election_Cycles', 'Recommended_Action', 'Notes'
            ])

            # 1. Duplicate Candidate Names
            self.stdout.write('Finding duplicate candidates...')
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        TRIM(COALESCE(e.first_name, '') || ' ' || COALESCE(e.last_name, '')) as full_name,
                        COUNT(*) as occurrence_count,
                        ARRAY_AGG(DISTINCT c.committee_id) as committee_ids,
                        ARRAY_AGG(DISTINCT c.candidate_office_id::text) as offices,
                        ARRAY_AGG(DISTINCT e.city) as cities,
                        ARRAY_AGG(DISTINCT c.election_cycle_id::text) as cycles
                    FROM "Committees" c
                    JOIN "Names" e ON c.name_id = e.name_id
                    WHERE c.candidate_id IS NOT NULL
                    GROUP BY full_name
                    HAVING COUNT(*) >= %s
                    ORDER BY occurrence_count DESC
                    LIMIT 500
                """, [min_occurrences])

                for row in cursor.fetchall():
                    name, count, ids, offices, cities, cycles = row
                    if not name or name.strip() == '':
                        continue

                    # Determine if same office or different offices
                    unique_offices = set([o for o in offices if o])
                    unique_cities = set([c for c in cities if c])

                    if len(unique_offices) <= 1:
                        action = 'LIKELY_MERGE'
                        notes = 'Same office across cycles - likely same person'
                    elif len(unique_offices) > 1:
                        action = 'REVIEW_NEEDED'
                        notes = f'Multiple offices: {", ".join(str(o) for o in unique_offices)}'
                    else:
                        action = 'REVIEW_NEEDED'
                        notes = ''

                    writer.writerow([
                        'CANDIDATE',
                        name,
                        count,
                        '; '.join(str(i) for i in ids[:10]),  # Limit to first 10 IDs
                        '; '.join(str(o) for o in unique_offices),
                        '; '.join(str(c) for c in unique_cities),
                        '; '.join(str(c) for c in cycles if c),
                        action,
                        notes
                    ])

            candidate_count = cursor.rowcount
            self.stdout.write(f'  Found {candidate_count} duplicate candidate groups')

            # 2. Duplicate Committee Names
            self.stdout.write('Finding duplicate committees...')
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        COALESCE(n.last_name, '') as committee_name,
                        COUNT(*) as occurrence_count,
                        ARRAY_AGG(c.committee_id) as committee_ids,
                        ARRAY_AGG(DISTINCT c.organization_date::text) as org_dates,
                        ARRAY_AGG(DISTINCT c.candidate_id::text) as types
                    FROM "Committees" c
                    JOIN "Names" n ON c.name_id = n.name_id
                    WHERE n.last_name IS NOT NULL AND n.last_name != ''
                    GROUP BY n.last_name
                    HAVING COUNT(*) >= %s
                    ORDER BY occurrence_count DESC
                    LIMIT 500
                """, [min_occurrences])

                for row in cursor.fetchall():
                    name, count, ids, org_dates, types = row

                    # Check if any have negative IDs (synthetic records)
                    negative_ids = [i for i in ids if i < 0]
                    positive_ids = [i for i in ids if i >= 0]

                    if negative_ids and positive_ids:
                        action = 'MERGE_SYNTHETIC'
                        notes = f'{len(negative_ids)} synthetic records, {len(positive_ids)} real records'
                    elif len(positive_ids) > 1:
                        action = 'REVIEW_NEEDED'
                        notes = 'Multiple real committees with same name'
                    else:
                        action = 'SYNTHETIC_ONLY'
                        notes = 'Only synthetic records'

                    writer.writerow([
                        'COMMITTEE',
                        name,
                        count,
                        '; '.join(str(i) for i in ids[:10]),
                        '',  # No office for committees
                        '',  # No cities
                        '',
                        action,
                        notes
                    ])

            committee_count = cursor.rowcount
            self.stdout.write(f'  Found {committee_count} duplicate committee groups')

            # 3. Entity duplicates (donors/individuals)
            self.stdout.write('Finding duplicate entities...')
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) as full_name,
                        COUNT(*) as occurrence_count,
                        (ARRAY_AGG(name_id ORDER BY name_id))[1:10] as entity_ids,
                        ARRAY_AGG(DISTINCT city) as cities,
                        ARRAY_AGG(DISTINCT state) as states
                    FROM "Names"
                    WHERE last_name IS NOT NULL AND last_name != ''
                    GROUP BY full_name
                    HAVING COUNT(*) >= %s
                    ORDER BY occurrence_count DESC
                    LIMIT 1000
                """, [max(min_occurrences, 5)])  # Higher threshold for entities

                for row in cursor.fetchall():
                    name, count, ids, cities, states = row
                    if not name or name.strip() == '':
                        continue

                    unique_cities = set([c for c in cities if c])
                    unique_states = set([s for s in states if s])

                    # If same city/state, likely same person
                    if len(unique_cities) <= 1 and len(unique_states) <= 1:
                        action = 'LIKELY_MERGE'
                        notes = 'Same location across records'
                    elif len(unique_cities) <= 3:
                        action = 'REVIEW_NEEDED'
                        notes = f'Multiple locations: {", ".join(str(c) for c in unique_cities)}'
                    else:
                        action = 'DIFFERENT_PEOPLE'
                        notes = 'Many different locations - likely different people'

                    writer.writerow([
                        'ENTITY',
                        name,
                        count,
                        '; '.join(str(i) for i in ids),
                        '',
                        '; '.join(str(c) for c in unique_cities),
                        '',
                        action,
                        notes
                    ])

            entity_count = cursor.rowcount
            self.stdout.write(f'  Found {entity_count} duplicate entity groups')

        self.stdout.write(self.style.SUCCESS(f'\nReport saved to: {output_file}'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  - Candidate duplicates: {candidate_count}')
        self.stdout.write(f'  - Committee duplicates: {committee_count}')
        self.stdout.write(f'  - Entity duplicates: {entity_count}')
        self.stdout.write(f'\nRecommended actions:')
        self.stdout.write(f'  LIKELY_MERGE: High confidence same person/entity')
        self.stdout.write(f'  MERGE_SYNTHETIC: Synthetic records should be merged with real')
        self.stdout.write(f'  REVIEW_NEEDED: Manual review required')
        self.stdout.write(f'  DIFFERENT_PEOPLE: Likely different people with same name')
