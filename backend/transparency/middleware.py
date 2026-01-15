"""
Middleware for Django:
- Zstandard Compression
- Rate Limiting / Anti-Scraping Protection
"""

import time
import hashlib
from collections import defaultdict
from django.core.cache import cache
from django.http import JsonResponse
import zstandard as zstd
from django.utils.deprecation import MiddlewareMixin


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to protect against scraping and abuse.

    Limits:
    - 100 requests per minute for normal users
    - 30 requests per minute for API endpoints
    - Blocks suspicious bot patterns
    """

    # Rate limits (requests per minute)
    GENERAL_LIMIT = 100
    API_LIMIT = 30

    # Suspicious patterns that indicate scraping
    BOT_USER_AGENTS = [
        'scrapy', 'crawler', 'spider', 'bot', 'curl', 'wget',
        'python-requests', 'httpx', 'aiohttp', 'selenium'
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get client identifier (IP + User Agent hash)
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()

        # Check for bot user agents
        if any(bot in user_agent for bot in self.BOT_USER_AGENTS):
            return JsonResponse({
                'error': 'Automated access is not permitted',
                'status': 'blocked'
            }, status=403)

        # Check for missing user agent (often bots)
        if not user_agent or len(user_agent) < 10:
            return JsonResponse({
                'error': 'Invalid request',
                'status': 'blocked'
            }, status=403)

        # Determine rate limit based on path
        is_api = '/transparency/' in request.path or '/api/' in request.path
        limit = self.API_LIMIT if is_api else self.GENERAL_LIMIT

        # Create cache key
        cache_key = f"ratelimit:{client_ip}:{int(time.time() // 60)}"

        # Get current request count
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            return JsonResponse({
                'error': 'Rate limit exceeded. Please slow down.',
                'retry_after': 60 - (int(time.time()) % 60)
            }, status=429)

        # Increment counter
        cache.set(cache_key, current_count + 1, timeout=60)

        response = self.get_response(request)

        # Add rate limit headers
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(max(0, limit - current_count - 1))

        return response

    def get_client_ip(self, request):
        """Get the real client IP, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to prevent scraping and protect data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Prevent embedding in iframes (clickjacking protection)
        response['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'

        # Prevent caching of sensitive data
        if '/transparency/' in request.path or '/api/' in request.path:
            response['Cache-Control'] = 'private, no-store, must-revalidate'

        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.opencorporates.com;"
        )

        return response


class ZstdMiddleware(MiddlewareMixin):
    """
    Middleware to compress responses using Zstandard when client supports it.
    Falls back to Django's GZipMiddleware for clients that don't support zstd.

    Zstd advantages over gzip:
    - 3-5x faster compression
    - 10-20% better compression ratio
    - Modern browsers (Chrome 123+, Firefox 126+, Edge 123+) support it
    """

    # Minimum size to compress (don't compress tiny responses)
    MIN_LENGTH = 200

    # Compression level (1-22, 3 is default, good balance of speed/ratio)
    COMPRESSION_LEVEL = 3

    # Content types to compress
    COMPRESSIBLE_TYPES = (
        'application/json',
        'application/javascript',
        'text/html',
        'text/plain',
        'text/css',
        'text/xml',
        'application/xml',
    )

    def __init__(self, get_response):
        self.get_response = get_response
        # Create a reusable compressor for better performance
        self.compressor = zstd.ZstdCompressor(level=self.COMPRESSION_LEVEL)

    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)

    def process_response(self, request, response):
        # Check if client accepts zstd encoding
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if 'zstd' not in accept_encoding:
            return response

        # Don't compress if already compressed
        if response.has_header('Content-Encoding'):
            return response

        # Check content type
        content_type = response.get('Content-Type', '').split(';')[0]
        if content_type not in self.COMPRESSIBLE_TYPES:
            return response

        # Don't compress streaming responses
        if response.streaming:
            return response

        # Get content
        content = response.content

        # Don't compress small responses
        if len(content) < self.MIN_LENGTH:
            return response

        # Compress with zstd
        try:
            compressed = self.compressor.compress(content)

            # Only use compressed version if it's actually smaller
            if len(compressed) < len(content):
                response.content = compressed
                response['Content-Encoding'] = 'zstd'
                response['Content-Length'] = len(compressed)
                # Add Vary header for caching
                if response.has_header('Vary'):
                    vary = response['Vary']
                    if 'Accept-Encoding' not in vary:
                        response['Vary'] = vary + ', Accept-Encoding'
                else:
                    response['Vary'] = 'Accept-Encoding'
        except Exception:
            # If compression fails, return original response
            pass

        return response


