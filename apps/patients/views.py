import logging

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils import get_actor_email
from .filters import PatientFilter
from .models import Patient
from .serializers import PatientSerializer, PatientListSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Patients'], summary='List patients'),
    retrieve=extend_schema(tags=['Patients'], summary='Retrieve a patient'),
    create=extend_schema(
        tags=['Patients'],
        summary='Register a new patient',
        responses={
            201: PatientSerializer,
            400: OpenApiResponse(description='Validation error (e.g. invalid CPF, duplicate)'),
        },
    ),
    update=extend_schema(tags=['Patients'], summary='Update a patient'),
    partial_update=extend_schema(tags=['Patients'], summary='Partially update a patient'),
    destroy=extend_schema(
        tags=['Patients'],
        summary='Deactivate a patient (soft delete)',
        responses={200: OpenApiResponse(description='Patient deactivated')},
    ),
)
class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patients.
    Supports search, filtering and ordering.
    """

    queryset = Patient.objects.filter(is_active=True).select_related('created_by')
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = PatientFilter
    search_fields = ['first_name', 'last_name', 'cpf', 'email', 'phone']
    ordering_fields = ['last_name', 'first_name', 'date_of_birth', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        queryset = Patient.objects.select_related('created_by')
        params = getattr(self.request, 'query_params', self.request.GET)
        show_inactive = params.get('show_inactive', '').lower() == 'true'
        if not show_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('last_name', 'first_name')

    def perform_create(self, serializer):
        patient = serializer.save(created_by=self.request.user)
        actor_email = get_actor_email(self.request.user)
        logger.info(
            f'Patient created by={actor_email} patient_id={patient.pk} '
            f'name={patient.full_name} cpf={patient.cpf}')

    def perform_destroy(self, instance):
        """Soft delete — mark as inactive instead of removing from DB."""
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        actor_email = get_actor_email(self.request.user)
        logger.info(
            f'Patient deactivated by={actor_email} patient_id={instance.pk} '
            f'name={instance.full_name} cpf={instance.cpf}')

    def destroy(self, request, *args, **kwargs):
        """Override to return 200 with message instead of 204 (since it's a soft delete)."""
        self.perform_destroy(self.get_object())
        return Response(
            {'detail': 'Patient deactivated successfully.'},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=['Patients'],
        summary='Full clinical history of a patient',
        responses={200: OpenApiResponse(description='Appointments and medical records')},
    )
    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """Return all appointments and medical records for a given patient."""
        patient = self.get_object()
        from apps.appointments.serializers import AppointmentListSerializer
        from apps.records.serializers import MedicalRecordListSerializer

        appointments = patient.appointments.select_related('doctor').order_by('-scheduled_at')
        records = patient.medical_records.select_related('doctor').order_by('-created_at')

        actor_email = get_actor_email(request.user)
        logger.info(
            f'Patient history requested by={actor_email} patient_id={patient.pk} '
            f'name={patient.full_name} appointments={appointments.count()} records={records.count()}')

        return Response({
            'patient': PatientListSerializer(patient).data,
            'appointments': AppointmentListSerializer(appointments, many=True).data,
            'medical_records': MedicalRecordListSerializer(records, many=True).data,
        })
