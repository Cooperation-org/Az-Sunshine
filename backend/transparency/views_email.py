# backend/transparency/views_email.py
"""
Email Campaign Views - Phase 1 Requirement 1b
Complete implementation with real email sending and tracking
"""

from django.utils import timezone
from django.shortcuts import redirect
from django.http import HttpResponse
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

from .models import (
    EmailTemplate,
    EmailCampaign,
    EmailLog,
    CandidateStatementOfInterest,
)
from .serializers import (
    EmailTemplateSerializer,
    EmailCampaignSerializer,
    EmailLogSerializer,
    EmailLogListSerializer,
)
from .services.email_service import EmailService

import logging

logger = logging.getLogger(__name__)


# ==================== EMAIL TEMPLATE VIEWSET ====================

class EmailTemplateViewSet(viewsets.ModelViewSet):
    """Manage email templates"""
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        queryset = EmailTemplate.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-created_at')


# ==================== EMAIL CAMPAIGN VIEWSET ====================

class EmailCampaignViewSet(viewsets.ModelViewSet):
    """Manage email campaigns"""
    queryset = EmailCampaign.objects.all()
    serializer_class = EmailCampaignSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        return EmailCampaign.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send campaign emails"""
        campaign = self.get_object()
        
        if campaign.status != 'draft':
            return Response(
                {'error': 'Campaign must be in draft status to send'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidates for this campaign
        candidates = campaign.candidates.all()
        
        if not candidates.exists():
            return Response(
                {'error': 'No candidates selected for this campaign'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update campaign status
        campaign.status = 'sending'
        campaign.save()
        
        # Send emails
        email_service = EmailService()
        sent_count = 0
        failed_count = 0
        
        for candidate in candidates:
            try:
                # Generate tracking ID
                tracking_id = email_service.generate_tracking_id()
                
                # Prepare email content
                subject = campaign.template.subject.replace('{{candidate_name}}', candidate.candidate_name)
                subject = subject.replace('{{office}}', candidate.office.name if candidate.office else '')
                
                body = campaign.template.body.replace('{{candidate_name}}', candidate.candidate_name)
                body = body.replace('{{office}}', candidate.office.name if candidate.office else '')
                
                # Add tracking pixel
                body_with_tracking = email_service.add_tracking_to_body(body, tracking_id)
                
                # Send email
                sent = email_service.send_email(
                    to_email=candidate.email,
                    subject=subject,
                    body=body_with_tracking,
                    tracking_id=tracking_id
                )
                
                # Create email log
                EmailLog.objects.create(
                    campaign=campaign,
                    candidate=candidate,
                    template=campaign.template,
                    tracking_id=tracking_id,
                    subject=subject,
                    body=body,
                    status='sent' if sent else 'failed',
                    sent_at=timezone.now() if sent else None,
                    error_message='' if sent else 'Failed to send'
                )
                
                if sent:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending email to {candidate.email}: {e}")
                failed_count += 1
        
        # Update campaign status
        campaign.status = 'sent'
        campaign.sent_at = timezone.now()
        campaign.save()
        
        return Response({
            'success': True,
            'sent': sent_count,
            'failed': failed_count,
            'total': candidates.count()
        })


# ==================== EMAIL LOG VIEWSET ====================

class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View email logs and history"""
    queryset = EmailLog.objects.all()
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmailLogListSerializer
        return EmailLogSerializer
    
    def get_queryset(self):
        queryset = EmailLog.objects.select_related(
            'campaign',
            'candidate',
            'template'
        ).all()
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign', None)
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(sent_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(sent_at__lte=date_to)
        
        return queryset.order_by('-sent_at')


# ==================== EMAIL STATISTICS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def email_statistics(request):
    """Get email campaign statistics"""
    
    # Date range filter
    date_from = request.query_params.get('date_from', None)
    date_to = request.query_params.get('date_to', None)
    
    queryset = EmailLog.objects.filter(status='sent')
    
    if date_from:
        queryset = queryset.filter(sent_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(sent_at__lte=date_to)
    
    # Calculate statistics
    total_sent = queryset.count()
    total_opened = queryset.filter(opened_at__isnull=False).count()
    total_clicked = queryset.filter(clicked_at__isnull=False).count()
    
    open_rate = (total_opened / total_sent * 100) if total_sent > 0 else 0
    click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
    
    # Get top performing campaigns
    top_campaigns = EmailCampaign.objects.filter(
        status='sent'
    ).annotate(
        total_sent=models.Count('emaillog'),
        total_opened=models.Count('emaillog', filter=models.Q(emaillog__opened_at__isnull=False)),
        total_clicked=models.Count('emaillog', filter=models.Q(emaillog__clicked_at__isnull=False))
    ).order_by('-total_opened')[:5]
    
    return Response({
        'total_sent': total_sent,
        'total_opened': total_opened,
        'total_clicked': total_clicked,
        'open_rate': round(open_rate, 1),
        'click_rate': round(click_rate, 1),
        'top_campaigns': EmailCampaignSerializer(top_campaigns, many=True).data
    })


# ==================== SEND SINGLE EMAIL ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def send_single_email(request):
    """Send a single email to a candidate"""
    
    try:
        candidate_id = request.data.get('candidate_id')
        template_id = request.data.get('template_id')
        custom_subject = request.data.get('subject', None)
        custom_body = request.data.get('body', None)
        
        if not candidate_id or not template_id:
            return Response(
                {'error': 'candidate_id and template_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get candidate and template
        candidate = CandidateStatementOfInterest.objects.get(id=candidate_id)
        template = EmailTemplate.objects.get(id=template_id)
        
        if not candidate.email:
            return Response(
                {'error': 'Candidate has no email address'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare email content
        email_service = EmailService()
        tracking_id = email_service.generate_tracking_id()
        
        # Use custom content or template content
        subject = custom_subject or template.subject
        body = custom_body or template.body
        
        # Replace variables
        subject = subject.replace('{{candidate_name}}', candidate.candidate_name)
        subject = subject.replace('{{office}}', candidate.office.name if candidate.office else '')
        
        body = body.replace('{{candidate_name}}', candidate.candidate_name)
        body = body.replace('{{office}}', candidate.office.name if candidate.office else '')
        
        # Add tracking
        body_with_tracking = email_service.add_tracking_to_body(body, tracking_id)
        
        # Send email
        sent = email_service.send_email(
            to_email=candidate.email,
            subject=subject,
            body=body_with_tracking,
            tracking_id=tracking_id
        )
        
        if sent:
            # Create email log
            EmailLog.objects.create(
                candidate=candidate,
                template=template,
                tracking_id=tracking_id,
                subject=subject,
                body=body,
                status='sent',
                sent_at=timezone.now()
            )
            
            return Response({
                'success': True,
                'message': f'Email sent to {candidate.email}',
                'tracking_id': tracking_id
            })
        else:
            return Response(
                {'error': 'Failed to send email'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except CandidateStatementOfInterest.DoesNotExist:
        return Response(
            {'error': 'Candidate not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except EmailTemplate.DoesNotExist:
        return Response(
            {'error': 'Template not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error sending single email: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== EMAIL TRACKING ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def track_email_open(request, tracking_id):
    """
    Track email opens via 1x1 transparent pixel
    GET /api/v1/email-tracking/open/<tracking_id>/
    """
    try:
        email_log = EmailLog.objects.get(tracking_id=tracking_id)
        
        # Only record first open
        if not email_log.opened_at:
            email_log.opened_at = timezone.now()
            email_log.save()
            logger.info(f"Email opened: {tracking_id}")
        
        # Return 1x1 transparent GIF pixel
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
        return HttpResponse(pixel, content_type='image/gif')
        
    except EmailLog.DoesNotExist:
        logger.warning(f"Tracking ID not found: {tracking_id}")
        # Still return pixel to avoid broken images
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
        return HttpResponse(pixel, content_type='image/gif')
    except Exception as e:
        logger.error(f"Error tracking email open: {e}", exc_info=True)
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'
        return HttpResponse(pixel, content_type='image/gif')


@api_view(['GET'])
@permission_classes([AllowAny])
def track_email_click(request, tracking_id):
    """
    Track email link clicks and redirect
    GET /api/v1/email-tracking/click/<tracking_id>/?url=<destination>
    """
    try:
        email_log = EmailLog.objects.get(tracking_id=tracking_id)
        
        # Only record first click
        if not email_log.clicked_at:
            email_log.clicked_at = timezone.now()
            email_log.save()
            logger.info(f"Email clicked: {tracking_id}")
        
        # Get redirect URL from query params
        redirect_url = request.GET.get('url', 'https://arizonasunshine.org')
        
        # Redirect to actual destination
        return redirect(redirect_url)
        
    except EmailLog.DoesNotExist:
        logger.warning(f"Tracking ID not found: {tracking_id}")
        # Redirect to homepage
        return redirect('https://arizonasunshine.org')
    except Exception as e:
        logger.error(f"Error tracking email click: {e}", exc_info=True)
        return redirect('https://arizonasunshine.org')


# ==================== BULK EMAIL SENDING ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def send_bulk_emails(request):
    """
    Send bulk emails to multiple candidates
    POST /api/v1/email/send-bulk/
    Body: {
        "candidate_ids": [1, 2, 3],
        "template_id": 1,
        "custom_subject": "Optional custom subject",
        "custom_body": "Optional custom body"
    }
    """
    
    try:
        candidate_ids = request.data.get('candidate_ids', [])
        template_id = request.data.get('template_id')
        custom_subject = request.data.get('subject', None)
        custom_body = request.data.get('body', None)
        
        if not candidate_ids or not template_id:
            return Response(
                {'error': 'candidate_ids and template_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get template
        template = EmailTemplate.objects.get(id=template_id)
        
        # Get candidates
        candidates = CandidateStatementOfInterest.objects.filter(
            id__in=candidate_ids,
            email__isnull=False
        ).exclude(email='')
        
        if not candidates.exists():
            return Response(
                {'error': 'No valid candidates with email addresses'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send emails
        email_service = EmailService()
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for candidate in candidates:
            try:
                tracking_id = email_service.generate_tracking_id()
                
                # Prepare content
                subject = custom_subject or template.subject
                body = custom_body or template.body
                
                subject = subject.replace('{{candidate_name}}', candidate.candidate_name)
                subject = subject.replace('{{office}}', candidate.office.name if candidate.office else '')
                
                body = body.replace('{{candidate_name}}', candidate.candidate_name)
                body = body.replace('{{office}}', candidate.office.name if candidate.office else '')
                
                # Add tracking
                body_with_tracking = email_service.add_tracking_to_body(body, tracking_id)
                
                # Send
                sent = email_service.send_email(
                    to_email=candidate.email,
                    subject=subject,
                    body=body_with_tracking,
                    tracking_id=tracking_id
                )
                
                # Log
                EmailLog.objects.create(
                    candidate=candidate,
                    template=template,
                    tracking_id=tracking_id,
                    subject=subject,
                    body=body,
                    status='sent' if sent else 'failed',
                    sent_at=timezone.now() if sent else None,
                    error_message='' if sent else 'Failed to send'
                )
                
                if sent:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send to {candidate.email}")
                    
            except Exception as e:
                logger.error(f"Error sending bulk email to {candidate.email}: {e}")
                results['failed'] += 1
                results['errors'].append(f"{candidate.email}: {str(e)}")
        
        return Response({
            'success': True,
            'results': results,
            'message': f"Sent {results['success']} emails, {results['failed']} failed"
        })
        
    except EmailTemplate.DoesNotExist:
        return Response(
            {'error': 'Template not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error sending bulk emails: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )