"""
Django Webhook Receiver for Real-Time SOI Scraping Updates
File: transparency/views_soi_webhook.py

FIXED: Added @csrf_exempt to all POST endpoints
"""

import os
from datetime import datetime
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt  # Import this
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

# Cache keys
WEBHOOK_STATUS_KEY = "soi_webhook_status"
WEBHOOK_HISTORY_KEY = "soi_webhook_history"

# Security: Webhook secret (set in environment)
WEBHOOK_SECRET = os.getenv('SOI_WEBHOOK_SECRET', 'your-secret-key-change-this')


def verify_webhook_signature(request_body, signature):
    """Verify webhook signature for security"""
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt  # ✅ CRITICAL: Disable CSRF for webhook endpoint
@require_http_methods(['POST'])
def webhook_receiver(request):
    """
    Receive real-time updates from SOI scraper
    
    Expected payload:
    {
        "session_id": "scrape_20250112_143000",
        "status": "running|completed|error",
        "progress": 0-100,
        "message": "Descriptive message",
        "timestamp": "2025-01-12T14:30:00",
        "data": {
            "total_candidates": 50,
            "created": 10,
            "updated": 5,
            ...
        }
    }
    """
    try:
        payload = request.data
        
        # Validate required fields
        required_fields = ['session_id', 'status', 'progress', 'message']
        if not all(field in payload for field in required_fields):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store in cache for frontend to fetch
        session_id = payload['session_id']
        
        # Get or create status object
        current_status = cache.get(WEBHOOK_STATUS_KEY) or {
            'scrape_id': session_id,
            'status': 'idle',
            'progress': 0,
            'current_step': 'Initializing',
            'logs': [],
            'started_at': datetime.now().isoformat(),
            'stats': {}
        }
        
        # Update with new data
        current_status.update({
            'scrape_id': session_id,
            'status': payload['status'],
            'progress': payload['progress'],
            'current_step': payload.get('message', 'Processing...'),
            'stats': payload.get('data', {}),
        })
        
        # Add log entry
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {payload['message']}"
        current_status['logs'].append(log_entry)
        
        # Keep only last 50 logs
        if len(current_status['logs']) > 50:
            current_status['logs'] = current_status['logs'][-50:]
        
        # Mark completion time
        if payload['status'] in ['completed', 'error']:
            current_status['completed_at'] = datetime.now().isoformat()
        
        # Save to cache (1 hour expiry)
        cache.set(WEBHOOK_STATUS_KEY, current_status, timeout=3600)
        
        # Save to history if completed
        if payload['status'] == 'completed':
            save_to_webhook_history(current_status)
        
        return Response({
            'success': True,
            'message': 'Webhook received',
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_status(request):
    """
    Get current webhook status (for frontend polling)
    GET /api/v1/soi/webhook/status/
    """
    current_status = cache.get(WEBHOOK_STATUS_KEY)
    
    if not current_status:
        return Response({
            'status': 'idle',
            'message': 'No scraping in progress'
        })
    
    return Response(current_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_history(request):
    """
    Get webhook history
    GET /api/v1/soi/webhook/history/
    """
    history = cache.get(WEBHOOK_HISTORY_KEY, [])
    return Response({'history': history[-20:]})


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt  # ✅ CRITICAL: Disable CSRF for trigger endpoint
def trigger_local_scraping(request):
    """
    Trigger scraping on local/home machine via webhook callback
    
    This sends a webhook to your home machine to start scraping.
    Home machine must have a Flask/FastAPI endpoint listening.
    
    POST /api/v1/soi/trigger-local/
    """
    try:
        logger.info("🚀 Trigger local scraping called")
        
        # Get home machine webhook URL from settings
        from django.conf import settings
        home_webhook_url = getattr(settings, 'HOME_SCRAPER_WEBHOOK_URL', None)
        
        if not home_webhook_url:
            logger.error("❌ HOME_SCRAPER_WEBHOOK_URL not configured in settings")
            return Response(
                {
                    'error': 'Home scraper webhook not configured',
                    'detail': 'HOME_SCRAPER_WEBHOOK_URL is not set in Django settings'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        logger.info(f"📡 Sending trigger to: {home_webhook_url}")
        
        # Get webhook secret from settings
        webhook_secret = getattr(settings, 'SOI_WEBHOOK_SECRET', 'change-this-secret-key')
        
        # Send trigger to home machine
        import requests
        response = requests.post(
            home_webhook_url,
            json={
                'action': 'start_scraping',
                'triggered_by': 'web_ui',
                'timestamp': datetime.now().isoformat()
            },
            headers={
                'X-Service-Secret': webhook_secret,
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        logger.info(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Set initial status
            scrape_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            initial_status = {
                'scrape_id': scrape_id,
                'status': 'triggered',
                'progress': 5,
                'current_step': 'Triggering home scraper...',
                'logs': [
                    f"[{datetime.now().strftime('%H:%M:%S')}] Scrape triggered from web UI",
                    f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for home machine response..."
                ],
                'started_at': datetime.now().isoformat(),
                'stats': {}
            }
            cache.set(WEBHOOK_STATUS_KEY, initial_status, timeout=3600)
            
            logger.info(f"✅ Scraping triggered successfully - {scrape_id}")
            
            return Response({
                'success': True,
                'message': 'Scraping triggered on home machine',
                'scrape_id': scrape_id,
                'webhook_url': home_webhook_url
            })
        else:
            error_msg = f'Failed to trigger scraping: {response.status_code} - {response.text}'
            logger.error(f"❌ {error_msg}")
            return Response(
                {'error': error_msg},
                status=status.HTTP_502_BAD_GATEWAY
            )
            
    except requests.exceptions.Timeout:
        error_msg = 'Timeout connecting to home scraper - check if service is running'
        logger.error(f"❌ {error_msg}")
        return Response(
            {'error': error_msg},
            status=status.HTTP_504_GATEWAY_TIMEOUT
        )
    except requests.exceptions.ConnectionError as e:
        error_msg = f'Cannot connect to home scraper: {str(e)}'
        logger.error(f"❌ {error_msg}")
        return Response(
            {'error': error_msg, 'detail': 'Check if home machine is online and ngrok/webhook URL is correct'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        logger.error(f"❌ {error_msg}", exc_info=True)
        return Response(
            {'error': error_msg},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def save_to_webhook_history(status_data):
    """Save completed scrape to history"""
    history = cache.get(WEBHOOK_HISTORY_KEY, [])
    history.append({
        'scrape_id': status_data['scrape_id'],
        'status': status_data['status'],
        'started_at': status_data['started_at'],
        'completed_at': status_data.get('completed_at'),
        'stats': status_data.get('stats', {}),
    })
    # Keep last 20 runs
    cache.set(WEBHOOK_HISTORY_KEY, history[-20:], timeout=86400 * 7)