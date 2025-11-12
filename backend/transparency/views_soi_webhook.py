"""
Django Webhook Receiver for Real-Time SOI Scraping Updates
File: transparency/views_soi_webhook.py

This receives updates from the scraper (running on home machine or cron)
and stores them in cache for the React frontend to display in real-time.
"""

import os
from datetime import datetime
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import hmac
import hashlib

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
@csrf_exempt
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
        # Optional: Verify signature for security
        # signature = request.headers.get('X-Webhook-Signature', '')
        # if not verify_webhook_signature(request.body, signature):
        #     return Response(
        #         {'error': 'Invalid signature'},
        #         status=status.HTTP_401_UNAUTHORIZED
        #     )
        
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
        import logging
        logging.error(f"Webhook error: {e}")
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
@csrf_exempt
def trigger_local_scraping(request):
    """
    Trigger scraping on local/home machine via webhook callback
    
    This sends a webhook to your home machine to start scraping.
    Home machine must have a Flask/FastAPI endpoint listening.
    
    POST /api/v1/soi/trigger-local/
    """
    try:
        # Get home machine webhook URL from environment
        home_webhook_url = os.getenv('HOME_SCRAPER_WEBHOOK_URL')
        
        if not home_webhook_url:
            return Response(
                {'error': 'Home scraper webhook not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Send trigger to home machine
        import requests
        response = requests.post(
            home_webhook_url,
            json={
                'action': 'start_scraping',
                'triggered_by': 'web_ui',
                'timestamp': datetime.now().isoformat()
            },
            timeout=10
        )
        
        if response.status_code == 200:
            # Set initial status
            initial_status = {
                'scrape_id': f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'status': 'triggered',
                'progress': 0,
                'current_step': 'Triggering home scraper...',
                'logs': ['[Starting] Scrape triggered from web UI'],
                'started_at': datetime.now().isoformat(),
                'stats': {}
            }
            cache.set(WEBHOOK_STATUS_KEY, initial_status, timeout=3600)
            
            return Response({
                'success': True,
                'message': 'Scraping triggered on home machine',
                'status': initial_status
            })
        else:
            return Response(
                {'error': f'Failed to trigger scraping: {response.status_code}'},
                status=status.HTTP_502_BAD_GATEWAY
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
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