from django.db import models


class PatientQuerySet(models.QuerySet):
    """Reusable, chainable query methods for Patient."""

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def with_creator(self):
        return self.select_related('created_by')

    def with_stats(self):
        """Annotate with appointment and medical record counts."""
        return self.annotate(
            appointments_count=models.Count('appointments', distinct=True),
            medical_records_count=models.Count('medical_records', distinct=True),
        )

    def search_by_name(self, name):
        return self.filter(
            models.Q(first_name__icontains=name)
            | models.Q(last_name__icontains=name)
        )

    def with_insurance(self):
        return self.exclude(
            models.Q(insurance_provider__isnull=True)
            | models.Q(insurance_provider='')
        )

    def without_insurance(self):
        return self.filter(
            models.Q(insurance_provider__isnull=True)
            | models.Q(insurance_provider='')
        )

    def by_blood_type(self, blood_type):
        return self.filter(blood_type=blood_type)

    def by_gender(self, gender):
        return self.filter(gender=gender)

    def by_city(self, city):
        return self.filter(city__icontains=city)

    def by_state(self, state):
        return self.filter(state__iexact=state)

    def ordered(self):
        return self.order_by('last_name', 'first_name')


class PatientManager(models.Manager):
    """Custom manager for Patient with chainable QuerySet helpers."""

    def get_queryset(self) -> PatientQuerySet:
        return PatientQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()

    def with_creator(self):
        return self.get_queryset().with_creator()

    def with_stats(self):
        return self.get_queryset().with_stats()

    def search_by_name(self, name):
        return self.get_queryset().search_by_name(name)

    def with_insurance(self):
        return self.get_queryset().with_insurance()

    def without_insurance(self):
        return self.get_queryset().without_insurance()

    def by_blood_type(self, blood_type):
        return self.get_queryset().by_blood_type(blood_type)

    def by_gender(self, gender):
        return self.get_queryset().by_gender(gender)

    def by_city(self, city):
        return self.get_queryset().by_city(city)

    def by_state(self, state):
        return self.get_queryset().by_state(state)

    def ordered(self):
        return self.get_queryset().ordered()

