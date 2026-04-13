from django.db import models
from django.conf import settings
from apps.patients.models import Patient
from .managers import AppointmentManager


class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CONFIRMED = 'confirmed', 'Confirmed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    class AppointmentType(models.TextChoices):
        CONSULTATION = 'consultation', 'Consultation'
        FOLLOW_UP = 'follow_up', 'Follow-up'
        EXAM = 'exam', 'Exam'
        PROCEDURE = 'procedure', 'Procedure'
        EMERGENCY = 'emergency', 'Emergency'
        TELEMEDICINE = 'telemedicine', 'Telemedicine'

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments_as_doctor',
        limit_choices_to={'role': 'doctor'},
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=30, help_text='Duration in minutes')
    appointment_type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.CONSULTATION,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    reason = models.TextField(help_text='Reason for the appointment')
    notes = models.TextField(blank=True, null=True, help_text='Internal notes')
    cancellation_reason = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AppointmentManager()

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'{self.patient.full_name} — {self.doctor} @ {self.scheduled_at:%d/%m/%Y %H:%M}'

