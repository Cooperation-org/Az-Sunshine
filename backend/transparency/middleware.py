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
