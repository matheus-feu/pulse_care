import logging

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.mixins import ActorContextMixin, SoftDeleteMixin
from core.swagger import extend_schema_with_examples, request_example, response_example
from .filters import PatientFilter
from .models import Patient
from .serializers import PatientSerializer, PatientListSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Patients'], summary='List patients'),
    retrieve=extend_schema(tags=['Patients'], summary='Retrieve a patient'),
    create=extend_schema_with_examples(
        tags=['Patients'],
        summary='Register a new patient',
        responses={
            201: PatientSerializer,
            400: OpenApiResponse(description='Validation error (e.g. invalid CPF, duplicate)'),
        },
        request_examples=[
            request_example(
                'Create patient',
                {
                    'first_name': 'Maria',
                    'last_name': 'Silva',
                    'date_of_birth': '1992-04-12',
                    'gender': 'female',
                    'cpf': '12345678901',
                    'phone': '11988887777',
                    'email': 'maria.silva@email.com',
                    'blood_type': 'O+',
                },
            ),
        ],
        response_examples=[
            response_example(
                'Patient created',
                {
                    'id': 15,
                    'first_name': 'Maria',
                    'last_name': 'Silva',
                    'full_name': 'Maria Silva',
                    'date_of_birth': '1992-04-12',
                    'age': 33,
                    'gender': 'female',
                    'cpf': '123.456.789-01',
                    'phone': '11988887777',
                    'email': 'maria.silva@email.com',
                    'blood_type': 'O+',
                    'is_active': True,
                    'created_by': 'Admin PulseCare (Administrator)',
                    'created_at': '2026-03-29T10:30:00-03:00',
                    'updated_at': '2026-03-29T10:30:00-03:00',
                },
                status_codes=201,
            ),
        ],
    ),
    update=extend_schema(tags=['Patients'], summary='Update a patient'),
    partial_update=extend_schema(tags=['Patients'], summary='Partially update a patient'),
    destroy=extend_schema(
        tags=['Patients'],
        summary='Deactivate a patient (soft delete)',
        responses={200: OpenApiResponse(description='Patient deactivated')},
    ),
)
class PatientViewSet(ActorContextMixin, SoftDeleteMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing patients.
    Supports search, filtering and ordering.
    """

    queryset = Patient.objects.active().with_creator()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    soft_delete_response_message = 'Patient deactivated successfully.'
    filterset_class = PatientFilter
    search_fields = ['first_name', 'last_name', 'cpf', 'email', 'phone']
    ordering_fields = ['last_name', 'first_name', 'date_of_birth', 'created_at']
    ordering = ['last_name', 'first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        queryset = Patient.objects.with_creator()

        if self.action == 'list':
            queryset = queryset.with_stats()

        params = getattr(self.request, 'query_params', self.request.GET)
        show_inactive = params.get('show_inactive', '').lower() == 'true'
        if not show_inactive:
            queryset = queryset.active()
        return queryset.ordered()

    def perform_create(self, serializer):
        patient = serializer.save(created_by=self.request.user)
        actor_email = self.actor_email()
        logger.info(
            f'Patient created by={actor_email} patient_id={patient.pk} '
            f'name={patient.full_name} cpf={patient.cpf}')

    def perform_soft_delete(self, instance):
        super().perform_soft_delete(instance)
        actor_email = self.actor_email()
        logger.info(
            f'Patient deactivated by={actor_email} patient_id={instance.pk} '
            f'name={instance.full_name} cpf={instance.cpf}')


    @extend_schema_with_examples(
        tags=['Patients'],
        summary='Full clinical history of a patient',
        responses={200: OpenApiResponse(description='Appointments and medical records')},
        response_examples=[
            response_example(
                'Patient history result',
                {
                    'patient': {
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
                    'appointments': [
                        {
                            'id': 42,
                            'patient': 15,
                            'patient_name': 'Maria Silva',
                            'doctor': 7,
                            'doctor_name': 'Gregory House',
                            'scheduled_at': '2026-03-28T14:30:00-03:00',
                            'duration_minutes': 30,
                            'appointment_type': 'consultation',
                            'status': 'completed',
                            'reason': 'Routine checkup',
                        }
                    ],
                    'medical_records': [
                        {
                            'id': 13,
                            'patient': 15,
                            'patient_name': 'Maria Silva',
                            'doctor': 7,
                            'doctor_name': 'Gregory House',
                            'chief_complaint': 'Headache',
                            'diagnosis': 'Tension headache',
                            'icd10_code': 'G44.2',
                            'created_at': '2026-03-28T15:15:00-03:00',
                        }
                    ],
                },
                status_codes=200,
            ),
        ],
    )
    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """Return all appointments and medical records for a given patient."""
        patient = self.get_object()
        from apps.appointments.serializers import AppointmentListSerializer
        from apps.records.serializers import MedicalRecordListSerializer

        appointments = patient.appointments.select_related('doctor').order_by('-scheduled_at')
        records = patient.medical_records.select_related('doctor').order_by('-created_at')

        actor_email = self.actor_email(request)
        logger.info(
            f'Patient history requested by={actor_email} patient_id={patient.pk} '
            f'name={patient.full_name} appointments={appointments.count()} records={records.count()}')

        return Response({
            'patient': PatientListSerializer(patient).data,
            'appointments': AppointmentListSerializer(appointments, many=True).data,
            'medical_records': MedicalRecordListSerializer(records, many=True).data,
        })
