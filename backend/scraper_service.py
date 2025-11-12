"""
Flask Service for Home Machine SOI Scraper - FIXED VERSION
File: scraper_service.py (Run on your home/office machine)

This version properly parses scraper output to extract stats.
"""

from flask import Flask, request, jsonify
import os
import subprocess
import threading
import logging
import re
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
DJANGO_PROJECT_PATH = os.getenv('DJANGO_PROJECT_PATH', '/path/to/your/django/project')
VPS_WEBHOOK_URL = os.getenv('VPS_WEBHOOK_URL', 'http://127.0.0.1:8000/api/v1/soi/webhook/')
SERVICE_SECRET = os.getenv('SERVICE_SECRET', 'change-this-secret-key')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 5000))

# Track running scrapes
active_scrapes = {}


def send_webhook_update(session_id, status, progress, message, data=None):
    """Send progress update to VPS webhook"""
    try:
        payload = {
            'session_id': session_id,
            'status': status,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        logger.info(f"📤 Sending webhook: {message} ({progress}%)")
        
        response = requests.post(
            VPS_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"✅ Webhook sent successfully")
        
    except Exception as e:
        logger.error(f"❌ Webhook failed: {e}")


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


def verify_request_signature(request):
    """Verify request signature for security"""
    signature = request.headers.get('X-Service-Secret', '')
    return signature == SERVICE_SECRET


def run_scraper_command(session_id):
    """Run Django management command to scrape SOI data"""
    try:
        logger.info("🚀 Starting SOI scraper...")
        send_webhook_update(session_id, 'running', 10, 'Starting scraper...', {})
        
        # Build command
        manage_py = os.path.join(DJANGO_PROJECT_PATH, 'manage.py')
        
        cmd = [
            'python',
            manage_py,
            'soi_scraper_webhook',
            f'--webhook-url={VPS_WEBHOOK_URL}'
        ]
        
        # Run command
        send_webhook_update(session_id, 'running', 20, 'Running scraper command...', {})
        
        result = subprocess.run(
            cmd,
            cwd=DJANGO_PROJECT_PATH,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        logger.info(f"📥 Scraper return code: {result.returncode}")
        
        if result.returncode == 0:
            logger.info("✅ Scraper completed successfully")
            
            # Parse output to extract stats
            output = result.stdout + result.stderr
            stats = parse_scraper_stats(output)
            
            # Log the full output for debugging
            logger.info("📝 Scraper output preview:")
            for line in output.split('\n')[-20:]:  # Last 20 lines
                if line.strip():
                    logger.info(f"  {line}")
            
            # Send final success webhook with parsed stats
            send_webhook_update(
                session_id, 
                'completed', 
                100, 
                'Scraping completed successfully',
                stats
            )
            
            return {'success': True, 'output': output, 'stats': stats}
        else:
            logger.error(f"❌ Scraper failed: {result.stderr}")
            send_webhook_update(
                session_id,
                'error',
                0,
                f'Scraper failed: {result.stderr[:200]}',
                {}
            )
            return {'success': False, 'error': result.stderr}
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Scraper timed out")
        send_webhook_update(
            session_id,
            'error',
            0,
            'Scraper timed out after 10 minutes',
            {}
        )
        return {'success': False, 'error': 'Timeout after 10 minutes'}
    except Exception as e:
        logger.error(f"💥 Scraper error: {e}")
        send_webhook_update(
            session_id,
            'error',
            0,
            f'Error: {str(e)}',
            {}
        )
        return {'success': False, 'error': str(e)}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SOI Scraper Service',
        'timestamp': datetime.now().isoformat(),
        'active_scrapes': len(active_scrapes),
        'vps_webhook': VPS_WEBHOOK_URL,
        'django_project': DJANGO_PROJECT_PATH
    })


@app.route('/trigger', methods=['POST'])
def trigger_scrape():
    """
    Trigger SOI scraping
    
    POST /trigger
    Headers: X-Service-Secret: your-secret-key
    Body: {
        "action": "start_scraping",
        "triggered_by": "web_ui|cron|manual"
    }
    """
    # Verify signature
    if not verify_request_signature(request):
        logger.warning("⚠️  Unauthorized trigger attempt")
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if already running
    if active_scrapes:
        logger.warning("⚠️  Scraper already running")
        return jsonify({
            'error': 'Scraper already running',
            'active_scrapes': list(active_scrapes.keys())
        }), 409
    
    # Get request data
    data = request.get_json() or {}
    triggered_by = data.get('triggered_by', 'unknown')
    
    logger.info(f"📥 Scrape triggered by: {triggered_by}")
    
    # Run scraper in background thread
    scrape_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    active_scrapes[scrape_id] = {
        'started_at': datetime.now().isoformat(),
        'triggered_by': triggered_by,
        'status': 'running'
    }
    
    # Send initial webhook
    send_webhook_update(
        scrape_id,
        'triggered',
        5,
        'Scraping triggered, starting up...',
        {}
    )
    
    def run_in_background():
        try:
            result = run_scraper_command(scrape_id)
            active_scrapes[scrape_id]['status'] = 'completed' if result['success'] else 'error'
            active_scrapes[scrape_id]['completed_at'] = datetime.now().isoformat()
            active_scrapes[scrape_id]['result'] = result
        except Exception as e:
            logger.error(f"Background task error: {e}")
            active_scrapes[scrape_id]['status'] = 'error'
            active_scrapes[scrape_id]['error'] = str(e)
            send_webhook_update(
                scrape_id,
                'error',
                0,
                f'Background error: {str(e)}',
                {}
            )
        finally:
            # Clean up after 1 hour
            import time
            time.sleep(3600)
            active_scrapes.pop(scrape_id, None)
    
    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Scraping started',
        'scrape_id': scrape_id,
        'webhook_url': VPS_WEBHOOK_URL
    })


@app.route('/status', methods=['GET'])
def get_status():
    """Get current scraper status"""
    return jsonify({
        'active_scrapes': active_scrapes,
        'count': len(active_scrapes)
    })


@app.route('/stop/<scrape_id>', methods=['POST'])
def stop_scrape(scrape_id):
    """Stop a running scrape (not implemented - would need process management)"""
    if not verify_request_signature(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if scrape_id in active_scrapes:
        # In a production system, you'd kill the subprocess here
        return jsonify({
            'message': 'Stop functionality not implemented',
            'scrape_id': scrape_id
        }), 501
    
    return jsonify({'error': 'Scrape not found'}), 404


if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🏠 SOI Scraper Service Starting")
    logger.info("=" * 70)
    logger.info(f"Django Project: {DJANGO_PROJECT_PATH}")
    logger.info(f"VPS Webhook: {VPS_WEBHOOK_URL}")
    logger.info(f"Service Port: {SERVICE_PORT}")
    logger.info("=" * 70)
    
    # Run Flask app
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=SERVICE_PORT,
        debug=False,
        threaded=True
    )