from django.utils import timezone
from rest_framework import serializers

from apps.patients.serializers import PatientListSerializer
from apps.users.serializers import UserSerializer
from .models import Appointment

VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    Appointment.Status.SCHEDULED: {
        Appointment.Status.CONFIRMED,
        Appointment.Status.CANCELLED,
    },
    Appointment.Status.CONFIRMED: {
        Appointment.Status.IN_PROGRESS,
        Appointment.Status.CANCELLED,
        Appointment.Status.NO_SHOW,
    },
    Appointment.Status.IN_PROGRESS: {
        Appointment.Status.COMPLETED,
        Appointment.Status.CANCELLED,
    },
    Appointment.Status.COMPLETED: set(),
    Appointment.Status.CANCELLED: set(),
    Appointment.Status.NO_SHOW: set(),
}


class AppointmentSerializer(serializers.ModelSerializer):
    patient_detail = PatientListSerializer(source='patient', read_only=True)
    doctor_detail = UserSerializer(source='doctor', read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate_scheduled_at(self, value):
        """Appointments must be scheduled in the future."""
        if value <= timezone.now():
            raise serializers.ValidationError(
                'The appointment must be scheduled for a future date/time.',
                code='scheduled_in_past',
            )
        return value

    def validate_doctor(self, value):
        """Only active users with the 'doctor' role can be assigned."""
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
        doctor = attrs.get('doctor', getattr(self.instance, 'doctor', None))
        scheduled_at = attrs.get('scheduled_at', getattr(self.instance, 'scheduled_at', None))
        duration = attrs.get('duration_minutes', getattr(self.instance, 'duration_minutes', 30))

        if doctor and scheduled_at:
            from datetime import timedelta
            start = scheduled_at
            end = scheduled_at + timedelta(minutes=duration)

            overlap_qs = Appointment.objects.filter(
                doctor=doctor,
                status__in=[
                    Appointment.Status.SCHEDULED,
                    Appointment.Status.CONFIRMED,
                    Appointment.Status.IN_PROGRESS,
                ],
                scheduled_at__lt=end,
            ).exclude(
                scheduled_at__lte=start - timedelta(minutes=1),
            )

            if self.instance:
                overlap_qs = overlap_qs.exclude(pk=self.instance.pk)

            if overlap_qs.exists():
                raise serializers.ValidationError(
                    {'scheduled_at': 'This doctor already has an appointment during this time slot.'},
                    code='schedule_conflict',
                )

        return attrs


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list and nested views."""
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'scheduled_at', 'duration_minutes', 'appointment_type',
            'status', 'reason',
        ]


class AppointmentStatusSerializer(serializers.ModelSerializer):
    """Used only for status transitions with validation."""

    class Meta:
        model = Appointment
        fields = ['status', 'cancellation_reason', 'notes']

    def validate_status(self, value):
        """Enforce valid status transitions."""
        if not self.instance:
            return value

        current = self.instance.status
        allowed = VALID_STATUS_TRANSITIONS.get(current, set())

        if value not in allowed:
            allowed_display = ', '.join(sorted(allowed)) or 'none (terminal state)'
            raise serializers.ValidationError(
                f'Cannot transition from "{current}" to "{value}". '
                f'Allowed transitions: {allowed_display}.',
                code='invalid_status_transition',
            )
        return value

    def validate(self, attrs):
        new_status = attrs.get('status')
        cancellation_reason = attrs.get('cancellation_reason')

        if new_status == Appointment.Status.CANCELLED and not cancellation_reason:
            raise serializers.ValidationError(
                {'cancellation_reason': 'A cancellation reason is required when cancelling an appointment.'},
                code='cancellation_reason_required',
            )

        return attrs
