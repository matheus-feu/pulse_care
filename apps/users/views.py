import logging

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response

from core.mixins import ActorContextMixin, SoftDeleteMixin
from core.swagger import DETAIL_RESPONSE_SERIALIZER, extend_schema_with_examples, request_example, response_example
from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)


class IsSystemAdmin(BasePermission):
    """Allow access only to admin-role users, staff admins, or superusers."""

    message = 'Only administrators can manage system users.'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.is_staff or user.role == User.Role.ADMIN)
        )


@extend_schema_view(
    list=extend_schema(
        tags=['Users'],
        summary='List all active users (admin only)',
        parameters=[
            OpenApiParameter('role', str, description='Filter by role (admin, doctor, nurse, receptionist)'),
        ],
    ),
    retrieve=extend_schema(tags=['Users'], summary='Retrieve a user (admin only)'),
    create=extend_schema_with_examples(
        tags=['Users'],
        summary='Create a new user (admin only)',
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
        request_examples=[
            request_example(
                'Create doctor user',
                {
                    'username': 'dr.house',
                    'email': 'house@pulsecare.com',
                    'first_name': 'Gregory',
                    'last_name': 'House',
                    'role': 'doctor',
                    'license_number': 'CRM12345',
                    'specialty': 'Diagnostic Medicine',
                    'phone': '11988887777',
                    'password': 'DoctorPass@123',
                    'confirm_password': 'DoctorPass@123',
                },
            ),
        ],
        response_examples=[
            response_example(
                'User created',
                {
                    'id': 7,
                    'username': 'dr.house',
                    'email': 'house@pulsecare.com',
                    'first_name': 'Gregory',
                    'last_name': 'House',
                    'full_name': 'Gregory House',
                    'role': 'doctor',
                    'license_number': 'CRM12345',
                    'specialty': 'Diagnostic Medicine',
                    'phone': '11988887777',
                    'avatar': None,
                    'is_active': True,
                    'is_staff': False,
                    'created_at': '2026-03-29T10:00:00-03:00',
                    'updated_at': '2026-03-29T10:00:00-03:00',
                },
                status_codes=201,
            ),
        ],
    ),
    update=extend_schema(tags=['Users'], summary='Update a user (admin only)'),
    partial_update=extend_schema(tags=['Users'], summary='Partially update a user (admin only)'),
    destroy=extend_schema(
        tags=['Users'],
        summary='Deactivate a user (soft delete, admin only)',
        responses={200: OpenApiResponse(description='User deactivated')},
    ),
)
class UserViewSet(ActorContextMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing system users (staff members).
    Only admins can manage other users.
    Authenticated users can access only their own self-service endpoints.
    """

    admin_actions = {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'}

    queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    serializer_class = UserSerializer
    soft_delete_response_message = 'User deactivated successfully.'
    search_fields = ['first_name', 'last_name', 'email', 'role']
    ordering_fields = ['first_name', 'last_name', 'created_at', 'role']
    filterset_fields = ['role', 'is_active', 'is_staff']

    def get_permissions(self):
        if self.action in self.admin_actions:
            return [IsSystemAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update', 'update_profile']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        if not IsSystemAdmin().has_permission(self.request, self):
            return queryset.filter(pk=self.request.user.pk).order_by('first_name', 'last_name')
        params = getattr(self.request, 'query_params', self.request.GET)
        role = params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset.order_by('first_name', 'last_name')

    def perform_create(self, serializer):
        user = serializer.save()
        actor_email = self.actor_email()
        logger.info(
            f'User created by={actor_email} user_id={user.pk} email={user.email} role={user.role}')

    def perform_soft_delete(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError(
                {'detail': 'You cannot deactivate your own account.'},
                code='self_deactivation',
            )
        super().perform_soft_delete(instance)
        actor_email = self.actor_email()
        logger.info(
            f'User deactivated by={actor_email} user_id={instance.pk} '
            f'email={instance.email} role={instance.role}')


    @extend_schema_with_examples(
        tags=['Users'],
        summary='Get the authenticated user profile',
        responses={200: UserSerializer},
        response_examples=[
            response_example(
                'Authenticated profile',
                {
                    'id': 2,
                    'username': 'matheus',
                    'email': 'email@emai.com',
                    'first_name': 'Matheus',
                    'last_name': 'Feu',
                    'full_name': 'Matheus Feu',
                    'role': 'receptionist',
                    'license_number': None,
                    'specialty': None,
                    'phone': '11999999999',
                    'avatar': None,
                    'is_active': True,
                    'is_staff': False,
                    'created_at': '2026-03-29T01:10:04-03:00',
                    'updated_at': '2026-03-29T01:10:04-03:00',
                },
            ),
        ],
    )
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        actor_email = self.actor_email(request)
        logger.info(f'Profile requested by user_id={request.user.pk} email={actor_email}')
        return Response(UserSerializer(request.user).data)

    @extend_schema_with_examples(
        tags=['Users'],
        summary='Update the authenticated user profile',
        request=UserUpdateSerializer,
        responses={200: UserSerializer},
        request_examples=[
            request_example(
                'Profile update',
                {
                    'first_name': 'Matheus',
                    'last_name': 'Feulo',
                    'phone': '11977776666',
                },
            ),
        ],
    )
    @action(detail=False, methods=['patch'], url_path='me/update')
    def update_profile(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        actor_email = self.actor_email(request)
        logger.info(f'Profile updated by user_id={request.user.pk} email={actor_email}')
        return Response(UserSerializer(request.user).data)

    @extend_schema_with_examples(
        tags=['Users'],
        summary='Change the authenticated user password',
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=DETAIL_RESPONSE_SERIALIZER,
                description='Password updated successfully.',
            ),
            400: OpenApiResponse(description='Validation error or incorrect password'),
        },
        request_examples=[
            request_example(
                'Change password request',
                {
                    'current_password': 'Senha@123',
                    'new_password': 'NovaSenha@123',
                    'confirm_new_password': 'NovaSenha@123',
                },
            ),
        ],
        response_examples=[
            response_example(
                'Password change success',
                {
                    'detail': 'Password updated successfully.',
                },
                status_codes=200,
            ),
        ],
    )
    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            logger.info(
                f'Password change rejected for user_id={user.pk} '
                f'email={self.actor_email(request)} reason=incorrect_current_password')
            raise AuthenticationFailed(
                detail='Current password is incorrect.',
                code='incorrect_password',
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        logger.info(f'Password changed for user_id={user.pk} email={self.actor_email(request)}')
        return Response({'detail': 'Password updated successfully.'})
