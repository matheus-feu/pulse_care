from django.conf import settings
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.users.serializers import UserSerializer
from apps.patients.serializers import PatientListSerializer
from .models import MedicalRecord, RecordAttachment

# 10 MB default limit
MAX_ATTACHMENT_SIZE_MB = getattr(settings, 'MAX_ATTACHMENT_SIZE_MB', 10)

ALLOWED_ATTACHMENT_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp',
    '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt',
}


class RecordAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RecordAttachment
        fields = ['id', 'file', 'attachment_type', 'description', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']

    def validate_file(self, value):
        # Size check
        max_bytes = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError(
                f'File size exceeds the {MAX_ATTACHMENT_SIZE_MB} MB limit.',
                code='file_too_large',
            )
        # Extension check
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
            raise serializers.ValidationError(
                f'File type "{ext}" is not allowed. '
                f'Accepted: {", ".join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))}.',
                code='file_type_not_allowed',
            )
        return value


class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_detail = PatientListSerializer(source='patient', read_only=True)
    doctor_detail = UserSerializer(source='doctor', read_only=True)
    attachments = RecordAttachmentSerializer(many=True, read_only=True)
    bmi = serializers.SerializerMethodField()

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_bmi(self, obj):
        return obj.bmi

    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate_doctor(self, value):
        if value is None:
            return value
        if not value.is_active:
            raise serializers.ValidationError(
                'The selected doctor is inactive.',
                code='doctor_inactive',
            )
        if value.role != 'doctor':
            raise serializers.ValidationError(
                'The selected user does not have the doctor role.',
                code='not_a_doctor',
            )
        return value

    def validate_patient(self, value):
        if value is not None and not value.is_active:
            raise serializers.ValidationError(
                'The selected patient is inactive.',
                code='patient_inactive',
            )
        return value

    def validate(self, attrs):
        appointment = attrs.get('appointment')
        patient = attrs.get('patient', getattr(self.instance, 'patient', None))

        # If linking to an appointment, the patient must match
        if appointment and patient and appointment.patient_id != patient.pk:
            raise serializers.ValidationError(
                {'appointment': 'The appointment does not belong to the selected patient.'},
                code='appointment_patient_mismatch',
            )

        # Prevent duplicate records for the same appointment
        if appointment:
            qs = MedicalRecord.objects.filter(appointment=appointment)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'appointment': 'A medical record already exists for this appointment.'},
                    code='record_already_exists',
                )

        return attrs


class MedicalRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list and nested views."""
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    attachments_count = serializers.SerializerMethodField()

    @extend_schema_field(serializers.IntegerField())
    def get_attachments_count(self, obj):
        return int(getattr(obj, 'attachments_count', 0) or 0)

    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'chief_complaint', 'diagnosis', 'icd10_code', 'created_at',
            'attachments_count',
        ]
