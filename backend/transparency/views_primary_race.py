"""
Primary Race View - For Golda's Demo
Shows detailed primary race analysis with IE spending breakdown
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, F
from .models import Committee, Transaction, TransactionType, Cycle, Party, Office, Entity
from decimal import Decimal


@api_view(['GET'])
@permission_classes([AllowAny])
def primary_race_detail(request):
    """
    Get detailed primary race information with IE spending analysis

    Query params:
    - office: Office name (e.g., "Attorney General")
    - party: Party name (e.g., "Republican", "Democratic")
    - cycle: Election cycle year (e.g., "2022", "2024")
    """
    office_name = request.GET.get('office')
    party_name = request.GET.get('party')
    cycle_year = request.GET.get('cycle')

    if not all([office_name, party_name, cycle_year]):
        return Response({
            'error': 'Missing required parameters: office, party, cycle'
        }, status=400)

    # Get the race components
    try:
        office = Office.objects.get(name=office_name)
        party = Party.objects.get(name=party_name)
        cycle = Cycle.objects.get(name=cycle_year)
    except (Office.DoesNotExist, Party.DoesNotExist, Cycle.DoesNotExist) as e:
        return Response({
            'error': f'Not found: {str(e)}'
        }, status=404)

    # Get all IE transaction types
    ie_types = TransactionType.objects.filter(
        Q(name__icontains='Independent Expenditure') | Q(name__icontains='Ind. Expend')
    )

    # Get all candidates in this primary race
    candidates = Committee.objects.filter(
        election_cycle=cycle,
        candidate_party=party,
        candidate_office=office,
        candidate__isnull=False
    ).select_related('candidate', 'candidate_office', 'candidate_party')

    if candidates.count() < 2:
        return Response({
            'error': 'Not a primary race (fewer than 2 candidates)',
            'candidates_count': candidates.count()
        }, status=404)

    # Build candidate data with IE spending
    candidates_data = []
    all_ie_spenders = []  # Track all IE committees for "biggest spenders" section

    for comm in candidates:
        cand_name = comm.candidate.full_name if comm.candidate else "Unknown"

        # Calculate IE FOR this candidate
        ie_for_amount = Transaction.objects.filter(
            subject_committee=comm,
            transaction_type__in=ie_types,
            is_for_benefit=True,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Calculate IE AGAINST this candidate
        ie_against_amount = Transaction.objects.filter(
            subject_committee=comm,
            transaction_type__in=ie_types,
            is_for_benefit=False,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Get IE spenders FOR this candidate
        ie_for_spenders = Transaction.objects.filter(
            subject_committee=comm,
            transaction_type__in=ie_types,
            is_for_benefit=True,
            deleted=False
        ).values(
            'committee__committee_id',
            'committee__name__last_name',
            'committee__name__first_name'
        ).annotate(
            total=Sum('amount'),
            count=Count('transaction_id')
        ).order_by('-total')

        # Get IE spenders AGAINST this candidate
        ie_against_spenders = Transaction.objects.filter(
            subject_committee=comm,
            transaction_type__in=ie_types,
            is_for_benefit=False,
            deleted=False
        ).values(
            'committee__committee_id',
            'committee__name__last_name',
            'committee__name__first_name'
        ).annotate(
            total=Sum('amount'),
            count=Count('transaction_id')
        ).order_by('-total')

        # Format spenders
        for_spenders_list = []
        for spender in ie_for_spenders:
            spender_name = f"{spender['committee__name__first_name'] or ''} {spender['committee__name__last_name']}".strip()
            for_spenders_list.append({
                'committee_id': spender['committee__committee_id'],
                'name': spender_name,
                'amount': float(abs(spender['total'])),
                'transaction_count': spender['count']
            })
            all_ie_spenders.append({
                'committee_id': spender['committee__committee_id'],
                'name': spender_name,
                'amount': abs(float(spender['total'])),
                'benefit': 'FOR',
                'candidate': cand_name
            })

        against_spenders_list = []
        for spender in ie_against_spenders:
            spender_name = f"{spender['committee__name__first_name'] or ''} {spender['committee__name__last_name']}".strip()
            against_spenders_list.append({
                'committee_id': spender['committee__committee_id'],
                'name': spender_name,
                'amount': float(abs(spender['total'])),
                'transaction_count': spender['count']
            })
            all_ie_spenders.append({
                'committee_id': spender['committee__committee_id'],
                'name': spender_name,
                'amount': abs(float(spender['total'])),
                'benefit': 'AGAINST',
                'candidate': cand_name
            })

        candidates_data.append({
            'committee_id': comm.committee_id,
            'name': cand_name,
            'ie_for': float(abs(ie_for_amount)),
            'ie_against': float(abs(ie_against_amount)),
            'total_ie': float(abs(ie_for_amount) + abs(ie_against_amount)),
            'ie_for_spenders': for_spenders_list,
            'ie_against_spenders': against_spenders_list
        })

    # Sort candidates by total IE (highest first)
    candidates_data.sort(key=lambda x: x['total_ie'], reverse=True)

    # Get biggest IE spenders across the entire race
    biggest_spenders = sorted(all_ie_spenders, key=lambda x: x['amount'], reverse=True)[:10]

    # Get biggest donors to IE committees
    # Find all unique IE committee IDs
    ie_committee_ids = list(set([s['committee_id'] for s in all_ie_spenders]))

    # Get top donors to these IE committees
    top_donors_to_ies = Transaction.objects.filter(
        committee_id__in=ie_committee_ids,
        transaction_type__income_expense_neutral=1,  # Contributions
        deleted=False
    ).values(
        'entity__name_id',
        'entity__last_name',
        'entity__first_name'
    ).annotate(
        total_contributed=Sum('amount'),
        contribution_count=Count('transaction_id')
    ).order_by('-total_contributed')[:10]

    donors_list = []
    for donor in top_donors_to_ies:
        donor_name = f"{donor['entity__first_name'] or ''} {donor['entity__last_name']}".strip()
        donors_list.append({
            'entity_id': donor['entity__name_id'],
            'name': donor_name,
            'total_contributed': float(donor['total_contributed']),
            'contribution_count': donor['contribution_count']
        })

    # Calculate race totals
    total_ie_for = sum(c['ie_for'] for c in candidates_data)
    total_ie_against = sum(c['ie_against'] for c in candidates_data)
    total_ie_race = sum(c['total_ie'] for c in candidates_data)

    return Response({
        'race': {
            'office': office_name,
            'party': party_name,
            'cycle': cycle_year,
            'candidate_count': len(candidates_data),
            'total_ie_for': total_ie_for,
            'total_ie_against': total_ie_against,
            'total_ie': total_ie_race
        },
        'candidates': candidates_data,
        'biggest_ie_spenders': biggest_spenders,
        'biggest_donors_to_ies': donors_list
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def available_primary_races(request):
    """
    List all available primary races (races with 2+ candidates)
    """
    # Get all IE transaction types
    ie_types = TransactionType.objects.filter(
        Q(name__icontains='Independent Expenditure') | Q(name__icontains='Ind. Expend')
    )

    # Get all cycles
    cycles = Cycle.objects.filter(name__in=['2024', '2022', '2020', '2018', '2016']).order_by('-name')

    primary_races = []

    for cycle in cycles:
        for party in Party.objects.filter(name__in=['Democratic', 'Republican']):
            # Get all candidate committees for this cycle/party
            committees = Committee.objects.filter(
                election_cycle=cycle,
                candidate_party=party,
                candidate__isnull=False
            ).select_related('candidate_office')

            # Group by office
            from collections import defaultdict
            races_by_office = defaultdict(list)
            for comm in committees:
                if comm.candidate_office:
                    races_by_office[comm.candidate_office.name].append(comm)

            # Filter for primaries (2+ candidates)
            for office_name, comms in races_by_office.items():
                if len(comms) >= 2:
                    # Calculate total IE spending in this race
                    total_ie = 0
                    for comm in comms:
                        ie_amount = Transaction.objects.filter(
                            subject_committee=comm,
                            transaction_type__in=ie_types,
                            deleted=False
                        ).aggregate(total=Sum('amount'))['total'] or 0
                        total_ie += abs(float(ie_amount))

                    primary_races.append({
                        'office': office_name,
                        'party': party.name,
                        'cycle': cycle.name,
                        'candidate_count': len(comms),
                        'total_ie': total_ie
                    })

    # Sort by total IE (highest first)
    primary_races.sort(key=lambda x: x['total_ie'], reverse=True)

    return Response({
        'count': len(primary_races),
        'races': primary_races
    })
