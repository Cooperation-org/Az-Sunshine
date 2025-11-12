"""
Updated SOI Views for Hybrid Scraping Approach
Replace your existing views_soi.py with this

This adapts the UI to show:
1. Instructions for local scraping (can't run on server)
2. CSV upload option
3. Manual data loading
4. Status tracking for manual workflow
"""

import os
from datetime import datetime
from django.core.cache import cache
from django.db.models import Count
from django.core.management import call_command
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from transparency.models import CandidateStatementOfInterest
from django.views.decorators.csrf import csrf_exempt

# Cache keys
SCRAPE_STATUS_KEY = "soi_scrape_status"
SCRAPE_HISTORY_KEY = "soi_scrape_history"


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def trigger_scraping(request):
    """
    UPDATED: Returns instructions for local scraping
    Since automated scraping doesn't work due to bot detection,
    this provides guidance for the hybrid approach
    """
    
    # Check if there's already a scraping process
    current_status = cache.get(SCRAPE_STATUS_KEY)
    if current_status and current_status.get("status") == "running":
        return Response(
            {"error": "A scraping/upload process is already in progress.", "current_status": current_status},
            status=status.HTTP_409_CONFLICT,
        )
    
    # Set initial status to show instructions
    scrape_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    status_data = {
        "scrape_id": scrape_id,
        "status": "awaiting_manual",
        "progress": 0,
        "current_step": "Ready for Manual Scraping",
        "steps_completed": [],
        "logs": [
            "[INFO] Automated scraping not available due to bot detection",
            "[INFO] Please use local scraping method:",
            "[STEP 1] Download and run local_scraper.py on your laptop",
            "[STEP 2] Upload the generated CSV file using the upload button",
            "[STEP 3] System will automatically load the data into database",
            "",
            "For details, see: Implementation Guide"
        ],
        "started_at": datetime.now().isoformat(),
        "stats": {
            "current_candidates": CandidateStatementOfInterest.objects.count(),
            "uncontacted": CandidateStatementOfInterest.objects.filter(contact_status='uncontacted').count(),
        },
        "instructions": {
            "method": "local_scraping",
            "steps": [
                "Run local_scraper.py on a machine with visible browser",
                "Wait for browser to open and solve any Cloudflare challenges",
                "Generated CSV will be saved as soi_candidates.csv",
                "Upload the CSV using the upload button in the UI"
            ]
        }
    }
    
    cache.set(SCRAPE_STATUS_KEY, status_data, timeout=3600)
    
    return Response(status_data)


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@csrf_exempt
def upload_soi_csv(request):
    """
    NEW: Upload CSV from local scraping
    POST /api/v1/soi/upload-csv/
    """
    
    if 'file' not in request.FILES:
        return Response(
            {"error": "No file provided. Please upload a CSV file."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    csv_file = request.FILES['file']
    
    # Validate file extension
    if not csv_file.name.endswith('.csv'):
        return Response(
            {"error": "Invalid file type. Please upload a CSV file."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save file temporarily
    upload_dir = os.path.join(os.getcwd(), 'data', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(upload_dir, f'soi_{timestamp}.csv')
    
    try:
        # Save uploaded file
        with open(file_path, 'wb+') as destination:
            for chunk in csv_file.chunks():
                destination.write(chunk)
        
        # Update status to show processing
        scrape_id = f"upload_{timestamp}"
        status_data = {
            "scrape_id": scrape_id,
            "status": "running",
            "progress": 50,
            "current_step": "Processing CSV",
            "logs": [
                f"[{datetime.now().strftime('%H:%M:%S')}] CSV file uploaded successfully",
                f"[{datetime.now().strftime('%H:%M:%S')}] File: {csv_file.name}",
                f"[{datetime.now().strftime('%H:%M:%S')}] Size: {csv_file.size} bytes",
                f"[{datetime.now().strftime('%H:%M:%S')}] Loading into database..."
            ],
            "started_at": datetime.now().isoformat(),
        }
        cache.set(SCRAPE_STATUS_KEY, status_data, timeout=3600)
        
        # Call the management command to load CSV
        from io import StringIO
        import sys
        
        # Capture command output
        old_stdout = sys.stdout
        sys.stdout = output_buffer = StringIO()
        
        try:
            call_command('load_soi_csv', file_path)
            command_output = output_buffer.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Get final stats
        total_candidates = CandidateStatementOfInterest.objects.count()
        uncontacted = CandidateStatementOfInterest.objects.filter(contact_status='uncontacted').count()
        contacted = CandidateStatementOfInterest.objects.filter(contact_status='contacted').count()
        pledged = CandidateStatementOfInterest.objects.filter(pledge_received=True).count()
        
        # Parse stats from command output
        import re
        created_match = re.search(r'Created:\s*(\d+)', command_output)
        updated_match = re.search(r'Updated:\s*(\d+)', command_output)
        
        created = int(created_match.group(1)) if created_match else 0
        updated = int(updated_match.group(1)) if updated_match else 0
        
        # Update final status
        final_status = {
            "scrape_id": scrape_id,
            "status": "completed",
            "progress": 100,
            "current_step": "Complete",
            "completed_at": datetime.now().isoformat(),
            "stats": {
                "total_candidates": total_candidates,
                "uncontacted": uncontacted,
                "contacted": contacted,
                "pledged": pledged,
                "processed": created + updated,
                "new_candidates": created,
                "updated_candidates": updated,
            },
            "logs": status_data["logs"] + [
                f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Processing complete",
                f"[{datetime.now().strftime('%H:%M:%S')}] Created: {created}",
                f"[{datetime.now().strftime('%H:%M:%S')}] Updated: {updated}",
                f"[{datetime.now().strftime('%H:%M:%S')}] Total in database: {total_candidates}"
            ]
        }
        
        cache.set(SCRAPE_STATUS_KEY, final_status, timeout=3600)
        save_to_history(final_status)
        
        return Response(final_status)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        error_status = {
            "scrape_id": scrape_id,
            "status": "error",
            "error": error_msg,
            "logs": status_data.get("logs", []) + [
                f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {error_msg}",
                f"[{datetime.now().strftime('%H:%M:%S')}] {error_trace}"
            ]
        }
        
        cache.set(SCRAPE_STATUS_KEY, error_status, timeout=3600)
        
        return Response(
            error_status,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def scraping_status(request):
    """Return current scraping/upload status"""
    current_status = cache.get(SCRAPE_STATUS_KEY)
    if not current_status:
        # Return idle status with current stats
        total = CandidateStatementOfInterest.objects.count()
        return Response({
            "status": "idle",
            "message": "No scraping in progress.",
            "current_stats": {
                "total_candidates": total,
                "uncontacted": CandidateStatementOfInterest.objects.filter(contact_status='uncontacted').count(),
            }
        })
    return Response(current_status)


@api_view(["GET"])
@permission_classes([AllowAny])
def scraping_history(request):
    """Return the 10 most recent scraping/upload runs"""
    history = cache.get(SCRAPE_HISTORY_KEY, [])
    return Response({"history": history[-10:]})


@api_view(["GET"])
@permission_classes([AllowAny])
def soi_dashboard_stats(request):
    """
    Return summarized dashboard statistics for SOI filings
    """
    try:
        total = CandidateStatementOfInterest.objects.count()
        uncontacted = CandidateStatementOfInterest.objects.filter(
            contact_status='uncontacted'
        ).count()
        contacted = CandidateStatementOfInterest.objects.filter(
            contact_status='contacted'
        ).count()
        pending_pledge = CandidateStatementOfInterest.objects.filter(
            contact_status='contacted',
            pledge_received=False
        ).count()
        pledged = CandidateStatementOfInterest.objects.filter(
            pledge_received=True
        ).count()

        by_office = (
            CandidateStatementOfInterest.objects
            .values("office__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return Response({
            "total_candidates": total,
            "uncontacted": uncontacted,
            "contacted": contacted,
            "pending_pledge": pending_pledge,
            "pledged": pledged,
            "by_office": list(by_office),
        })
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def soi_candidates_list(request):
    """
    Return list of SOI candidates
    """
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', None)
        office_id = request.GET.get('office', None)
        search = request.GET.get('search', None)
        
        # Build query
        queryset = CandidateStatementOfInterest.objects.select_related('office').all()
        
        if status_filter:
            queryset = queryset.filter(contact_status=status_filter)
        
        if office_id:
            queryset = queryset.filter(office_id=office_id)
        
        if search:
            queryset = queryset.filter(candidate_name__icontains=search)
        
        # Serialize data
        candidates = []
        for soi in queryset.order_by('-filing_date'):
            candidate_data = {
                'id': soi.id,
                'name': soi.candidate_name or '',
                'office': soi.office.name if soi.office else 'Unknown',
                'party': soi.party or '',
                'email': soi.email or '',
                'phone': soi.phone or '',
                'contacted': soi.contact_status != 'uncontacted',
                'contacted_at': soi.contacted_date.isoformat() if soi.contacted_date else None,
                'pledge_received': bool(soi.pledge_received),
                'filing_date': soi.filing_date.isoformat() if soi.filing_date else None,
                'notes': soi.notes or '',
                'contact_status': soi.contact_status or 'uncontacted',
            }
            candidates.append(candidate_data)
        
        return Response(candidates)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e), 'detail': 'Error fetching SOI candidates'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Helper functions
def save_to_history(status_data):
    """Save completed scraping run to cache."""
    history = cache.get(SCRAPE_HISTORY_KEY, [])
    history.append({
        "scrape_id": status_data["scrape_id"],
        "status": status_data["status"],
        "started_at": status_data.get("started_at"),
        "completed_at": status_data.get("completed_at"),
        "stats": status_data.get("stats", {}),
    })
    cache.set(SCRAPE_HISTORY_KEY, history[-20:], timeout=86400 * 7)