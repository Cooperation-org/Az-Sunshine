"""
SOI-specific views for Phase 1 completion
"""
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
import logging

from .models import CandidateStatementOfInterest, EmailTemplate, EmailLog, EmailCampaign
from .serializers import CandidateSOISerializer, EmailTemplateSerializer

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def soi_dashboard_stats(request):
    """Get SOI dashboard statistics"""
    try:
        stats = CandidateStatementOfInterest.objects.aggregate(
            total=Count('id'),
            uncontacted=Count('id', filter=Q(contact_status='uncontacted')),
            contacted=Count('id', filter=Q(contact_status='contacted')),
            acknowledged=Count('id', filter=Q(contact_status='acknowledged')),
            pledged=Count('id', filter=Q(pledge_received=True))
        )
        
        return Response({
            'total_candidates': stats['total'],
            'uncontacted': stats['uncontacted'],
            'contacted': stats['contacted'],
            'acknowledged': stats['acknowledged'],
            'pledged': stats['pledged'],
            'pending_pledge': stats['contacted'] - stats['pledged']
        })
        
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
    """Get SOI candidates list with filtering and pagination"""
    try:
        queryset = CandidateStatementOfInterest.objects.select_related('office').all()
        
        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(contact_status=status_filter)
        
        office_id = request.GET.get('office')
        if office_id:
            queryset = queryset.filter(office_id=office_id)
        
        pledge_filter = request.GET.get('pledge_received')
        if pledge_filter is not None:
            queryset = queryset.filter(pledge_received=pledge_filter.lower() == 'true')
        
        search_term = request.GET.get('search')
        if search_term:
            queryset = queryset.filter(
                Q(candidate_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(office__name__icontains=search_term)
            )
        
        # Order by filing date (newest first)
        queryset = queryset.order_by('-filing_date')
        
        # Pagination
        page_size = int(request.GET.get('page_size', 20))
        page = int(request.GET.get('page', 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        total_count = queryset.count()
        candidates = queryset[start_idx:end_idx]
        
        serializer = CandidateSOISerializer(candidates, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
        
    except Exception as e:
        logger.error(f"Error fetching SOI candidates: {e}")
        return Response({
            'error': str(e),
            'results': [],
            'count': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def mark_candidate_contacted(request, candidate_id):
    """Mark candidate as contacted"""
    try:
        candidate = CandidateStatementOfInterest.objects.get(id=candidate_id)
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
@permission_classes([AllowAny])
def mark_pledge_received(request, candidate_id):
    """Mark pledge as received"""
    try:
        candidate = CandidateStatementOfInterest.objects.get(id=candidate_id)
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
@permission_classes([AllowAny])
def send_bulk_emails(request):
    """Send bulk emails to candidates"""
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