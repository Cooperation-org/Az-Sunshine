# transparency/views_ie_analysis.py
"""
Phase 1 Completion: IE Analysis Views
Implements remaining requirements:
- IE spending aggregations by entity, race, and candidate
- IE donor tracking and tracing
- Grassroots threshold comparisons
- Enhanced race-level analytics
"""

from django.db.models import Sum, Count, Q, F, Value, CharField
from django.db.models.functions import Concat
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from django.core.cache import cache

from .models import (
    Committee, Transaction, Entity, Office, Cycle, Party
)


@api_view(['GET'])
@permission_classes([AllowAny])
def ie_spending_by_race(request):
    """
    Phase 1 Req 2a: Aggregate IE spending by race + Zstd compression
    GET /api/v1/ie-analysis/by-race/?office_id=1&cycle_id=1&date_from=2024-01-01&date_to=2024-12-31

    Returns IE spending for/against all candidates in a race
    Supports optional date_from and date_to filters for date range filtering
    """
    from transparency.utils.compressed_cache import CompressedCache

    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Build cache key (include date range if provided)
    cache_key = f'ie_spending_by_race_o{office_id}_c{cycle_id}'
    if date_from:
        cache_key += f'_df{date_from}'
    if date_to:
        cache_key += f'_dt{date_to}'

    # Try Zstd-compressed cache first (10 min TTL)
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        office = Office.objects.get(office_id=office_id)
        cycle = Cycle.objects.get(cycle_id=cycle_id)
    except (Office.DoesNotExist, Cycle.DoesNotExist):
        return Response(
            {'error': 'Invalid office_id or cycle_id'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get all candidates in this race
    candidates = Committee.objects.filter(
        candidate_office=office,
        election_cycle=cycle,
        candidate__isnull=False
    ).select_related('candidate', 'candidate_party', 'name')

    race_summary = []
    total_ie_for = Decimal('0')
    total_ie_against = Decimal('0')

    for candidate in candidates:
        # Build date filter for transactions
        date_filter = Q()
        if date_from:
            date_filter &= Q(transaction_date__gte=date_from)
        if date_to:
            date_filter &= Q(transaction_date__lte=date_to)

        # Get IE spending for this candidate
        ie_for = Transaction.objects.filter(
            date_filter,
            subject_committee=candidate,
            is_for_benefit=True,
            deleted=False
        ).aggregate(
            total=Sum('amount'),
            count=Count('transaction_id')
        )

        ie_against = Transaction.objects.filter(
            date_filter,
            subject_committee=candidate,
            is_for_benefit=False,
            deleted=False
        ).aggregate(
            total=Sum('amount'),
            count=Count('transaction_id')
        )
        
        for_amount = ie_for['total'] or Decimal('0')
        against_amount = ie_against['total'] or Decimal('0')
        net_amount = for_amount - against_amount
        
        total_ie_for += for_amount
        total_ie_against += against_amount
        
        race_summary.append({
            'committee_id': candidate.committee_id,
            'candidate_name': candidate.candidate.full_name if candidate.candidate else candidate.name.full_name,
            'party': candidate.candidate_party.name if candidate.candidate_party else None,
            'is_incumbent': candidate.is_incumbent,
            'ie_for': float(for_amount),
            'ie_for_count': ie_for['count'] or 0,
            'ie_against': float(against_amount),
            'ie_against_count': ie_against['count'] or 0,
            'ie_net': float(net_amount),
            'ie_total': float(for_amount + against_amount),
        })
    
    # Sort by total IE spending (descending)
    race_summary.sort(key=lambda x: x['ie_total'], reverse=True)

    response_data = {
        'office': {
            'office_id': office.office_id,
            'name': office.name,
            'office_type': office.office_type
        },
        'cycle': {
            'cycle_id': cycle.cycle_id,
            'name': cycle.name
        },
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
        },
        'summary': {
            'total_ie_for': float(total_ie_for),
            'total_ie_against': float(total_ie_against),
            'total_ie': float(total_ie_for + total_ie_against),
            'num_candidates': len(race_summary)
        },
        'candidates': race_summary
    }

    # Cache for 10 minutes with Zstd compression
    CompressedCache.set(cache_key, response_data, timeout=600)

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def ie_donors_by_candidate(request):
    """
    Phase 1 Req 2b-2c: Pull IE donors and trace funding
    GET /api/v1/ie-analysis/donors-by-candidate/?committee_id=123
    
    Traces IE spending back to original donors
    """
    committee_id = request.GET.get('committee_id')
    
    if not committee_id:
        return Response(
            {'error': 'committee_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        candidate = Committee.objects.get(committee_id=committee_id)
    except Committee.DoesNotExist:
        return Response(
            {'error': 'Invalid committee_id'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get all IE committees that spent on this candidate
    ie_committees = Committee.objects.filter(
        transactions__subject_committee=candidate,
        transactions__deleted=False
    ).distinct()
    
    # Get donors to those IE committees
    donors = Transaction.objects.filter(
        committee__in=ie_committees,
        transaction_type__income_expense_neutral=1,  # Contributions
        deleted=False
    ).values(
        'entity__name_id',
        'entity__last_name',
        'entity__first_name',
        'entity__entity_type__name',
        'entity__occupation',
        'entity__employer',
        'entity__city',
        'entity__state'
    ).annotate(
        total_contributed=Sum('amount'),
        num_contributions=Count('transaction_id')
    ).order_by('-total_contributed')[:50]  # Top 50 donors
    
    # Calculate indirect IE impact for each donor
    donor_list = []
    for donor in donors:
        # Get all IE spending by committees this donor contributed to
        committees_donated_to = Transaction.objects.filter(
            entity__name_id=donor['entity__name_id'],
            transaction_type__income_expense_neutral=1,
            deleted=False
        ).values_list('committee_id', flat=True).distinct()
        
        ie_impact = Transaction.objects.filter(
            committee_id__in=committees_donated_to,
            subject_committee=candidate,
            deleted=False
        ).aggregate(
            for_amount=Sum('amount', filter=Q(is_for_benefit=True)),
            against_amount=Sum('amount', filter=Q(is_for_benefit=False))
        )
        
        donor_list.append({
            'entity_id': donor['entity__name_id'],
            'name': f"{donor['entity__first_name'] or ''} {donor['entity__last_name']}".strip(),
            'entity_type': donor['entity__entity_type__name'],
            'occupation': donor['entity__occupation'],
            'employer': donor['entity__employer'],
            'location': f"{donor['entity__city']}, {donor['entity__state']}" if donor['entity__city'] and donor['entity__state'] else None,
            'total_contributed': float(donor['total_contributed']),
            'num_contributions': donor['num_contributions'],
            'ie_impact_for': float(ie_impact['for_amount'] or 0),
            'ie_impact_against': float(ie_impact['against_amount'] or 0),
            'ie_impact_total': float((ie_impact['for_amount'] or 0) + (ie_impact['against_amount'] or 0))
        })
    
    return Response({
        'candidate': {
            'committee_id': candidate.committee_id,
            'name': candidate.candidate.full_name if candidate.candidate else candidate.name.full_name,
            'office': candidate.candidate_office.name if candidate.candidate_office else None,
            'party': candidate.candidate_party.name if candidate.candidate_party else None
        },
        'ie_committees_count': ie_committees.count(),
        'top_donors': donor_list
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def grassroots_threshold_analysis(request):
    """
    Phase 1 Req 2d-2e: Grassroots threshold comparison + Zstd compression
    GET /api/v1/ie-analysis/grassroots-threshold/?cycle_id=1&office_id=1&threshold=5000

    Compares IE spending to grassroots threshold for all candidates
    """
    from transparency.utils.compressed_cache import CompressedCache

    cycle_id = request.GET.get('cycle_id', '')
    office_id = request.GET.get('office_id', '')
    threshold = Decimal(request.GET.get('threshold', '5000'))

    # Build cache key
    cache_key = f'grassroots_threshold_c{cycle_id}_o{office_id}_t{threshold}'

    # Try Zstd-compressed cache first (10 min TTL)
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)
    
    filters = Q(candidate__isnull=False)
    
    if cycle_id:
        filters &= Q(election_cycle_id=cycle_id)
    
    if office_id:
        filters &= Q(candidate_office_id=office_id)
    
    # Get all candidate committees
    candidates = Committee.objects.filter(filters).select_related(
        'candidate', 'candidate_office', 'candidate_party', 'name', 'election_cycle'
    )
    
    results = []
    over_threshold_count = 0
    
    for candidate in candidates:
        # Get IE totals
        ie_totals = Transaction.objects.filter(
            subject_committee=candidate,
            deleted=False
        ).aggregate(
            ie_for=Sum('amount', filter=Q(is_for_benefit=True)),
            ie_against=Sum('amount', filter=Q(is_for_benefit=False))
        )
        
        ie_for = ie_totals['ie_for'] or Decimal('0')
        ie_against = ie_totals['ie_against'] or Decimal('0')
        ie_total = ie_for + ie_against
        
        over_threshold = ie_total > threshold
        if over_threshold:
            over_threshold_count += 1
        
        results.append({
            'committee_id': candidate.committee_id,
            'candidate_name': candidate.candidate.full_name if candidate.candidate else candidate.name.full_name,
            'office': candidate.candidate_office.name if candidate.candidate_office else None,
            'party': candidate.candidate_party.name if candidate.candidate_party else None,
            'cycle': candidate.election_cycle.name if candidate.election_cycle else None,
            'ie_for': float(ie_for),
            'ie_against': float(ie_against),
            'ie_total': float(ie_total),
            'over_threshold': over_threshold,
            'times_threshold': float(ie_total / threshold) if threshold > 0 else 0,
            'amount_over_threshold': float(ie_total - threshold) if over_threshold else 0
        })
    
    # Sort by IE total (descending)
    results.sort(key=lambda x: x['ie_total'], reverse=True)

    response_data = {
        'threshold': float(threshold),
        'total_candidates': len(results),
        'over_threshold_count': over_threshold_count,
        'under_threshold_count': len(results) - over_threshold_count,
        'candidates': results
    }

    # Cache for 10 minutes with Zstd compression
    CompressedCache.set(cache_key, response_data, timeout=600)

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def ie_committees_spending(request):
    """
    Get all IE committees and their spending activity
    GET /api/v1/ie-analysis/ie-committees/?cycle_id=1
    """
    cycle_id = request.GET.get('cycle_id')
    
    # Get committees that have made IE spending
    filters = Q(
        transactions__subject_committee__isnull=False,
        transactions__deleted=False
    )
    
    if cycle_id:
        filters &= Q(election_cycle_id=cycle_id)
    
    ie_committees = Committee.objects.filter(filters).distinct().select_related(
        'name', 'sponsor', 'election_cycle'
    ).annotate(
        total_ie_spending=Sum(
            'transactions__amount',
            filter=Q(
                transactions__subject_committee__isnull=False,
                transactions__deleted=False
            )
        ),
        num_ie_transactions=Count(
            'transactions',
            filter=Q(
                transactions__subject_committee__isnull=False,
                transactions__deleted=False
            )
        ),
        candidates_supported=Count(
            'transactions__subject_committee',
            filter=Q(
                transactions__subject_committee__isnull=False,
                transactions__is_for_benefit=True,
                transactions__deleted=False
            ),
            distinct=True
        ),
        candidates_opposed=Count(
            'transactions__subject_committee',
            filter=Q(
                transactions__subject_committee__isnull=False,
                transactions__is_for_benefit=False,
                transactions__deleted=False
            ),
            distinct=True
        )
    ).order_by('-total_ie_spending')
    
    results = []
    for committee in ie_committees:
        results.append({
            'committee_id': committee.committee_id,
            'name': committee.name.full_name if committee.name else 'Unknown',
            'sponsor': committee.sponsor.full_name if committee.sponsor else None,
            'cycle': committee.election_cycle.name if committee.election_cycle else None,
            'total_ie_spending': float(committee.total_ie_spending or 0),
            'num_ie_transactions': committee.num_ie_transactions,
            'candidates_supported': committee.candidates_supported,
            'candidates_opposed': committee.candidates_opposed
        })
    
    return Response({
        'total_ie_committees': len(results),
        'total_ie_spending': sum(r['total_ie_spending'] for r in results),
        'ie_committees': results
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def donor_ie_impact_analysis(request):
    """
    Phase 1: Analyze a donor's total IE impact across all races
    GET /api/v1/ie-analysis/donor-impact/?entity_id=123
    
    Shows how a donor's contributions translate to IE spending
    """
    entity_id = request.GET.get('entity_id')
    
    if not entity_id:
        return Response(
            {'error': 'entity_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        entity = Entity.objects.get(name_id=entity_id)
    except Entity.DoesNotExist:
        return Response(
            {'error': 'Invalid entity_id'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get total contributions by this donor
    contribution_summary = Transaction.objects.filter(
        entity=entity,
        transaction_type__income_expense_neutral=1,
        deleted=False
    ).aggregate(
        total_contributed=Sum('amount'),
        num_contributions=Count('transaction_id')
    )
    
    # Get committees this donor contributed to
    committees_donated_to = Transaction.objects.filter(
        entity=entity,
        transaction_type__income_expense_neutral=1,
        deleted=False
    ).values_list('committee_id', flat=True).distinct()
    
    # Get all IE spending by those committees
    ie_impact = Transaction.objects.filter(
        committee_id__in=committees_donated_to,
        subject_committee__isnull=False,
        deleted=False
    ).values(
        'subject_committee__committee_id',
        'subject_committee__name__first_name',
        'subject_committee__name__last_name',
        'subject_committee__candidate_office__name',
        'subject_committee__candidate_party__name',
        'is_for_benefit'
    ).annotate(
        ie_total=Sum('amount'),
        num_transactions=Count('transaction_id')
    ).order_by('-ie_total')
    
    candidates_impacted = []
    total_ie_impact = Decimal('0')
    
    for impact in ie_impact:
        ie_amount = impact['ie_total'] or Decimal('0')
        total_ie_impact += ie_amount
        
        candidates_impacted.append({
            'committee_id': impact['subject_committee__committee_id'],
            'candidate_name': f"{impact['subject_committee__name__first_name'] or ''} {impact['subject_committee__name__last_name']}".strip(),
            'office': impact['subject_committee__candidate_office__name'],
            'party': impact['subject_committee__candidate_party__name'],
            'support_oppose': 'Support' if impact['is_for_benefit'] else 'Oppose',
            'ie_amount': float(ie_amount),
            'num_transactions': impact['num_transactions']
        })
    
    return Response({
        'donor': {
            'entity_id': entity.name_id,
            'name': entity.full_name,
            'entity_type': entity.entity_type.name if entity.entity_type else None,
            'occupation': entity.occupation,
            'employer': entity.employer
        },
        'contribution_summary': {
            'total_contributed': float(contribution_summary['total_contributed'] or 0),
            'num_contributions': contribution_summary['num_contributions']
        },
        'ie_impact_summary': {
            'total_ie_impact': float(total_ie_impact),
            'committees_donated_to': len(committees_donated_to),
            'candidates_impacted': len(candidates_impacted)
        },
        'candidates_impacted': candidates_impacted
    })
    

@api_view(['GET'])
@permission_classes([AllowAny])
def top_candidates_by_ie(request):
    """
    Phase 1 Visualization: Top candidates by IE spending + Zstd compression
    GET /api/v1/ie-analysis/top-candidates/

    Query params:
    - office_id: Filter by office (optional)
    - cycle_id: Filter by cycle (optional)
    - limit: Number of candidates to return (default 20)

    Returns top candidates sorted by total IE spending (for + against)
    """
    from transparency.utils.compressed_cache import CompressedCache

    office_id = request.GET.get('office_id', '')
    cycle_id = request.GET.get('cycle_id', '')
    limit = int(request.GET.get('limit', 20))

    # Build cache key
    cache_key = f'top_candidates_by_ie_o{office_id}_c{cycle_id}_l{limit}'

    # Try Zstd-compressed cache first (10 min TTL)
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)
    
    # Base queryset - candidate committees only
    committees = Committee.objects.filter(
        candidate__isnull=False
    ).select_related('candidate', 'candidate_party', 'candidate_office')
    
    # Apply filters
    if office_id:
        committees = committees.filter(candidate_office_id=office_id)
    if cycle_id:
        committees = committees.filter(election_cycle_id=cycle_id)
    
    # Aggregate IE spending for each candidate
    candidates_data = []
    total_ie_for = Decimal('0')
    total_ie_against = Decimal('0')
    
    for committee in committees:
        # IE spending FOR candidate
        ie_for = Transaction.objects.filter(
            subject_committee=committee,
            is_for_benefit=True,
            deleted=False
        ).aggregate(
            total=Sum('amount'),
            count=Count('transaction_id')
        )
        
        # IE spending AGAINST candidate
        ie_against = Transaction.objects.filter(
            subject_committee=committee,
            is_for_benefit=False,
            deleted=False
        ).aggregate(
            total=Sum('amount'),
            count=Count('transaction_id')
        )
        
        for_amount = ie_for['total'] or Decimal('0')
        against_amount = ie_against['total'] or Decimal('0')
        total_amount = for_amount + against_amount
        
        # Only include candidates with IE activity
        if total_amount > 0:
            total_ie_for += for_amount
            total_ie_against += against_amount
            
            candidates_data.append({
                'committee_id': committee.committee_id,
                'candidate_name': committee.candidate.full_name if committee.candidate else committee.name.full_name,
                'office': committee.candidate_office.name if committee.candidate_office else None,
                'party': committee.candidate_party.name if committee.candidate_party else None,
                'ie_for': float(for_amount),
                'ie_against': float(against_amount),
                'ie_net': float(for_amount - against_amount),
                'ie_total': float(total_amount),
                'ie_for_count': ie_for['count'] or 0,
                'ie_against_count': ie_against['count'] or 0,
            })
    
    # Sort by total IE spending (descending) and limit
    candidates_data.sort(key=lambda x: x['ie_total'], reverse=True)
    top_candidates = candidates_data[:limit]

    response_data = {
        'summary': {
            'total_ie_for': float(total_ie_for),
            'total_ie_against': float(total_ie_against),
            'total_ie': float(total_ie_for + total_ie_against),
            'num_candidates': len(top_candidates),
            'total_candidates_with_ie': len(candidates_data)
        },
        'candidates': top_candidates
    }

    # Cache for 10 minutes with Zstd compression
    CompressedCache.set(cache_key, response_data, timeout=600)

    return Response(response_data)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def money_flow_through_pacs(request):
    """
    Phase 1 Visualization: Track money flow through PACs
    GET /api/v1/ie-analysis/money-flow/
    
    Query params:
    - office_id: Filter by office (optional)
    - cycle_id: Filter by cycle (optional)
    - limit: Number of flows to return (default 10)
    
    Returns flow paths: Donors → IE Committees → Candidates
    """
    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')
    limit = int(request.GET.get('limit', 10))
    
    # Get IE committees
    ie_committees = Committee.objects.filter(
        committee_type__name__icontains='independent'
    ).select_related('name')
    
    flows = []
    total_donors = set()
    total_committees = set()
    total_candidates = set()
    total_amount = Decimal('0')
    
    for committee in ie_committees[:limit]:
        # Get contributions TO this IE committee (from donors)
        contributions = Transaction.objects.filter(
            committee=committee,
            transaction_type__income_expense_neutral='Income',
            deleted=False
        ).select_related('entity').values(
            'entity_id',
            'entity__first_name',
            'entity__last_name'
        ).annotate(
            donor_amount=Sum('amount')
        ).order_by('-donor_amount')
        
        # Get IE spending BY this committee
        ie_spending = Transaction.objects.filter(
            committee=committee,
            subject_committee__isnull=False,
            deleted=False
        ).select_related(
            'subject_committee__candidate'
        ).values(
            'subject_committee_id',
            'is_for_benefit'
        ).annotate(
            spending_amount=Sum('amount'),
            num_transactions=Count('transaction_id')
        )
        
        if contributions.exists() and ie_spending.exists():
            # Calculate flow totals
            total_contrib = sum(c['donor_amount'] for c in contributions if c['donor_amount'])
            total_spend = sum(s['spending_amount'] for s in ie_spending if s['spending_amount'])
            
            # Get top donor
            top_donor = contributions.first()
            top_donor_name = f"{top_donor['entity__first_name'] or ''} {top_donor['entity__last_name'] or ''}".strip()
            
            # Get top candidate target
            top_spending = list(ie_spending.order_by('-spending_amount'))[:1]
            if top_spending:
                target_committee = Committee.objects.get(
                    committee_id=top_spending[0]['subject_committee_id']
                )
                top_candidate = (
                    target_committee.candidate.full_name 
                    if target_committee.candidate 
                    else target_committee.name.full_name
                )
            else:
                top_candidate = None
            
            # Determine spending type
            support_spending = sum(
                s['spending_amount'] for s in ie_spending 
                if s['is_for_benefit'] and s['spending_amount']
            ) or Decimal('0')
            oppose_spending = sum(
                s['spending_amount'] for s in ie_spending 
                if not s['is_for_benefit'] and s['spending_amount']
            ) or Decimal('0')
            
            spending_type = 'Support' if support_spending > oppose_spending else 'Oppose'
            primary_amount = max(support_spending, oppose_spending)
            
            # Build flow details
            flow = {
                'committee_id': committee.committee_id,
                'committee_name': committee.name.full_name,
                'num_donors': contributions.count(),
                'num_candidates': ie_spending.values('subject_committee_id').distinct().count(),
                'total_amount': float(primary_amount),
                'top_donor': top_donor_name if top_donor_name else 'Anonymous',
                'top_candidate': top_candidate,
                'spending_type': spending_type,
                'details': {
                    'top_donors': [
                        {
                            'name': f"{c['entity__first_name'] or ''} {c['entity__last_name'] or ''}".strip(),
                            'amount': float(c['donor_amount'] or 0)
                        }
                        for c in contributions[:5]
                    ],
                    'total_contributions': float(total_contrib),
                    'total_spending': float(total_spend),
                    'support_spending': float(support_spending),
                    'oppose_spending': float(oppose_spending),
                }
            }
            
            flows.append(flow)
            
            # Track totals
            for c in contributions:
                if c['entity_id']:
                    total_donors.add(c['entity_id'])
            total_committees.add(committee.committee_id)
            for s in ie_spending:
                total_candidates.add(s['subject_committee_id'])
            total_amount += primary_amount
    
    # Sort by total amount descending
    flows.sort(key=lambda x: x['total_amount'], reverse=True)
    
    return Response({
        'summary': {
            'total_donors': len(total_donors),
            'total_committees': len(total_committees),
            'total_candidates': len(total_candidates),
            'total_amount': float(total_amount),
            'num_flows': len(flows)
        },
        'flows': flows[:limit]
    })