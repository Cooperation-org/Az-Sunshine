# transparency/views_fec.py
"""
FEC Federal Election Data API Endpoints

Provides access to FEC independent expenditure data for Arizona federal races.
The FECIndependentExpenditure model will be populated by another agent.

Endpoints:
- GET /api/fec/races/ - List federal races with spending totals
- GET /api/fec/race/<race>/<cycle>/ - Detailed spending for a specific race
- GET /api/fec/committees/ - List federal PACs that spent in Arizona
- GET /api/fec/search/ - Search expenditures by committee or candidate name
"""

from django.db.models import Sum, Count, Q, F
from django.db.models.functions import Abs
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from django.core.cache import cache

# Import the FEC model - will be created by another agent
try:
    from .models import FECIndependentExpenditure
    FEC_MODEL_AVAILABLE = True
except ImportError:
    FEC_MODEL_AVAILABLE = False


def fec_model_required(func):
    """Decorator to check if FEC model is available"""
    def wrapper(*args, **kwargs):
        if not FEC_MODEL_AVAILABLE:
            return Response(
                {
                    'error': 'FEC data not yet available',
                    'message': 'The FECIndependentExpenditure model has not been created yet. '
                               'Please wait for the data import to complete.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return func(*args, **kwargs)
    return wrapper


@api_view(['GET'])
@permission_classes([AllowAny])
@fec_model_required
def fec_races(request):
    """
    GET /api/fec/races/

    Returns list of federal races with spending totals.
    Groups by race (AZ-S1, AZ-01, etc.) and cycle.

    Query params:
    - cycle: Filter by election cycle (e.g., 2024)
    - race_type: Filter by race type (senate, house)

    Response:
    {
        "total_races": 10,
        "total_spending": 15000000.00,
        "races": [
            {
                "race": "AZ-S1",
                "cycle": 2024,
                "race_type": "senate",
                "total_spending": 5000000.00,
                "support_amount": 3000000.00,
                "oppose_amount": 2000000.00,
                "num_committees": 15,
                "num_expenditures": 250
            },
            ...
        ]
    }
    """
    cycle = request.GET.get('cycle')
    race_type = request.GET.get('race_type')

    # Build cache key
    cache_key = f'fec_races_c{cycle}_t{race_type}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    # Build filters
    filters = Q()
    if cycle:
        filters &= Q(cycle=int(cycle))
    if race_type:
        filters &= Q(candidate_office__iexact=race_type)

    # Aggregate by race and cycle
    races = FECIndependentExpenditure.objects.filter(filters).values(
        'race', 'cycle', 'candidate_office'
    ).annotate(
        total_spending=Sum(Abs('amount')),
        support_amount=Sum(Abs('amount'), filter=Q(is_support=True)),
        oppose_amount=Sum(Abs('amount'), filter=Q(is_support=False)),
        num_committees=Count('committee_id', distinct=True),
        num_expenditures=Count('fec_file_id')
    ).order_by('-total_spending')

    # Calculate totals
    total_spending = sum(r['total_spending'] or Decimal('0') for r in races)

    # Format response
    race_list = []
    for r in races:
        # Determine race type from candidate_office (H=House, S=Senate)
        race_type = 'house' if r['candidate_office'] == 'H' else 'senate' if r['candidate_office'] == 'S' else 'unknown'
        race_list.append({
            'race': r['race'],
            'cycle': r['cycle'],
            'race_type': race_type,
            'total_spending': float(r['total_spending'] or 0),
            'support_amount': float(r['support_amount'] or 0),
            'oppose_amount': float(r['oppose_amount'] or 0),
            'num_committees': r['num_committees'],
            'num_expenditures': r['num_expenditures']
        })

    response_data = {
        'total_races': len(race_list),
        'total_spending': float(total_spending),
        'races': race_list
    }

    # Cache for 10 minutes
    cache.set(cache_key, response_data, timeout=600)

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
@fec_model_required
def fec_race_detail(request, race, cycle):
    """
    GET /api/fec/race/<race>/<cycle>/

    Returns detailed spending for a specific race.
    Includes top spenders and candidate breakdown.

    Path params:
    - race: Race identifier (e.g., AZ-S1, AZ-01)
    - cycle: Election cycle (e.g., 2024)

    Response:
    {
        "race": "AZ-S1",
        "cycle": 2024,
        "race_type": "senate",
        "summary": {
            "total_spending": 5000000.00,
            "support_amount": 3000000.00,
            "oppose_amount": 2000000.00,
            "num_committees": 15,
            "num_expenditures": 250
        },
        "candidates": [
            {
                "candidate_name": "Jane Smith",
                "candidate_party": "DEM",
                "support_spending": 1500000.00,
                "oppose_spending": 500000.00,
                "net_spending": 1000000.00,
                "num_expenditures": 75
            },
            ...
        ],
        "top_spenders": [
            {
                "committee_id": "C12345678",
                "committee_name": "Americans for Progress",
                "total_spending": 1000000.00,
                "support_amount": 800000.00,
                "oppose_amount": 200000.00,
                "num_expenditures": 25
            },
            ...
        ],
        "recent_expenditures": [
            {
                "id": 12345,
                "committee_name": "Americans for Progress",
                "amount": 50000.00,
                "support_oppose": "S",
                "candidate_name": "Jane Smith",
                "expenditure_date": "2024-10-15",
                "purpose": "Digital advertising"
            },
            ...
        ]
    }
    """
    # Build cache key
    cache_key = f'fec_race_detail_{race}_{cycle}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    # Get all expenditures for this race
    expenditures = FECIndependentExpenditure.objects.filter(
        race=race,
        cycle=int(cycle)
    )

    if not expenditures.exists():
        return Response(
            {'error': f'No data found for race {race} in cycle {cycle}'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get race type from first record
    first_record = expenditures.first()
    race_type = 'house' if first_record and first_record.candidate_office == 'H' else 'senate' if first_record and first_record.candidate_office == 'S' else 'unknown'

    # Calculate summary
    summary = expenditures.aggregate(
        total_spending=Sum(Abs('amount')),
        support_amount=Sum(Abs('amount'), filter=Q(is_support=True)),
        oppose_amount=Sum(Abs('amount'), filter=Q(is_support=False)),
        num_committees=Count('committee_id', distinct=True),
        num_expenditures=Count('fec_file_id')
    )

    # Candidate breakdown
    candidates_data = expenditures.values(
        'candidate_name', 'candidate_party'
    ).annotate(
        support_spending=Sum(Abs('amount'), filter=Q(is_support=True)),
        oppose_spending=Sum(Abs('amount'), filter=Q(is_support=False)),
        num_expenditures=Count('fec_file_id')
    ).order_by('-support_spending')

    candidates = []
    for c in candidates_data:
        support = c['support_spending'] or Decimal('0')
        oppose = c['oppose_spending'] or Decimal('0')
        candidates.append({
            'candidate_name': c['candidate_name'],
            'candidate_party': c['candidate_party'],
            'support_spending': float(support),
            'oppose_spending': float(oppose),
            'net_spending': float(support - oppose),
            'num_expenditures': c['num_expenditures']
        })

    # Top spenders
    top_spenders_data = expenditures.values(
        'committee_id', 'committee_name'
    ).annotate(
        total_spending=Sum(Abs('amount')),
        support_amount=Sum(Abs('amount'), filter=Q(is_support=True)),
        oppose_amount=Sum(Abs('amount'), filter=Q(is_support=False)),
        num_expenditures=Count('fec_file_id')
    ).order_by('-total_spending')[:20]

    top_spenders = []
    for s in top_spenders_data:
        top_spenders.append({
            'committee_id': s['committee_id'],
            'committee_name': s['committee_name'],
            'total_spending': float(s['total_spending'] or 0),
            'support_amount': float(s['support_amount'] or 0),
            'oppose_amount': float(s['oppose_amount'] or 0),
            'num_expenditures': s['num_expenditures']
        })

    # Recent expenditures
    recent = expenditures.order_by('-expenditure_date')[:25]
    recent_expenditures = []
    for e in recent:
        recent_expenditures.append({
            'fec_file_id': e.fec_file_id,
            'committee_name': e.committee_name,
            'amount': float(abs(e.amount)),
            'support_oppose': 'S' if e.is_support else 'O',
            'candidate_name': e.candidate_name,
            'expenditure_date': e.expenditure_date.isoformat() if e.expenditure_date else None,
            'purpose': e.expenditure_description or ''
        })

    response_data = {
        'race': race,
        'cycle': int(cycle),
        'race_type': race_type,
        'summary': {
            'total_spending': float(summary['total_spending'] or 0),
            'support_amount': float(summary['support_amount'] or 0),
            'oppose_amount': float(summary['oppose_amount'] or 0),
            'num_committees': summary['num_committees'],
            'num_expenditures': summary['num_expenditures']
        },
        'candidates': candidates,
        'top_spenders': top_spenders,
        'recent_expenditures': recent_expenditures
    }

    # Cache for 10 minutes
    cache.set(cache_key, response_data, timeout=600)

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
@fec_model_required
def fec_committees(request):
    """
    GET /api/fec/committees/

    Returns list of federal PACs that spent in Arizona.
    Includes total spending and races targeted.

    Query params:
    - cycle: Filter by election cycle
    - min_spending: Minimum total spending threshold
    - limit: Number of committees to return (default 50)

    Response:
    {
        "total_committees": 100,
        "total_spending": 25000000.00,
        "committees": [
            {
                "committee_id": "C12345678",
                "committee_name": "Americans for Progress",
                "total_spending": 2500000.00,
                "support_amount": 2000000.00,
                "oppose_amount": 500000.00,
                "num_expenditures": 150,
                "races_targeted": ["AZ-S1", "AZ-01", "AZ-06"],
                "cycles_active": [2022, 2024]
            },
            ...
        ]
    }
    """
    cycle = request.GET.get('cycle')
    state = request.GET.get('state', 'AZ')  # Default to Arizona
    min_spending = request.GET.get('min_spending')
    limit = int(request.GET.get('limit', 50))

    # Build cache key
    cache_key = f'fec_committees_c{cycle}_s{state}_m{min_spending}_l{limit}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    # Build filters - always filter by state (races starting with state code)
    filters = Q(race__startswith=state)
    if cycle:
        filters &= Q(cycle=int(cycle))

    # Aggregate by committee
    committees_data = FECIndependentExpenditure.objects.filter(filters).values(
        'committee_id', 'committee_name'
    ).annotate(
        total_spending=Sum(Abs('amount')),
        support_amount=Sum(Abs('amount'), filter=Q(is_support=True)),
        oppose_amount=Sum(Abs('amount'), filter=Q(is_support=False)),
        num_expenditures=Count('fec_file_id')
    ).order_by('-total_spending')

    # Apply minimum spending filter
    if min_spending:
        committees_data = committees_data.filter(total_spending__gte=Decimal(min_spending))

    # Limit results
    committees_data = committees_data[:limit]

    # Get races and cycles for each committee
    committees = []
    total_spending = Decimal('0')

    for c in committees_data:
        committee_id = c['committee_id']

        # Get races targeted by this committee (filtered by state)
        races = list(FECIndependentExpenditure.objects.filter(
            filters,
            committee_id=committee_id
        ).values_list('race', flat=True).distinct())

        # Get cycles this committee was active (in this state)
        cycles = list(FECIndependentExpenditure.objects.filter(
            filters,
            committee_id=committee_id
        ).values_list('cycle', flat=True).distinct().order_by('cycle'))

        spending = c['total_spending'] or Decimal('0')
        total_spending += spending

        committees.append({
            'committee_id': committee_id,
            'committee_name': c['committee_name'],
            'total_spending': float(spending),
            'support_amount': float(c['support_amount'] or 0),
            'oppose_amount': float(c['oppose_amount'] or 0),
            'num_expenditures': c['num_expenditures'],
            'races_targeted': races,
            'cycles_active': cycles
        })

    response_data = {
        'total_committees': len(committees),
        'total_spending': float(total_spending),
        'committees': committees
    }

    # Cache for 10 minutes
    cache.set(cache_key, response_data, timeout=600)

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
@fec_model_required
def fec_search(request):
    """
    GET /api/fec/search/?q=<query>

    Search expenditures by committee name or candidate name.

    Query params:
    - q: Search query (required)
    - cycle: Filter by election cycle
    - race: Filter by race
    - limit: Number of results to return (default 50)

    Response:
    {
        "query": "Americans",
        "total_results": 150,
        "expenditures": [
            {
                "id": 12345,
                "committee_id": "C12345678",
                "committee_name": "Americans for Progress",
                "amount": 50000.00,
                "support_oppose": "S",
                "candidate_name": "Jane Smith",
                "candidate_party": "DEM",
                "race": "AZ-S1",
                "cycle": 2024,
                "expenditure_date": "2024-10-15",
                "purpose": "Digital advertising"
            },
            ...
        ],
        "facets": {
            "committees": [
                {"name": "Americans for Progress", "count": 75},
                ...
            ],
            "candidates": [
                {"name": "Jane Smith", "count": 50},
                ...
            ],
            "races": [
                {"name": "AZ-S1", "count": 100},
                ...
            ]
        }
    }
    """
    query = request.GET.get('q', '').strip()
    cycle = request.GET.get('cycle')
    race = request.GET.get('race')
    limit = int(request.GET.get('limit', 50))

    if not query:
        return Response(
            {'error': 'Search query is required. Use ?q=<query>'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(query) < 2:
        return Response(
            {'error': 'Search query must be at least 2 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Build filters
    filters = Q(committee_name__icontains=query) | Q(candidate_name__icontains=query)

    if cycle:
        filters &= Q(cycle=int(cycle))
    if race:
        filters &= Q(race=race)

    # Search expenditures
    results = FECIndependentExpenditure.objects.filter(filters).order_by(
        '-expenditure_date', '-amount'
    )

    total_results = results.count()

    # Get paginated results
    expenditures = []
    for e in results[:limit]:
        expenditures.append({
            'fec_file_id': e.fec_file_id,
            'committee_id': e.committee_id,
            'committee_name': e.committee_name,
            'amount': float(abs(e.amount)),
            'support_oppose': 'S' if e.is_support else 'O',
            'candidate_name': e.candidate_name,
            'candidate_party': e.candidate_party,
            'race': e.race,
            'cycle': e.cycle,
            'expenditure_date': e.expenditure_date.isoformat() if e.expenditure_date else None,
            'purpose': e.expenditure_description or ''
        })

    # Generate facets for filtering
    # Top committees
    committee_facets = results.values('committee_name').annotate(
        count=Count('fec_file_id')
    ).order_by('-count')[:10]

    # Top candidates
    candidate_facets = results.values('candidate_name').annotate(
        count=Count('fec_file_id')
    ).order_by('-count')[:10]

    # Races
    race_facets = results.values('race').annotate(
        count=Count('fec_file_id')
    ).order_by('-count')[:10]

    response_data = {
        'query': query,
        'total_results': total_results,
        'expenditures': expenditures,
        'facets': {
            'committees': [
                {'name': f['committee_name'], 'count': f['count']}
                for f in committee_facets
            ],
            'candidates': [
                {'name': f['candidate_name'], 'count': f['count']}
                for f in candidate_facets
            ],
            'races': [
                {'name': f['race'], 'count': f['count']}
                for f in race_facets
            ]
        }
    }

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def fec_status(request):
    """
    GET /api/fec/status/

    Returns the status of FEC data availability.
    Useful for frontend to know if FEC endpoints are ready.

    Response:
    {
        "available": true,
        "model_created": true,
        "record_count": 15000,
        "last_updated": "2024-10-15T12:00:00Z",
        "cycles_available": [2020, 2022, 2024],
        "races_available": ["AZ-S1", "AZ-01", ...]
    }
    """
    if not FEC_MODEL_AVAILABLE:
        return Response({
            'available': False,
            'model_created': False,
            'record_count': 0,
            'last_updated': None,
            'cycles_available': [],
            'races_available': [],
            'message': 'FECIndependentExpenditure model has not been created yet'
        })

    try:
        record_count = FECIndependentExpenditure.objects.count()

        if record_count == 0:
            return Response({
                'available': False,
                'model_created': True,
                'record_count': 0,
                'last_updated': None,
                'cycles_available': [],
                'races_available': [],
                'message': 'Model exists but no data has been imported yet'
            })

        # Get available cycles
        cycles = list(FECIndependentExpenditure.objects.values_list(
            'cycle', flat=True
        ).distinct().order_by('cycle'))

        # Get available races
        races = list(FECIndependentExpenditure.objects.values_list(
            'race', flat=True
        ).distinct().order_by('race'))

        # Get last updated (most recent expenditure date)
        last_record = FECIndependentExpenditure.objects.order_by('-expenditure_date').first()
        last_updated = last_record.expenditure_date.isoformat() if last_record and last_record.expenditure_date else None

        return Response({
            'available': True,
            'model_created': True,
            'record_count': record_count,
            'last_updated': last_updated,
            'cycles_available': cycles,
            'races_available': races
        })

    except Exception as e:
        return Response({
            'available': False,
            'model_created': True,
            'record_count': 0,
            'last_updated': None,
            'cycles_available': [],
            'races_available': [],
            'error': str(e)
        })
