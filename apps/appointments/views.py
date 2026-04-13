import logging

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.exceptions import Conflict
from core.mixins import ActorContextMixin
from core.swagger import extend_schema_with_examples, request_example, response_example
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
    create=extend_schema_with_examples(
        tags=['Appointments'],
        summary='Schedule a new appointment',
        responses={
            201: AppointmentSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
        request_examples=[
            request_example(
                'Schedule appointment',
                {
                    'patient': 15,
                    'doctor': 7,
                    'scheduled_at': '2026-03-30T14:30:00-03:00',
                    'duration_minutes': 30,
                    'appointment_type': 'consultation',
                    'status': 'scheduled',
                    'reason': 'Routine checkup',
                    'notes': 'First consultation with this doctor',
                },
            ),
        ],
        response_examples=[
            response_example(
                'Appointment created',
                {
                    'id': 42,
                    'patient': 15,
                    'doctor': 7,
                    'scheduled_at': '2026-03-30T14:30:00-03:00',
                    'duration_minutes': 30,
                    'appointment_type': 'consultation',
                    'status': 'scheduled',
                    'reason': 'Routine checkup',
                    'notes': 'First consultation with this doctor',
                    'cancellation_reason': '',
                    'created_by': 'Admin PulseCare (Administrator)',
                    'created_at': '2026-03-29T11:00:00-03:00',
                    'updated_at': '2026-03-29T11:00:00-03:00',
                    'patient_detail': {
                        'id': 15,
                        'full_name': 'Maria Silva',
                        'cpf': '123.456.789-01',
                        'date_of_birth': '1992-04-12',
                        'age': 33,
                        'gender': 'female',
                        'phone': '11988887777',
                        'blood_type': 'O+',
                        'is_active': True,
                    },
                    'doctor_detail': {
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
                        'created_at': '2026-03-20T09:00:00-03:00',
                        'updated_at': '2026-03-20T09:00:00-03:00',
                    },
                },
                status_codes=201,
            ),
        ],
    ),
    update=extend_schema(tags=['Appointments'], summary='Update an appointment'),
    partial_update=extend_schema(tags=['Appointments'], summary='Partially update an appointment'),
    destroy=extend_schema(
        tags=['Appointments'],
        summary='Delete an appointment',
        responses={204: OpenApiResponse(description='Appointment deleted')},
    ),
)
class AppointmentViewSet(ActorContextMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing appointments.
    Supports filtering by status, doctor, patient, type and date range.
    """

    queryset = Appointment.objects.with_relations()
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
        return Appointment.objects.with_relations().ordered()

    def perform_create(self, serializer):
        appointment = serializer.save(created_by=self.request.user)
        actor_email = self.actor_email()
        logger.info(
            f'Appointment created by={actor_email} appointment_id={appointment.pk} '
            f'patient_id={appointment.patient_id} doctor_id={appointment.doctor_id}')

    def perform_destroy(self, instance):
        if instance.status in (Appointment.Status.COMPLETED, Appointment.Status.IN_PROGRESS):
            raise Conflict(
                detail=f'Cannot delete an appointment with status "{instance.status}".',
            )
        actor_email = self.actor_email()
        logger.info(f'Appointment deleted by={actor_email} appointment_id={instance.pk}')
        super().perform_destroy(instance)

    @extend_schema_with_examples(
        tags=['Appointments'],
        summary='Update appointment status',
        request=AppointmentStatusSerializer,
        responses={
            200: AppointmentSerializer,
            400: OpenApiResponse(description='Invalid status transition'),
            409: OpenApiResponse(description='Status conflict'),
        },
        request_examples=[
            request_example(
                'Confirm appointment',
                {
                    'status': 'confirmed',
                },
            ),
            request_example(
                'Cancel appointment',
                {
                    'status': 'cancelled',
                    'cancellation_reason': 'Patient requested cancellation',
                    'notes': 'Reschedule suggested for next week',
                },
            ),
        ],
        response_examples=[
            response_example(
                'Status updated',
                {
                    'id': 42,
                    'patient': 15,
                    'doctor': 7,
                    'scheduled_at': '2026-03-30T14:30:00-03:00',
                    'duration_minutes': 30,
                    'appointment_type': 'consultation',
                    'status': 'confirmed',
                    'reason': 'Routine checkup',
                    'notes': 'Patient confirmed by phone',
                    'cancellation_reason': '',
                },
                status_codes=200,
            ),
        ],
    )
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Quick status transition: confirm, cancel, complete, no-show."""
        appointment = self.get_object()
        previous_status = appointment.status
        serializer = AppointmentStatusSerializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        actor_email = self.actor_email(request)
        logger.info(
            f'Appointment status updated by={actor_email} appointment_id={appointment.pk} '
            f'from={previous_status} to={appointment.status}')
        return Response(AppointmentSerializer(appointment).data)

    @extend_schema_with_examples(
        tags=['Appointments'],
        summary="Today's appointment schedule",
        responses={200: AppointmentListSerializer(many=True)},
        response_examples=[
            response_example(
                "Today's appointments",
                [
                    {
                        'id': 42,
                        'patient': 15,
                        'patient_name': 'Maria Silva',
                        'doctor': 7,
                        'doctor_name': 'Gregory House',
                        'scheduled_at': '2026-03-29T14:30:00-03:00',
                        'duration_minutes': 30,
                        'appointment_type': 'consultation',
                        'status': 'confirmed',
                        'reason': 'Routine checkup',
                    },
                    {
                        'id': 43,
                        'patient': 18,
                        'patient_name': 'Joao Souza',
                        'doctor': 7,
                        'doctor_name': 'Gregory House',
                        'scheduled_at': '2026-03-29T15:30:00-03:00',
                        'duration_minutes': 20,
                        'appointment_type': 'follow_up',
                        'status': 'scheduled',
                        'reason': 'Blood pressure follow-up',
                    },
                ],
                status_codes=200,
            ),
        ],
    )
    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        """Return every appointment scheduled for today (local timezone)."""
        queryset = self.get_queryset().today()
        actor_email = self.actor_email(request)
        logger.info(
            f'Today appointments requested by user_id={request.user.pk} '
            f'email={actor_email} total={queryset.count()}')
        return Response(AppointmentListSerializer(queryset, many=True).data)

    @extend_schema_with_examples(
        tags=['Appointments'],
        summary="Authenticated doctor's appointments",
        responses={200: AppointmentListSerializer(many=True)},
        response_examples=[
            response_example(
                "Doctor's appointments",
                [
                    {
                        'id': 42,
                        'patient': 15,
                        'patient_name': 'Maria Silva',
                        'doctor': 7,
                        'doctor_name': 'Gregory House',
                        'scheduled_at': '2026-03-30T14:30:00-03:00',
                        'duration_minutes': 30,
                        'appointment_type': 'consultation',
                        'status': 'confirmed',
                        'reason': 'Routine checkup',
                    }
                ],
                status_codes=200,
            ),
            response_example(
                'Forbidden for non-doctor user',
                {
                    'detail': 'Only doctors can access their own appointment list.',
                },
                status_codes=403,
            ),
        ],
    )
    @action(detail=False, methods=['get'], url_path='my')
    def my_appointments(self, request):
        """Return all appointments for the currently logged-in doctor."""
        if not request.user.is_doctor:
            return Response(
                {'detail': 'Only doctors can access their own appointment list.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        queryset = self.get_queryset().for_doctor(request.user)
        actor_email = self.actor_email(request)
        logger.info(
            f'My appointments requested by doctor_id={request.user.pk} '
            f'email={actor_email} total={queryset.count()}')
        return Response(AppointmentListSerializer(queryset, many=True).data)
