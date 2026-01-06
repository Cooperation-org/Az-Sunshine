
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
import os


# Initialize logger
logger = logging.getLogger(__name__)
NGROK_URL = "https://fc88ced25882.ngrok-free.app/run-scraper"
LOCAL_AGENT_URL = "http://localhost:5001/run-scraper"

# SECURITY: Load secret token from environment variable (NEVER hardcode!)
SECRET_TOKEN = os.environ.get('AZ_SUNSHINE_SECRET_TOKEN')
if not SECRET_TOKEN:
    logger.warning(" AZ_SUNSHINE_SECRET_TOKEN not set in environment! Using fallback for development only.")
    SECRET_TOKEN = os.environ.get('SECRET_TOKEN', 'CHANGE_ME_IN_PRODUCTION')

# Scraper status cache key
SCRAPER_STATUS_KEY = "soi_scraper_status"


def get_scraper_status():
    """Get current scraper status from cache"""
    default_status = {
        "status": "idle",
        "started_at": None,
        "completed_at": None,
        "new_candidates": 0,
        "total_scraped": 0,
        "error": None
    }
    return cache.get(SCRAPER_STATUS_KEY, default_status)


def set_scraper_status(status_data):
    """Set scraper status in cache (expires after 1 hour)"""
    cache.set(SCRAPER_STATUS_KEY, status_data, timeout=3600)


@require_http_methods(["GET"])
@csrf_exempt
def scraper_status(request):
    """
    Get current scraper status
    GET /api/v1/scraper-status/
    """
    status_data = get_scraper_status()
    return JsonResponse(status_data)


@require_http_methods(["POST"])
@csrf_exempt
def scraper_complete(request):
    """
    Called by laptop scraper when scraping is complete
    POST /api/v1/scraper-complete/

    Body: {
        "success": true/false,
        "new_candidates": 5,
        "total_scraped": 100,
        "error": null or "error message"
    }
    """
    try:
        # Verify secret token
        secret = request.headers.get('X-Secret', '')
        if secret != SECRET_TOKEN:
            return JsonResponse({"error": "Unauthorized"}, status=401)

        data = json.loads(request.body) if request.body else {}

        current_status = get_scraper_status()

        if data.get('success', False):
            set_scraper_status({
                "status": "complete",
                "started_at": current_status.get('started_at'),
                "completed_at": timezone.now().isoformat(),
                "new_candidates": data.get('new_candidates', 0),
                "total_scraped": data.get('total_scraped', 0),
                "error": None
            })
            logger.info(f"Scraper completed: {data.get('new_candidates', 0)} new candidates")
        else:
            set_scraper_status({
                "status": "error",
                "started_at": current_status.get('started_at'),
                "completed_at": timezone.now().isoformat(),
                "new_candidates": 0,
                "total_scraped": 0,
                "error": data.get('error', 'Unknown error')
            })
            logger.error(f"Scraper failed: {data.get('error')}")

        return JsonResponse({"success": True})

    except Exception as e:
        logger.error(f"Error in scraper_complete: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt  # CRITICAL: Must disable CSRF for API calls
def trigger_scrape(request):
    """
    Trigger scraping on home laptop via FastAPI agent
    POST /api/v1/trigger-scrape/

    Tries local agent first (localhost:5001), falls back to ngrok
    """
    # Set status to running
    set_scraper_status({
        "status": "running",
        "started_at": timezone.now().isoformat(),
        "completed_at": None,
        "new_candidates": 0,
        "total_scraped": 0,
        "error": None
    })

    # Try local agent first (for when Django runs on same machine)
    agent_url = LOCAL_AGENT_URL
    try:
        logger.info(f"Triggering scraper at {agent_url}")

        response = requests.post(
            agent_url,
            headers={
                "X-Secret": SECRET_TOKEN,
                "Content-Type": "application/json",
            },
            timeout=30,  # 30 second timeout (agent returns immediately now)
            json={}  # Send empty JSON body
        )
        
        # Check if we got HTML error page instead of JSON
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            logger.error(f"Received HTML response instead of JSON: {response.text[:200]}")
            return JsonResponse({
                "success": False,
                "error": "Agent returned HTML error page. Is the agent running on port 5001?"
            }, status=503)
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Scraper triggered: {result}")
        return JsonResponse({
            "success": True,
            "message": "Scraper triggered on home device",
            "result": result
        })
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
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
        logger.error(f"Request error: {e}")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({
            "success": False,
            "error": "Agent returned invalid JSON response"
        }, status=500)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
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
        logger.warning("Unauthorized upload attempt")
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
        new_candidates = []  # Track newly created candidates

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
                        'source_url': record.get('source_url', 'https://azsos.gov/elections'),
                    }
                )

                if created:
                    created_count += 1
                    # Add to new candidates list for frontend
                    new_candidates.append({
                        'id': candidate.id,
                        'candidate_name': candidate.candidate_name,
                        'office': office_name,
                        'party': candidate.party or '',
                        'email': candidate.email or '',
                        'phone': candidate.phone or '',
                        'filing_date': candidate.filing_date.isoformat() if candidate.filing_date else None,
                    })
                    if created_count <= 5:  # Log first 5 creations
                        logger.info(f"Created: {candidate_name} - {office_name}")
                else:
                    updated_count += 1
                    if updated_count <= 5:  # Log first 5 updates
                        logger.info(f"Updated: {candidate_name} - {office_name}")
                    
            except Exception as e:
                error_count += 1
                if len(error_details) < 10:
                    error_details.append(f"Row {idx} ({record.get('name', 'Unknown')}): {str(e)}")
                logger.error(f"Error processing record {idx}: {e}")
                continue
        
        result = {
            "success": True,
            "message": "Data received and processed",
            "stats": {
                "total": len(data),
                "created": created_count,
                "updated": updated_count,
                "errors": error_count
            },
            "new_candidates": new_candidates  # Return list of newly created candidates
        }

        if error_details:
            result["error_samples"] = error_details

        logger.info(f"Processing complete: Created={created_count}, Updated={updated_count}, Errors={error_count}")
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON data")
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON data"
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
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


