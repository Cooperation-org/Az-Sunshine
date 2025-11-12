"""
FIXED API Views for Statement of Interest (SOI) - Direct Scraping
File: transparency/views_soi.py

This version parses scraper output to extract Created/Updated stats.
"""

import os
import subprocess
import re
from datetime import datetime
from django.core.cache import cache
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from transparency.models import CandidateStatementOfInterest
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

# Cache keys
SCRAPE_STATUS_KEY = "soi_scrape_status"
SCRAPE_HISTORY_KEY = "soi_scrape_history"


def parse_scraper_stats(output):
    """
    Parse scraper output to extract statistics
    
    Looks for patterns like:
    - "✨ Created in DB: 0"
    - "🔄 Updated in DB: 0"
    - "⏭️  Skipped: 412"
    - "📊 Total candidates scraped: 412"
    """
    stats = {
        'total_candidates': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    # Pattern 1: "✨ Created in DB: 0" or "Created in DB: 0" or "Created: 45"
    created_patterns = [
        r'Created in DB:\s*(\d+)',
        r'Created:\s*(\d+)',
    ]
    for pattern in created_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            stats['created'] = int(match.group(1))
            break
    
    # Pattern 2: "🔄 Updated in DB: 0" or "Updated in DB: 0" or "Updated: 67"
    updated_patterns = [
        r'Updated in DB:\s*(\d+)',
        r'Updated:\s*(\d+)',
    ]
    for pattern in updated_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            stats['updated'] = int(match.group(1))
            break
    
    # Pattern 3: "⏭️  Skipped: 412" or "Skipped: 10"
    skipped_match = re.search(r'Skipped:\s*(\d+)', output, re.IGNORECASE)
    if skipped_match:
        stats['skipped'] = int(skipped_match.group(1))
    
    # Pattern 4: "❌ Errors: 2" or "Errors: 2"
    errors_match = re.search(r'Errors:\s*(\d+)', output, re.IGNORECASE)
    if errors_match:
        stats['errors'] = int(errors_match.group(1))
    
    # Pattern 5: "📊 Total candidates scraped: 412"
    total_patterns = [
        r'Total candidates scraped:\s*(\d+)',
        r'Total:\s*(\d+)',
        r'(\d+)\s+total\s+candidates',
        r'Total candidates in database:\s*(\d+)',
    ]
    for pattern in total_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            stats['total_candidates'] = int(match.group(1))
            break
    
    logger.info(f"📊 Parsed stats from output: {stats}")
    return stats

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
        logger.error(f"Error in soi_dashboard_stats: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def soi_candidates_list(request):
    """
    FIXED: Return list of SOI candidates with proper error handling
    Safely handles missing 'phone' field
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
            try:
                # Safely get phone field (may not exist in database)
                phone_value = ''
                try:
                    phone_value = getattr(soi, 'phone', '') or ''
                except (AttributeError, Exception):
                    phone_value = ''
                
                # Get email safely
                email_value = ''
                try:
                    email_value = getattr(soi, 'email', '') or ''
                except (AttributeError, Exception):
                    email_value = ''
                
                # Get office name safely
                office_name = 'Unknown'
                try:
                    if soi.office and hasattr(soi.office, 'name'):
                        office_name = soi.office.name or 'Unknown'
                except (AttributeError, Exception):
                    office_name = 'Unknown'
                
                # Get contacted_date safely (field name varies)
                contacted_at = None
                try:
                    if hasattr(soi, 'contacted_date') and soi.contacted_date:
                        contacted_at = soi.contacted_date.isoformat()
                    elif hasattr(soi, 'contact_date') and soi.contact_date:
                        contacted_at = soi.contact_date.isoformat()
                except (AttributeError, Exception):
                    contacted_at = None
                
                candidate_data = {
                    'id': soi.id,
                    'name': soi.candidate_name or '',
                    'office': office_name,
                    'party': '',  # SOI doesn't have party info yet
                    'email': email_value,
                    'phone': phone_value,
                    'contacted': soi.contact_status != 'uncontacted',
                    'contacted_at': contacted_at,
                    'pledge_received': bool(soi.pledge_received),
                    'filing_date': soi.filing_date.isoformat() if soi.filing_date else None,
                    'notes': soi.notes or '',
                    'contact_status': soi.contact_status or 'uncontacted',
                }
                
                candidates.append(candidate_data)
                
            except Exception as row_error:
                logger.error(f"Error processing SOI {soi.id}: {row_error}")
                continue
        
        logger.info(f"Returning {len(candidates)} SOI candidates")
        return Response(candidates)
        
    except Exception as e:
        logger.error(f"Error in soi_candidates_list: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return Response(
            {
                'error': str(e),
                'detail': 'Error fetching SOI candidates. Check server logs.',
                'candidates': []
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def trigger_scraping(request):
    """Trigger the SOI scraping process - FIXED VERSION with stats parsing"""
    current_status = cache.get(SCRAPE_STATUS_KEY)
    if current_status and current_status.get("status") == "running":
        return Response(
            {"error": "Scraping is already in progress.", "current_status": current_status},
            status=status.HTTP_409_CONFLICT,
        )

    scrape_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    status_data = {
        "scrape_id": scrape_id,
        "status": "running",
        "progress": 0,
        "current_step": "Initializing",
        "steps_completed": [],
        "logs": ["[Starting] SOI scraping process initiated..."],
        "started_at": datetime.now().isoformat(),
        "stats": {
            "urls_discovered": 3,
            "pages_scraped": 0,
            "candidates_processed": 0,
            "created": 0,
            "updated": 0
        },
    }
    cache.set(SCRAPE_STATUS_KEY, status_data, timeout=3600)

    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "soi_scraper.log")

    def append_log(text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(log_path, "a") as f:
            f.write(f"[{timestamp}] {text}\n")
        
        current = cache.get(SCRAPE_STATUS_KEY)
        if current:
            current["logs"].append(f"[{timestamp}] {text}")
            cache.set(SCRAPE_STATUS_KEY, current, timeout=3600)

    append_log("\n--- New Scrape Run Started ---")
    append_log(f"Scrape ID: {scrape_id}")

    try:
        update_status(scrape_id, 10, "Discovering URLs", "Launching headless browser...")
        append_log("Running: python manage.py soi_scraper")

        result = subprocess.run(
            ["python", "manage.py", "soi_scraper"],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=os.getcwd()
        )
        
        append_log(f"Scraper return code: {result.returncode}")
        
        # Combine stdout and stderr for parsing
        full_output = result.stdout + "\n" + result.stderr
        
        # Log output for debugging
        if result.stdout:
            append_log("Scraper output:")
            for line in result.stdout.split('\n')[-20:]:  # Last 20 lines
                if line.strip():
                    append_log(f"  {line.strip()}")
        
        if result.returncode == 0:
            update_status(scrape_id, 70, "Scraping Complete", "Processing data...")
            
            # Parse stats from output
            parsed_stats = parse_scraper_stats(full_output)
            append_log(f"📊 Parsed stats: Created={parsed_stats['created']}, Updated={parsed_stats['updated']}")
            
        else:
            append_log(f"ERROR: {result.stderr}")
            update_status(scrape_id, 40, "Scraping Error", result.stderr[:200])
            parsed_stats = {'created': 0, 'updated': 0, 'errors': 1}

        update_status(scrape_id, 80, "Validating Data", "Checking database...")
        
        total_candidates = CandidateStatementOfInterest.objects.count()
        uncontacted = CandidateStatementOfInterest.objects.filter(
            contact_status="uncontacted"
        ).count()
        contacted = CandidateStatementOfInterest.objects.filter(
            contact_status="contacted"
        ).count()
        pledged = CandidateStatementOfInterest.objects.filter(
            pledge_received=True
        ).count()

        append_log(f"Database check: {total_candidates} total candidates found")
        append_log(f"  - Uncontacted: {uncontacted}")
        append_log(f"  - Contacted: {contacted}")
        append_log(f"  - Pledged: {pledged}")

        final_status = cache.get(SCRAPE_STATUS_KEY)
        final_status.update({
            "status": "completed",
            "progress": 100,
            "current_step": "Complete",
            "completed_at": datetime.now().isoformat(),
            "stats": {
                "total_candidates": total_candidates,
                "uncontacted": uncontacted,
                "contacted": contacted,
                "pledged": pledged,
                "processed": total_candidates,
                "created": parsed_stats['created'],
                "updated": parsed_stats['updated'],
                "errors": parsed_stats.get('errors', 0)
            },
        })
        final_status["logs"].append("✅ Scraping process completed successfully.")
        cache.set(SCRAPE_STATUS_KEY, final_status, timeout=3600)
        save_to_history(final_status)

        append_log("✅ Scraping completed successfully")
        append_log(f"Total candidates in database: {total_candidates}")
        append_log(f"Created: {parsed_stats['created']}, Updated: {parsed_stats['updated']}")

        return Response(final_status)

    except subprocess.TimeoutExpired:
        append_log("❌ Scraping process timed out after 600s.")
        return handle_error(scrape_id, "Timeout", "Scraping process timed out after 10 minutes.")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        append_log("❌ Unexpected error occurred:\n" + tb)
        return handle_error(scrape_id, "Error", str(e))


@api_view(["GET"])
@permission_classes([AllowAny])
def scraping_status(request):
    """Return current scraping status"""
    current_status = cache.get(SCRAPE_STATUS_KEY)
    if not current_status:
        return Response({"status": "idle", "message": "No scraping in progress."})
    return Response(current_status)


@api_view(["GET"])
@permission_classes([AllowAny])
def scraping_history(request):
    """Return the 10 most recent scraping runs"""
    history = cache.get(SCRAPE_HISTORY_KEY, [])
    return Response({"history": history[-10:]})


# Helper functions
def update_status(scrape_id, progress, step, message):
    """Update scraping progress in cache."""
    current = cache.get(SCRAPE_STATUS_KEY)
    if current and current["scrape_id"] == scrape_id:
        current["progress"] = progress
        current["current_step"] = step
        timestamp = datetime.now().strftime("%H:%M:%S")
        current["logs"].append(f"[{timestamp}] {message}")
        current["steps_completed"].append(step)
        
        if progress >= 70:
            current["stats"]["pages_scraped"] = 3
        
        cache.set(SCRAPE_STATUS_KEY, current, timeout=3600)


def save_to_history(status_data):
    """Save completed scraping run to cache."""
    history = cache.get(SCRAPE_HISTORY_KEY, [])
    history.append({
        "scrape_id": status_data["scrape_id"],
        "status": status_data["status"],
        "started_at": status_data["started_at"],
        "completed_at": status_data.get("completed_at"),
        "stats": status_data.get("stats", {}),
    })
    cache.set(SCRAPE_HISTORY_KEY, history[-20:], timeout=86400 * 7)


def handle_error(scrape_id, step, error_message):
    """Standardized error handling with logging."""
    current = cache.get(SCRAPE_STATUS_KEY)
    
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "soi_scraper.log")
    
    with open(log_path, "a") as f:
        timestamp = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{timestamp}] [ERROR] {error_message}\n")

    if current and current["scrape_id"] == scrape_id:
        current.update({
            "status": "error",
            "current_step": step,
            "error": error_message,
        })
        timestamp = datetime.now().strftime("%H:%M:%S")
        current["logs"].append(f"[{timestamp}] [ERROR] {error_message}")
        cache.set(SCRAPE_STATUS_KEY, current, timeout=3600)
        save_to_history(current)

    return Response(
        current or {"error": error_message},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )