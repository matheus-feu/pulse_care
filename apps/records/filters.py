import django_filters

from .models import MedicalRecord


class MedicalRecordFilter(django_filters.FilterSet):
    patient = django_filters.NumberFilter(field_name='patient_id')
    doctor = django_filters.NumberFilter(field_name='doctor_id')
    appointment = django_filters.NumberFilter(field_name='appointment_id')
    icd10_code = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateFilter(
        field_name='created_at', lookup_expr='date__gte',
        label='Created from (YYYY-MM-DD)'
    )
    created_before = django_filters.DateFilter(
        field_name='created_at', lookup_expr='date__lte',
        label='Created until (YYYY-MM-DD)'
    )

    class Meta:
        model = MedicalRecord
        fields = ['patient', 'doctor', 'appointment', 'icd10_code']
