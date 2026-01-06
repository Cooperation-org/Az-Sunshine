"""
Django management command to remove duplicate transactions from the database.

The duplicate bug was caused by import_mdb_corrected.py using Transaction.objects.create()
instead of update_or_create(), resulting in ~522,000 duplicate records.

Usage:
    python manage.py deduplicate_transactions --dry-run  # Preview what will be deleted
    python manage.py deduplicate_transactions            # Actually delete duplicates

Author: Claude Code
Date: 2025-01-03
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from transparency.models import Transaction


class Command(BaseCommand):
    help = 'Remove duplicate transactions from the database (keeps lowest transaction_id)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually deleting'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10000,
            help='Number of records to delete per batch (default: 10000)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        self.stdout.write('=' * 70)
        self.stdout.write('TRANSACTION DEDUPLICATION')
        self.stdout.write('=' * 70)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Step 1: Count total and unique transactions
        self.stdout.write('\nAnalyzing transactions...')

        with connection.cursor() as cursor:
            # Count totals
            cursor.execute('SELECT COUNT(*) FROM "Transactions"')
            total_count = cursor.fetchone()[0]

            # Count duplicates using the natural key
            cursor.execute('''
                SELECT COUNT(*)
                FROM (
                    SELECT committee_id, entity_id, amount, transaction_date, transaction_type_id
                    FROM "Transactions"
                    GROUP BY committee_id, entity_id, amount, transaction_date, transaction_type_id
                    HAVING COUNT(*) > 1
                ) dups
            ''')
            duplicate_groups = cursor.fetchone()[0]

            # Count how many records will be deleted
            cursor.execute('''
                SELECT SUM(cnt - 1)
                FROM (
                    SELECT COUNT(*) as cnt
                    FROM "Transactions"
                    GROUP BY committee_id, entity_id, amount, transaction_date, transaction_type_id
                    HAVING COUNT(*) > 1
                ) dups
            ''')
            duplicates_to_delete = cursor.fetchone()[0] or 0

        self.stdout.write(f'\nStatistics:')
        self.stdout.write(f'  Total transactions:     {total_count:,}')
        self.stdout.write(f'  Duplicate groups:       {duplicate_groups:,}')
        self.stdout.write(f'  Records to delete:      {duplicates_to_delete:,}')
        self.stdout.write(f'  Records after cleanup:  {total_count - duplicates_to_delete:,}')

        if duplicates_to_delete == 0:
            self.stdout.write(self.style.SUCCESS('\nNo duplicates found! Database is clean.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN: Would delete {duplicates_to_delete:,} duplicate records.'
            ))

            # Show some sample duplicates
            self.stdout.write('\nSample duplicate groups (first 5):')
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT
                        committee_id,
                        entity_id,
                        amount,
                        transaction_date,
                        transaction_type_id,
                        COUNT(*) as duplicate_count,
                        array_agg(transaction_id ORDER BY transaction_id) as transaction_ids
                    FROM "Transactions"
                    GROUP BY committee_id, entity_id, amount, transaction_date, transaction_type_id
                    HAVING COUNT(*) > 1
                    ORDER BY COUNT(*) DESC
                    LIMIT 5
                ''')
                for row in cursor.fetchall():
                    self.stdout.write(
                        f'  Committee {row[0]}, Entity {row[1]}, '
                        f'${row[2]}, {row[3]}, Type {row[4]}: '
                        f'{row[5]} duplicates (keeping ID {row[6][0]})'
                    )

            self.stdout.write(self.style.WARNING(
                '\nRun without --dry-run to delete duplicates.'
            ))
            return

        # Step 2: Identify duplicates to delete
        self.stdout.write('\nIdentifying duplicates to delete...')

        with connection.cursor() as cursor:
            # Create temp table with IDs to delete (keeps lowest transaction_id per group)
            cursor.execute('''
                CREATE TEMP TABLE IF NOT EXISTS ids_to_delete AS
                SELECT transaction_id
                FROM (
                    SELECT
                        transaction_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY committee_id, entity_id, amount,
                                         transaction_date, transaction_type_id
                            ORDER BY transaction_id
                        ) as rn
                    FROM "Transactions"
                ) ranked
                WHERE rn > 1
            ''')

            cursor.execute('SELECT COUNT(*) FROM ids_to_delete')
            ids_count = cursor.fetchone()[0]
            self.stdout.write(f'  Found {ids_count:,} duplicate IDs to remove')

            # Step 2a: Clear modifies_transaction references pointing to duplicates
            self.stdout.write('\nClearing modifies_transaction references...')
            cursor.execute('''
                UPDATE "Transactions"
                SET modifies_transaction_id = NULL
                WHERE modifies_transaction_id IN (SELECT transaction_id FROM ids_to_delete)
            ''')
            refs_cleared = cursor.rowcount
            self.stdout.write(f'  Cleared {refs_cleared:,} foreign key references')

        # Step 3: Delete duplicates in batches
        self.stdout.write(f'\nDeleting duplicates in batches of {batch_size:,}...')

        total_deleted = 0
        batch_num = 0

        while True:
            batch_num += 1

            with connection.cursor() as cursor:
                # Delete batch from temp table
                cursor.execute('''
                    DELETE FROM "Transactions"
                    WHERE transaction_id IN (
                        SELECT transaction_id FROM ids_to_delete LIMIT %s
                    )
                ''', [batch_size])

                deleted_count = cursor.rowcount

                total_deleted += deleted_count

                # Also remove from temp table to track progress
                cursor.execute('''
                    DELETE FROM ids_to_delete
                    WHERE ctid IN (
                        SELECT ctid FROM ids_to_delete LIMIT %s
                    )
                ''', [batch_size])

                if deleted_count > 0:
                    self.stdout.write(
                        f'  Batch {batch_num}: Deleted {deleted_count:,} records '
                        f'(Total: {total_deleted:,}/{duplicates_to_delete:,})'
                    )

                if deleted_count < batch_size:
                    break

        # Drop temp table
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS ids_to_delete')

        # Step 4: Verify
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM "Transactions"')
            final_count = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*)
                FROM (
                    SELECT 1
                    FROM "Transactions"
                    GROUP BY committee_id, entity_id, amount, transaction_date, transaction_type_id
                    HAVING COUNT(*) > 1
                ) remaining_dups
            ''')
            remaining_dups = cursor.fetchone()[0]

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('DEDUPLICATION COMPLETE'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'  Total deleted:         {total_deleted:,}')
        self.stdout.write(f'  Records remaining:     {final_count:,}')
        self.stdout.write(f'  Duplicate groups left: {remaining_dups}')

        if remaining_dups == 0:
            self.stdout.write(self.style.SUCCESS('\nAll duplicates successfully removed!'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ {remaining_dups} duplicate groups still exist. Run again to continue.'
            ))
