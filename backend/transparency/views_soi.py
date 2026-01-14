"""
SOI-specific views for Phase 1 completion
"""
import uuid
import requests
from django.utils import timezone
from django.db.models import Count, Q
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
import logging

from .models import CandidateStatementOfInterest, EmailTemplate, EmailLog, EmailCampaign, SOIScrapeJob, Office
from .serializers import CandidateSOISerializer, EmailTemplateSerializer

logger = logging.getLogger(__name__)

# Laptop agent configuration (via SSH tunnel)
LAPTOP_AGENT_URL = getattr(settings, 'LAPTOP_AGENT_URL', 'http://localhost:5001')

@api_view(['GET'])
@permission_classes([AllowAny])
def soi_dashboard_stats(request):
    """Get SOI dashboard statistics + Zstd compression"""
    from transparency.utils.compressed_cache import CompressedCache

    cache_key = 'soi_dashboard_stats_v1'

    # Try Zstd-compressed cache first (5 min TTL)
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        stats = CandidateStatementOfInterest.objects.aggregate(
            total=Count('id'),
            uncontacted=Count('id', filter=Q(contact_status='uncontacted')),
            contacted=Count('id', filter=Q(contact_status='contacted')),
            acknowledged=Count('id', filter=Q(contact_status='acknowledged')),
            pledged=Count('id', filter=Q(pledge_received=True))
        )

        response_data = {
            'total_candidates': stats['total'],
            'uncontacted': stats['uncontacted'],
            'contacted': stats['contacted'],
            'acknowledged': stats['acknowledged'],
            'pledged': stats['pledged'],
            'pending_pledge': stats['contacted'] - stats['pledged']
        }

        # Cache for 5 minutes with Zstd compression
        CompressedCache.set(cache_key, response_data, timeout=300)

        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching SOI stats: {e}")
        return Response({
            'total_candidates': 0,
            'uncontacted': 0,
            'contacted': 0,
            'acknowledged': 0,
            'pledged': 0,
            'pending_pledge': 0
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def soi_candidates_list(request):
    """Get SOI candidates list with filtering and pagination + Zstd compression"""
    from transparency.utils.compressed_cache import CompressedCache

    # Build cache key from request parameters
    status_filter = request.GET.get('status', '')
    office_id = request.GET.get('office', '')
    pledge_filter = request.GET.get('pledge_received', '')
    search_term = request.GET.get('search', '')
    page_size = int(request.GET.get('page_size', 20))
    page = int(request.GET.get('page', 1))

    cache_key = f'soi_candidates_list_st{status_filter}_o{office_id}_pf{pledge_filter}_s{search_term}_pg{page}_ps{page_size}'

    # Try Zstd-compressed cache first (5 min TTL)
    cached_data = CompressedCache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        queryset = CandidateStatementOfInterest.objects.select_related('office').all()

        # Apply filters
        if status_filter:
            queryset = queryset.filter(contact_status=status_filter)

        if office_id:
            queryset = queryset.filter(office_id=office_id)

        if pledge_filter:
            queryset = queryset.filter(pledge_received=pledge_filter.lower() == 'true')

        if search_term:
            queryset = queryset.filter(
                Q(candidate_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(office__name__icontains=search_term)
            )

        # Order by filing date (newest first)
        queryset = queryset.order_by('-filing_date')

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        total_count = queryset.count()
        candidates = queryset[start_idx:end_idx]

        serializer = CandidateSOISerializer(candidates, many=True)

        response_data = {
            'results': serializer.data,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }

        # Cache for 5 minutes with Zstd compression
        CompressedCache.set(cache_key, response_data, timeout=300)

        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching SOI candidates: {e}")
        return Response({
            'error': str(e),
            'results': [],
            'count': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # SECURITY FIX: Require auth for modifications
def mark_candidate_contacted(request, pk):
    """Mark candidate as contacted - REQUIRES AUTHENTICATION"""
    try:
        candidate = CandidateStatementOfInterest.objects.get(id=pk)
        candidate.contact_status = 'contacted'
        candidate.contact_date = timezone.now().date()
        candidate.contacted_by = request.data.get('contacted_by', 'System')
        candidate.save()
        
        serializer = CandidateSOISerializer(candidate)
        return Response(serializer.data)
        
    except CandidateStatementOfInterest.DoesNotExist:
        return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error marking candidate contacted: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # SECURITY FIX: Require auth for modifications
def mark_pledge_received(request, pk):
    """Mark pledge as received - REQUIRES AUTHENTICATION"""
    try:
        candidate = CandidateStatementOfInterest.objects.get(id=pk)
        candidate.pledge_received = True
        candidate.pledge_date = timezone.now().date()
        candidate.contact_status = 'acknowledged'
        candidate.notes = request.data.get('notes', candidate.notes)
        candidate.save()
        
        serializer = CandidateSOISerializer(candidate)
        return Response(serializer.data)
        
    except CandidateStatementOfInterest.DoesNotExist:
        return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error marking pledge received: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def email_templates(request):
    """Get all email templates"""
    try:
        templates = EmailTemplate.objects.filter(is_active=True)
        serializer = EmailTemplateSerializer(templates, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error fetching email templates: {e}")
        return Response([], status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # SECURITY FIX: Require auth
def send_bulk_emails(request):
    """Send bulk emails to candidates - REQUIRES AUTHENTICATION"""
    try:
        from .services.email_service import EmailService
        
        candidate_ids = request.data.get('candidate_ids', [])
        template_id = request.data.get('template_id')
        custom_subject = request.data.get('custom_subject')
        custom_body = request.data.get('custom_body')
        
        if not candidate_ids or not template_id:
            return Response(
                {'error': 'candidate_ids and template_id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email_service = EmailService()
        results = email_service.send_bulk_emails(
            candidate_ids, 
            template_id,
            custom_subject,
            custom_body
        )
        
        return Response({
            'success': True,
            'results': results,
            'message': f"Sent {results.get('success', 0)} emails, {results.get('failed', 0)} failed"
        })
        
    except Exception as e:
        logger.error(f"Error sending bulk emails: {e}")
        return Response(
            {'error': str(e), 'success': False}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def email_stats(request):
    """Get email campaign statistics"""
    try:
        total_sent = EmailLog.objects.filter(status='sent').count()
        total_opened = EmailLog.objects.filter(opened_at__isnull=False).count()
        total_clicked = EmailLog.objects.filter(clicked_at__isnull=False).count()
        
        open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        
        recent_campaigns = EmailCampaign.objects.filter(
            status='sent'
        ).order_by('-sent_at')[:5].values(
            'name', 'sent_at', 'template__name'
        )
        
        return Response({
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'open_rate': round(open_rate, 1),
            'click_rate': round(click_rate, 1),
            'recent_campaigns': list(recent_campaigns)
        })
        
    except Exception as e:
        logger.error(f"Error fetching email stats: {e}")
        return Response({
            'total_sent': 0,
            'total_opened': 0,
            'total_clicked': 0,
            'open_rate': 0,
            'click_rate': 0,
            'recent_campaigns': []
        })


# ==================== SOI SCRAPER ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([AllowAny])  # Can add auth later
def trigger_soi_scrape(request):
    """
    Trigger SOI scrape via laptop agent (through SSH tunnel).

    POST /api/soi/trigger-scrape/

    Returns job_id to track progress.
    """
    try:
        # Create job record
        job_id = str(uuid.uuid4())
        job = SOIScrapeJob.objects.create(
            job_id=job_id,
            status='pending',
            triggered_by=request.META.get('REMOTE_ADDR', 'unknown')
        )

        # Try to trigger laptop agent
        try:
            response = requests.post(
                f"{LAPTOP_AGENT_URL}/scrape",
                json={
                    'job_id': job_id,
                    'callback_url': request.build_absolute_uri('/api/soi/scrape-callback/')
                },
                timeout=10
            )

            if response.status_code == 200:
                job.status = 'running'
                job.started_at = timezone.now()
                job.save()

                return Response({
                    'success': True,
                    'job_id': job_id,
                    'status': 'running',
                    'message': 'Scrape started on laptop agent'
                })
            else:
                job.status = 'failed'
                job.error_message = f"Laptop agent returned {response.status_code}: {response.text}"
                job.save()

                return Response({
                    'success': False,
                    'job_id': job_id,
                    'status': 'failed',
                    'message': f"Laptop agent error: {response.status_code}"
                }, status=status.HTTP_502_BAD_GATEWAY)

        except requests.exceptions.ConnectionError:
            job.status = 'failed'
            job.error_message = 'Cannot connect to laptop agent. Is the SSH tunnel running?'
            job.save()

            return Response({
                'success': False,
                'job_id': job_id,
                'status': 'failed',
                'message': 'Laptop agent not reachable. Check SSH tunnel.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except requests.exceptions.Timeout:
            job.status = 'failed'
            job.error_message = 'Laptop agent request timed out'
            job.save()

            return Response({
                'success': False,
                'job_id': job_id,
                'status': 'failed',
                'message': 'Laptop agent timed out'
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)

    except Exception as e:
        logger.error(f"Error triggering SOI scrape: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # Laptop agent callback
def soi_scrape_callback(request):
    """
    Callback endpoint for laptop agent to submit scrape results.

    POST /api/soi/scrape-callback/
    {
        "job_id": "uuid",
        "status": "completed|failed",
        "candidates": [...],
        "error": "optional error message"
    }
    """
    try:
        job_id = request.data.get('job_id')
        scrape_status = request.data.get('status')
        candidates = request.data.get('candidates', [])
        error = request.data.get('error', '')

        if not job_id:
            return Response({'error': 'job_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = SOIScrapeJob.objects.get(job_id=job_id)
        except SOIScrapeJob.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

        job.completed_at = timezone.now()
        job.candidates_found = len(candidates)

        if scrape_status == 'failed':
            job.status = 'failed'
            job.error_message = error
            job.save()
            return Response({'success': True, 'message': 'Job marked as failed'})

        # Process candidates
        created = 0
        updated = 0

        for candidate_data in candidates:
            try:
                name = candidate_data.get('name', '').strip()
                office_name = candidate_data.get('office', '').strip()

                if not name or len(name) < 2:
                    continue

                # Get or create office
                office = None
                if office_name and len(office_name) > 2:
                    office, _ = Office.objects.get_or_create(
                        name=office_name,
                        defaults={'office_type': 'STATE'}
                    )

                if not office:
                    continue

                # Check if candidate exists
                soi, was_created = CandidateStatementOfInterest.objects.get_or_create(
                    candidate_name=name,
                    office=office,
                    defaults={
                        'email': candidate_data.get('email', ''),
                        'phone': candidate_data.get('phone', ''),
                        'party': candidate_data.get('party', ''),
                        'filing_date': timezone.now().date(),
                        'contact_status': 'uncontacted',
                        'pledge_received': False
                    }
                )

                if was_created:
                    created += 1
                else:
                    # Update if new info available
                    changed = False
                    if candidate_data.get('email') and not soi.email:
                        soi.email = candidate_data['email']
                        changed = True
                    if candidate_data.get('phone') and not soi.phone:
                        soi.phone = candidate_data['phone']
                        changed = True
                    if changed:
                        soi.save()
                        updated += 1

            except Exception as e:
                logger.error(f"Error processing candidate {candidate_data}: {e}")

        job.status = 'completed'
        job.candidates_created = created
        job.candidates_updated = updated
        job.save()

        logger.info(f"SOI Scrape {job_id} completed: {created} created, {updated} updated")

        return Response({
            'success': True,
            'created': created,
            'updated': updated,
            'total_found': len(candidates)
        })

    except Exception as e:
        logger.error(f"Error processing scrape callback: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def soi_scrape_status(request, job_id):
    """
    Get status of a scrape job.

    GET /api/soi/scrape-status/<job_id>/
    """
    try:
        job = SOIScrapeJob.objects.get(job_id=job_id)
        return Response({
            'job_id': job.job_id,
            'status': job.status,
            'candidates_found': job.candidates_found,
            'candidates_created': job.candidates_created,
            'candidates_updated': job.candidates_updated,
            'error_message': job.error_message,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
            'created_at': job.created_at
        })
    except SOIScrapeJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def soi_scrape_history(request):
    """
    Get recent scrape job history.

    GET /api/soi/scrape-history/
    """
    jobs = SOIScrapeJob.objects.all()[:20]
    return Response([{
        'job_id': job.job_id,
        'status': job.status,
        'candidates_found': job.candidates_found,
        'candidates_created': job.candidates_created,
        'candidates_updated': job.candidates_updated,
        'created_at': job.created_at,
        'completed_at': job.completed_at
    } for job in jobs])


@api_view(['GET'])
@permission_classes([AllowAny])
def soi_agent_health(request):
    """
    Check if laptop agent is reachable via SSH tunnel.

    GET /api/soi/agent-health/
    """
    try:
        response = requests.get(f"{LAPTOP_AGENT_URL}/health", timeout=5)
        if response.status_code == 200:
            return Response({
                'agent_status': 'online',
                'agent_response': response.json()
            })
        else:
            return Response({
                'agent_status': 'error',
                'message': f"Agent returned {response.status_code}"
            })
    except requests.exceptions.ConnectionError:
        return Response({
            'agent_status': 'offline',
            'message': 'Cannot connect to laptop agent. SSH tunnel may be down.'
        })
    except requests.exceptions.Timeout:
        return Response({
            'agent_status': 'timeout',
            'message': 'Laptop agent request timed out'
        })