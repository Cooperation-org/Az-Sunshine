"""
Fix missing subject_committee_id in IE transactions.

The issue: SubjectCommitteeID in the MDB is a NameID (pointing to Names/Entity table),
but the import script tried to map it to Committee records. Many IE targets are
"Legacy Names Claimed as Committees" entities that don't have Committee records.

This script:
1. Creates minimal Committee records for Legacy Names entities that are IE targets
2. Re-reads the MDB to get original SubjectCommitteeID values
3. Updates transactions to link to the correct subject_committee
"""

import os
import subprocess
import csv
import io
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from transparency.models import Transaction, Committee, Entity, EntityType


class Command(BaseCommand):
    help = 'Fix missing subject_committee_id in IE transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mdb-file',
            default='/home/deploy/2025 1020 CFS_Export_PRR.mdb',
            help='Path to the MDB file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for updates'
        )

    def handle(self, *args, **options):
        mdb_file = options['mdb_file']
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        if not os.path.exists(mdb_file):
            self.stderr.write(f"MDB file not found: {mdb_file}")
            return

        self.stdout.write("=" * 60)
        self.stdout.write("Fix Missing subject_committee_id in IE Transactions")
        self.stdout.write("=" * 60)

        # Step 1: Build NameID -> CommitteeID mapping from existing committees
        self.stdout.write("\n[Step 1] Building NameID -> CommitteeID mapping...")
        name_to_committee = {}
        for c in Committee.objects.all():
            if c.name_id:
                name_to_committee[c.name_id] = c.committee_id
        self.stdout.write(f"  Found {len(name_to_committee):,} existing committee mappings")

        # Step 2: Find Legacy Names entity type
        legacy_type = EntityType.objects.filter(name__icontains='Legacy Names').first()
        if not legacy_type:
            self.stderr.write("Could not find 'Legacy Names Claimed as Committees' entity type")
            return
        self.stdout.write(f"  Legacy entity type ID: {legacy_type.entity_type_id}")

        # Step 3: Export transactions from MDB and collect SubjectCommitteeIDs
        # Use streaming to avoid loading entire file into memory
        self.stdout.write("\n[Step 2] Reading SubjectCommitteeIDs from MDB (streaming)...")
        self.stdout.write("  This may take several minutes for large files...")

        # Collect transaction_id -> subject_committee_name_id mappings
        subject_mappings = {}
        subject_name_ids = set()
        ie_types = {'215', '217', '33', '34', '223', '225', '76', '243', '274'}
        row_count = 0

        try:
            # Use Popen for streaming instead of run() which loads everything into memory
            process = subprocess.Popen(
                ['mdb-export', mdb_file, 'Transactions'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Read header line first
            header_line = process.stdout.readline()
            if not header_line:
                self.stderr.write("Failed to read header from MDB export")
                return

            headers = header_line.strip().split(',')
            # Find column indices
            try:
                txn_id_idx = headers.index('TransactionID')
                type_idx = headers.index('TransactionTypeID')
                subject_idx = headers.index('SubjectCommitteeID')
            except ValueError as e:
                self.stderr.write(f"Missing expected column: {e}")
                return

            # Stream and process each line
            for line in process.stdout:
                row_count += 1
                if row_count % 500000 == 0:
                    self.stdout.write(f"  Processed {row_count:,} rows...")

                # Parse CSV line (simple split - may need improvement for quoted fields)
                parts = line.strip().split(',')
                if len(parts) <= max(txn_id_idx, type_idx, subject_idx):
                    continue

                txn_type = parts[type_idx]
                subject_id_str = parts[subject_idx].strip().strip('"')

                if subject_id_str and txn_type in ie_types:
                    try:
                        subject_name_id = int(subject_id_str)
                        transaction_id = int(parts[txn_id_idx])
                        subject_mappings[transaction_id] = subject_name_id
                        subject_name_ids.add(subject_name_id)
                    except (ValueError, TypeError):
                        pass

            process.wait()
            if process.returncode != 0:
                stderr = process.stderr.read()
                self.stderr.write(f"mdb-export failed: {stderr}")
                return

        except Exception as e:
            self.stderr.write(f"Error reading MDB: {e}")
            return

        self.stdout.write(f"  Total rows in MDB: {row_count:,}")
        self.stdout.write(f"  IE transactions with SubjectCommitteeID: {len(subject_mappings):,}")
        self.stdout.write(f"  Unique SubjectCommitteeIDs: {len(subject_name_ids):,}")

        # Step 4: Find SubjectCommitteeIDs that need new Committee records
        self.stdout.write("\n[Step 3] Identifying missing committee mappings...")
        missing_name_ids = subject_name_ids - set(name_to_committee.keys())
        self.stdout.write(f"  SubjectCommitteeIDs already mapped to committees: {len(subject_name_ids) - len(missing_name_ids):,}")
        self.stdout.write(f"  SubjectCommitteeIDs needing new committees: {len(missing_name_ids):,}")

        # Step 5: Create Committee records for missing entities
        # Include not just Legacy Names but also other candidate/committee entity types
        candidate_type_ids = [2, 10, 11, 12, 15, 47]  # Legacy, Candidate types, Support/Oppose, Non-AZ Candidate

        if missing_name_ids and not dry_run:
            self.stdout.write("\n[Step 4] Creating Committee records for missing entities...")

            # Get entities for these name_ids that are committee-like types
            target_entities = Entity.objects.filter(
                name_id__in=missing_name_ids,
                entity_type_id__in=candidate_type_ids
            )
            self.stdout.write(f"  Found {target_entities.count()} eligible entities")

            created_count = 0
            # Use negative committee_ids for legacy committees to avoid conflicts
            # Start from -1 and go down
            existing_negative = Committee.objects.filter(committee_id__lt=0).order_by('committee_id').first()
            next_negative_id = (existing_negative.committee_id - 1) if existing_negative else -1

            with db_transaction.atomic():
                for entity in target_entities:
                    # Check if committee already exists for this name_id
                    if entity.name_id in name_to_committee:
                        continue

                    # Create minimal committee record
                    Committee.objects.create(
                        committee_id=next_negative_id,
                        name_id=entity.name_id,
                        is_incumbent=False,
                        benefits_ballot_measure=False
                    )
                    name_to_committee[entity.name_id] = next_negative_id
                    next_negative_id -= 1
                    created_count += 1

                    if created_count % 100 == 0:
                        self.stdout.write(f"  Created {created_count} committee records...")

            self.stdout.write(f"  Created {created_count} new Committee records for Legacy Names")
        elif dry_run and missing_name_ids:
            self.stdout.write(f"  [DRY RUN] Would create committees for {len(missing_name_ids)} Legacy Names")

        # Step 6: Update transactions with correct subject_committee
        self.stdout.write("\n[Step 5] Updating transactions with subject_committee...")

        updated_count = 0
        skipped_count = 0
        not_found_count = 0

        # Get current state of transactions
        transaction_ids = list(subject_mappings.keys())

        # Process in batches
        for i in range(0, len(transaction_ids), batch_size):
            batch_ids = transaction_ids[i:i + batch_size]
            transactions = Transaction.objects.filter(transaction_id__in=batch_ids)

            updates = []
            for txn in transactions:
                subject_name_id = subject_mappings.get(txn.transaction_id)
                if not subject_name_id:
                    continue

                committee_id = name_to_committee.get(subject_name_id)
                if not committee_id:
                    not_found_count += 1
                    continue

                if txn.subject_committee_id == committee_id:
                    skipped_count += 1
                    continue

                txn.subject_committee_id = committee_id
                updates.append(txn)

            if updates and not dry_run:
                Transaction.objects.bulk_update(updates, ['subject_committee_id'])
                updated_count += len(updates)

                if updated_count % 10000 == 0:
                    self.stdout.write(f"  Updated {updated_count:,} transactions...")
            elif dry_run:
                updated_count += len(updates)

        self.stdout.write(f"\n{'[DRY RUN] Would update' if dry_run else 'Updated'}: {updated_count:,} transactions")
        self.stdout.write(f"Already correct: {skipped_count:,}")
        self.stdout.write(f"SubjectCommitteeID not mappable: {not_found_count:,}")

        # Step 7: Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 60)

        # Check final state
        ie_types_int = [215, 217, 33, 34, 223, 225, 76, 243, 274]
        total_ie = Transaction.objects.filter(transaction_type_id__in=ie_types_int).count()
        with_subject = Transaction.objects.filter(
            transaction_type_id__in=ie_types_int,
            subject_committee__isnull=False
        ).count()

        self.stdout.write(f"Total IE transactions: {total_ie:,}")
        self.stdout.write(f"With subject_committee: {with_subject:,}")
        self.stdout.write(f"Coverage: {with_subject/total_ie*100:.1f}%")

        self.stdout.write("\nDone!")
