"""
Candidate Aggregate Views

Provides aggregated financial data across all committees for a candidate
in a given election cycle. This solves the problem where the same person
has multiple committees (different entity IDs) for the same race.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Committee, Transaction, Entity


# Nickname mapping for name matching (same as fix_missing_offices.py)
NICKNAME_MAP = {
    'BOB': ['ROBERT', 'ROB', 'BOBBY'],
    'ROBERT': ['BOB', 'ROB', 'BOBBY'],
    'BILL': ['WILLIAM', 'WILL', 'BILLY'],
    'WILLIAM': ['BILL', 'WILL', 'BILLY'],
    'JIM': ['JAMES', 'JIMMY'],
    'JAMES': ['JIM', 'JIMMY'],
    'MIKE': ['MICHAEL', 'MICK'],
    'MICHAEL': ['MIKE', 'MICK'],
    'TOM': ['THOMAS', 'TOMMY'],
    'THOMAS': ['TOM', 'TOMMY'],
    'DICK': ['RICHARD', 'RICK'],
    'RICHARD': ['DICK', 'RICK'],
    'AL': ['ALBERT', 'ALAN'],
    'DAN': ['DANIEL', 'DANNY'],
    'DANIEL': ['DAN', 'DANNY'],
    'ED': ['EDWARD', 'EDDIE'],
    'EDWARD': ['ED', 'EDDIE'],
    'JOE': ['JOSEPH', 'JOEY'],
    'JOSEPH': ['JOE', 'JOEY'],
    'DAVE': ['DAVID'],
    'DAVID': ['DAVE'],
    'ANDY': ['ANDREW', 'DREW'],
    'ANDREW': ['ANDY', 'DREW'],
    'STEVE': ['STEVEN', 'STEPHEN'],
    'STEVEN': ['STEVE'],
    'STEPHEN': ['STEVE'],
    'CHRIS': ['CHRISTOPHER'],
    'CHRISTOPHER': ['CHRIS'],
    'MATT': ['MATTHEW'],
    'MATTHEW': ['MATT'],
    'TONY': ['ANTHONY'],
    'ANTHONY': ['TONY'],
    'NICK': ['NICHOLAS'],
    'NICHOLAS': ['NICK'],
    'TERRY': ['TERRENCE', 'THERESA'],
    'DON': ['DONALD'],
    'DONALD': ['DON'],
    'DOUG': ['DOUGLAS'],
    'DOUGLAS': ['DOUG'],
    'JACK': ['JOHN'],
    'JOHN': ['JACK', 'JOHNNY'],
    'VIC': ['VICTOR', 'VICTORIA'],
    'VICTOR': ['VIC'],
}


def names_match(name1, name2):
    """Check if two first names could be the same person."""
    if not name1 or not name2:
        return False
    n1 = name1.upper().strip()
    n2 = name2.upper().strip()
    if n1 == n2:
        return True
    if n1 in n2 or n2 in n1:
        return True
    if n2 in NICKNAME_MAP.get(n1, []):
        return True
    if n1 in NICKNAME_MAP.get(n2, []):
        return True
    return False


def find_related_committees(committee):
    """
    Find all committees that appear to be for the same candidate
    in the same election cycle.
    """
    if not committee.candidate or not committee.election_cycle:
        return [committee]

    candidate = committee.candidate
    cycle = committee.election_cycle

    # Find committees in same cycle with matching last name
    potential_matches = Committee.objects.filter(
        election_cycle=cycle,
        candidate__last_name__iexact=candidate.last_name.strip() if candidate.last_name else ''
    ).select_related('candidate', 'candidate_office', 'name')

    # Filter to those with matching first name
    related = []
    for c in potential_matches:
        if c.candidate and candidate.first_name and c.candidate.first_name:
            if names_match(candidate.first_name, c.candidate.first_name):
                related.append(c)

    return related if related else [committee]


@api_view(['GET'])
@permission_classes([AllowAny])
def candidate_aggregate(request, committee_id):
    """
    Get aggregated financial data across all committees for a candidate.

    This endpoint finds all committees that appear to be for the same
    candidate (based on name matching) in the same election cycle and
    aggregates their financial data.

    Returns:
        - Primary committee info
        - List of all related committees
        - Aggregated totals (income, expenses, IE for/against)
        - Combined IE spending breakdown by committee
    """
    try:
        primary_committee = Committee.objects.select_related(
            'name', 'candidate', 'candidate_party', 'candidate_office', 'election_cycle'
        ).get(committee_id=committee_id)
    except Committee.DoesNotExist:
        return Response({'error': 'Committee not found'}, status=404)

    # Find all related committees
    related_committees = find_related_committees(primary_committee)
    committee_ids = [c.committee_id for c in related_committees]

    # Calculate aggregated totals
    total_income = Decimal('0')
    total_expenses = Decimal('0')
    total_ie_for = Decimal('0')
    total_ie_against = Decimal('0')

    committees_data = []
    all_ie_by_committee = []

    for c in related_committees:
        income = c.get_total_income()
        expenses = c.get_total_expenses()
        ie_summary = c.get_ie_spending_summary()

        ie_for = Decimal(str(ie_summary.get('for', {}).get('total', 0)))
        ie_against = Decimal(str(ie_summary.get('against', {}).get('total', 0)))

        total_income += income
        total_expenses += expenses
        total_ie_for += ie_for
        total_ie_against += ie_against

        committees_data.append({
            'committee_id': c.committee_id,
            'name': c.name.full_name if c.name else None,
            'candidate_name': c.candidate.full_name if c.candidate else None,
            'income': str(income),
            'expenses': str(expenses),
            'ie_for': str(ie_for),
            'ie_against': str(ie_against),
        })

        # Get IE spending breakdown for this committee
        ie_breakdown = c.get_ie_spending_by_committee()
        for ie in ie_breakdown:
            all_ie_by_committee.append({
                'target_committee_id': c.committee_id,
                'target_committee_name': c.name.full_name if c.name else None,
                'spending_committee_id': ie.get('committee_id'),
                'spending_committee_name': ie.get('committee__name__full_name') or ie.get('committee__name'),
                'total_ie': str(ie.get('total_ie', 0)),
                'total_for': str(ie.get('total_for', 0)),
                'total_against': str(ie.get('total_against', 0)),
            })

    # Build response
    response_data = {
        'primary_committee': {
            'committee_id': primary_committee.committee_id,
            'name': primary_committee.name.full_name if primary_committee.name else None,
            'candidate': {
                'name_id': primary_committee.candidate.name_id if primary_committee.candidate else None,
                'full_name': primary_committee.candidate.full_name if primary_committee.candidate else None,
            } if primary_committee.candidate else None,
            'office': {
                'office_id': primary_committee.candidate_office.office_id if primary_committee.candidate_office else None,
                'name': primary_committee.candidate_office.name if primary_committee.candidate_office else None,
            } if primary_committee.candidate_office else None,
            'party': {
                'party_id': primary_committee.candidate_party.party_id if primary_committee.candidate_party else None,
                'name': primary_committee.candidate_party.name if primary_committee.candidate_party else None,
            } if primary_committee.candidate_party else None,
            'cycle': {
                'cycle_id': primary_committee.election_cycle.cycle_id if primary_committee.election_cycle else None,
                'name': primary_committee.election_cycle.name if primary_committee.election_cycle else None,
            } if primary_committee.election_cycle else None,
        },
        'is_aggregated': len(related_committees) > 1,
        'related_committees_count': len(related_committees),
        'related_committees': committees_data,
        'aggregated_totals': {
            'total_income': str(total_income),
            'total_expenses': str(total_expenses),
            'total_ie_for': str(total_ie_for),
            'total_ie_against': str(total_ie_against),
            'net_ie': str(total_ie_for - total_ie_against),
        },
        'ie_spending_by_committee': all_ie_by_committee,
    }

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def candidate_aggregate_ie_spending(request, committee_id):
    """
    Get aggregated IE spending summary for a candidate across all their committees.

    This is a drop-in replacement for the existing ie_spending endpoint
    that aggregates across related committees.
    """
    try:
        primary_committee = Committee.objects.select_related(
            'name', 'candidate', 'candidate_office', 'election_cycle'
        ).get(committee_id=committee_id)
    except Committee.DoesNotExist:
        return Response({'error': 'Committee not found'}, status=404)

    related_committees = find_related_committees(primary_committee)

    total_ie_for = Decimal('0')
    total_ie_against = Decimal('0')
    ie_for_count = 0
    ie_against_count = 0

    combined_ie_by_committee = {}

    for c in related_committees:
        ie_summary = c.get_ie_spending_summary()

        total_ie_for += Decimal(str(ie_summary.get('for', {}).get('total', 0)))
        total_ie_against += Decimal(str(ie_summary.get('against', {}).get('total', 0)))
        ie_for_count += ie_summary.get('for', {}).get('count', 0)
        ie_against_count += ie_summary.get('against', {}).get('count', 0)

        # Aggregate IE by spending committee
        ie_breakdown = c.get_ie_spending_by_committee()
        for ie in ie_breakdown:
            spending_committee_id = ie.get('committee_id')
            if spending_committee_id not in combined_ie_by_committee:
                combined_ie_by_committee[spending_committee_id] = {
                    'committee_id': spending_committee_id,
                    'committee__name': ie.get('committee__name__full_name') or ie.get('committee__name'),
                    'total_ie': Decimal('0'),
                    'total_for': Decimal('0'),
                    'total_against': Decimal('0'),
                }
            combined_ie_by_committee[spending_committee_id]['total_ie'] += Decimal(str(ie.get('total_ie', 0)))
            combined_ie_by_committee[spending_committee_id]['total_for'] += Decimal(str(ie.get('total_for', 0)))
            combined_ie_by_committee[spending_committee_id]['total_against'] += Decimal(str(ie.get('total_against', 0)))

    # Convert to list and sort by total IE
    ie_by_committee_list = sorted(
        [
            {
                'committee_id': v['committee_id'],
                'committee__name': v['committee__name'],
                'total_ie': str(v['total_ie']),
                'total_for': str(v['total_for']),
                'total_against': str(v['total_against']),
            }
            for v in combined_ie_by_committee.values()
        ],
        key=lambda x: abs(Decimal(x['total_ie'])),
        reverse=True
    )

    response_data = {
        'committee_id': primary_committee.committee_id,
        'candidate_name': primary_committee.candidate.full_name if primary_committee.candidate else None,
        'office': primary_committee.candidate_office.name if primary_committee.candidate_office else None,
        'party': primary_committee.candidate_party.name if primary_committee.candidate_party else None,
        'is_aggregated': len(related_committees) > 1,
        'related_committees_count': len(related_committees),
        'ie_spending': {
            'for': {
                'total': str(total_ie_for),
                'count': ie_for_count,
            },
            'against': {
                'total': str(total_ie_against),
                'count': ie_against_count,
            },
            'net': str(total_ie_for - total_ie_against),
        },
        'ie_by_committee': ie_by_committee_list,
    }

    return Response(response_data)
