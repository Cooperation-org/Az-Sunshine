
from django.utils import timezone
from django.db.models import Sum, Count, Q, Prefetch, F
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.cache import cache

from .models import *
from .services.email_service import EmailService
from .serializers import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import requests
import json
import logging


# Initialize logger
logger = logging.getLogger(__name__)
NGROK_URL = "https://modularly-unsoulish-krystle.ngrok-free.dev/run-scraper"
SECRET_TOKEN = "MY_SECRET_123"


@require_http_methods(["POST"])
@csrf_exempt  # CRITICAL: Must disable CSRF for API calls
def trigger_scrape(request):
    """
    Trigger scraping on home laptop via FastAPI agent
    POST /api/v1/trigger-scrape/
    
    This should call the LOCAL agent at http://localhost:5001
    which is then exposed via ngrok tunnel
    """
    try:
        logger.info(f"🚀 Triggering scraper at {NGROK_URL}")
        
        response = requests.post(
            NGROK_URL,
            headers={
                "X-Secret": SECRET_TOKEN,
                "Content-Type": "application/json"
            },
            timeout=600,  # 10 minute timeout for scraping to complete
            json={}  # Send empty JSON body
        )
        
        # Check if we got HTML error page instead of JSON
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            logger.error(f"❌ Received HTML response instead of JSON: {response.text[:200]}")
            return JsonResponse({
                "success": False,
                "error": "Agent returned HTML error page. Is the agent running on port 5001?"
            }, status=503)
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"✅ Scraper triggered: {result}")
        return JsonResponse({
            "success": True,
            "message": "Scraper triggered on home device",
            "result": result
        })
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error: {e}")
        return JsonResponse({
            "success": False,
            "error": f"Cannot connect to agent at {NGROK_URL}. Is ngrok tunnel active?"
        }, status=503)
        
    except requests.exceptions.Timeout:
        return JsonResponse({
            "success": False,
            "error": "Request to agent timed out (10 min limit)"
        }, status=504)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        return JsonResponse({
            "success": False,
            "error": "Agent returned invalid JSON response"
        }, status=500)
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return JsonResponse({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def upload_scraped(request):
    """
    Receive scraped data from home laptop
    POST /api/v1/upload-scraped/
    """
    # Security check
    token = request.headers.get("X-Secret")
    if token != SECRET_TOKEN:
        logger.warning("❌ Unauthorized upload attempt")
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        # Parse incoming data
        data = json.loads(request.body.decode())
        
        logger.info(f"📥 Received {len(data)} records from home scraper")
        
        from .models import CandidateStatementOfInterest, Office
        from django.utils import timezone
        from datetime import datetime
        
        created_count = 0
        updated_count = 0
        error_count = 0
        error_details = []  # Track first 10 errors for debugging
        
        for idx, record in enumerate(data):
            try:
                # Get candidate name FIRST
                candidate_name = record.get('name', '').strip()
                if not candidate_name or len(candidate_name) < 2:
                    error_count += 1
                    if len(error_details) < 10:
                        error_details.append(f"Row {idx}: Empty candidate name")
                    continue
                
                # Get or create office (with better error handling)
                office_name = record.get('office', '').strip()
                
                if not office_name or len(office_name) < 2:
                    error_count += 1
                    if len(error_details) < 10:
                        error_details.append(f"Row {idx} ({candidate_name}): Empty office name")
                    continue
                
                # Create office with a unique office_id
                office, office_created = Office.objects.get_or_create(
                    name=office_name,
                    defaults={
                        'office_id': abs(hash(office_name)) % 1000000,  # Use abs() to ensure positive
                        'office_type': 'STATE'
                    }
                )
                
                if office_created:
                    logger.info(f"✨ Created new office: {office_name}")
                
                # Parse filing date
                filing_date_str = record.get('filing_date')
                if filing_date_str:
                    try:
                        filing_date = datetime.fromisoformat(filing_date_str).date()
                    except:
                        filing_date = timezone.now().date()
                else:
                    filing_date = timezone.now().date()
                
                # Create or update candidate SOI
                candidate, created = CandidateStatementOfInterest.objects.update_or_create(
                    candidate_name=candidate_name,
                    office=office,
                    defaults={
                        'email': record.get('email', '').strip(),
                        'phone': record.get('phone', '').strip(),
                        'party': record.get('party', '').strip(),
                        'filing_date': filing_date,
                        'contact_status': 'uncontacted',
                        'pledge_received': False,
                        'source_url': record.get('source_url', 'https://azsos.gov/elections'),  # ADD THIS LINE
                    }
                )
                
                if created:
                    created_count += 1
                    if created_count <= 5:  # Log first 5 creations
                        logger.info(f"✅ Created: {candidate_name} - {office_name}")
                else:
                    updated_count += 1
                    if updated_count <= 5:  # Log first 5 updates
                        logger.info(f"🔄 Updated: {candidate_name} - {office_name}")
                    
            except Exception as e:
                error_count += 1
                if len(error_details) < 10:
                    error_details.append(f"Row {idx} ({record.get('name', 'Unknown')}): {str(e)}")
                logger.error(f"❌ Error processing record {idx}: {e}")
                continue
        
        result = {
            "success": True,
            "message": "Data received and processed",
            "stats": {
                "total": len(data),
                "created": created_count,
                "updated": updated_count,
                "errors": error_count
            }
        }
        
        if error_details:
            result["error_samples"] = error_details
        
        logger.info(f"✅ Processing complete: Created={created_count}, Updated={updated_count}, Errors={error_count}")
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON data")
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON data"
        }, status=400)
        
    except Exception as e:
        logger.error(f"❌ Error processing upload: {e}", exc_info=True)
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

