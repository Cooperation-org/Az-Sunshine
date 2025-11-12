"""
Django Management Command: Load SOI data from CSV
Place in: transparency/management/commands/load_soi_csv.py

This allows you to:
1. Scrape on your local machine (where browser works)
2. Upload CSV to server
3. Load into database with this command

Usage:
    python manage.py load_soi_csv data/soi_candidates.csv
    python manage.py load_soi_csv data/soi_candidates.csv --dry-run
"""

import csv
import sys
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
import logging

from transparency.models import CandidateStatementOfInterest, Office

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Load SOI candidate data from CSV file into database'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file containing candidate data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to database'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        
        self.stdout.write('='*70)
        self.stdout.write(self.style.SUCCESS('📊 SOI CSV Loader'))
        self.stdout.write('='*70)
        self.stdout.write(f'Source: {csv_file}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔄 DRY RUN MODE - No changes will be saved'))
        
        self.stdout.write('')
        
        # Load CSV
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                candidates = list(reader)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ File not found: {csv_file}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error reading CSV: {e}'))
            import traceback
            traceback.print_exc()
            return
        
        if not candidates:
            self.stdout.write(self.style.WARNING('⚠️  CSV is empty'))
            return
        
        self.stdout.write(f'Found {len(candidates)} candidates in CSV')
        self.stdout.write('')
        
        # Show sample
        if candidates:
            self.stdout.write('Sample candidate:')
            sample = candidates[0]
            self.stdout.write(f"  Name: {sample.get('name', 'N/A')}")
            self.stdout.write(f"  Office: {sample.get('office', 'N/A')}")
            self.stdout.write(f"  Party: {sample.get('party', 'N/A')}")
            self.stdout.write(f"  Email: {sample.get('email', 'N/A')}")
            self.stdout.write(f"  Phone: {sample.get('phone', 'N/A')}")
            self.stdout.write('')
        
        # Load into database
        stats = self.load_to_database(candidates, dry_run)
        
        # Print results
        self.stdout.write('')
        self.stdout.write('='*70)
        self.stdout.write(self.style.SUCCESS('📊 RESULTS'))
        self.stdout.write('='*70)
        self.stdout.write(self.style.SUCCESS(f"✨ Created: {stats['created']}"))
        self.stdout.write(self.style.WARNING(f"🔄 Updated: {stats['updated']}"))
        self.stdout.write(f"⏭️  Skipped: {stats['skipped']}")
        
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errors: {stats['errors']}"))
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('🔄 DRY RUN - No changes were saved'))
            self.stdout.write('Run without --dry-run to save to database')
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ Data loaded successfully!'))
            
            if stats['created'] > 0:
                self.stdout.write('')
                self.stdout.write('='*70)
                self.stdout.write('📋 NEXT STEPS:')
                self.stdout.write('='*70)
                self.stdout.write(f"1️⃣  {stats['created']} new candidates need contact")
                self.stdout.write('2️⃣  Go to Django Admin: /admin/transparency/candidatestatementofinterest/')
                self.stdout.write('3️⃣  Filter by "Uncontacted"')
                self.stdout.write('4️⃣  Send info packets manually')
                self.stdout.write('5️⃣  Mark as "contacted" after sending')
    
    def load_to_database(self, candidates, dry_run=False):
        """Load candidates into database"""
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        try:
            with transaction.atomic():
                for i, row in enumerate(candidates, 1):
                    try:
                        result = self.process_candidate(row)
                        stats[result] += 1
                        
                        # Show progress every 20 candidates
                        if i % 20 == 0:
                            sys.stdout.write(f'\rProcessed {i}/{len(candidates)} candidates...')
                            sys.stdout.flush()
                        
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"Error processing row {i}: {e}", exc_info=True)
                
                if i % 20 != 0:  # Clear progress line
                    sys.stdout.write(f'\rProcessed {i}/{len(candidates)} candidates...  \n')
                    sys.stdout.flush()
                
                if dry_run:
                    # Rollback transaction in dry run
                    transaction.set_rollback(True)
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Database error: {e}'))
            import traceback
            traceback.print_exc()
        
        return stats
    
    def process_candidate(self, row):
        """Process a single candidate row"""
        name = row.get('name', '').strip()
        office_name = row.get('office', '').strip()
        email = row.get('email', '').strip()
        phone = row.get('phone', '').strip()
        party = row.get('party', '').strip()
        source_url = row.get('source_url', '').strip()
        
        # Validate
        if not name or len(name) < 2:
            logger.debug(f"Skipping invalid name: {name}")
            return 'skipped'
        
        if not office_name or len(office_name) < 2:
            logger.debug(f"Skipping {name} - no valid office")
            return 'skipped'
        
        # Get or create Office
        office, created = Office.objects.get_or_create(
            name=office_name,
            defaults={'office_type': 'STATE'}
        )
        
        if created:
            logger.info(f"Created new office: {office_name}")
        
        # Get or create Candidate SOI
        try:
            soi = CandidateStatementOfInterest.objects.get(
                candidate_name=name,
                office=office
            )
            
            # Update if we have new data
            updated = False
            
            if email and not soi.email:
                soi.email = email
                updated = True
            
            if phone and not soi.phone:
                soi.phone = phone
                updated = True
            
            if party and not soi.party:
                soi.party = party
                updated = True
            
            if source_url and not soi.source_url:
                soi.source_url = source_url
                updated = True
            
            if updated:
                soi.save()
                logger.info(f"Updated: {name}")
                return 'updated'
            else:
                return 'skipped'
            
        except CandidateStatementOfInterest.DoesNotExist:
            # Create new
            CandidateStatementOfInterest.objects.create(
                candidate_name=name,
                office=office,
                email=email if email else None,
                phone=phone if phone else None,
                party=party if party else '',
                source_url=source_url if source_url else '',
                filing_date=datetime.now().date(),
                contact_status='uncontacted',  # Default per Ben's spec
                pledge_received=False
            )
            logger.info(f"Created: {name} for {office_name}")
            return 'created'