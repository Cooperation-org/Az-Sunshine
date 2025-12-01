# backend/transparency/services/email_service.py
"""
Email Service - Phase 1 Requirement 1b
Handles email sending, tracking, and template processing
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template import Template, Context
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending and tracking emails"""
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.tracking_base_url = settings.TRACKING_BASE_URL
    
    def generate_tracking_id(self):
        """Generate a unique tracking ID for an email"""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]
    
    def add_tracking_to_body(self, body, tracking_id):
        """
        Add tracking pixel and wrap links with click tracking
        """
        # Add tracking pixel at the end of the email
        tracking_pixel = f'<img src="{self.tracking_base_url}/api/v1/email-tracking/open/{tracking_id}/" width="1" height="1" alt="" />'
        
        # Convert plain text to HTML if needed
        if '<html>' not in body.lower() and '<body>' not in body.lower():
            body_html = f"""
            <html>
            <body>
                {body.replace(chr(10), '<br>')}
                {tracking_pixel}
            </body>
            </html>
            """
        else:
            # Insert tracking pixel before closing body tag
            body_html = body.replace('</body>', f'{tracking_pixel}</body>')
        
        # TODO: Wrap links with click tracking
        # For now, we'll keep links as-is
        # In production, you'd parse HTML and replace hrefs with tracking URLs
        
        return body_html
    
    def send_email(self, to_email, subject, body, tracking_id=None):
        """
        Send an email with optional tracking
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body (HTML or plain text)
            tracking_id (str): Optional tracking ID
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # If tracking_id provided, add tracking
            if tracking_id:
                html_body = self.add_tracking_to_body(body, tracking_id)
            else:
                html_body = body
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=self._strip_html(html_body),  # Plain text fallback
                from_email=self.from_email,
                to=[to_email]
            )
            
            # Attach HTML version
            email.attach_alternative(html_body, "text/html")
            
            # Send
            email.send()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False
    
    def send_bulk_emails(self, candidate_ids, template_id, custom_data=None):
        """
        Send bulk emails to multiple candidates
        
        Args:
            candidate_ids (list): List of candidate IDs
            template_id (int): Email template ID
            custom_data (dict): Optional custom data for template variables
        
        Returns:
            dict: Results with success/failure counts
        """
        from transparency.models import CandidateStatementOfInterest, EmailTemplate, EmailLog
        from django.utils import timezone
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Get template
            template = EmailTemplate.objects.get(id=template_id)
            
            # Get candidates
            candidates = CandidateStatementOfInterest.objects.filter(
                id__in=candidate_ids,
                email__isnull=False
            ).exclude(email='')
            
            for candidate in candidates:
                try:
                    # Generate tracking ID
                    tracking_id = self.generate_tracking_id()
                    
                    # Prepare subject and body with variable replacement
                    subject = template.subject
                    body = template.body
                    
                    # Replace variables
                    subject = subject.replace('{{candidate_name}}', candidate.candidate_name)
                    subject = subject.replace('{{office}}', candidate.office.name if candidate.office else '')
                    
                    body = body.replace('{{candidate_name}}', candidate.candidate_name)
                    body = body.replace('{{office}}', candidate.office.name if candidate.office else '')
                    
                    # Send email
                    sent = self.send_email(
                        to_email=candidate.email,
                        subject=subject,
                        body=body,
                        tracking_id=tracking_id
                    )
                    
                    # Create email log
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
                    logger.error(f"Error sending email to candidate {candidate.id}: {e}")
                    results['failed'] += 1
                    results['errors'].append(f"{candidate.email}: {str(e)}")
            
            return results
            
        except EmailTemplate.DoesNotExist:
            logger.error(f"Template {template_id} not found")
            results['failed'] = len(candidate_ids)
            results['errors'].append("Template not found")
            return results
        except Exception as e:
            logger.error(f"Error in bulk email sending: {e}", exc_info=True)
            results['failed'] = len(candidate_ids)
            results['errors'].append(str(e))
            return results
    
    def _strip_html(self, html_text):
        """Strip HTML tags for plain text version"""
        import re
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html_text)
        # Replace <br> with newlines
        text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        return text