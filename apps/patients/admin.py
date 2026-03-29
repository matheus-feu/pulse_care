from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'cpf', 'date_of_birth', 'age', 'gender',
        'phone', 'blood_type', 'is_active', 'created_at',
    ]
    list_filter = ['gender', 'blood_type', 'is_active', 'state']
    search_fields = ['first_name', 'last_name', 'cpf', 'email', 'phone']
    ordering = ['last_name', 'first_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'cpf', 'rg'),
        }),
        ('Contact', {
            'fields': ('phone', 'email'),
        }),
        ('Address', {
            'fields': ('zip_code', 'street', 'number', 'complement', 'neighborhood', 'city', 'state'),
            'classes': ('collapse',),
        }),
        ('Medical Information', {
            'fields': ('blood_type', 'allergies', 'chronic_conditions', 'current_medications', 'notes'),
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'),
            'classes': ('collapse',),
        }),
        ('Insurance', {
            'fields': ('insurance_provider', 'insurance_plan', 'insurance_number'),
            'classes': ('collapse',),
        }),
        ('Meta', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

