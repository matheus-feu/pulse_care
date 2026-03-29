import django_filters

from .models import Appointment


class AppointmentFilter(django_filters.FilterSet):
    patient = django_filters.NumberFilter(field_name='patient_id')
    doctor = django_filters.NumberFilter(field_name='doctor_id')
    status = django_filters.ChoiceFilter(choices=Appointment.Status.choices)
    appointment_type = django_filters.ChoiceFilter(choices=Appointment.AppointmentType.choices)
    date_from = django_filters.DateFilter(
        field_name='scheduled_at', lookup_expr='date__gte',
        label='Scheduled from (YYYY-MM-DD)'
    )
    date_to = django_filters.DateFilter(
        field_name='scheduled_at', lookup_expr='date__lte',
        label='Scheduled until (YYYY-MM-DD)'
    )
    date = django_filters.DateFilter(field_name='scheduled_at', lookup_expr='date', label='Exact date (YYYY-MM-DD)')

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'status', 'appointment_type']
