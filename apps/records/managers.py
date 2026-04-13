from django.db import models


class MedicalRecordQuerySet(models.QuerySet):
	"""Reusable, chainable query methods for MedicalRecord."""

	def with_relations(self):
		return self.select_related('patient', 'doctor', 'appointment')

	def with_attachments(self):
		return self.prefetch_related('attachments')

	def with_attachment_count(self):
		return self.annotate(
			attachments_count=models.Count('attachments', distinct=True),
		)

	def for_patient(self, patient):
		return self.filter(patient=patient)

	def for_doctor(self, doctor):
		return self.filter(doctor=doctor)

	def by_icd10(self, code):
		return self.filter(icd10_code__icontains=code)

	def search_by_diagnosis(self, term):
		return self.filter(
			models.Q(diagnosis__icontains=term)
			| models.Q(chief_complaint__icontains=term)
		)

	def with_follow_up(self):
		"""Records that have a follow-up recommendation."""
		return self.filter(follow_up_in_days__isnull=False)

	def with_referrals(self):
		"""Records that include referrals."""
		return self.exclude(
			models.Q(referrals__isnull=True) | models.Q(referrals='')
		)

	def with_prescription(self):
		"""Records that include a prescription."""
		return self.exclude(
			models.Q(prescription__isnull=True) | models.Q(prescription='')
		)

	def ordered(self):
		return self.order_by('-created_at')


class MedicalRecordManager(models.Manager):
	"""Custom manager for MedicalRecord with chainable QuerySet helpers."""

	def get_queryset(self) -> MedicalRecordQuerySet:
		return MedicalRecordQuerySet(self.model, using=self._db)

	def with_relations(self):
		return self.get_queryset().with_relations()

	def with_attachments(self):
		return self.get_queryset().with_attachments()

	def with_attachment_count(self):
		return self.get_queryset().with_attachment_count()

	def for_patient(self, patient):
		return self.get_queryset().for_patient(patient)

	def for_doctor(self, doctor):
		return self.get_queryset().for_doctor(doctor)

	def by_icd10(self, code):
		return self.get_queryset().by_icd10(code)

	def search_by_diagnosis(self, term):
		return self.get_queryset().search_by_diagnosis(term)

	def with_follow_up(self):
		return self.get_queryset().with_follow_up()

	def with_referrals(self):
		return self.get_queryset().with_referrals()

	def with_prescription(self):
		return self.get_queryset().with_prescription()

	def ordered(self):
		return self.get_queryset().ordered()


class RecordAttachmentQuerySet(models.QuerySet):
	"""Reusable, chainable query methods for RecordAttachment."""

	def for_record(self, record):
		return self.filter(record=record)

	def by_type(self, attachment_type):
		return self.filter(attachment_type=attachment_type)

	def exam_results(self):
		return self.filter(attachment_type='exam_result')

	def prescriptions(self):
		return self.filter(attachment_type='prescription')

	def images(self):
		return self.filter(attachment_type='image')

	def uploaded_by_user(self, user):
		return self.filter(uploaded_by=user)


class RecordAttachmentManager(models.Manager):
	"""Custom manager for RecordAttachment with chainable QuerySet helpers."""

	def get_queryset(self) -> RecordAttachmentQuerySet:
		return RecordAttachmentQuerySet(self.model, using=self._db)

	def for_record(self, record):
		return self.get_queryset().for_record(record)

	def by_type(self, attachment_type):
		return self.get_queryset().by_type(attachment_type)

	def exam_results(self):
		return self.get_queryset().exam_results()

	def prescriptions(self):
		return self.get_queryset().prescriptions()

	def images(self):
		return self.get_queryset().images()

	def uploaded_by_user(self, user):
		return self.get_queryset().uploaded_by_user(user)
