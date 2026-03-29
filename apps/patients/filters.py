import django_filters

from core.utils import age_cutoff_date
from .models import Patient


class PatientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_by_name', label='Full name (partial)')
    age_min = django_filters.NumberFilter(field_name='date_of_birth', lookup_expr='lte', method='filter_age_min',
                                          label='Minimum age')
    age_max = django_filters.NumberFilter(field_name='date_of_birth', lookup_expr='gte', method='filter_age_max',
                                          label='Maximum age')
    city = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(lookup_expr='iexact')
    blood_type = django_filters.ChoiceFilter(choices=Patient.BloodType.choices)
    gender = django_filters.ChoiceFilter(choices=Patient.Gender.choices)
    has_insurance = django_filters.BooleanFilter(method='filter_has_insurance', label='Has insurance')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = Patient
        fields = ['gender', 'blood_type', 'city', 'state', 'is_active']

    def filter_by_name(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(Q(first_name__icontains=value) | Q(last_name__icontains=value))

    def filter_age_min(self, queryset, name, value):
        return queryset.filter(date_of_birth__lte=age_cutoff_date(int(value)))

    def filter_age_max(self, queryset, name, value):
        return queryset.filter(date_of_birth__gte=age_cutoff_date(int(value)))

    def filter_has_insurance(self, queryset, name, value):
        if value:
            return queryset.exclude(insurance_provider__isnull=True).exclude(insurance_provider='')
        return queryset.filter(insurance_provider__isnull=True)
