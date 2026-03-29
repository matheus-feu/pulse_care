from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers


def _normalize_status_codes(status_codes=None):
    if status_codes is None:
        return None
    if isinstance(status_codes, (list, tuple, set)):
        return [str(code) for code in status_codes]
    return [str(status_codes)]


def request_example(name, value, summary=None, description=None):
    return OpenApiExample(
        name=name,
        value=value,
        summary=summary or name,
        description=description,
        request_only=True,
    )


def response_example(name, value, summary=None, description=None, status_codes=200):
    return OpenApiExample(
        name=name,
        value=value,
        summary=summary or name,
        description=description,
        response_only=True,
        status_codes=_normalize_status_codes(status_codes),
    )


def extend_schema_with_examples(*, request_examples=None, response_examples=None, **kwargs):
    examples = [
        *(request_examples or []),
        *(response_examples or []),
    ]
    if examples:
        kwargs['examples'] = examples
    return extend_schema(**kwargs)


AUTH_TOKEN_REQUEST_SERIALIZER = inline_serializer(
    name='AuthTokenRequest',
    fields={
        'email': serializers.EmailField(),
        'password': serializers.CharField(write_only=True),
    },
)

AUTH_TOKEN_RESPONSE_SERIALIZER = inline_serializer(
    name='AuthTokenResponse',
    fields={
        'refresh': serializers.CharField(),
        'access': serializers.CharField(),
    },
)

TOKEN_REFRESH_REQUEST_SERIALIZER = inline_serializer(
    name='TokenRefreshRequest',
    fields={
        'refresh': serializers.CharField(),
    },
)

TOKEN_REFRESH_RESPONSE_SERIALIZER = inline_serializer(
    name='TokenRefreshResponse',
    fields={
        'access': serializers.CharField(),
    },
)

PASSWORD_RESET_REQUEST_RESPONSE_SERIALIZER = inline_serializer(
    name='PasswordResetRequestResponse',
    fields={
        'detail': serializers.CharField(required=False),
        'otp': serializers.CharField(required=False),
        'delivery_mode': serializers.CharField(required=False),
    },
)

DETAIL_RESPONSE_SERIALIZER = inline_serializer(
    name='DetailResponse',
    fields={
        'detail': serializers.CharField(),
    },
)

