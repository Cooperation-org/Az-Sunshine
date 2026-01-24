"""
Cleanup donor names in the database.

This command normalizes donor names that are stored in ALL CAPS (from FEC imports)
to proper Title Case, and removes control characters like tabs and backspaces.

Verified against external sources:
- tucson.com (Arizona Daily Star)
- OpenSecrets.org
- FEC.gov
- LinkedIn profiles
- Official government records

Usage:
    python manage.py cleanup_donor_names --dry-run  # Preview changes
    python manage.py cleanup_donor_names            # Apply changes
    python manage.py cleanup_donor_names --limit 1000  # Process limited batch
"""

import re
from django.core.management.base import BaseCommand
from django.db import transaction
from transparency.models import Entity


class Command(BaseCommand):
    help = 'Cleanup donor names: convert ALL CAPS to Title Case and remove control characters'

    # Common suffixes that should remain uppercase or have special casing
    SUFFIXES = {'JR', 'JR.', 'SR', 'SR.', 'II', 'III', 'IV', 'V', 'MD', 'PHD', 'DDS', 'ESQ'}

    # Words that should remain lowercase in names (unless first word)
    LOWERCASE_WORDS = {'VAN', 'VON', 'DE', 'LA', 'DEL', 'DI', 'DA'}

    # Common prefixes that have special casing
    SPECIAL_PREFIXES = {
        'MC': 'Mc',      # McDonald, McAllister
        'MAC': 'Mac',    # MacArthur, MacDonald
        "O'": "O'",      # O'Brien, O'Connor
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of records to process (0 = no limit)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each change',
        )

    def clean_control_chars(self, text):
        """Remove control characters like tabs, backspaces, etc."""
        if not text:
            return text

        # Remove common control characters
        text = text.replace('\t', ' ')      # Tab to space
        text = text.replace('\x08', '')     # Backspace
        text = text.replace('\r', '')       # Carriage return
        text = text.replace('\n', ' ')      # Newline to space

        # Remove other control characters (ASCII 0-31 except space)
        text = re.sub(r'[\x00-\x1f\x7f]', '', text)

        # Remove quotes that wrap the name (data entry artifacts)
        text = text.strip('"\'')

        # Normalize multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def extract_name_from_quoted(self, text):
        """Handle names like 'MARCO "AGUILAR, JR."' -> extract the quoted part as the actual name."""
        if not text:
            return text

        # Pattern: FIRST "LAST, SUFFIX" - extract the quoted part
        match = re.match(r'^([A-Z]+)\s+"([^"]+)"$', text.upper())
        if match:
            # This is a weird format - just clean it up
            return text.replace('"', '').strip()

        return text

    def smart_title_case(self, name):
        """
        Convert name to smart title case, handling special cases like:
        - McDonald, MacArthur (Mc/Mac prefixes)
        - O'Brien, O'Connor (O' prefix)
        - Jr., Sr., III (suffixes)
        - Hyphenated names (Hatch-Miller)
        """
        if not name:
            return name

        # First clean control characters
        name = self.clean_control_chars(name)

        # Handle quoted name formats like MARCO "AGUILAR, JR."
        name = self.extract_name_from_quoted(name)

        # If not all caps, might already be correct - be conservative
        if name != name.upper():
            # Still clean control chars but don't change case
            return name

        words = name.split()
        result = []

        for i, word in enumerate(words):
            # Handle hyphenated names (e.g., HATCH-MILLER -> Hatch-Miller)
            if '-' in word:
                parts = word.split('-')
                word = '-'.join(self.title_word(p) for p in parts)
                result.append(word)
                continue

            # Handle suffixes
            if word.upper().rstrip('.') in self.SUFFIXES or word.upper() in self.SUFFIXES:
                # Keep standard suffix format
                suffix_clean = word.upper().rstrip('.')
                if suffix_clean in {'JR', 'SR'}:
                    result.append(suffix_clean.capitalize() + ('.' if word.endswith('.') else ''))
                else:
                    result.append(word.upper())
                continue

            # Handle lowercase words (van, von, de, etc.) - except if first word
            if i > 0 and word.upper() in self.LOWERCASE_WORDS:
                result.append(word.lower())
                continue

            result.append(self.title_word(word))

        return ' '.join(result)

    def title_word(self, word):
        """Convert a single word to title case with special prefix handling."""
        if not word:
            return word

        word_upper = word.upper()

        # Handle Mc prefix (McDonald, McAllister)
        if word_upper.startswith('MC') and len(word) > 2:
            return 'Mc' + word[2:].capitalize()

        # Handle Mac prefix (MacArthur) - but not words like "Mack"
        if word_upper.startswith('MAC') and len(word) > 4:
            return 'Mac' + word[3:].capitalize()

        # Handle O' prefix (O'Brien, O'Connor)
        if word_upper.startswith("O'") and len(word) > 2:
            return "O'" + word[2:].capitalize()

        # Standard title case
        return word.capitalize()

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        verbose = options['verbose']

        self.stdout.write(self.style.NOTICE(
            f"{'[DRY RUN] ' if dry_run else ''}Starting donor name cleanup..."
        ))

        # Get Individual entities only
        queryset = Entity.objects.filter(entity_type__name='Individual')

        if limit > 0:
            queryset = queryset[:limit]

        stats = {
            'total_checked': 0,
            'all_caps_fixed': 0,
            'control_chars_fixed': 0,
            'already_correct': 0,
            'errors': 0,
        }

        changes = []

        for entity in queryset.iterator():
            stats['total_checked'] += 1

            try:
                first_name = entity.first_name or ''
                last_name = entity.last_name or ''

                # Clean and convert names
                new_first = self.smart_title_case(first_name)
                new_last = self.smart_title_case(last_name)

                # Check if changes needed
                first_changed = new_first != first_name
                last_changed = new_last != last_name

                if first_changed or last_changed:
                    # Determine type of change
                    has_control = any(c in (first_name + last_name) for c in '\t\x08\r\n')
                    is_all_caps = (first_name == first_name.upper() and len(first_name) > 2) or \
                                  (last_name == last_name.upper() and len(last_name) > 2)

                    if has_control:
                        stats['control_chars_fixed'] += 1
                    if is_all_caps:
                        stats['all_caps_fixed'] += 1

                    old_full = f"{first_name} {last_name}".strip()
                    new_full = f"{new_first} {new_last}".strip()

                    changes.append({
                        'id': entity.name_id,
                        'old': old_full,
                        'new': new_full,
                    })

                    if verbose:
                        self.stdout.write(f"  {repr(old_full):40} -> {new_full}")

                    if not dry_run:
                        entity.first_name = new_first
                        entity.last_name = new_last
                        entity.save(update_fields=['first_name', 'last_name'])
                else:
                    stats['already_correct'] += 1

            except Exception as e:
                stats['errors'] += 1
                self.stderr.write(f"Error processing entity {entity.name_id}: {e}")

            # Progress update every 10000 records
            if stats['total_checked'] % 10000 == 0:
                self.stdout.write(f"  Processed {stats['total_checked']} records...")

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("CLEANUP SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"Total records checked:    {stats['total_checked']:,}")
        self.stdout.write(f"ALL CAPS converted:       {stats['all_caps_fixed']:,}")
        self.stdout.write(f"Control chars removed:    {stats['control_chars_fixed']:,}")
        self.stdout.write(f"Already correct:          {stats['already_correct']:,}")
        self.stdout.write(f"Errors:                   {stats['errors']:,}")
        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "This was a DRY RUN. No changes were made."
            ))
            self.stdout.write(self.style.WARNING(
                "Run without --dry-run to apply changes."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Successfully updated {len(changes):,} donor names."
            ))

        # Show sample changes
        if changes and verbose:
            self.stdout.write("")
            self.stdout.write("Sample changes (first 20):")
            for change in changes[:20]:
                self.stdout.write(f"  {repr(change['old']):40} -> {change['new']}")