class FastPagination(PageNumberPagination):
    """
    Pagination without count() for very large datasets.
    Returns approximate count or None to avoid slow COUNT(*) queries.
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500

    def paginate_queryset(self, queryset, request, view=None):
        """Paginate without calling count()"""
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)

        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1

        # Don't call paginator.page() which triggers count()
        # Just slice the queryset directly
        offset = (page_number - 1) * page_size
        limit = page_size

        # Get one extra item to know if there's a next page
        items = list(queryset[offset:offset + limit + 1])

        self.has_next = len(items) > limit
        self.has_previous = page_number > 1
        self.page_number = page_number

        # Return only the requested items (not the +1)
        return items[:limit] if items else []

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link() if self.has_next else None,
            'previous': self.get_previous_link() if self.has_previous else None,
            'results': data,
            'count': None,  # Skip expensive count
        })


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

        # Search by candidate name or committee name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__full_name__icontains=search) |
                Q(candidate__full_name__icontains=search) |
                Q(name__last_name__icontains=search) |
                Q(name__first_name__icontains=search) |
                Q(candidate__last_name__icontains=search) |
                Q(candidate__first_name__icontains=search)
            )

        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CommitteeDetailSerializer
        return CommitteeSerializer
    
    @action(detail=True, methods=['get'], url_path='ie_spending')
    def ie_spending(self, request, pk=None):
        """Get IE spending for/against candidate (used by frontend)"""
        committee = self.get_object()
        summary = committee.get_ie_spending_summary()

        return Response({
            'committee_id': committee.committee_id,
            'candidate_name': committee.name.full_name if committee.candidate else None,
            'office': committee.candidate_office.name if committee.candidate_office else None,
            'party': committee.candidate_party.name if committee.candidate_party else None,
            'total_for': summary.get('total_for', 0),
            'total_against': summary.get('total_against', 0),
            'net_benefit': summary.get('net_benefit', 0),
        })

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
    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')
    party_id = request.GET.get('party_id', None)

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id parameters are required'},
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
    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')
    limit = int(request.GET.get('limit', 20))

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id parameters are required'},
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


@api_view(['GET'])
@permission_classes([AllowAny])
def committees_top_by_ie(request):
    """
    Get top committees ranked by total IE spending
    Used by Visualizations page for top candidates chart
    """
    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')
    limit = int(request.GET.get('limit', 10))

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id parameters are required'},
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

    # Get IE spending aggregated by candidate
    race_spending = RaceAggregationManager.get_race_ie_spending(office, cycle, None)

    # Sort by total IE and limit results
    sorted_candidates = sorted(
        race_spending,
        key=lambda x: abs(float(x.get('total_ie', 0))),
        reverse=True
    )[:limit]

    return Response({
        'results': sorted_candidates,
        'count': len(sorted_candidates)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def races_money_flow(request):
    """
    Get money flow data for Sankey diagram
    Combines donor -> IE committee -> candidate flows
    """
    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')
    limit = int(request.GET.get('limit', 12))

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id parameters are required'},
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

    # Get candidates and their IE spending
    candidates_data = RaceAggregationManager.get_race_ie_spending(office, cycle, None)

    # Get top donors to IE committees
    donors_data = RaceAggregationManager.get_top_ie_donors_by_race(office, cycle, limit)

    return Response({
        'candidates': list(candidates_data),
        'top_donors': list(donors_data)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def races_detailed_money_flow(request):
    """
    Get detailed money flow: Donors -> Specific IE Committees -> Candidates
    Shows actual transaction paths for top donors
    NOTE: Temporarily using aggregated data like races_money_flow until we optimize the complex query
    """
    office_id = request.GET.get('office_id')
    cycle_id = request.GET.get('cycle_id')
    donor_limit = int(request.GET.get('donor_limit', 6))

    if not office_id or not cycle_id:
        return Response(
            {'error': 'office_id and cycle_id parameters are required'},
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

    # For now, use the existing aggregated data
    # TODO: Implement detailed committee-specific flows
    candidates_data = RaceAggregationManager.get_race_ie_spending(office, cycle, None)
    donors_data = RaceAggregationManager.get_top_ie_donors_by_race(office, cycle, donor_limit)

    return Response({
        'candidates': list(candidates_data),
        'top_donors': list(donors_data),
        'metadata': {
            'donor_limit': donor_limit,
            'note': 'Using aggregated data - detailed committee flows coming soon'
        }
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

        # Search by purpose or committee name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(purpose__icontains=search) |
                Q(committee__name__full_name__icontains=search) |
                Q(subject_committee__name__full_name__icontains=search) |
                Q(entity__full_name__icontains=search)
            )

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
    """Adapter endpoint: /api/candidates/ -> maps to committees with candidates + Zstd compression"""
    from transparency.utils.compressed_cache import CompressedCache

    # Build cache key from request parameters
    page_num = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 100)
    office_id = request.query_params.get('office_id') or request.query_params.get('office', '')
    party_id = request.query_params.get('party', '')
    cycle_id = request.query_params.get('cycle', '')
    search = request.query_params.get('search', '')
    cache_key = f'candidates_list_p{page_num}_s{page_size}_o{office_id}_pt{party_id}_c{cycle_id}_q{search}'

    # Try to get from Zstd-compressed cache (10 minute cache)
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    queryset = Committee.objects.filter(candidate__isnull=False).select_related(
        'name', 'candidate', 'candidate_party', 'candidate_office', 'election_cycle'
    )

    # Apply filters
    if office_id:
        queryset = queryset.filter(candidate_office_id=office_id)

    if party_id:
        queryset = queryset.filter(candidate_party_id=party_id)

    if cycle_id:
        queryset = queryset.filter(election_cycle_id=cycle_id)

    # Apply search filter
    if search:
        queryset = queryset.filter(
            Q(candidate__first_name__icontains=search) |
            Q(candidate__last_name__icontains=search) |
            Q(name__first_name__icontains=search) |
            Q(name__last_name__icontains=search) |
            Q(candidate_office__name__icontains=search)
        )
    
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
            'committee_id': committee.committee_id,
            'candidate': {
                'full_name': committee.candidate.full_name if committee.candidate else None,
            } if committee.candidate else None,
            'name': {
                'full_name': committee.name.full_name if committee.name else None,
            } if committee.name else None,
            'candidate_office': {
                'name': committee.candidate_office.name if committee.candidate_office else None,
            } if committee.candidate_office else None,
            'candidate_party': {
                'name': committee.candidate_party.name if committee.candidate_party else None,
            } if committee.candidate_party else None,
            'election_cycle': {
                'name': committee.election_cycle.name if committee.election_cycle else None,
            } if committee.election_cycle else None,
            'is_incumbent': committee.candidate.is_incumbent if committee.candidate and hasattr(committee.candidate, 'is_incumbent') else False,
            'contacted': contacted,
            'contacted_at': contacted_at,
            'ie_total_for': float(committee.ie_total_for or 0),
            'ie_total_against': float(committee.ie_total_against or 0),
        })

    # Build response data
    if page is not None:
        response_data = {
            'results': result_data,
            'count': queryset.count(),
            'next': None,  # Will be added by paginator
            'previous': None  # Will be added by paginator
        }
    else:
        response_data = {
            'results': result_data,
            'count': len(result_data)
        }

    # Cache for 10 minutes with Zstd compression
    CompressedCache.set(cache_key, response_data, timeout=600)

    if page is not None:
        return paginator.get_paginated_response(result_data)

    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def donors_list(request):
    """OPTIMIZED: Use top_donors_mv materialized view + Zstd compression"""
    from transparency.utils.compressed_cache import CompressedCache

    # Build cache key from request parameters
    page_num = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 100)
    search = request.query_params.get('search', '')
    cache_key = f'donors_list_mv_p{page_num}_s{page_size}_q{search}'

    # Try to get from Zstd-compressed cache (10 minute cache)
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    # Use materialized view for blazing fast results!
    page_size = int(page_size)
    offset = (int(page_num) - 1) * page_size

    # Build search filter
    search_sql = ""
    search_params = []
    if search:
        search_sql = "WHERE d.entity_name ILIKE %s"
        search_params = [f"%{search}%"]

    # Query from materialized view ONLY - blazing fast with complete data!
    sql = f"""
        SELECT
            d.entity_id,
            d.entity_name as full_name,
            d.city,
            d.state,
            d.entity_type,
            ABS(d.total_contributed) as total_contribution,
            d.contribution_count as num_contributions
        FROM top_donors_mv d
        {search_sql}
        ORDER BY d.total_contributed DESC
        LIMIT %s OFFSET %s
    """

    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(sql, search_params + [page_size + 1, offset])
        rows = cursor.fetchall()

    # Check if there are more results
    has_next = len(rows) > page_size
    results = rows[:page_size]

    # Transform to match frontend expectations
    result_data = []
    for row in results:
        entity_type = {'name': row[4]} if row[4] else None
        donor_name = row[1] or 'Unknown'
        result_data.append({
            'id': row[0],
            'name': donor_name,
            'full_name': donor_name,
            'city': row[2],
            'state': row[3],
            'entity_type': entity_type,
            'total_contribution': float(row[5]) if row[5] else 0.0,
            'num_contributions': int(row[6]) if row[6] else 0,
            'linked_committees': 0,
            'ie_impact': 0.0,
        })

    # Get approximate count from materialized view (fast!)
    with connection.cursor() as cursor:
        if search:
            cursor.execute("SELECT COUNT(*) FROM top_donors_mv WHERE entity_name ILIKE %s", [f"%{search}%"])
        else:
            cursor.execute("SELECT COUNT(*) FROM top_donors_mv")
        total_count = cursor.fetchone()[0]

    # Build response
    response_data = {
        'results': result_data,
        'count': total_count,  # Fast count from materialized view
        'next': f'/api/v1/donors/?page={int(page_num) + 1}&page_size={page_size}' + (f'&search={search}' if search else '') if has_next else None,
        'previous': f'/api/v1/donors/?page={int(page_num) - 1}&page_size={page_size}' + (f'&search={search}' if search else '') if int(page_num) > 1 else None,
    }

    # Cache with Zstd compression for 10 minutes
    CompressedCache.set(cache_key, response_data, timeout=600)

    logger.info(f"Donors list loaded from MV: {len(result_data)} donors (page {page_num})")
    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def expenditures_list(request):
    """OPTIMIZED: Use raw SQL + Zstd compression for fast independent expenditure listing"""
    from transparency.utils.compressed_cache import CompressedCache
    from django.db import connection

    # Get pagination params
    page_num = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    search = request.query_params.get('search', '')

    # Build cache key
    cache_key = f'expenditures_list_p{page_num}_s{page_size}_q{search}'
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    # Calculate offset
    offset = (page_num - 1) * page_size

    # Build search conditions
    search_sql = ""
    search_params = []
    if search:
        search_sql = """
            AND (
                t.memo ILIKE %s
                OR COALESCE(cn.first_name || ' ' || cn.last_name, cn.last_name) ILIKE %s
                OR COALESCE(scn.first_name || ' ' || scn.last_name, scn.last_name) ILIKE %s
            )
        """
        search_term = f"%{search}%"
        search_params = [search_term, search_term, search_term]

    # Optimized SQL query with minimal JOINs
    sql = f"""
        SELECT
            t.transaction_id,
            t.transaction_date,
            t.amount,
            t.is_for_benefit,
            t.memo,
            COALESCE(cn.first_name || ' ' || cn.last_name, cn.last_name, 'Unknown') as committee_name,
            COALESCE(scn.first_name || ' ' || scn.last_name, scn.last_name, 'Unknown') as candidate_name
        FROM "Transactions" t
        LEFT JOIN "Committees" c ON t.committee_id = c.committee_id
        LEFT JOIN "Names" cn ON c.name_id = cn.name_id
        LEFT JOIN "Committees" sc ON t.subject_committee_id = sc.committee_id
        LEFT JOIN "Names" scn ON sc.name_id = scn.name_id
        WHERE t.subject_committee_id IS NOT NULL
          AND t.deleted = false
          {search_sql}
        ORDER BY t.transaction_date DESC NULLS LAST
        LIMIT %s OFFSET %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, search_params + [page_size + 1, offset])
        rows = cursor.fetchall()

    # Check if there are more results
    has_next = len(rows) > page_size
    results = rows[:page_size]

    # Format results
    result_data = []
    for row in results:
        transaction_id, transaction_date, amount, is_for_benefit, memo, committee_name, candidate_name = row

        # Build purpose
        if memo and memo.strip():
            purpose = memo.strip()
        else:
            support_type = 'Support' if is_for_benefit else 'Oppose'
            purpose = f"{support_type} {candidate_name}"

        result_data.append({
            'transaction_id': transaction_id,
            'transaction_date': transaction_date.isoformat() if transaction_date else None,
            'amount': float(amount) if amount else 0.0,
            'is_for_benefit': is_for_benefit,
            'committee': {
                'name': {
                    'full_name': committee_name
                }
            },
            'subject_committee': {
                'name': {
                    'full_name': candidate_name
                }
            },
            'purpose': purpose
        })

    # Get approximate count (fast query on indexed column)
    with connection.cursor() as cursor:
        count_sql = f"""
            SELECT COUNT(*)
            FROM "Transactions" t
            LEFT JOIN "Committees" c ON t.committee_id = c.committee_id
            LEFT JOIN "Names" cn ON c.name_id = cn.name_id
            LEFT JOIN "Committees" sc ON t.subject_committee_id = sc.committee_id
            LEFT JOIN "Names" scn ON sc.name_id = scn.name_id
            WHERE t.subject_committee_id IS NOT NULL
              AND t.deleted = false
              {search_sql}
        """
        cursor.execute(count_sql, search_params)
        total_count = cursor.fetchone()[0]

    # Build paginated response
    next_url = f'/api/v1/expenditures/?page={page_num + 1}&page_size={page_size}'
    prev_url = f'/api/v1/expenditures/?page={page_num - 1}&page_size={page_size}'
    if search:
        next_url += f'&search={search}'
        prev_url += f'&search={search}'

    response_data = {
        'results': result_data,
        'count': total_count,  # Fast count with index
        'next': next_url if has_next else None,
        'previous': prev_url if page_num > 1 else None,
    }

    # Cache for 5 minutes with Zstd compression
    CompressedCache.set(cache_key, response_data, timeout=300)

    logger.info(f"Expenditures loaded: {len(result_data)} (page {page_num})")
    return Response(response_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def expenditures_list_OLD_SLOW(request):
    """OLD SLOW VERSION - kept for reference"""
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
            committee_data = item.get('committee', {})
            subject_comm = item.get('subject_committee', {})
            memo = item.get('memo', '').strip()
            is_for_benefit = item.get('is_for_benefit')

            # Get committee name
            committee_name = committee_data.get('name', 'Unknown') if committee_data else 'Unknown'

            # Get candidate/subject committee name
            candidate_name = subject_comm.get('candidate_name', 'Unknown') if subject_comm else 'Unknown'

            # Build purpose: use memo if available, otherwise use Support/Oppose + candidate name
            if memo:
                purpose = memo
            else:
                support_type = 'Support' if is_for_benefit else 'Oppose'
                purpose = f"{support_type} {candidate_name}"

            # Format to match frontend expectations
            result_data.append({
                'transaction_id': item.get('transaction_id'),
                'transaction_date': item.get('transaction_date'),
                'amount': item.get('amount'),
                'is_for_benefit': is_for_benefit,
                'committee': {
                    'name': {
                        'full_name': committee_name
                    }
                },
                'subject_committee': {
                    'name': {
                        'full_name': candidate_name
                    }
                },
                'purpose': purpose
            })
        return paginator.get_paginated_response(result_data)
    
    serializer = TransactionSerializer(queryset, many=True)
    result_data = []
    for item in serializer.data:
        committee_data = item.get('committee', {})
        subject_comm = item.get('subject_committee', {})
        memo = item.get('memo', '').strip()
        is_for_benefit = item.get('is_for_benefit')

        # Get committee name
        committee_name = committee_data.get('name', 'Unknown') if committee_data else 'Unknown'

        # Get candidate/subject committee name
        candidate_name = subject_comm.get('candidate_name', 'Unknown') if subject_comm else 'Unknown'

        # Build purpose: use memo if available, otherwise use Support/Oppose + candidate name
        if memo:
            purpose = memo
        else:
            support_type = 'Support' if is_for_benefit else 'Oppose'
            purpose = f"{support_type} {candidate_name}"

        # Format to match frontend expectations
        result_data.append({
            'transaction_id': item.get('transaction_id'),
            'transaction_date': item.get('transaction_date'),
            'amount': item.get('amount'),
            'is_for_benefit': is_for_benefit,
            'committee': {
                'name': {
                    'full_name': committee_name
                }
            },
            'subject_committee': {
                'name': {
                    'full_name': candidate_name
                }
            },
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
        logger.info("Returning cached dashboard data")
        return Response(cached_data)
    
    logger.info("Computing fresh dashboard data...")
    
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
        
        logger.info("Dashboard data computed and cached")
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