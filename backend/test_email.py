"""
Email Testing Script for Arizona Sunshine
Run with: python manage.py shell < test_email.py
Or: python manage.py shell
>>> exec(open('test_email.py').read())
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from transparency.models import CandidateStatementOfInterest

def test_basic_email():
    """Test 1: Send a basic text email"""
    print("\n" + "="*60)
    print("TEST 1: Basic Email")
    print("="*60)
    
    try:
        result = send_mail(
            subject='Arizona Sunshine - Email System Test',
            message='This is a test email from the SOI tracking system.\n\nIf you receive this, SMTP is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        
        if result == 1:
            print("SUCCESS: Basic email sent!")
            print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
            print(f"   To: {settings.EMAIL_HOST_USER}")
            return True
        else:
            print("FAILED: Email not sent (result = 0)")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"\nCheck your .env file:")
        print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
        return False


def test_html_email():
    """Test 2: Send an HTML email with tracking"""
    print("\n" + "="*60)
    print("TEST 2: HTML Email with Tracking")
    print("="*60)
    
    try:
        tracking_id = "test_" + str(hash(str(os.urandom(16))))
        tracking_pixel_url = f"{settings.TRACKING_BASE_URL}/api/v1/email-tracking/open/{tracking_id}/"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #6B5B95;">Arizona Sunshine - HTML Email Test</h2>
            <p>This is a test email with HTML formatting.</p>
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px;">
                <h3>Features Tested:</h3>
                <ul>
                    <li>HTML rendering</li>
                    <li>Email styling</li>
                    <li>Tracking pixel (see below)</li>
                </ul>
            </div>
            <p style="margin-top: 20px;">
                <a href="{settings.TRACKING_BASE_URL}" 
                   style="background-color: #6B5B95; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Visit Dashboard
                </a>
            </p>
            <img src="{tracking_pixel_url}" width="1" height="1" alt="" style="display:none;" />
        </body>
        </html>
        """
        
        email = EmailMessage(
            subject='Arizona Sunshine - HTML Email Test',
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],
        )
        email.content_subtype = 'html'
        
        result = email.send()
        
        if result == 1:
            print("SUCCESS: HTML email sent!")
            print(f"   Tracking ID: {tracking_id}")
            print(f"   Tracking URL: {tracking_pixel_url}")
            return True
        else:
            print("FAILED: HTML email not sent")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


def test_soi_email_template():
    """Test 3: Send email using SOI template"""
    print("\n" + "="*60)
    print("TEST 3: SOI Campaign Email Template")
    print("="*60)
    
    try:
        # Get a sample candidate or create a test one
        candidate = CandidateStatementOfInterest.objects.first()
        
        if not candidate:
            print(" No candidates in database. Creating test candidate...")
            from transparency.models import Office
            office, _ = Office.objects.get_or_create(
                office_id=9999,
                defaults={'name': 'Test Office', 'office_type': 'TEST'}
            )
            candidate = CandidateStatementOfInterest.objects.create(
                candidate_name="Test Candidate",
                office=office,
                email=settings.EMAIL_HOST_USER,
                filing_date='2024-01-01',
                contact_status='uncontacted'
            )
            print(f"Created test candidate: {candidate.candidate_name}")
        
        # Create personalized email
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #6B5B95; color: white; padding: 20px; text-align: center;">
                <h1>Arizona Sunshine</h1>
            </div>
            
            <div style="padding: 30px;">
                <p>Dear {candidate.candidate_name},</p>
                
                <p>We hope this message finds you well. We are reaching out regarding your 
                candidacy for <strong>{candidate.office.name}</strong>.</p>
                
                <p>We would like to request your Statement of Interest (SOI) to better 
                understand your campaign priorities and how we might work together.</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Your Filing Information:</h3>
                    <ul>
                        <li><strong>Office:</strong> {candidate.office.name}</li>
                        <li><strong>Filing Date:</strong> {candidate.filing_date}</li>
                        <li><strong>Status:</strong> {candidate.contact_status}</li>
                    </ul>
                </div>
                
                <p>Please let us know if you have any questions or would like to discuss this further.</p>
                
                <p style="margin-top: 30px;">
                    Best regards,<br>
                    <strong>Arizona Sunshine Team</strong>
                </p>
            </div>
            
            <div style="background-color: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #666;">
                Arizona Sunshine Campaign Finance Transparency Project
            </div>
        </body>
        </html>
        """
        
        email = EmailMessage(
            subject=f'Statement of Interest Request - {candidate.candidate_name}',
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],  # Send to yourself for testing
        )
        email.content_subtype = 'html'
        
        result = email.send()
        
        if result == 1:
            print("SUCCESS: SOI template email sent!")
            print(f"   Candidate: {candidate.candidate_name}")
            print(f"   Office: {candidate.office.name}")
            return True
        else:
            print("FAILED: SOI template email not sent")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all email tests"""
    print("\n" + "🔔"*30)
    print("ARIZONA SUNSHINE - EMAIL SYSTEM TEST SUITE")
    print("🔔"*30)
    
    print(f"\nConfiguration:")
    print(f"  Backend: {settings.EMAIL_BACKEND}")
    print(f"  Host: {settings.EMAIL_HOST}")
    print(f"  Port: {settings.EMAIL_PORT}")
    print(f"  TLS: {settings.EMAIL_USE_TLS}")
    print(f"  From: {settings.DEFAULT_FROM_EMAIL}")
    
    results = {
        'basic': test_basic_email(),
        'html': test_html_email(),
        'soi_template': test_soi_email_template(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nALL TESTS PASSED! Email system is fully functional.")
    else:
        print("\n SOME TESTS FAILED. Check configuration above.")
        print("\nTroubleshooting:")
        print("  1. Verify .env file has correct EMAIL_HOST_PASSWORD (Gmail App Password)")
        print("  2. Check that port 587 is not blocked by firewall")
        print("  3. Ensure 2-Factor Authentication is enabled on Gmail")
        print("  4. Generate new App Password at: https://myaccount.google.com/apppasswords")
    
    print("\n" + "="*60 + "\n")

# Auto-run all tests when script is executed
if __name__ == '__main__':
    run_all_tests()
else:
    # If imported in shell, provide helper message
    print("\nEmail test script loaded!")
    print("Run: run_all_tests()")