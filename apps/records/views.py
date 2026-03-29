import logging

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils import get_actor_email
from .filters import MedicalRecordFilter
from .models import MedicalRecord, RecordAttachment
from .serializers import (
    MedicalRecordSerializer,
    MedicalRecordListSerializer,
    RecordAttachmentSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=['Records'], summary='List medical records'),
    retrieve=extend_schema(tags=['Records'], summary='Retrieve a medical record'),
    create=extend_schema(
        tags=['Records'],
        summary='Create a new medical record',
        responses={
            201: MedicalRecordSerializer,
            400: OpenApiResponse(description='Validation error'),
            403: OpenApiResponse(description='Only doctors can create records'),
        },
    ),
    update=extend_schema(tags=['Records'], summary='Update a medical record'),
    partial_update=extend_schema(tags=['Records'], summary='Partially update a medical record'),
    destroy=extend_schema(
        tags=['Records'],
        summary='Delete a medical record',
        responses={204: OpenApiResponse(description='Record deleted')},
    ),
)
class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medical records.
    Only doctors should create/update; all authenticated staff can read.
    """

    queryset = MedicalRecord.objects.select_related('patient', 'doctor', 'appointment')
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = MedicalRecordFilter
    search_fields = [
        'patient__first_name',
        'patient__last_name',
        'patient__cpf',
        'diagnosis',
        'icd10_code',
        'chief_complaint']
    ordering_fields = ['created_at', 'patient__last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return MedicalRecordListSerializer
        return MedicalRecordSerializer

    def get_queryset(self):
        return (
            MedicalRecord.objects
            .select_related('patient', 'doctor', 'appointment')
            .prefetch_related('attachments')
            .order_by('-created_at')
        )

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_doctor:
            raise PermissionDenied(
                detail='Only users with the doctor role can create medical records.',
                code='doctor_only',
            )
        record = serializer.save()
        actor_email = get_actor_email(user)
        logger.info(
            f'Medical record created by={actor_email} record_id={record.pk} '
            f'patient_id={record.patient_id} doctor_id={record.doctor_id}')

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_doctor:
            raise PermissionDenied(
                detail='Only users with the doctor role can update medical records.',
                code='doctor_only',
            )
        serializer.save()

    @extend_schema(
        tags=['Records'],
        summary='Upload an attachment to a medical record',
        request=RecordAttachmentSerializer,
        responses={
            201: RecordAttachmentSerializer,
            400: OpenApiResponse(description='Invalid file (size/type)'),
        },
    )
    @action(
        detail=True,
        methods=['post'],
        url_path='attachments',
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_attachment(self, request, pk=None):
        """Upload a file (exam result, image, prescription, etc.) to a record."""
        record = self.get_object()
        serializer = RecordAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(record=record, uploaded_by=request.user)
        actor_email = get_actor_email(request.user)
        logger.info(
            f'Record attachment uploaded by={actor_email} record_id={record.pk} '
            f'attachment_id={attachment.pk} filename={attachment.file.name}')
        return Response(
            RecordAttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=['Records'],
        summary='List attachments of a medical record',
        responses={200: RecordAttachmentSerializer(many=True)},
    )
    @action(detail=True, methods=['get'], url_path='attachments')
    def list_attachments(self, request, pk=None):
        """List all file attachments linked to this medical record."""
        record = self.get_object()
        attachments = record.attachments.all()
        actor_email = get_actor_email(request.user)
        logger.info(
            f'Record attachments listed by={actor_email} record_id={record.pk} '
            f'attachments_count={attachments.count()}')
        serializer = RecordAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)


@extend_schema(tags=['Records'])
class RecordAttachmentViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Delete a specific attachment from a medical record."""
    queryset = RecordAttachment.objects.all()
    serializer_class = RecordAttachmentSerializer
    permission_classes = [IsAuthenticated]