# Add CORS headers manually if needed
def add_cors_headers(response):
    """Add CORS headers to response"""
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, X-Secret"
    return response

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
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = CandidateStatementOfInterest.objects.select_related(
            'office', 'entity'
        )
        
        # Filter by contact status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(contact_status=status_param)
        
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
        """Phase 1 Requirement 2a: Aggregate IE spending for/against candidate"""
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
        """Phase 1 Requirement 2b: Which committees spent IE money on this candidate"""
        committee = self.get_object()
        breakdown = committee.get_ie_spending_by_committee()
        
        return Response({
            'committee_id': committee.committee_id,
            'candidate_name': committee.name.full_name if committee.candidate else None,
            'ie_committees': list(breakdown)
        })
    
    @action(detail=True, methods=['get'])
    def ie_donors(self, request, pk=None):
        """Phase 1 Requirement 2c: Aggregate IE donors by race and candidate"""
        committee = self.get_object()
        donors = committee.get_ie_donors()
        
        return Response({
            'committee_id': committee.committee_id,
            'candidate_name': committee.name.full_name if committee.candidate else None,
            'top_donors': list(donors)
        })
    
    @action(detail=True, methods=['get'])
    def grassroots_threshold(self, request, pk=None):
        """Phase 1 Requirement 2d-2e: Compare to grassroots threshold"""
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
    
    @action(detail=False, methods=['get'])
    def top(self, request):
        """Top committees by IE spending"""
        limit = int(request.query_params.get('limit', 10))
        
        committees = Committee.objects.filter(
            candidate__isnull=False
        ).annotate(
            total_ie_for=Sum(
                'subject_of_ies__amount',
                filter=Q(subject_of_ies__is_for_benefit=True, subject_of_ies__deleted=False)
            ),
            total_ie_against=Sum(
                'subject_of_ies__amount',
                filter=Q(subject_of_ies__is_for_benefit=False, subject_of_ies__deleted=False)
            )
        )
        
        # Calculate total and sort
        committees_with_totals = []
        for committee in committees:
            total = (committee.total_ie_for or Decimal('0')) + (committee.total_ie_against or Decimal('0'))
            committees_with_totals.append((committee, total))
        
        committees_with_totals.sort(key=lambda x: x[1], reverse=True)
        top_committees = [c[0] for c in committees_with_totals[:limit]]
        
        serializer = self.get_serializer(top_committees, many=True)
        result_data = serializer.data
        for i, (committee, total) in enumerate(committees_with_totals[:limit]):
            result_data[i]['total'] = float(total)
            result_data[i]['name'] = committee.name.full_name if committee.name else 'Unknown'
        
        return Response(result_data)


# ==================== PHASE 1: ENTITY/DONOR VIEWS ====================