class AnalyticsMiddleware(MiddlewareMixin):
    """
    Analytics tracking middleware - captures site visits for the analytics dashboard.
    Similar to Google Analytics but self-hosted.
    """

    # Paths to exclude from tracking (static files, API health checks, etc.)
    EXCLUDE_PATHS = [
        '/static/',
        '/media/',
        '/admin/',
        '/favicon.ico',
        '/robots.txt',
        '/api/v1/analytics/',  # Don't track analytics endpoints
        '/health/',
    ]

    # Paths to exclude from full tracking (only count, don't store details)
    API_PATHS = [
        '/transparency/',
        '/api/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the response first
        response = self.get_response(request)

        # Only track successful GET requests
        if request.method != 'GET' or response.status_code >= 400:
            return response

        # Skip excluded paths
        path = request.path
        if any(path.startswith(exc) for exc in self.EXCLUDE_PATHS):
            return response

        # Track the visit asynchronously to not slow down the response
        try:
            self.track_visit(request, path)
        except Exception:
            pass  # Don't let analytics tracking break the site

        return response

    def track_visit(self, request, path):
        """Record the visit in the database."""
        import uuid
        from threading import Thread

        # Get client info
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')

        # Generate session ID from IP + User Agent (stable for same visitor)
        session_data = f"{client_ip}:{user_agent}:{request.session.session_key or ''}"
        session_id = hashlib.md5(session_data.encode()).hexdigest()

        # Get or create visitor ID from cookie
        visitor_id = request.COOKIES.get('_az_vid', '')
        if not visitor_id:
            visitor_id = str(uuid.uuid4())[:32]

        # Parse user agent for device/browser info
        device_type, browser, os = self.parse_user_agent(user_agent)

        # Run the database insert in a separate thread to not block response
        def save_visit():
            from transparency.models import SiteVisit

            # Get geolocation from IP (using free IP-API service)
            geo_data = self.get_geolocation(client_ip)

            SiteVisit.objects.create(
                session_id=session_id,
                visitor_id=visitor_id,
                path=path[:500],
                referrer=referrer[:1000] if referrer else '',
                ip_address=client_ip,
                user_agent=user_agent[:500] if user_agent else '',
                device_type=device_type,
                browser=browser,
                os=os,
                country=geo_data.get('country', ''),
                country_code=geo_data.get('country_code', ''),
                region=geo_data.get('region', ''),
                city=geo_data.get('city', ''),
                latitude=geo_data.get('lat'),
                longitude=geo_data.get('lon'),
                user=request.user if request.user.is_authenticated else None,
            )

        # Run in background thread
        Thread(target=save_visit, daemon=True).start()

    def get_client_ip(self, request):
        """Get the real client IP, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    def parse_user_agent(self, user_agent):
        """Parse user agent string to extract device, browser, and OS."""
        ua = user_agent.lower()

        # Device type
        if 'mobile' in ua or 'android' in ua and 'tablet' not in ua:
            device_type = 'mobile'
        elif 'tablet' in ua or 'ipad' in ua:
            device_type = 'tablet'
        else:
            device_type = 'desktop'

        # Browser detection
        if 'edg' in ua:
            browser = 'Edge'
        elif 'chrome' in ua and 'chromium' not in ua:
            browser = 'Chrome'
        elif 'firefox' in ua:
            browser = 'Firefox'
        elif 'safari' in ua and 'chrome' not in ua:
            browser = 'Safari'
        elif 'opera' in ua or 'opr' in ua:
            browser = 'Opera'
        else:
            browser = 'Other'

        # OS detection
        if 'windows' in ua:
            os = 'Windows'
        elif 'mac os' in ua or 'macintosh' in ua:
            os = 'macOS'
        elif 'linux' in ua and 'android' not in ua:
            os = 'Linux'
        elif 'android' in ua:
            os = 'Android'
        elif 'iphone' in ua or 'ipad' in ua:
            os = 'iOS'
        else:
            os = 'Other'

        return device_type, browser, os

    def get_geolocation(self, ip_address):
        """Get geolocation data from IP address using free IP-API service."""
        import requests

        # Skip for local/private IPs
        if ip_address in ['127.0.0.1', '0.0.0.0', 'localhost'] or ip_address.startswith('192.168.') or ip_address.startswith('10.'):
            return {}

        # Check cache first (avoid hitting API repeatedly for same IP)
        cache_key = f"geo:{ip_address}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Free IP geolocation API (no API key needed, 45 requests/minute)
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,region,city,lat,lon",
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    result = {
                        'country': data.get('country', ''),
                        'country_code': data.get('countryCode', ''),
                        'region': data.get('region', ''),
                        'city': data.get('city', ''),
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                    }
                    # Cache for 24 hours
                    cache.set(cache_key, result, timeout=86400)
                    return result
        except Exception:
            pass

        return {}
