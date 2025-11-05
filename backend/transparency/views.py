# views.py for Arizona Sunshine Transparency Project - PHASE 1
# API endpoints for React frontend

from django.db.models import Sum, Count, Q, F, Prefetch
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    Committee, Entity, Transaction, Office, Cycle, Party,
    CandidateStatementOfInterest, BallotMeasure, Report,
    RaceAggregationManager, Phase1DataValidator
)
from .serializers import (
    CommitteeSerializer, CommitteeDetailSerializer,
    EntitySerializer, EntityDetailSerializer,
    TransactionSerializer, CandidateSOISerializer,
    OfficeSerializer, CycleSerializer, RaceAggregationSerializer
)


# ==================== PAGINATION ====================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500


# ==================== PHASE 1: CANDIDATE TRACKING ====================

class CandidateSOIViewSet(viewsets.ModelViewSet):
    """
    Phase 1 Requirement 1: New candidate notification
    Track statements of interest, emails, and pledge status
    """
    queryset = CandidateStatementOfInterest.objects.all()
    serializer_class = CandidateSOISerializer
    permission_classes = [AllowAny]  # Adjust based on your auth requirements
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = CandidateStatementOfInterest.objects.select_related(
            'office', 'entity'
        )
        
        # Filter by contact status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(contact_status=status)
        
        # Filter by pledge received
        pledge = self.request.query_params.get('pledge_received', None)
        if pledge is not None:
            queryset = queryset.filter(pledge_received=pledge.lower() == 'true')
        
        # Filter by office
        office_id = self.request.query_params.get('office', None)
        if office_id:
            queryset = queryset.filter(office_id=office_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(filing_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(filing_date__lte=date_to)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def uncontacted(self, request):
        """Get all uncontacted candidates for email outreach"""
        uncontacted = self.get_queryset().filter(
            contact_status='uncontacted'
        ).order_by('-filing_date')
        
        page = self.paginate_queryset(uncontacted)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_pledges(self, request):
        """Get candidates contacted but no pledge received"""
        pending = self.get_queryset().filter(
            contact_status='contacted',
            pledge_received=False
        ).order_by('-contact_date')
        
        page = self.paginate_queryset(pending)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary_stats(self, request):
        """Dashboard stats for SOI tracking"""
        queryset = self.get_queryset()
        
        stats = {
            'total_filings': queryset.count(),
            'uncontacted': queryset.filter(contact_status='uncontacted').count(),
            'contacted': queryset.filter(contact_status='contacted').count(),
            'acknowledged': queryset.filter(contact_status='acknowledged').count(),
            'pledges_received': queryset.filter(pledge_received=True).count(),
            'pledge_rate': 0,
            'recent_filings_7days': queryset.filter(
                filing_date__gte=timezone.now().date() - timedelta(days=7)
            ).count(),
        }
        
        contacted_total = queryset.exclude(contact_status='uncontacted').count()
        if contacted_total > 0:
            stats['pledge_rate'] = round(
                (stats['pledges_received'] / contacted_total) * 100, 1
            )
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def mark_contacted(self, request, pk=None):
        """Mark candidate as contacted"""
        soi = self.get_object()
        soi.contact_status = 'contacted'
        soi.contact_date = timezone.now().date()
        soi.contacted_by = request.data.get('contacted_by', '')
        soi.save()
        
        serializer = self.get_serializer(soi)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_pledge_received(self, request, pk=None):
        """Mark pledge as received"""
        soi = self.get_object()
        soi.pledge_received = True
        soi.pledge_date = timezone.now().date()
        soi.contact_status = 'acknowledged'
        soi.notes = request.data.get('notes', soi.notes)
        soi.save()
        
        serializer = self.get_serializer(soi)
        return Response(serializer.data)


# ==================== PHASE 1: CANDIDATE/COMMITTEE VIEWS ====================

class CommitteeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Committee data with IE spending aggregations
    Phase 1 Requirements 2a-2e: Track outside spending
    """
    queryset = Committee.objects.all()
    serializer_class = CommitteeSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = Committee.objects.select_related(
            'name', 'candidate', 'candidate_party', 'candidate_office',
            'election_cycle', 'sponsor', 'chairperson', 'treasurer'
        ).prefetch_related(
            Prefetch(
                'transactions',
                queryset=Transaction.objects.filter(deleted=False).select_related(
                    'transaction_type', 'entity', 'category'
                )
            )
        )
        
        # Filter candidate committees only
        candidates_only = self.request.query_params.get('candidates_only', None)
        if candidates_only == 'true':
            queryset = queryset.filter(candidate__isnull=False)
        
        # Filter by office
        office_id = self.request.query_params.get('office', None)
        if office_id:
            queryset = queryset.filter(candidate_office_id=office_id)
        
        # Filter by party
        party_id = self.request.query_params.get('party', None)
        if party_id:
            queryset = queryset.filter(candidate_party_id=party_id)
        
        # Filter by cycle
        cycle_id = self.request.query_params.get('cycle', None)
        if cycle_id:
            queryset = queryset.filter(election_cycle_id=cycle_id)
        
        # Filter active only
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(termination_date__isnull=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CommitteeDetailSerializer
        return CommitteeSerializer
    
    @action(detail=True, methods=['get'])
    def ie_spending_summary(self, request, pk=None):
        """
        Phase 1 Requirement 2a: Aggregate IE spending for/against candidate
        Ben: "Aggregate by entity, race, and candidate"
        """
        committee = self.get_object()
        summary = committee.get_ie_spending_summary()
        
        return Response({
            'committee_id': committee.committee_id,
            'candidate_name': committee.name.full_name if committee.candidate else None,
            'office': committee.candidate_office.name if committee.candidate_office else None,
            'party': committee.candidate_party.name if committee.candidate_party else None,
            'ie_spending': summary
        })
    
    @action(detail=True, methods=['get'])
    def ie_spending_by_committee(self, request, pk=None):
        """
        Phase 1 Requirement 2b: Pull donors to relevant IEs
        Shows which committees spent IE money on this candidate
        """
        committee = self.get_object()
        breakdown = committee.get_ie_spending_by_committee()
        
        return Response({
            'committee_id': committee.committee_id,
            'candidate_name': committee.name.full_name if committee.candidate else None,
            'ie_committees': list(breakdown)
        })
    
    @action(detail=True, methods=['get'])
    def ie_donors(self, request, pk=None):
        """
        Phase 1 Requirement 2c: Aggregate IE donors by race and candidate
        Ben: "Pull donors (individual and super PAC) to relevant IEs"
        """
        committee = self.get_object()
        donors = committee.get_ie_donors()
        
        return Response({
            'committee_id': committee.committee_id,
            'candidate_name': committee.name.full_name if committee.candidate else None,
            'top_donors': list(donors)
        })
    
    @action(detail=True, methods=['get'])
    def grassroots_threshold(self, request, pk=None):
        """
        Phase 1 Requirement 2d-2e: Compare to grassroots threshold
        Default AZ threshold is $5,000
        """
        committee = self.get_object()
        threshold = Decimal(request.query_params.get('threshold', '5000'))
        
        comparison = committee.compare_to_grassroots_threshold(float(threshold))
        
        return Response({
            'committee_id': committee.committee_id,
            'candidate_name': committee.name.full_name if committee.candidate else None,
            'comparison': comparison
        })
    
    @action(detail=True, methods=['get'])
    def financial_summary(self, request, pk=None):
        """Overall financial summary: income, expenses, cash on hand"""
        committee = self.get_object()
        
        return Response({
            'committee_id': committee.committee_id,
            'name': committee.name.full_name,
            'total_income': committee.get_total_income(),
            'total_expenses': committee.get_total_expenses(),
            'cash_balance': committee.get_cash_balance(),
            'ie_for': committee.get_ie_for(),
            'ie_against': committee.get_ie_against(),
        })


# ==================== PHASE 1: ENTITY/DONOR VIEWS ====================

class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Entity (donor/individual/organization) data
    Phase 1: Track donor impact through IE committees
    """
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = Entity.objects.select_related('entity_type', 'county')
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(last_name__icontains=search) |
                Q(first_name__icontains=search)
            )
        
        # Filter by entity type
        entity_type = self.request.query_params.get('entity_type', None)
        if entity_type:
            queryset = queryset.filter(entity_type_id=entity_type)
        
        # Filter by city/state
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        state = self.request.query_params.get('state', None)
        if state:
            queryset = queryset.filter(state=state)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EntityDetailSerializer
        return EntitySerializer
    
    @action(detail=True, methods=['get'])
    def ie_impact_by_candidate(self, request, pk=None):
        """
        Phase 1 Requirement 2e: Total IE spending funded indirectly by donor
        Ben: "Compare total IE spending funded indirectly by a given donor or entity"
        """
        entity = self.get_object()
        impact = entity.get_total_ie_impact_by_candidate()
        
        return Response({
            'entity_id': entity.name_id,
            'entity_name': entity.full_name,
            'ie_impact_by_candidate': list(impact)
        })
    
    @action(detail=True, methods=['get'])
    def contribution_summary(self, request, pk=None):
        """Summary of all contributions made by this entity"""
        entity = self.get_object()
        summary = entity.get_contribution_summary()
        
        return Response({
            'entity_id': entity.name_id,
            'entity_name': entity.full_name,
            'contribution_summary': summary
        })
    
    @action(detail=False, methods=['get'])
    def top_donors(self, request):
        """Top donors by total contribution amount"""
        limit = int(request.query_params.get('limit', 50))
        cycle_id = request.query_params.get('cycle', None)
        
        filters = {
            'transactions__transaction_type__income_expense_neutral': 1,
            'transactions__deleted': False
        }
        
        if cycle_id:
            filters['transactions__committee__election_cycle_id'] = cycle_id
        
        top_donors = Entity.objects.filter(
            **filters
        ).annotate(
            total_contributed=Sum('transactions__amount'),
            num_contributions=Count('transactions__transaction_id')
        ).order_by('-total_contributed')[:limit]
        
        serializer = self.get_serializer(top_donors, many=True)
        return Response(serializer.data)


# ==================== PHASE 1: RACE AGGREGATION ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def race_ie_spending(request):
    """
    Phase 1 Requirement: Aggregate by race
    Ben: "Aggregate by entity, race, and candidate"
    
    Query params:
    - office: office_id (required)
    - cycle: cycle_id (required)
    - party: party_id (optional)
    """
    office_id = request.GET.get('office')
    cycle_id = request.GET.get('cycle')
    party_id = request.GET.get('party', None)
    
    if not office_id or not cycle_id:
        return Response(
            {'error': 'office and cycle parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        office = Office.objects.get(office_id=office_id)
        cycle = Cycle.objects.get(cycle_id=cycle_id)
        party = Party.objects.get(party_id=party_id) if party_id else None
    except (Office.DoesNotExist, Cycle.DoesNotExist, Party.DoesNotExist):
        return Response(
            {'error': 'Invalid office, cycle, or party ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    race_spending = RaceAggregationManager.get_race_ie_spending(
        office, cycle, party
    )
    
    return Response({
        'office': office.name,
        'cycle': cycle.name,
        'party': party.name if party else 'All Parties',
        'candidates': list(race_spending)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def race_top_donors(request):
    """
    Phase 1 Requirement: Top IE donors by race
    Ben: "Aggregate IE donors by race and candidate"
    
    Query params:
    - office: office_id (required)
    - cycle: cycle_id (required)
    - limit: number of donors to return (default 20)
    """
    office_id = request.GET.get('office')
    cycle_id = request.GET.get('cycle')
    limit = int(request.GET.get('limit', 20))
    
    if not office_id or not cycle_id:
        return Response(
            {'error': 'office and cycle parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        office = Office.objects.get(office_id=office_id)
        cycle = Cycle.objects.get(cycle_id=cycle_id)
    except (Office.DoesNotExist, Cycle.DoesNotExist):
        return Response(
            {'error': 'Invalid office or cycle ID'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    top_donors = RaceAggregationManager.get_top_ie_donors_by_race(
        office, cycle, limit
    )
    
    return Response({
        'office': office.name,
        'cycle': cycle.name,
        'top_donors': list(top_donors)
    })


# ==================== PHASE 1: TRANSACTION VIEWS ====================

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Transaction data (contributions and expenditures)
    """
    queryset = Transaction.objects.filter(deleted=False)
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]
    pagination_class = LargeResultsSetPagination
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(deleted=False).select_related(
            'committee', 'committee__name',
            'entity', 'transaction_type', 'category',
            'subject_committee', 'subject_committee__name'
        )
        
        # Filter by committee
        committee_id = self.request.query_params.get('committee', None)
        if committee_id:
            queryset = queryset.filter(committee_id=committee_id)
        
        # Filter by entity (donor/payee)
        entity_id = self.request.query_params.get('entity', None)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        
        # Filter by transaction type
        txn_type = self.request.query_params.get('type', None)
        if txn_type == 'contributions':
            queryset = queryset.filter(transaction_type__income_expense_neutral=1)
        elif txn_type == 'expenses':
            queryset = queryset.filter(transaction_type__income_expense_neutral=2)
        
        # Filter IE transactions only
        ie_only = self.request.query_params.get('ie_only', None)
        if ie_only == 'true':
            queryset = queryset.filter(subject_committee__isnull=False)
        
        # Filter by subject (for IE spending)
        subject_id = self.request.query_params.get('subject_committee', None)
        if subject_id:
            queryset = queryset.filter(subject_committee_id=subject_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        # Filter by amount range
        amount_min = self.request.query_params.get('amount_min', None)
        amount_max = self.request.query_params.get('amount_max', None)
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        
        # Order by
        order_by = self.request.query_params.get('order_by', '-transaction_date')
        queryset = queryset.order_by(order_by)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def ie_transactions(self, request):
        """All independent expenditure transactions"""
        ie_txns = self.get_queryset().filter(
            subject_committee__isnull=False
        )
        
        page = self.paginate_queryset(ie_txns)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def large_contributions(self, request):
        """Contributions above a threshold (default $1000)"""
        threshold = Decimal(request.query_params.get('threshold', '1000'))
        
        large_contribs = self.get_queryset().filter(
            transaction_type__income_expense_neutral=1,
            amount__gte=threshold
        )
        
        page = self.paginate_queryset(large_contribs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


# ==================== PHASE 1: LOOKUP/REFERENCE DATA ====================

class OfficeViewSet(viewsets.ReadOnlyModelViewSet):
    """Available offices for filtering"""
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Return all offices


class CycleViewSet(viewsets.ReadOnlyModelViewSet):
    """Available election cycles"""
    queryset = Cycle.objects.all().order_by('-begin_date')
    serializer_class = CycleSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Return all cycles


# ==================== PHASE 1: DATA VALIDATION ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def validate_phase1_data(request):
    """
    Data validation endpoint for Phase 1
    Checks data integrity per Ben's requirements
    """
    ie_validation = Phase1DataValidator.validate_ie_tracking()
    candidate_validation = Phase1DataValidator.validate_candidate_tracking()
    donor_validation = Phase1DataValidator.validate_donor_tracking()
    integrity_issues = Phase1DataValidator.check_data_integrity()
    
    return Response({
        'ie_tracking': ie_validation,
        'candidate_tracking': candidate_validation,
        'donor_tracking': donor_validation,
        'integrity_issues': integrity_issues,
        'validation_timestamp': timezone.now().isoformat()
    })


# ==================== PHASE 1: DASHBOARD SUMMARY ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_summary(request):
    """
    High-level stats for Phase 1 dashboard
    """
    # Get current cycle (most recent)
    current_cycle = Cycle.objects.order_by('-begin_date').first()
    
    # Candidate committees in current cycle
    candidate_count = Committee.objects.filter(
        candidate__isnull=False,
        election_cycle=current_cycle
    ).count()
    
    # Total IE spending in current cycle
    ie_spending = Transaction.objects.filter(
        subject_committee__isnull=False,
        subject_committee__election_cycle=current_cycle,
        deleted=False
    ).aggregate(total=Sum('amount'))
    
    # Candidates exceeding grassroots threshold
    candidates_over_threshold = 0
    threshold = Decimal('5000')
    
    for committee in Committee.objects.filter(
        candidate__isnull=False,
        election_cycle=current_cycle
    ):
        ie_for = committee.get_ie_for()
        ie_against = committee.get_ie_against()
        if ie_for > threshold or ie_against > threshold:
            candidates_over_threshold += 1
    
    # SOI stats
    soi_stats = {
        'total_filings': CandidateStatementOfInterest.objects.count(),
        'uncontacted': CandidateStatementOfInterest.objects.filter(
            contact_status='uncontacted'
        ).count(),
        'pledges_received': CandidateStatementOfInterest.objects.filter(
            pledge_received=True
        ).count(),
    }
    
    return Response({
        'current_cycle': current_cycle.name if current_cycle else None,
        'candidate_committees': candidate_count,
        'total_ie_spending': ie_spending['total'] or Decimal('0.00'),
        'candidates_over_grassroots_threshold': candidates_over_threshold,
        'grassroots_threshold': threshold,
        'soi_tracking': soi_stats,
        'last_updated': timezone.now().isoformat()
    })