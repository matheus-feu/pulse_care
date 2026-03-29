import logging

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import UserSerializer
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

    @extend_schema(
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
    Public endpoint — request a password reset link.
    Always returns 200 (doesn't reveal if the email exists).
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Accounts'],
        summary='Request password reset',
        description=(
                'Send a password reset e-mail to the given address. '
                'The response is always 200 to avoid user enumeration.'
        ),
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(description='Reset e-mail sent (if account exists)')},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_data = serializer.get_reset_data()
        if reset_data:
            user = reset_data['user']
            uid = reset_data['uid']
            token = reset_data['token']

            # In production, send a link to the frontend reset page.
            # For now, include uid + token in the e-mail body.
            frontend_url = f'http://localhost:3000/reset-password?uid={uid}&token={token}'

            send_notification_email(
                subject='[PulseCare] Password reset request',
                body=(
                    f'Hello, {user.first_name}!\n\n'
                    f'We received a request to reset your password.\n\n'
                    f'Use the link below to set a new password:\n'
                    f'{frontend_url}\n\n'
                    f'Or use the following values via the API:\n'
                    f'  uid   : {uid}\n'
                    f'  token : {token}\n\n'
                    f'If you did not request this, just ignore this e-mail.\n\n'
                    f'PulseCare Team'
                ),
                recipient_list=[user.email],
                log_context=f'accounts.password_reset_request user_id={user.pk}',
            )
            logger.info(f'Password reset e-mail sent to user_id={user.pk} email={user.email}')
        else:
            logger.info(f'Password reset requested for unknown email={serializer.validated_data["email"]}')

        return Response(
            {'detail': 'If an account with this email exists, a reset link has been sent.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Public endpoint — set a new password with uid + token."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Accounts'],
        summary='Confirm password reset',
        description='Validate the uid + token and set a new password.',
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(description='Password reset successfully'),
            400: OpenApiResponse(description='Invalid/expired token or validation error'),
        },
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
