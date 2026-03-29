import logging

from drf_spectacular.utils import OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import UserSerializer
from core.swagger import (
    DETAIL_RESPONSE_SERIALIZER,
    PASSWORD_RESET_REQUEST_RESPONSE_SERIALIZER,
    extend_schema_with_examples,
    request_example,
    response_example,
)
from core.utils import send_notification_email
from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Public endpoint — anyone can create an account."""

    permission_classes = [AllowAny]

    @extend_schema_with_examples(
        tags=['Accounts'],
        summary='Register a new account',
        description=(
                'Create a new user with default role **receptionist**. '
                'An admin can later promote the user to another role.'
        ),
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
        request_examples=[
            request_example(
                'Receptionist registration',
                {
                    'username': 'matheus.feu',
                    'email': 'email@email.com',
                    'first_name': 'Matheus',
                    'last_name': 'Feu',
                    'phone': '11999999999',
                    'password': 'StrongPass@123',
                    'confirm_password': 'StrongPass@123',
                },
            ),
        ],
        response_examples=[
            response_example(
                'Registration success',
                {
                    'id': 12,
                    'username': 'matheus',
                    'email': 'matheus@email.com',
                    'first_name': 'Matheus',
                    'last_name': 'Feulo',
                    'full_name': 'Matheus Feulo',
                    'role': 'receptionist',
                    'license_number': None,
                    'specialty': None,
                    'phone': '11999999999',
                    'avatar': None,
                    'is_active': True,
                    'is_staff': False,
                    'created_at': '2026-03-29T02:10:04-03:00',
                    'updated_at': '2026-03-29T02:10:04-03:00',
                },
                status_codes=201,
            ),
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(
            f'New account registered email={user.email} '
            f'username={user.username} role={user.role}',
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class PasswordResetRequestView(APIView):
    """
    Public endpoint — request a password reset OTP (One Time Password).
    Always returns 200 (doesn't reveal if the email exists).
    """

    permission_classes = [AllowAny]

    @extend_schema_with_examples(
        tags=['Accounts'],
        summary='Request password reset OTP',
        description=(
                'Send a one-time password (OTP) to the given e-mail address. '
                'The response is always 200 to avoid user enumeration.'
        ),
        request=PasswordResetRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=PASSWORD_RESET_REQUEST_RESPONSE_SERIALIZER,
                description='Reset OTP sent (if account exists)',
            ),
        },
        request_examples=[
            request_example(
                'Password reset request',
                {
                    'email': 'email@email.com',
                },
            ),
        ],
        response_examples=[
            response_example(
                'Password reset response',
                {
                    'otp': '302321',
                },
                status_codes=200,
            ),
        ],
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response: dict = {}

        reset_data = serializer.save()
        if reset_data:
            user = reset_data['user']
            otp = reset_data['otp']
            response['otp'] = otp

            try:
                send_notification_email(
                    subject='Password reset',
                    body=(
                        f'Hello, {user.first_name}!\n\n'
                        f'Use the OTP below to reset your password:\n\n'
                        f'  OTP: {otp}\n\n'
                        f'This code expires in a few minutes.\n'
                        f'If you did not request this, ignore this e-mail.\n\n'
                        f'PulseCare Team'
                    ),
                    recipient_list=[user.email],
                    log_context=f'accounts.password_reset_request user_id={user.pk}',
                )
                logger.info(f'Password reset OTP sent user_id={user.pk} email={user.email}')
            except Exception:
                logger.exception(f'Password reset OTP delivery failed user_id={user.pk} email={user.email}')

        return Response(response, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Public endpoint — set a new password with e-mail + OTP (One Time Password)."""

    permission_classes = [AllowAny]

    @extend_schema_with_examples(
        tags=['Accounts'],
        summary='Confirm password reset with OTP',
        description='Validate e-mail + OTP and set a new password.',
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(
                response=DETAIL_RESPONSE_SERIALIZER,
                description='Password reset successfully',
            ),
            400: OpenApiResponse(description='Invalid/expired OTP or validation error'),
        },
        request_examples=[
            request_example(
                'Password reset confirmation',
                {
                    'email': 'email@email.com',
                    'otp': '302321',
                    'new_password': 'NovaSenha@123',
                    'confirm_new_password': 'NovaSenha@123',
                },
            ),
        ],
        response_examples=[
            response_example(
                'Password reset success',
                {
                    'detail': 'Password has been reset successfully. You can now log in.',
                },
                status_codes=200,
            ),
        ],
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(f'Password reset completed user_id={user.pk} email={user.email}')
        return Response(
            {'detail': 'Password has been reset successfully. You can now log in.'},
            status=status.HTTP_200_OK,
        )
