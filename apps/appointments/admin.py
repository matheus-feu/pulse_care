from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'doctor', 'scheduled_at', 'duration_minutes',
        'appointment_type', 'status', 'created_at',
    ]
    list_filter = ['status', 'appointment_type', 'scheduled_at']
    search_fields = ['patient__first_name', 'patient__last_name', 'patient__cpf', 'reason']
    ordering = ['-scheduled_at']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    autocomplete_fields = ['patient', 'doctor']

    fieldsets = (
        ('Appointment', {
            'fields': ('patient', 'doctor', 'scheduled_at', 'duration_minutes', 'appointment_type', 'status'),
        }),
        ('Details', {
            'fields': ('reason', 'notes', 'cancellation_reason'),
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

