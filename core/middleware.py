import logging
import time
import uuid

from django.utils.deprecation import MiddlewareMixin

from core.utils import _get_client_ip, get_actor_email

logger = logging.getLogger('api.requests')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Logs every HTTP request with:
      - Unique request_id (UUID4, also injected into response header)
      - HTTP method and path
      - Authenticated user (or 'anonymous')
      - Response status code
      - Total elapsed time in ms
      - Client IP address

    Log level:
      - 5xx  → ERROR
      - 4xx  → WARNING
      - 2xx/3xx → INFO
    """

    def process_request(self, request):
        request._start_time = time.monotonic()
        request._request_id = str(uuid.uuid4())

    def process_response(self, request, response):
        # Some requests (e.g. from middleware failures) may not have _start_time
        duration_ms = 0
        if hasattr(request, '_start_time'):
            duration_ms = round((time.monotonic() - request._start_time) * 1000, 2)

        request_id = getattr(request, '_request_id', '-')
        response['X-Request-Id'] = request_id

        user = getattr(request, 'user', None)
        username = get_actor_email(user)

        status_code = response.status_code
        log_extra = {
            'request_id': request_id,
            'method': request.method,
            'path': request.get_full_path(),
            'status_code': status_code,
            'duration_ms': duration_ms,
            'user': username,
            'ip': _get_client_ip(request),
        }

        msg = (
            f'[{request_id}] {request.method} {request.get_full_path()} '
            f'→ {status_code} ({duration_ms} ms) user={username}'
        )

        if status_code >= 500:
            logger.error(msg, extra=log_extra)
        elif status_code >= 400:
            logger.warning(msg, extra=log_extra)
        else:
            logger.info(msg, extra=log_extra)

        return response

    def process_exception(self, request, exception):
        request_id = getattr(request, '_request_id', '-')
        logger.exception(
            f'[{request_id}] Unhandled exception on {request.method} {request.get_full_path()}',
            exc_info=exception,
            extra={'request_id': request_id},
        )
        return None


class HealthCheckMiddleware(MiddlewareMixin):
    """
    Returns a 200 OK immediately for GET /health/ without hitting the database
    or going through authentication — useful for container / load-balancer probes.
    """

    HEALTH_URL = '/health/'

    def process_request(self, request):
        if request.path == self.HEALTH_URL and request.method == 'GET':
            from django.http import JsonResponse
            return JsonResponse({'status': 'ok'})
        return None
