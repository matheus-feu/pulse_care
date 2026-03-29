import logging

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from core.utils import get_actor_email
from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=['Users'],
        summary='List all active users',
        parameters=[
            OpenApiParameter('role', str, description='Filter by role (admin, doctor, nurse, receptionist)'),
        ],
    ),
    retrieve=extend_schema(tags=['Users'], summary='Retrieve a user'),
    create=extend_schema(
        tags=['Users'],
        summary='Create a new user (admin only)',
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
    ),
    update=extend_schema(tags=['Users'], summary='Update a user'),
    partial_update=extend_schema(tags=['Users'], summary='Partially update a user'),
    destroy=extend_schema(
        tags=['Users'],
        summary='Deactivate a user (soft delete, admin only)',
        responses={200: OpenApiResponse(description='User deactivated')},
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system users (staff members).
    Admins can create/delete; authenticated users can view and update profiles.
    """

    queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    serializer_class = UserSerializer
    search_fields = ['first_name', 'last_name', 'email', 'role']
    ordering_fields = ['first_name', 'last_name', 'created_at', 'role']
    filterset_fields = ['role', 'is_active', 'is_staff']

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update', 'update_profile']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        params = getattr(self.request, 'query_params', self.request.GET)
        role = params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset.order_by('first_name', 'last_name')

    def perform_create(self, serializer):
        user = serializer.save()
        actor_email = get_actor_email(self.request.user)
        logger.info(
            f'User created by={actor_email} user_id={user.pk} email={user.email} role={user.role}')

    def perform_destroy(self, instance):
        """Soft delete — deactivate instead of removing from DB."""
        if instance.pk == self.request.user.pk:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {'detail': 'You cannot deactivate your own account.'},
                code='self_deactivation',
            )
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        actor_email = get_actor_email(self.request.user)
        logger.info(
            f'User deactivated by={actor_email} user_id={instance.pk} '
            f'email={instance.email} role={instance.role}')

    def destroy(self, request, *args, **kwargs):
        """Override to return 200 with message instead of 204 (since it's a soft delete)."""
        self.perform_destroy(self.get_object())
        return Response(
            {'detail': 'User deactivated successfully.'},
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=['Users'], summary='Get the authenticated user profile')
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        actor_email = get_actor_email(request.user)
        logger.info(f'Profile requested by user_id={request.user.pk} email={actor_email}')
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        tags=['Users'],
        summary='Update the authenticated user profile',
        request=UserUpdateSerializer,
        responses={200: UserSerializer},
    )
    @action(detail=False, methods=['patch'], url_path='me/update')
    def update_profile(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        actor_email = get_actor_email(request.user)
        logger.info(f'Profile updated by user_id={request.user.pk} email={actor_email}')
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        tags=['Users'],
        summary='Change the authenticated user password',
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password updated successfully.'),
            400: OpenApiResponse(description='Validation error or incorrect password'),
        },
    )
    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            logger.info(
                f'Password change rejected for user_id={user.pk} '
                f'email={get_actor_email(user)} reason=incorrect_current_password')
            raise AuthenticationFailed(
                detail='Current password is incorrect.',
                code='incorrect_password',
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        logger.info(f'Password changed for user_id={user.pk} email={get_actor_email(user)}')
        return Response({'detail': 'Password updated successfully.'})