class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    """Entity (donor/individual/organization) data"""
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
                Q(last_name__icontains=search) | Q(first_name__icontains=search)
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
        """Total IE spending funded indirectly by donor"""
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
        try:
            limit = int(request.query_params.get('limit', 50))
            cycle_id = request.query_params.get('cycle', None)
            
            filters = Q(
                transactions__transaction_type__income_expense_neutral=1,
                transactions__deleted=False
            )
            
            if cycle_id:
                filters &= Q(transactions__committee__election_cycle_id=cycle_id)
            
            top_donors = Entity.objects.filter(filters).annotate(
                total_contributed=Sum('transactions__amount'),
                num_contributions=Count('transactions__transaction_id', distinct=True)
            ).order_by('-total_contributed')[:limit]
            
            serializer = self.get_serializer(top_donors, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Top donors error: {e}", exc_info=True)
            return Response([], status=status.HTTP_200_OK)


# ==================== PHASE 1: RACE AGGREGATION ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def race_ie_spending(request):
    """Phase 1 Requirement: Aggregate by race"""
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
    
    race_spending = RaceAggregationManager.get_race_ie_spending(office, cycle, party)
    
    return Response({
        'office': office.name,
        'cycle': cycle.name,
        'party': party.name if party else 'All Parties',
        'candidates': list(race_spending)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def race_top_donors(request):
    """Phase 1 Requirement: Top IE donors by race"""
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
    
    top_donors = RaceAggregationManager.get_top_ie_donors_by_race(office, cycle, limit)
    
    return Response({
        'office': office.name,
        'cycle': cycle.name,
        'top_donors': list(top_donors)
    })


# ==================== PHASE 1: TRANSACTION VIEWS ====================

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Transaction data (contributions and expenditures)"""
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
        
        # Apply filters
        committee_id = self.request.query_params.get('committee', None)
        if committee_id:
            queryset = queryset.filter(committee_id=committee_id)
        
        entity_id = self.request.query_params.get('entity', None)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        
        txn_type = self.request.query_params.get('type', None)
        if txn_type == 'contributions':
            queryset = queryset.filter(transaction_type__income_expense_neutral=1)
        elif txn_type == 'expenses':
            queryset = queryset.filter(transaction_type__income_expense_neutral=2)
        
        ie_only = self.request.query_params.get('ie_only', None)
        if ie_only == 'true':
            queryset = queryset.filter(subject_committee__isnull=False)
        
        subject_id = self.request.query_params.get('subject_committee', None)
        if subject_id:
            queryset = queryset.filter(subject_committee_id=subject_id)
        
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(transaction_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction_date__lte=date_to)
        
        amount_min = self.request.query_params.get('amount_min', None)
        amount_max = self.request.query_params.get('amount_max', None)
        if amount_min:
            queryset = queryset.filter(amount__gte=amount_min)
        if amount_max:
            queryset = queryset.filter(amount__lte=amount_max)
        
        order_by = self.request.query_params.get('order_by', '-transaction_date')
        queryset = queryset.order_by(order_by)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def ie_transactions(self, request):
        """All independent expenditure transactions"""
        ie_txns = self.get_queryset().filter(subject_committee__isnull=False)
        
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
    pagination_class = None


class CycleViewSet(viewsets.ReadOnlyModelViewSet):
    """Available election cycles"""
    queryset = Cycle.objects.all().order_by('-begin_date')
    serializer_class = CycleSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    """Available parties for filtering"""
    queryset = Party.objects.all().order_by('name')
    serializer_class = PartySerializer
    permission_classes = [AllowAny]
    pagination_class = None


# ==================== PHASE 1: DATA VALIDATION ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def validate_phase1_data(request):
    """Data validation endpoint for Phase 1"""
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
    """High-level stats for Phase 1 dashboard - OPTIMIZED"""
    try:
        current_cycle = Cycle.objects.order_by('-begin_date').first()
        candidate_count = Committee.objects.filter(candidate__isnull=False).count()
        
        ie_spending = Transaction.objects.filter(
            subject_committee__isnull=False,
            deleted=False
        ).aggregate(total=Sum('amount'))
        
        # OPTIMIZED: Single query for threshold calculation
        threshold = Decimal('5000')
        candidates_over_threshold = Committee.objects.filter(
            candidate__isnull=False
        ).annotate(
            ie_for_total=Sum(
                'subject_of_ies__amount',
                filter=Q(subject_of_ies__is_for_benefit=True, subject_of_ies__deleted=False)
            ),
            ie_against_total=Sum(
                'subject_of_ies__amount',
                filter=Q(subject_of_ies__is_for_benefit=False, subject_of_ies__deleted=False)
            )
        ).filter(
            Q(ie_for_total__gt=threshold) | Q(ie_against_total__gt=threshold)
        ).count()
        
        # SOI stats with error handling
        try:
            soi_stats = {
                'total_filings': CandidateStatementOfInterest.objects.count(),
                'uncontacted': CandidateStatementOfInterest.objects.filter(
                    contact_status='uncontacted'
                ).count(),
                'pledges_received': CandidateStatementOfInterest.objects.filter(
                    pledge_received=True
                ).count(),
            }
        except Exception as soi_error:
            logger.error(f"Error getting SOI stats: {soi_error}")
            soi_stats = {'total_filings': 0, 'uncontacted': 0, 'pledges_received': 0}
        
        return Response({
            'current_cycle': current_cycle.name if current_cycle else None,
            'candidate_committees': candidate_count,
            'total_ie_spending': float(ie_spending['total'] or Decimal('0.00')),
            'candidates_over_grassroots_threshold': candidates_over_threshold,
            'grassroots_threshold': float(threshold),
            'soi_tracking': soi_stats,
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Dashboard summary error: {e}", exc_info=True)
        return Response({
            'error': str(e),
            'current_cycle': None,
            'candidate_committees': 0,
            'total_ie_spending': 0,
            'candidates_over_grassroots_threshold': 0,
            'grassroots_threshold': 5000,
            'soi_tracking': {'total_filings': 0, 'uncontacted': 0, 'pledges_received': 0},
            'last_updated': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


# ==================== FRONTEND ADAPTER ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request):
    """Adapter endpoint for frontend metrics call"""
    current_cycle = Cycle.objects.order_by('-begin_date').first()
    
    if current_cycle:
        candidate_count = Committee.objects.filter(
            candidate__isnull=False,
            election_cycle=current_cycle
        ).count()
        
        ie_spending = Transaction.objects.filter(
            subject_committee__isnull=False,
            subject_committee__election_cycle=current_cycle,
            deleted=False
        ).aggregate(total=Sum('amount'))
    else:
        candidate_count = Committee.objects.filter(candidate__isnull=False).count()
        ie_spending = Transaction.objects.filter(
            subject_committee__isnull=False,
            deleted=False
        ).aggregate(total=Sum('amount'))
    
    num_expenditures = Transaction.objects.filter(
        subject_committee__isnull=False,
        deleted=False
    ).count()
    
    return Response({
        'total_expenditures': float(ie_spending['total'] or Decimal('0.00')),
        'num_candidates': candidate_count,
        'num_expenditures': num_expenditures,
        'candidates': []
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def donors_top(request):
    """Top donors endpoint - OPTIMIZED"""
    try:
        limit = int(request.query_params.get('limit', 50))
        cycle_id = request.query_params.get('cycle', None)
        
        filters = Q(
            transactions__transaction_type__income_expense_neutral=1,
            transactions__deleted=False
        )
        
        if cycle_id:
            filters &= Q(transactions__committee__election_cycle_id=cycle_id)
        
        top_donors = Entity.objects.filter(filters).annotate(
            total_contributed=Sum('transactions__amount'),
            num_contributions=Count('transactions__transaction_id', distinct=True)
        ).order_by('-total_contributed')[:limit]
        
        result = [
            {
                'name': donor.full_name,
                'total_contribution': float(donor.total_contributed or 0),
                'num_contributions': donor.num_contributions or 0
            }
            for donor in top_donors
        ]
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Top donors error: {e}", exc_info=True)
        return Response([], status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def candidates_list(request):
    """Adapter endpoint: /api/candidates/ -> maps to committees with candidates"""
    queryset = Committee.objects.filter(candidate__isnull=False).select_related(
        'name', 'candidate', 'candidate_party', 'candidate_office', 'election_cycle'
    )
    
    # Apply filters
    office_id = request.query_params.get('office', None)
    if office_id:
        queryset = queryset.filter(candidate_office_id=office_id)
    
    party_id = request.query_params.get('party', None)
    if party_id:
        queryset = queryset.filter(candidate_party_id=party_id)
    
    cycle_id = request.query_params.get('cycle', None)
    if cycle_id:
        queryset = queryset.filter(election_cycle_id=cycle_id)
    
    # Annotate with IE totals
    queryset = queryset.annotate(
        ie_total_for=Sum(
            'subject_of_ies__amount',
            filter=Q(subject_of_ies__is_for_benefit=True, subject_of_ies__deleted=False)
        ),
        ie_total_against=Sum(
            'subject_of_ies__amount',
            filter=Q(subject_of_ies__is_for_benefit=False, subject_of_ies__deleted=False)
        )
    )
    
    # Pagination
    paginator = LargeResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    # Transform to match frontend expectations
    result_data = []
    for committee in (page if page is not None else queryset):
        # Get contact status from CandidateSOI if exists
        try:
            soi = CandidateStatementOfInterest.objects.filter(
                entity=committee.candidate
            ).order_by('-filing_date').first()
            contacted = soi.contact_status == 'contacted' if soi else False
            contacted_at = soi.contact_date.isoformat() if soi and soi.contact_date else None
        except:
            contacted = False
            contacted_at = None
        
        result_data.append({
            'id': committee.committee_id,
            'name': committee.candidate.full_name if committee.candidate else committee.name.full_name,
            'race': committee.candidate_office.name if committee.candidate_office else None,
            'party': committee.candidate_party.name if committee.candidate_party else None,
            'contacted': contacted,
            'contacted_at': contacted_at,
            'ie_total_for': float(committee.ie_total_for or 0),
            'ie_total_against': float(committee.ie_total_against or 0),
        })
    
    if page is not None:
        return paginator.get_paginated_response(result_data)
    
    return Response({'results': result_data, 'count': len(result_data)})


@api_view(['GET'])
@permission_classes([AllowAny])
def donors_list(request):
    """Adapter endpoint: /api/donors/ -> maps to entities with contribution data"""
    queryset = Entity.objects.filter(
        transactions__transaction_type__income_expense_neutral=1,
        transactions__deleted=False
    ).annotate(
        total_contribution=Sum('transactions__amount'),
        num_contributions=Count('transactions__transaction_id'),
        linked_committees=Count('transactions__committee', distinct=True)
    ).distinct().order_by('-total_contribution')
    
    # Filter by search term if provided
    search = request.query_params.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(last_name__icontains=search) | Q(first_name__icontains=search)
        )
    
    # Pagination
    paginator = LargeResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    # Transform to match frontend expectations
    result_data = []
    for entity in (page if page is not None else queryset):
        # Calculate IE impact (total IE spending by committees this donor contributed to)
        committees_donated_to = Committee.objects.filter(
            transactions__entity=entity,
            transactions__transaction_type__income_expense_neutral=1,
            transactions__deleted=False
        ).distinct()
        
        ie_impact = Transaction.objects.filter(
            committee__in=committees_donated_to,
            subject_committee__isnull=False,
            deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        result_data.append({
            'id': entity.name_id,
            'name': entity.full_name,
            'total_contribution': float(entity.total_contribution or 0),
            'linked_committees': entity.linked_committees or 0,
            'ie_impact': float(ie_impact),
            'num_contributions': entity.num_contributions or 0,
        })
    
    if page is not None:
        return paginator.get_paginated_response(result_data)
    
    return Response({'results': result_data, 'count': len(result_data)})


@api_view(['GET'])
@permission_classes([AllowAny])
def expenditures_list(request):
    """Adapter endpoint: /api/expenditures/ -> maps to transactions with IE filter"""
    queryset = Transaction.objects.filter(
        subject_committee__isnull=False,
        transaction_type__income_expense_neutral=2,
        deleted=False
    ).select_related(
        'committee', 'committee__name',
        'subject_committee', 'subject_committee__name',
        'entity', 'transaction_type'
    ).order_by('-transaction_date')
    
    # Pagination
    paginator = LargeResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = TransactionSerializer(page, many=True)
        result_data = []
        for item in serializer.data:
            subject_comm = item.get('subject_committee', {})
            memo = item.get('memo', '').strip()
            is_for_benefit = item.get('is_for_benefit')
            candidate_name = subject_comm.get('candidate_name') if subject_comm else 'Candidate'
            
            # Build purpose: use memo if available, otherwise use Support/Oppose + candidate name
            if memo:
                purpose = memo
            else:
                support_type = 'Support' if is_for_benefit else 'Oppose'
                purpose = f"{support_type} {candidate_name}"
            
            result_data.append({
                'date': item.get('transaction_date'),
                'amount': item.get('amount'),
                'support_oppose': 'Support' if is_for_benefit else 'Oppose',
                'ie_committee': {'name': item.get('committee', {}).get('name', 'Unknown')},
                'candidate_name': candidate_name,
                'purpose': purpose
            })
        return paginator.get_paginated_response(result_data)
    
    serializer = TransactionSerializer(queryset, many=True)
    result_data = []
    for item in serializer.data:
        subject_comm = item.get('subject_committee', {})
        memo = item.get('memo', '').strip()
        is_for_benefit = item.get('is_for_benefit')
        candidate_name = subject_comm.get('candidate_name') if subject_comm else 'Candidate'
        
        if memo:
            purpose = memo
        else:
            support_type = 'Support' if is_for_benefit else 'Oppose'
            purpose = f"{support_type} {candidate_name}"
        
        result_data.append({
            'date': item.get('transaction_date'),
            'amount': item.get('amount'),
            'support_oppose': 'Support' if is_for_benefit else 'Oppose',
            'ie_committee': {'name': item.get('committee', {}).get('name', 'Unknown')},
            'candidate_name': candidate_name,
            'purpose': purpose
        })
    return Response({'results': result_data})


@api_view(['GET'])
@permission_classes([AllowAny])
def committees_top(request):
    """Top committees by IE spending"""
    limit = int(request.query_params.get('limit', 10))
    
    committees = Committee.objects.filter(
        candidate__isnull=False
    ).annotate(
        total_ie_for=Sum(
            'subject_of_ies__amount',
            filter=Q(subject_of_ies__is_for_benefit=True, subject_of_ies__deleted=False)
        ),
        total_ie_against=Sum(
            'subject_of_ies__amount',
            filter=Q(subject_of_ies__is_for_benefit=False, subject_of_ies__deleted=False)
        )
    )
    
    result = []
    for committee in committees:
        total = (committee.total_ie_for or Decimal('0')) + (committee.total_ie_against or Decimal('0'))
        result.append({
            'committee_id': committee.committee_id,
            'name': committee.name.full_name if committee.name else 'Unknown',
            'total': float(total)
        })
    
    result.sort(key=lambda x: x['total'], reverse=True)
    return Response(result[:limit])


# ==================== OPTIMIZED DASHBOARD ENDPOINT ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_summary_optimized(request):
    """
    OPTIMIZED: Single query dashboard with 5-minute caching
    This reduces load time from ~3-5 seconds to ~100-300ms
    """
    
    # Try to get cached data first
    cache_key = 'dashboard_summary_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("✅ Returning cached dashboard data")
        return Response(cached_data)
    
    logger.info("🔄 Computing fresh dashboard data...")
    
    try:
        # Get current cycle
        current_cycle = Cycle.objects.order_by('-begin_date').first()
        
        # Single optimized query for IE spending totals
        ie_stats = Transaction.objects.filter(
            subject_committee__isnull=False,
            deleted=False
        ).aggregate(
            total_ie=Sum('amount'),
            count_ie=Count('transaction_id')
        )
        
        # Single query for candidate count
        candidate_count = Committee.objects.filter(
            candidate__isnull=False
        ).count()
        
        # Single query for candidates over threshold
        threshold = Decimal('5000')
        candidates_over_threshold = Committee.objects.filter(
            candidate__isnull=False
        ).annotate(
            ie_total=Sum(
                'subject_of_ies__amount',
                filter=Q(subject_of_ies__deleted=False)
            )
        ).filter(ie_total__gt=threshold).count()
        
        # SOI stats with error handling
        try:
            soi_stats = CandidateStatementOfInterest.objects.aggregate(
                total=Count('id'),
                uncontacted=Count('id', filter=Q(contact_status='uncontacted')),
                pledged=Count('id', filter=Q(pledge_received=True))
            )
        except Exception as soi_error:
            logger.error(f"SOI stats error: {soi_error}")
            soi_stats = {'total': 0, 'uncontacted': 0, 'pledged': 0}
        
        response_data = {
            'current_cycle': current_cycle.name if current_cycle else None,
            'candidate_committees': candidate_count,
            'total_ie_spending': float(ie_stats['total_ie'] or Decimal('0.00')),
            'num_expenditures': ie_stats['count_ie'] or 0,
            'candidates_over_grassroots_threshold': candidates_over_threshold,
            'grassroots_threshold': 5000,
            'soi_tracking': soi_stats,
            'last_updated': timezone.now().isoformat(),
            'cached': False
        }
        
        # Cache for 5 minutes (300 seconds)
        cache.set(cache_key, response_data, timeout=300)
        
        logger.info("✅ Dashboard data computed and cached")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return Response({
            'error': str(e),
            'current_cycle': None,
            'candidate_committees': 0,
            'total_ie_spending': 0,
            'num_expenditures': 0,
            'candidates_over_grassroots_threshold': 0,
            'grassroots_threshold': 5000,
            'soi_tracking': {'total': 0, 'uncontacted': 0, 'pledged': 0},
            'last_updated': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_charts_data(request):
    """
    OPTIMIZED: Separate endpoint for chart data with 10-minute cache
    Load this after the main dashboard for progressive enhancement
    """
    
    cache_key = 'dashboard_charts_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    try:
        # Top 10 committees - optimized query
        top_committees = Committee.objects.filter(
            candidate__isnull=False
        ).annotate(
            total_ie=Sum(
                'subject_of_ies__amount',
                filter=Q(subject_of_ies__deleted=False)
            )
        ).filter(
            total_ie__isnull=False
        ).order_by('-total_ie')[:10].values(
            'committee_id',
            'total_ie',
            name_full=F('name__last_name')
        )
        
        # Top 10 donors - optimized query
        top_donors = Entity.objects.filter(
            transactions__transaction_type__income_expense_neutral=1,
            transactions__deleted=False
        ).annotate(
            total_contributed=Sum('transactions__amount')
        ).order_by('-total_contributed')[:10].values(
            'name_id',
            'total_contributed',
            name_full=F('last_name')
        )
        
        # Support vs Oppose totals
        support_oppose = Transaction.objects.filter(
            subject_committee__isnull=False,
            deleted=False
        ).aggregate(
            support=Sum('amount', filter=Q(is_for_benefit=True)),
            oppose=Sum('amount', filter=Q(is_for_benefit=False))
        )
        
        response_data = {
            'top_committees': list(top_committees),
            'top_donors': list(top_donors),
            'support_oppose': {
                'support': float(support_oppose['support'] or 0),
                'oppose': float(support_oppose['oppose'] or 0)
            }
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, response_data, timeout=600)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Charts data error: {e}", exc_info=True)
        return Response({
            'top_committees': [],
            'top_donors': [],
            'support_oppose': {'support': 0, 'oppose': 0}
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_recent_expenditures(request):
    """
    OPTIMIZED: Latest 10 expenditures with minimal data
    Separate endpoint for progressive loading
    """
    
    cache_key = 'dashboard_recent_exp_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    try:
        # Only fetch what we need, no complex JOINs
        recent = Transaction.objects.filter(
            subject_committee__isnull=False,
            deleted=False
        ).select_related(
            'committee__name',
            'subject_committee__name'
        ).order_by('-transaction_date')[:10].values(
            'transaction_date',
            'amount',
            'is_for_benefit',
            committee_name=F('committee__name__last_name'),
            candidate_name=F('subject_committee__name__last_name')
        )
        
        response_data = list(recent)
        
        # Cache for 5 minutes
        cache.set(cache_key, response_data, timeout=300)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Recent expenditures error: {e}", exc_info=True)
        return Response([])


@api_view(['POST'])
@permission_classes([AllowAny])
def clear_dashboard_cache(request):
    """
    Clear dashboard cache manually (useful after data imports)
    POST /api/v1/dashboard/clear-cache/
    """
    try:
        cache.delete('dashboard_summary_v1')
        cache.delete('dashboard_charts_v1')
        cache.delete('dashboard_recent_exp_v1')
        return Response({'success': True, 'message': 'Dashboard cache cleared'})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)



# Add this near the bottom of views.py, after the other endpoints

@api_view(['GET'])
@permission_classes([AllowAny])
def soi_candidates_list(request):
    """
    Get SOI candidates list with pagination
    GET /api/v1/soi/candidates/
    """
    try:
        queryset = CandidateStatementOfInterest.objects.select_related('office').all()
        
        # Apply filters
        status = request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(contact_status=status)
        
        office_id = request.query_params.get('office', None)
        if office_id:
            queryset = queryset.filter(office_id=office_id)
        
        # Order by filing date (newest first)
        queryset = queryset.order_by('-filing_date')
        
        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        # Transform to match frontend expectations
        result_data = []
        for candidate in (page if page is not None else queryset):
            result_data.append({
                'id': candidate.id,
                'name': candidate.candidate_name,
                'candidate_name': candidate.candidate_name,
                'office': candidate.office.name if candidate.office else 'Unknown',
                'party': candidate.party or '',
                'email': candidate.email or '',
                'phone': candidate.phone or '',
                'filing_date': candidate.filing_date.isoformat() if candidate.filing_date else None,
                'contact_status': candidate.contact_status,
                'contacted': candidate.contact_status != 'uncontacted',
                'contact_date': candidate.contact_date.isoformat() if candidate.contact_date else None,
                'pledge_received': candidate.pledge_received,
                'pledge_date': candidate.pledge_date.isoformat() if candidate.pledge_date else None,
            })
        
        if page is not None:
            return paginator.get_paginated_response(result_data)
        
        return Response({'results': result_data, 'count': len(result_data)})
        
    except Exception as e:
        logger.error(f"Error fetching SOI candidates: {e}", exc_info=True)
        return Response({
            'error': str(e),
            'results': [],
            'count': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def soi_dashboard_stats(request):
    """
    Get SOI dashboard statistics
    GET /api/v1/soi/dashboard-stats/
    """
    try:
        queryset = CandidateStatementOfInterest.objects.all()
        
        stats = {
            'total_candidates': queryset.count(),
            'uncontacted': queryset.filter(contact_status='uncontacted').count(),
            'contacted': queryset.filter(contact_status='contacted').count(),
            'pending_pledge': queryset.filter(
                contact_status='contacted',
                pledge_received=False
            ).count(),
            'pledged': queryset.filter(pledge_received=True).count(),
        }
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error fetching SOI stats: {e}", exc_info=True)
        return Response({
            'total_candidates': 0,
            'uncontacted': 0,
            'contacted': 0,
            'pending_pledge': 0,
            'pledged': 0,
        })
        

@api_view(['GET'])
@permission_classes([AllowAny])
def email_templates(request):
    """Get all email templates"""
    templates = EmailTemplate.objects.filter(is_active=True)
    serializer = EmailTemplateSerializer(templates, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def send_bulk_emails(request):
    """Send bulk emails to candidates"""
    candidate_ids = request.data.get('candidate_ids', [])
    template_id = request.data.get('template_id')
    custom_data = request.data.get('custom_data', {})
    
    if not candidate_ids or not template_id:
        return Response({'error': 'candidate_ids and template_id are required'}, status=400)
    
    email_service = EmailService()
    results = email_service.send_bulk_emails(candidate_ids, template_id)
    
    return Response({
        'success': True,
        'results': results,
        'message': f"Sent {results['success']} emails, {results['failed']} failed"
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def email_stats(request):
    """Get email campaign statistics"""
    total_sent = EmailLog.objects.filter(status='sent').count()
    total_opened = EmailLog.objects.filter(opened_at__isnull=False).count()
    total_clicked = EmailLog.objects.filter(clicked_at__isnull=False).count()
    
    open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
    click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
    
    return Response({
        'total_sent': total_sent,
        'total_opened': total_opened,
        'total_clicked': total_clicked,
        'open_rate': round(open_rate, 1),
        'click_rate': round(click_rate, 1),
    })