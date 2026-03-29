import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class Conflict(APIException):
    """409 — resource state conflict (e.g. duplicate, invalid transition)."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'This action conflicts with the current state of the resource.'
    default_code = 'conflict'


class BusinessRuleViolation(APIException):
    """422 — request is syntactically valid but violates a business rule."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'The request could not be processed due to a business rule violation.'
    default_code = 'business_rule_violation'


def _error_item(*, code: str, detail: str, attr: str | None = None) -> dict:
    return {'code': code, 'detail': detail, 'attr': attr}


def _get_error_type(status_code: int) -> str:
    if status_code == 401 or status_code == 403:
        return 'authentication_error'
    if status_code == 422:
        return 'validation_error'
    if 400 <= status_code < 500:
        return 'client_error'
    return 'server_error'


def _flatten_validation_errors(detail, attr_prefix: str = '') -> list[dict]:
    """
    Recursively flatten DRF's nested validation detail into a flat list
    of ``{code, detail, attr}`` dicts.
    """
    items: list[dict] = []

    if isinstance(detail, list):
        for error in detail:
            if hasattr(error, 'code'):
                items.append(_error_item(
                    code=error.code or 'invalid',
                    detail=str(error),
                    attr=attr_prefix or None,
                ))
            else:
                items.append(_error_item(
                    code='invalid',
                    detail=str(error),
                    attr=attr_prefix or None,
                ))

    elif isinstance(detail, dict):
        for field, child in detail.items():
            full_attr = f'{attr_prefix}.{field}' if attr_prefix else field
            if field == 'non_field_errors':
                items.extend(_flatten_validation_errors(child, attr_prefix=''))
            else:
                items.extend(_flatten_validation_errors(child, attr_prefix=full_attr))

    else:
        code = getattr(detail, 'code', 'invalid') if hasattr(detail, 'code') else 'invalid'
        items.append(_error_item(code=code, detail=str(detail), attr=attr_prefix or None))

    return items


def custom_exception_handler(exc, context):
    """
    Custom DRF exception handler that wraps every error in a uniform envelope.
    """

    # Convert Django-native exceptions to DRF equivalents so they are handled
    if isinstance(exc, Http404):
        from rest_framework.exceptions import NotFound
        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
        exc = DRFPermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        from rest_framework.exceptions import ValidationError
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, 'message_dict') else exc.messages)

    # Let DRF handle the exception first (sets headers, status, etc.)
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception → 500
        logger.exception('Unhandled exception', exc_info=exc)
        response = Response(
            {
                'type': 'server_error',
                'errors': [_error_item(
                    code='internal_error',
                    detail='An unexpected error occurred. Please try again later.',
                )],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return response

    status_code = response.status_code
    error_type = _get_error_type(status_code)

    # Validation / field-level errors (400) have nested structures
    if status_code == status.HTTP_400_BAD_REQUEST and isinstance(response.data, (dict, list)):
        errors = _flatten_validation_errors(response.data)
    else:
        # Single-detail errors (401, 403, 404, 405, 409, 429 …)
        detail = response.data
        if isinstance(detail, dict):
            raw_detail = detail.get('detail', str(detail))
            raw_code = getattr(raw_detail, 'code', None) or getattr(exc, 'default_code', 'error')
            errors = [_error_item(code=raw_code, detail=str(raw_detail))]
        elif isinstance(detail, list):
            errors = _flatten_validation_errors(detail)
        else:
            errors = [_error_item(code=getattr(exc, 'default_code', 'error'), detail=str(detail))]

    response.data = {
        'type': error_type,
        'errors': errors,
    }

    return response
