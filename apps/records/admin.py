from django.contrib import admin
from .models import MedicalRecord, RecordAttachment


class RecordAttachmentInline(admin.TabularInline):
    model = RecordAttachment
    extra = 0
    readonly_fields = ['uploaded_by', 'uploaded_at']
    fields = ['file', 'attachment_type', 'description', 'uploaded_by', 'uploaded_at']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'patient', 'doctor', 'chief_complaint', 'diagnosis',
        'icd10_code', 'created_at',
    ]
    list_filter = ['doctor', 'created_at']
    search_fields = [
        'patient__first_name', 'patient__last_name', 'patient__cpf',
        'diagnosis', 'icd10_code', 'chief_complaint',
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [RecordAttachmentInline]

    fieldsets = (
        ('Patient & Doctor', {
            'fields': ('patient', 'doctor', 'appointment'),
        }),
        ('Clinical Assessment', {
            'fields': ('chief_complaint', 'history_of_present_illness', 'physical_examination'),
        }),
        ('Vital Signs', {
            'fields': (
                'blood_pressure', 'heart_rate', 'respiratory_rate',
                'temperature', 'oxygen_saturation', 'weight', 'height',
            ),
            'classes': ('collapse',),
        }),
        ('Diagnosis & Treatment', {
            'fields': ('diagnosis', 'icd10_code', 'prescription', 'treatment_plan', 'referrals', 'follow_up_in_days'),
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(RecordAttachment)
class RecordAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'attachment_type', 'description', 'uploaded_by', 'uploaded_at']
    list_filter = ['attachment_type']
    readonly_fields = ['uploaded_at', 'uploaded_by']

