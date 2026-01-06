"""
Fix Missing Office Data for Committees

This management command identifies committees that have a candidate linked
but no office set, and attempts to fix them by finding matching committees
with the same candidate name in the same election cycle.

Usage:
    python manage.py fix_missing_offices --dry-run   # Preview changes
    python manage.py fix_missing_offices             # Apply changes
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from transparency.models import Committee, Entity, Office
import json
from datetime import datetime


# Common nickname mappings for name matching
NICKNAME_MAP = {
    'BOB': ['ROBERT', 'ROB', 'BOBBY'],
    'ROBERT': ['BOB', 'ROB', 'BOBBY'],
    'BILL': ['WILLIAM', 'WILL', 'BILLY', 'WILLY'],
    'WILLIAM': ['BILL', 'WILL', 'BILLY', 'WILLY'],
    'JIM': ['JAMES', 'JIMMY', 'JAMIE'],
    'JAMES': ['JIM', 'JIMMY', 'JAMIE'],
    'MIKE': ['MICHAEL', 'MICK', 'MIKEY'],
    'MICHAEL': ['MIKE', 'MICK', 'MIKEY'],
    'TOM': ['THOMAS', 'TOMMY'],
    'THOMAS': ['TOM', 'TOMMY'],
    'DICK': ['RICHARD', 'RICK', 'RICKY', 'RICH'],
    'RICHARD': ['DICK', 'RICK', 'RICKY', 'RICH'],
    'AL': ['ALBERT', 'ALAN', 'ALLAN', 'ALLEN'],
    'ALBERT': ['AL', 'BERT'],
    'DAN': ['DANIEL', 'DANNY'],
    'DANIEL': ['DAN', 'DANNY'],
    'ED': ['EDWARD', 'EDDIE', 'TED', 'TEDDY'],
    'EDWARD': ['ED', 'EDDIE', 'TED', 'TEDDY'],
    'JOE': ['JOSEPH', 'JOEY'],
    'JOSEPH': ['JOE', 'JOEY'],
    'DAVE': ['DAVID'],
    'DAVID': ['DAVE'],
    'ANDY': ['ANDREW', 'DREW'],
    'ANDREW': ['ANDY', 'DREW'],
    'STEVE': ['STEVEN', 'STEPHEN'],
    'STEVEN': ['STEVE', 'STEPHEN'],
    'STEPHEN': ['STEVE', 'STEVEN'],
    'CHRIS': ['CHRISTOPHER', 'CHRISTIAN'],
    'CHRISTOPHER': ['CHRIS'],
    'CHRISTIAN': ['CHRIS'],
    'MATT': ['MATTHEW'],
    'MATTHEW': ['MATT'],
    'TONY': ['ANTHONY'],
    'ANTHONY': ['TONY'],
    'NICK': ['NICHOLAS', 'NICKY'],
    'NICHOLAS': ['NICK', 'NICKY'],
    'PAT': ['PATRICK', 'PATRICIA'],
    'PATRICK': ['PAT', 'PADDY'],
    'PATRICIA': ['PAT', 'PATTY', 'TRICIA'],
    'ALEX': ['ALEXANDER', 'ALEXANDRA', 'ALEXIS'],
    'ALEXANDER': ['ALEX', 'XANDER'],
    'ALEXANDRA': ['ALEX', 'SANDRA'],
    'KATE': ['KATHERINE', 'CATHERINE', 'KATIE', 'KATHY'],
    'KATHERINE': ['KATE', 'KATIE', 'KATHY', 'KAT'],
    'CATHERINE': ['KATE', 'KATIE', 'CATHY', 'CAT'],
    'BETH': ['ELIZABETH', 'BETTY', 'LIZ', 'LIZZIE'],
    'ELIZABETH': ['BETH', 'BETTY', 'LIZ', 'LIZZIE', 'ELIZA'],
    'SUE': ['SUSAN', 'SUSIE', 'SUZANNE'],
    'SUSAN': ['SUE', 'SUSIE'],
    'SUZANNE': ['SUE', 'SUZY'],
    'CHUCK': ['CHARLES', 'CHARLIE'],
    'CHARLES': ['CHUCK', 'CHARLIE', 'CHAS'],
    'CHARLIE': ['CHARLES', 'CHUCK'],
    'FRANK': ['FRANCIS', 'FRANCISCO'],
    'FRANCIS': ['FRANK', 'FRAN'],
    'GREG': ['GREGORY'],
    'GREGORY': ['GREG'],
    'JEFF': ['JEFFREY', 'GEOFFREY'],
    'JEFFREY': ['JEFF'],
    'GEOFFREY': ['JEFF', 'GEOFF'],
    'LARRY': ['LAWRENCE', 'LAURENCE'],
    'LAWRENCE': ['LARRY'],
    'LAURENCE': ['LARRY'],
    'RON': ['RONALD', 'RONNIE'],
    'RONALD': ['RON', 'RONNIE'],
    'TED': ['THEODORE', 'EDWARD'],
    'THEODORE': ['TED', 'TEDDY', 'THEO'],
    'PHIL': ['PHILIP', 'PHILLIP'],
    'PHILIP': ['PHIL'],
    'PHILLIP': ['PHIL'],
    'VIC': ['VICTOR', 'VICTORIA'],
    'VICTOR': ['VIC', 'VICK'],
    'VICTORIA': ['VIC', 'VICKY', 'TORI'],
    'BEN': ['BENJAMIN', 'BENNY'],
    'BENJAMIN': ['BEN', 'BENNY'],
    'KEN': ['KENNETH', 'KENNY'],
    'KENNETH': ['KEN', 'KENNY'],
    'SAM': ['SAMUEL', 'SAMANTHA'],
    'SAMUEL': ['SAM', 'SAMMY'],
    'SAMANTHA': ['SAM', 'SAMMY'],
    'TERRY': ['TERRENCE', 'THERESA', 'TERESA'],
    'TERRENCE': ['TERRY'],
    'THERESA': ['TERRY', 'TESS'],
    'TERESA': ['TERRY', 'TESS'],
    'DON': ['DONALD', 'DONNY'],
    'DONALD': ['DON', 'DONNY'],
    'DOUG': ['DOUGLAS'],
    'DOUGLAS': ['DOUG'],
    'FRED': ['FREDERICK', 'FREDDY'],
    'FREDERICK': ['FRED', 'FREDDY'],
    'JACK': ['JOHN', 'JACKSON'],
    'JOHN': ['JACK', 'JOHNNY', 'JON'],
    'JON': ['JOHN', 'JONATHAN', 'JOHNNY'],
    'JONATHAN': ['JON', 'JOHN'],
    'JERRY': ['GERALD', 'JEROME', 'GERALDO'],
    'GERALD': ['JERRY', 'GERRY'],
    'JEROME': ['JERRY'],
    'WALLY': ['WALTER', 'WALT'],
    'WALTER': ['WALT', 'WALLY'],
    'PEGGY': ['MARGARET', 'MAGGIE', 'MEG'],
    'MARGARET': ['PEGGY', 'MAGGIE', 'MEG', 'MARGE'],
    'SANDY': ['SANDRA', 'ALEXANDER', 'ALEXANDRA'],
    'SANDRA': ['SANDY'],
}


def names_match(name1, name2):
    """Check if two first names could be the same person (including nicknames)."""
    if not name1 or not name2:
        return False

    n1 = name1.upper().strip()
    n2 = name2.upper().strip()

    # Exact match
    if n1 == n2:
        return True

    # One contains the other (handles middle initials, etc.)
    if n1 in n2 or n2 in n1:
        return True

    # Nickname match
    n1_nicknames = NICKNAME_MAP.get(n1, [])
    n2_nicknames = NICKNAME_MAP.get(n2, [])

    if n2 in n1_nicknames:
        return True
    if n1 in n2_nicknames:
        return True

    return False


class Command(BaseCommand):
    help = 'Fix committees with candidate but no office by matching with sibling committees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--committee-id',
            type=int,
            help='Fix only a specific committee ID',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output JSON file for changes log',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_id = options.get('committee_id')
        output_file = options.get('output')

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('FIX MISSING OFFICE DATA'))
        self.stdout.write(self.style.NOTICE(f'Mode: {"DRY RUN" if dry_run else "LIVE"}'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write('')

        # Find committees with candidate but no office
        queryset = Committee.objects.filter(
            candidate__isnull=False,
            candidate_office__isnull=True,
            election_cycle__isnull=False
        ).select_related('candidate', 'election_cycle', 'name')

        if specific_id:
            queryset = queryset.filter(committee_id=specific_id)

        total = queryset.count()
        self.stdout.write(f'Found {total} committees with candidate but no office')
        self.stdout.write('')

        fixed = []
        not_fixed = []

        for committee in queryset:
            candidate = committee.candidate
            cycle = committee.election_cycle

            if not candidate.first_name or not candidate.last_name:
                not_fixed.append({
                    'committee_id': committee.committee_id,
                    'name': committee.name.full_name,
                    'candidate': candidate.full_name,
                    'reason': 'Candidate missing first or last name'
                })
                continue

            # Find matching committees in same cycle with office set
            matches = Committee.objects.filter(
                election_cycle=cycle,
                candidate__last_name__iexact=candidate.last_name.strip(),
                candidate_office__isnull=False
            ).exclude(committee_id=committee.committee_id).select_related(
                'candidate', 'candidate_office'
            )

            found_match = None
            for match in matches:
                if match.candidate and match.candidate.first_name:
                    if names_match(candidate.first_name, match.candidate.first_name):
                        found_match = match
                        break

            if found_match:
                office = found_match.candidate_office

                self.stdout.write(self.style.SUCCESS(
                    f'MATCH: Committee {committee.committee_id} ({committee.name.full_name})'
                ))
                self.stdout.write(f'  Candidate: {candidate.full_name}')
                self.stdout.write(f'  Matched with: {found_match.committee_id} ({found_match.candidate.full_name})')
                self.stdout.write(f'  Office: {office.name}')

                if not dry_run:
                    committee.candidate_office = office
                    committee.save(update_fields=['candidate_office'])
                    self.stdout.write(self.style.SUCCESS('  -> FIXED'))
                else:
                    self.stdout.write(self.style.WARNING('  -> Would fix (dry-run)'))

                self.stdout.write('')

                fixed.append({
                    'committee_id': committee.committee_id,
                    'name': committee.name.full_name,
                    'candidate': candidate.full_name,
                    'cycle': cycle.name,
                    'matched_committee': found_match.committee_id,
                    'matched_candidate': found_match.candidate.full_name,
                    'office_id': office.office_id,
                    'office_name': office.name
                })
            else:
                not_fixed.append({
                    'committee_id': committee.committee_id,
                    'name': committee.name.full_name,
                    'candidate': candidate.full_name,
                    'cycle': cycle.name if cycle else None,
                    'reason': 'No matching committee with office found'
                })

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('SUMMARY'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(f'Total processed: {total}')
        self.stdout.write(self.style.SUCCESS(f'Fixed: {len(fixed)}'))
        self.stdout.write(self.style.WARNING(f'Not fixed: {len(not_fixed)}'))

        # Check Burns specifically
        burns_fixed = [f for f in fixed if f['committee_id'] == 201000016]
        if burns_fixed:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Burns (201000016) was FIXED!'))
            self.stdout.write(f'  Office: {burns_fixed[0]["office_name"]}')

        # Output to file if requested
        if output_file:
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'dry_run': dry_run,
                'total_processed': total,
                'fixed': fixed,
                'not_fixed': not_fixed
            }
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            self.stdout.write(f'\nLog written to: {output_file}')

        return
