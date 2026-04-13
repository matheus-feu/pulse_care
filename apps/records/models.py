from django.db import models
from django.conf import settings
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from .managers import MedicalRecordManager, RecordAttachmentManager


class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_records',
    )
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medical_record',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_records_created',
        limit_choices_to={'role': 'doctor'},
    )

    # Clinical assessment
    chief_complaint = models.TextField(help_text='Main reason for the visit')
    history_of_present_illness = models.TextField(blank=True, null=True)
    physical_examination = models.TextField(blank=True, null=True)

    # Vital signs
    blood_pressure = models.CharField(max_length=20, blank=True, null=True, help_text='e.g. 120/80 mmHg')
    heart_rate = models.PositiveSmallIntegerField(blank=True, null=True, help_text='bpm')
    respiratory_rate = models.PositiveSmallIntegerField(blank=True, null=True, help_text='breaths/min')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, help_text='°C')
    oxygen_saturation = models.PositiveSmallIntegerField(blank=True, null=True, help_text='%')
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='kg')
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='cm')

    # Diagnosis and treatment
    diagnosis = models.TextField()
    icd10_code = models.CharField(max_length=10, blank=True, null=True, verbose_name='ICD-10 Code')
    prescription = models.TextField(blank=True, null=True)
    treatment_plan = models.TextField(blank=True, null=True)
    referrals = models.TextField(blank=True, null=True, help_text='Referrals to specialists or exams')
    follow_up_in_days = models.PositiveSmallIntegerField(blank=True, null=True, help_text='Follow-up in X days')
    notes = models.TextField(blank=True, null=True, help_text='Additional notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MedicalRecordManager()

    class Meta:
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
        ordering = ['-created_at']

    def __str__(self):
        return f'Record #{self.pk} — {self.patient.full_name} ({self.created_at:%d/%m/%Y})'

    @property
    def bmi(self):
        if self.weight and self.height and self.height > 0:
            height_m = float(self.height) / 100
            return round(float(self.weight) / (height_m ** 2), 1)
        return None


class RecordAttachment(models.Model):
    class AttachmentType(models.TextChoices):
        EXAM_RESULT = 'exam_result', 'Exam Result'
        IMAGE = 'image', 'Image'
        PRESCRIPTION = 'prescription', 'Prescription'
        REFERRAL = 'referral', 'Referral'
        OTHER = 'other', 'Other'

    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    file = models.FileField(upload_to='records/attachments/%Y/%m/')
    attachment_type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices,
        default=AttachmentType.OTHER,
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='record_attachments',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    objects = RecordAttachmentManager()

    class Meta:
        verbose_name = 'Record Attachment'
        verbose_name_plural = 'Record Attachments'

    def __str__(self):
        return f'{self.get_attachment_type_display()} — Record #{self.record_id}'

