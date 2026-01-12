"""
Zstandard Compression Middleware for Django
Provides faster compression than gzip with better compression ratios
"""

import zstandard as zstd
from django.utils.deprecation import MiddlewareMixin


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
