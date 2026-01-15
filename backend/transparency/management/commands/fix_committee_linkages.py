"""
Fix Committee Office/Cycle Linkages for IE Spending Reports

This management command fixes 1107 committees that are missing candidate_office data,
causing $62.5M in IE spending to be excluded from reports. These committees have
negative IDs and were imported from MDB files.

The command:
1. Parses committee names to determine the office they're associated with
2. Determines the election cycle from transaction dates
3. Logs all changes to a file for audit purposes
4. Only applies changes when run with --apply flag (DRY RUN by default)

Usage:
    python manage.py fix_committee_linkages              # Dry run - show what would change
    python manage.py fix_committee_linkages --apply      # Apply the changes
    python manage.py fix_committee_linkages --verbose    # Show detailed output

Author: Management script for Arizona Sunshine Transparency Project
"""

import re
import logging
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum, Min, Max, Count
from django.db.models.functions import Abs
from django.utils import timezone

from transparency.models import Committee, Transaction, Office, Cycle


# Configure logging
LOG_FILE = '/opt/az_sunshine/backend/committee_linkage_fixes.log'


class Command(BaseCommand):
    help = 'Fix committees with IE spending but missing candidate_office/election_cycle'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.office_cache = {}
        self.cycle_cache = {}
        self.stats = {
            'total_processed': 0,
            'fixed_office': 0,
            'fixed_cycle': 0,
            'skipped_unclear': 0,
            'skipped_no_transactions': 0,
            'ie_amount_before': Decimal('0'),
            'ie_amount_after': Decimal('0'),
        }
        self.changes = []
        self.skipped = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually apply the fixes (default is dry-run mode)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each committee',
        )
        parser.add_argument(
            '--committee-id',
            type=int,
            help='Process only a specific committee ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of committees to process',
        )

    def setup_logging(self):
        """Setup file logging for audit trail."""
        self.file_logger = logging.getLogger('committee_linkages')
        self.file_logger.setLevel(logging.INFO)

        # Remove existing handlers
        self.file_logger.handlers = []

        # Add file handler
        fh = logging.FileHandler(LOG_FILE)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.file_logger.addHandler(fh)

    def load_office_cache(self):
        """Load all offices into cache for fast lookup."""
        for office in Office.objects.all():
            self.office_cache[office.office_id] = office
            # Also index by name for pattern matching
            self.office_cache[office.name.upper()] = office

    def load_cycle_cache(self):
        """Load all cycles into cache for fast lookup."""
        for cycle in Cycle.objects.all():
            if cycle.name:  # Skip cycles with empty names
                self.cycle_cache[cycle.name] = cycle
                self.cycle_cache[cycle.cycle_id] = cycle

    def parse_district_number(self, text):
        """
        Extract district number from committee name.
        Handles formats like: "District 17", "District No. 17", "D17", "SD17", "HD17", "LD 17",
        "Senator 24", "Senate District 5", etc.

        IMPORTANT: Filters out 4-digit numbers which are likely years (e.g., "SENATE 2008").
        """
        patterns = [
            # Most specific patterns first
            r'District\s*(?:No\.?\s*)?(\d{1,2})\b',   # "District 17", "District No. 17"
            r'(?:SD|HD|LD)\s*[-]?\s*(\d{1,2})\b',     # "SD 17", "HD 17", "LD 17"
            r'Dist(?:rict)?\s*(\d{1,2})\b',           # "Dist 17"
            r'#\s*(\d{1,2})\b',                       # "#17"
            r'\bSENATOR\s+(\d{1,2})\b',               # "Senator 24"
            r'\bSENATE\s+(\d{1,2})\b',                # "Senate 24" (NOT "Senate 2008")
            r'\bREP(?:RESENTATIVE)?\s+(\d{1,2})\b',   # "Rep 24"
            r'\bHOUSE\s+(\d{1,2})\b',                 # "House 24"
            r'\b(\d{1,2})\s*(?:STATE\s+)?(?:SENATE|SENATOR)\b',  # "24 Senate"
            r'\b(\d{1,2})\s*(?:STATE\s+)?(?:HOUSE|REP)\b',       # "24 House"
            r'(?:SENATE|SENATOR)[/\-](\d{1,2})\b',    # "Senate/12", "Senate-12"
            r'(?:HOUSE|REP)[/\-](\d{1,2})\b',         # "House/12", "House-12"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                # Valid Arizona legislative districts are 1-30
                if 1 <= num <= 30:
                    return num
        return None

    def determine_office(self, committee_name):
        """
        Parse committee name to determine the office.
        Returns (office, reasoning) or (None, reason_skipped)

        IMPORTANT: Only returns an office if the name clearly indicates one.
        Ambiguous cases are skipped with explanation.
        """
        if not committee_name:
            return None, "SKIPPED - No committee name"

        name_upper = committee_name.upper()

        # Statewide offices (check first as they're most specific)
        if 'GOVERNOR' in name_upper or re.search(r'\bFOR GOV\b', name_upper):
            return self.office_cache.get('GOVERNOR'), "Name contains 'Governor'"

        if 'ATTORNEY GENERAL' in name_upper or re.search(r'\bFOR AG\b', name_upper):
            return self.office_cache.get('ATTORNEY GENERAL'), "Name contains 'Attorney General'"

        if 'SECRETARY OF STATE' in name_upper or re.search(r'\bFOR SOS\b', name_upper):
            return self.office_cache.get('SECRETARY OF STATE'), "Name contains 'Secretary of State'"

        if 'CORPORATION COMMISSION' in name_upper or 'CORP COMM' in name_upper:
            return self.office_cache.get('CORPORATION COMMISSIONER'), "Name contains 'Corporation Commission'"

        if 'TREASURER' in name_upper and 'STATE' in name_upper:
            return self.office_cache.get('STATE TREASURER'), "Name contains 'State Treasurer'"

        if 'SUPERINTENDENT' in name_upper:
            return self.office_cache.get('SUPERINTENDENT OF PUBLIC INSTRUCTION'), "Name contains 'Superintendent'"

        if 'MINE INSPECTOR' in name_upper:
            return self.office_cache.get('STATE MINE INSPECTOR'), "Name contains 'Mine Inspector'"

        # Legislative offices - need district number
        district = self.parse_district_number(committee_name)

        # Check for Senate indicators
        is_senate = (
            'SENATOR' in name_upper or
            'SENATE' in name_upper or
            re.search(r'\bSD\s*[-]?\s*\d+', name_upper)
        )

        # Check for House/Representative indicators
        is_house = (
            'REPRESENTATIVE' in name_upper or
            'HOUSE' in name_upper or
            re.search(r'\bHD\s*[-]?\s*\d+', name_upper)
        )

        # Check for generic LD (Legislative District) without Senate/House indicator
        is_ld_only = (
            re.search(r'\bLD\s*[-]?\s*\d+', name_upper) and
            not is_senate and
            not is_house
        )

        if is_senate and district:
            if 1 <= district <= 30:
                office_name = f"STATE SENATOR - DISTRICT NO. {district}"
                office = self.office_cache.get(office_name)
                if office:
                    return office, f"Senate candidate, District {district}"
                # Try alternative format
                for key, val in self.office_cache.items():
                    if isinstance(key, str) and 'SENATOR' in key and f" {district}" in key:
                        return val, f"Senate candidate, District {district}"
            return None, f"SKIPPED - Invalid senate district {district}"

        # Senate indicator but no district found
        if is_senate and not district:
            return None, f"SKIPPED - Senate candidate but no district number found"

        if is_house and district:
            if 1 <= district <= 30:
                # Try both formats for House districts
                office_name = f"STATE REPRESENTATIVE - DISTRICT NO. {district}"
                office = self.office_cache.get(office_name)
                if office:
                    return office, f"House candidate, District {district}"
                # Try alternative format
                office_name = f"STATE REPRESENTATIVE - DISTRICT {district}"
                office = self.office_cache.get(office_name)
                if office:
                    return office, f"House candidate, District {district}"
                # Search through cache
                for key, val in self.office_cache.items():
                    if isinstance(key, str) and 'REPRESENTATIVE' in key and f" {district}" in key:
                        return val, f"House candidate, District {district}"
            return None, f"SKIPPED - Invalid house district {district}"

        # House indicator but no district found
        if is_house and not district:
            return None, f"SKIPPED - House candidate but no district number found"

        # LD without Senate/House indicator - ambiguous
        if is_ld_only and district:
            return None, f"SKIPPED - LD {district} without Senate/House indicator - ambiguous"

        # US Congress
        if 'CONGRESS' in name_upper or re.search(r'\bCD\s*[-]?\s*\d+', name_upper):
            cd_match = re.search(r'(?:CD|CONGRESSIONAL DISTRICT)\s*[-]?\s*(\d+)', name_upper)
            if cd_match:
                cd = int(cd_match.group(1))
                office_name = f"U.S. REPRESENTATIVE IN CONGRESS - DISTRICT NO. {cd}"
                office = self.office_cache.get(office_name)
                if office:
                    return office, f"US Congress, District {cd}"
            return None, f"SKIPPED - Congress reference but couldn't determine district"

        # Check for other indicators that might help
        # Party committees, PACs, ballot measures - not candidate offices
        if any(term in name_upper for term in [
            'PARTY', 'PAC', 'PROPOSITION', 'PROP ', 'BALLOT', 'MEASURE',
            'OPPOSES', 'SUPPORTS', 'YES ON', 'NO ON', 'POLITICAL ACTION',
            'DEMOCRATIC', 'REPUBLICAN', 'GREEN PARTY', 'LIBERTARIAN',
            'FEDERATION', 'COMMITTEE', 'ASSOCIATION', 'UNION', 'COUNCIL'
        ]):
            return None, "SKIPPED - Appears to be party/PAC/ballot measure, not candidate"

        # City/County offices - different jurisdiction
        if any(term in name_upper for term in [
            'CITY COUNCIL', 'MAYOR', 'SUPERVISOR', 'COUNTY', 'SCHOOL BOARD',
            'TEMPE', 'PHOENIX', 'TUCSON', 'MESA', 'SCOTTSDALE', 'CHANDLER',
            'GILBERT', 'GLENDALE', 'PEORIA', 'SURPRISE', 'FLAGSTAFF'
        ]):
            return None, "SKIPPED - Appears to be local/city office, not state office"

        return None, "SKIPPED - Cannot determine office from name"

    def determine_cycle(self, committee):
        """
        Determine the election cycle based on transaction dates.
        Returns (cycle, reasoning) or (None, reason_skipped)
        """
        # Get transaction date range for IE spending targeting this committee
        date_range = Transaction.objects.filter(
            subject_committee=committee,
            deleted=False
        ).aggregate(
            min_date=Min('transaction_date'),
            max_date=Max('transaction_date')
        )

        min_date = date_range['min_date']
        max_date = date_range['max_date']

        if not min_date or not max_date:
            return None, "SKIPPED - No transaction dates found"

        # Convert to timezone-aware datetime for comparison
        min_dt = timezone.make_aware(datetime.combine(min_date, datetime.min.time()))
        max_dt = timezone.make_aware(datetime.combine(max_date, datetime.max.time()))

        # Find cycles that overlap with the transaction date range
        # Prefer the cycle where most transactions fall
        overlapping_cycles = Cycle.objects.filter(
            begin_date__lte=max_dt,
            end_date__gte=min_dt,
            name__regex=r'^\d{4}$'  # Only cycles with year names
        ).order_by('-begin_date')

        if not overlapping_cycles.exists():
            return None, f"SKIPPED - No cycle found for dates {min_date} to {max_date}"

        # If only one cycle overlaps, use it
        if overlapping_cycles.count() == 1:
            cycle = overlapping_cycles.first()
            return cycle, f"Single cycle {cycle.name} covers dates {min_date} to {max_date}"

        # If multiple cycles, use the one where most activity falls
        # For simplicity, use the max_date to determine the primary cycle
        for cycle in overlapping_cycles:
            if cycle.begin_date <= max_dt <= cycle.end_date:
                return cycle, f"Latest transaction ({max_date}) falls in cycle {cycle.name}"

        # Fallback to most recent overlapping cycle
        cycle = overlapping_cycles.first()
        return cycle, f"Using most recent overlapping cycle {cycle.name}"

    def get_ie_amount(self, committee):
        """Get total IE spending targeting this committee."""
        result = Transaction.objects.filter(
            subject_committee=committee,
            deleted=False,
            transaction_type__income_expense_neutral=2
        ).aggregate(total=Sum(Abs('amount')))
        return result['total'] or Decimal('0')

    def process_committee(self, committee, apply=False, verbose=False):
        """
        Process a single committee to fix office and cycle linkages.
        Returns True if any changes were made/would be made.
        """
        self.stats['total_processed'] += 1

        committee_name = committee.name.last_name if committee.name else None
        ie_amount = self.get_ie_amount(committee)

        if ie_amount == 0:
            self.stats['skipped_no_transactions'] += 1
            return False

        # Determine office from name
        office, office_reason = self.determine_office(committee_name)

        # Determine cycle from transaction dates
        cycle, cycle_reason = self.determine_cycle(committee)

        # Record change info
        change_record = {
            'committee_id': committee.committee_id,
            'committee_name': committee_name,
            'ie_amount': float(ie_amount),
            'original_office_id': committee.candidate_office_id,
            'original_cycle_id': committee.election_cycle_id,
            'new_office_id': office.office_id if office else None,
            'new_office_name': office.name if office else None,
            'office_reason': office_reason,
            'new_cycle_id': cycle.cycle_id if cycle else None,
            'new_cycle_name': cycle.name if cycle else None,
            'cycle_reason': cycle_reason,
        }

        # Check if this is a skip case
        if not office and 'SKIPPED' in office_reason:
            self.stats['skipped_unclear'] += 1
            self.skipped.append(change_record)

            if verbose:
                self.stdout.write(self.style.WARNING(
                    f"SKIP: {committee.committee_id} - {committee_name}"
                ))
                self.stdout.write(f"  Reason: {office_reason}")
                self.stdout.write(f"  IE Amount: ${ie_amount:,.2f}")

            self.file_logger.info(
                f"SKIPPED | ID: {committee.committee_id} | "
                f"Name: {committee_name} | "
                f"IE: ${ie_amount:,.2f} | "
                f"Reason: {office_reason}"
            )
            return False

        # We have at least an office to set
        changes_made = False

        if office and committee.candidate_office_id != office.office_id:
            if apply:
                committee.candidate_office = office
                changes_made = True
            self.stats['fixed_office'] += 1
            self.stats['ie_amount_after'] += ie_amount

        if cycle and committee.election_cycle_id != cycle.cycle_id:
            if apply:
                committee.election_cycle = cycle
                changes_made = True
            self.stats['fixed_cycle'] += 1

        if changes_made and apply:
            committee.save(update_fields=['candidate_office', 'election_cycle'])

        self.changes.append(change_record)

        if verbose or office:
            status = "FIXED" if apply else "WOULD FIX"
            self.stdout.write(self.style.SUCCESS(
                f"{status}: {committee.committee_id} - {committee_name}"
            ))
            self.stdout.write(f"  Office: {office.name if office else 'N/A'} ({office_reason})")
            self.stdout.write(f"  Cycle: {cycle.name if cycle else 'N/A'} ({cycle_reason})")
            self.stdout.write(f"  IE Amount: ${ie_amount:,.2f}")
            self.stdout.write("")

        self.file_logger.info(
            f"{'FIXED' if apply else 'WOULD_FIX'} | "
            f"ID: {committee.committee_id} | "
            f"Name: {committee_name} | "
            f"Office: {office.name if office else 'N/A'} | "
            f"Cycle: {cycle.name if cycle else 'N/A'} | "
            f"IE: ${ie_amount:,.2f}"
        )

        return True

    def generate_restore_query(self):
        """Generate SQL that can restore original values if needed."""
        restore_queries = []
        for change in self.changes:
            if change['new_office_id'] is not None:
                orig_office = change['original_office_id'] or 'NULL'
                orig_cycle = change['original_cycle_id'] or 'NULL'
                restore_queries.append(
                    f"-- Restore committee {change['committee_id']}: {change['committee_name']}\n"
                    f"UPDATE \"Committees\" SET "
                    f"candidate_office_id = {orig_office}, "
                    f"election_cycle_id = {orig_cycle} "
                    f"WHERE committee_id = {change['committee_id']};"
                )
        return "\n".join(restore_queries)

    def handle(self, *args, **options):
        apply = options['apply']
        verbose = options['verbose']
        specific_id = options.get('committee_id')
        limit = options.get('limit')

        # Setup
        self.setup_logging()
        self.load_office_cache()
        self.load_cycle_cache()

        # Header
        mode = "APPLYING CHANGES" if apply else "DRY RUN"
        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('FIX COMMITTEE OFFICE/CYCLE LINKAGES'))
        self.stdout.write(self.style.NOTICE(f'Mode: {mode}'))
        self.stdout.write(self.style.NOTICE(f'Log file: {LOG_FILE}'))
        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write('')

        self.file_logger.info('=' * 70)
        self.file_logger.info(f'Starting fix_committee_linkages - Mode: {mode}')
        self.file_logger.info('=' * 70)

        # Get committees to process
        queryset = Committee.objects.filter(
            subject_of_ies__isnull=False,  # Has IE spending targeting them
            candidate_office__isnull=True   # No office set
        ).select_related('name', 'candidate_office', 'election_cycle').distinct()

        if specific_id:
            queryset = queryset.filter(committee_id=specific_id)

        if limit:
            queryset = queryset[:limit]

        total_count = queryset.count()
        self.stdout.write(f'Found {total_count} committees to process')
        self.stdout.write('')

        # Calculate total IE spending before fixes
        self.stats['ie_amount_before'] = Transaction.objects.filter(
            subject_committee__in=queryset,
            deleted=False,
            transaction_type__income_expense_neutral=2
        ).aggregate(total=Sum(Abs('amount')))['total'] or Decimal('0')

        # Process each committee
        for committee in queryset:
            self.process_committee(committee, apply=apply, verbose=verbose)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('SUMMARY'))
        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(f"Total committees processed: {self.stats['total_processed']}")
        self.stdout.write(self.style.SUCCESS(
            f"Committees with office fixed: {self.stats['fixed_office']}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Committees with cycle fixed: {self.stats['fixed_cycle']}"
        ))
        self.stdout.write(self.style.WARNING(
            f"Skipped (unclear office): {self.stats['skipped_unclear']}"
        ))
        self.stdout.write(self.style.WARNING(
            f"Skipped (no transactions): {self.stats['skipped_no_transactions']}"
        ))
        self.stdout.write('')
        self.stdout.write(f"Total IE spending before fixes: ${self.stats['ie_amount_before']:,.2f}")
        self.stdout.write(self.style.SUCCESS(
            f"IE spending now included in reports: ${self.stats['ie_amount_after']:,.2f}"
        ))

        if not apply:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'This was a DRY RUN. Use --apply to make actual changes.'
            ))

        # Log summary
        self.file_logger.info('=' * 70)
        self.file_logger.info('SUMMARY')
        self.file_logger.info(f"Total processed: {self.stats['total_processed']}")
        self.file_logger.info(f"Fixed office: {self.stats['fixed_office']}")
        self.file_logger.info(f"Fixed cycle: {self.stats['fixed_cycle']}")
        self.file_logger.info(f"Skipped unclear: {self.stats['skipped_unclear']}")
        self.file_logger.info(f"Skipped no transactions: {self.stats['skipped_no_transactions']}")
        self.file_logger.info(f"IE before: ${self.stats['ie_amount_before']:,.2f}")
        self.file_logger.info(f"IE after: ${self.stats['ie_amount_after']:,.2f}")
        self.file_logger.info('=' * 70)

        # Write restore query to file if changes were made
        if apply and self.changes:
            restore_file = '/opt/az_sunshine/backend/committee_linkage_restore.sql'
            with open(restore_file, 'w') as f:
                f.write("-- Restore script generated at {}\n".format(datetime.now().isoformat()))
                f.write("-- Run this script to undo all changes made by fix_committee_linkages\n\n")
                f.write(self.generate_restore_query())
            self.stdout.write(f'\nRestore script written to: {restore_file}')
            self.file_logger.info(f'Restore script written to: {restore_file}')
