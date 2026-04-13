from datetime import timedelta

from django.db import models
from django.utils import timezone


class AppointmentQuerySet(models.QuerySet):
	"""Reusable, chainable query methods for Appointment."""

	def with_relations(self):
		return self.select_related('patient', 'doctor', 'created_by')

	def for_doctor(self, doctor):
		return self.filter(doctor=doctor)

	def for_patient(self, patient):
		return self.filter(patient=patient)

	def by_status(self, status):
		return self.filter(status=status)

	def pending(self):
		"""Appointments that are scheduled or confirmed (awaiting attendance)."""
		return self.filter(status__in=['scheduled', 'confirmed'])

	def completed(self):
		return self.filter(status='completed')

	def cancelled(self):
		return self.filter(status='cancelled')

	def in_progress(self):
		return self.filter(status='in_progress')

	def today(self):
		"""Appointments scheduled for today (local timezone)."""
		return self.filter(scheduled_at__date=timezone.localdate())

	def upcoming(self):
		"""Future appointments that are still pending."""
		return self.pending().filter(scheduled_at__gte=timezone.now())

	def past(self):
		"""Appointments whose scheduled time has already passed."""
		return self.filter(scheduled_at__lt=timezone.now())

	def date_range(self, start, end):
		return self.filter(scheduled_at__date__gte=start, scheduled_at__date__lte=end)

	def on_date(self, date):
		return self.filter(scheduled_at__date=date)

	def by_type(self, appointment_type):
		return self.filter(appointment_type=appointment_type)

	def emergencies(self):
		return self.filter(appointment_type='emergency')

	def no_show_candidates(self, hours=2):
		"""
		Pending appointments whose scheduled time has passed by more than
		``hours`` hours -- candidates for automatic NO_SHOW marking.
		"""
		threshold = timezone.now() - timedelta(hours=hours)
		return self.pending().filter(scheduled_at__lte=threshold)

	def ordered(self):
		return self.order_by('-scheduled_at')


class AppointmentManager(models.Manager):
	"""Custom manager for Appointment with chainable QuerySet helpers."""

	def get_queryset(self) -> AppointmentQuerySet:
		return AppointmentQuerySet(self.model, using=self._db)

	def with_relations(self):
		return self.get_queryset().with_relations()

	def for_doctor(self, doctor):
		return self.get_queryset().for_doctor(doctor)

	def for_patient(self, patient):
		return self.get_queryset().for_patient(patient)

	def by_status(self, status):
		return self.get_queryset().by_status(status)

	def pending(self):
		return self.get_queryset().pending()

	def completed(self):
		return self.get_queryset().completed()

	def cancelled(self):
		return self.get_queryset().cancelled()

	def in_progress(self):
		return self.get_queryset().in_progress()

	def today(self):
		return self.get_queryset().today()

	def upcoming(self):
		return self.get_queryset().upcoming()

	def past(self):
		return self.get_queryset().past()

	def date_range(self, start, end):
		return self.get_queryset().date_range(start, end)

	def on_date(self, date):
		return self.get_queryset().on_date(date)

	def by_type(self, appointment_type):
		return self.get_queryset().by_type(appointment_type)

	def emergencies(self):
		return self.get_queryset().emergencies()

	def no_show_candidates(self, hours=2):
		return self.get_queryset().no_show_candidates(hours)

	def ordered(self):
		return self.get_queryset().ordered()
