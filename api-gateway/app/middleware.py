import json
import time
import logging
import re
from collections import defaultdict
from django.http import JsonResponse
from django.conf import settings
import jwt

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    """
    Validates JWT tokens on all routes.
    If a valid token is provided, user identity headers are injected.
    If no token is provided, requests pass through (downstream services
    can decide whether to require auth).
    
    This approach lets the frontend work seamlessly while still 
    demonstrating JWT validation at the gateway level.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=['HS256'],
                )
                
                # Check token type
                if payload.get('type') != 'access':
                    return JsonResponse({'error': 'Invalid token type'}, status=401)

                # Inject user info into request for downstream use
                request.META['HTTP_X_USER_ID'] = str(payload.get('user_id', ''))
                request.META['HTTP_X_USER_EMAIL'] = payload.get('email', '')
                request.META['HTTP_X_USER_ROLE'] = payload.get('role', '')
                request.user_id = payload.get('user_id')
                request.user_role = payload.get('role')

                logger.info(json.dumps({
                    'type': 'jwt_auth',
                    'user_id': payload.get('user_id'),
                    'role': payload.get('role'),
                    'path': request.path,
                }))

            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token has expired'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'error': 'Invalid token'}, status=401)

        return self.get_response(request)


class RequestLoggingMiddleware:
    """
    Logs every request with method, path, status code, and response time.
    Uses structured JSON logging format.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration_ms = (time.time() - start_time) * 1000

        # Update metrics
        _metrics['total_requests'] += 1
        _metrics['total_response_time_ms'] += duration_ms
        
        if response.status_code >= 400:
            _metrics['error_count'] += 1
        
        status_key = str(response.status_code)
        _metrics['status_codes'][status_key] = _metrics['status_codes'].get(status_key, 0) + 1

        logger.info(json.dumps({
            'type': 'request_log',
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration_ms, 2),
            'ip': self._get_client_ip(request),
            'user_id': getattr(request, 'user_id', None),
        }))

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class RateLimitMiddleware:
    """
    Simple in-memory token bucket rate limiter per IP address.
    Default: 100 requests per minute.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 100)
        self.window_seconds = 60
        self.requests = defaultdict(list)

    def __call__(self, request):
        ip = self._get_client_ip(request)
        now = time.time()

        # Clean old requests outside the window
        self.requests[ip] = [
            t for t in self.requests[ip]
            if t > now - self.window_seconds
        ]

        if len(self.requests[ip]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after_seconds': self.window_seconds,
            }, status=429)

        self.requests[ip].append(now)
        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


# ---- Metrics storage (in-memory, used by RequestLoggingMiddleware and MetricsView) ----
_metrics = {
    'total_requests': 0,
    'error_count': 0,
    'total_response_time_ms': 0,
    'status_codes': {},
}


def get_metrics():
    """Return current metrics snapshot."""
    avg_response_time = 0
    if _metrics['total_requests'] > 0:
        avg_response_time = round(
            _metrics['total_response_time_ms'] / _metrics['total_requests'], 2
        )
    
    return {
        'total_requests': _metrics['total_requests'],
        'error_count': _metrics['error_count'],
        'avg_response_time_ms': avg_response_time,
        'status_codes': dict(_metrics['status_codes']),
    }
