import logging

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.exceptions import Conflict
from core.utils import get_actor_email
from .filters import AppointmentFilter
from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    AppointmentListSerializer,
    AppointmentStatusSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Appointments'], summary='List appointments'),
    retrieve=extend_schema(tags=['Appointments'], summary='Retrieve an appointment'),
    create=extend_schema(
        tags=['Appointments'],
        summary='Schedule a new appointment',
        responses={
            201: AppointmentSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
    ),
    update=extend_schema(tags=['Appointments'], summary='Update an appointment'),
    partial_update=extend_schema(tags=['Appointments'], summary='Partially update an appointment'),
    destroy=extend_schema(
        tags=['Appointments'],
        summary='Delete an appointment',
        responses={204: OpenApiResponse(description='Appointment deleted')},
    ),
)
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments.
    Supports filtering by status, doctor, patient, type and date range.
    """

    queryset = Appointment.objects.select_related('patient', 'doctor', 'created_by')
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = AppointmentFilter
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__cpf', 'reason']
    ordering_fields = ['scheduled_at', 'status', 'appointment_type', 'created_at']
    ordering = ['-scheduled_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AppointmentListSerializer
        if self.action == 'update_status':
            return AppointmentStatusSerializer
        return AppointmentSerializer

    def get_queryset(self):
        return (
            Appointment.objects
            .select_related('patient', 'doctor', 'created_by')
            .order_by('-scheduled_at')
        )

    def perform_create(self, serializer):
        appointment = serializer.save(created_by=self.request.user)
        actor_email = get_actor_email(self.request.user)
        logger.info(
            f'Appointment created by={actor_email} appointment_id={appointment.pk} '
            f'patient_id={appointment.patient_id} doctor_id={appointment.doctor_id}')

    def perform_destroy(self, instance):
        if instance.status in (Appointment.Status.COMPLETED, Appointment.Status.IN_PROGRESS):
            raise Conflict(
                detail=f'Cannot delete an appointment with status "{instance.status}".',
            )
        actor_email = get_actor_email(self.request.user)
        logger.info(
            f'Appointment deleted by={actor_email} appointment_id={instance.pk}')
        super().perform_destroy(instance)

    @extend_schema(
        tags=['Appointments'],
        summary='Update appointment status',
        request=AppointmentStatusSerializer,
        responses={
            200: AppointmentSerializer,
            400: OpenApiResponse(description='Invalid status transition'),
            409: OpenApiResponse(description='Status conflict'),
        },
    )
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Quick status transition: confirm, cancel, complete, no-show."""
        appointment = self.get_object()
        previous_status = appointment.status
        serializer = AppointmentStatusSerializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        actor_email = get_actor_email(request.user)
        logger.info(
            f'Appointment status updated by={actor_email} appointment_id={appointment.pk} '
            f'from={previous_status} to={appointment.status}')
        return Response(AppointmentSerializer(appointment).data)

    @extend_schema(
        tags=['Appointments'],
        summary="Today's appointment schedule",
        responses={200: AppointmentListSerializer(many=True)},
    )
    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        """Return every appointment scheduled for today (local timezone)."""
        queryset = self.get_queryset().filter(scheduled_at__date=timezone.localdate())
        actor_email = get_actor_email(request.user)
        logger.info(
            f'Today appointments requested by user_id={request.user.pk} '
            f'email={actor_email} total={queryset.count()}')
        return Response(AppointmentListSerializer(queryset, many=True).data)

    @extend_schema(
        tags=['Appointments'],
        summary="Authenticated doctor's appointments",
        responses={200: AppointmentListSerializer(many=True)},
    )
    @action(detail=False, methods=['get'], url_path='my')
    def my_appointments(self, request):
        """Return all appointments for the currently logged-in doctor."""
        if not request.user.is_doctor:
            return Response(
                {'detail': 'Only doctors can access their own appointment list.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        queryset = self.get_queryset().filter(doctor=request.user)
        actor_email = get_actor_email(request.user)
        logger.info(
            f'My appointments requested by doctor_id={request.user.pk} '
            f'email={actor_email} total={queryset.count()}')
        return Response(AppointmentListSerializer(queryset, many=True).data)
