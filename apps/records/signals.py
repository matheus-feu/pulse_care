import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MedicalRecord

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MedicalRecord, dispatch_uid='records.medical_record_post_save_notify_doctor')
def medical_record_post_save_notify_doctor(sender, instance: MedicalRecord, created: bool, **kwargs):
    """Queue doctor notification when a new medical record is created."""
    if not created:
        return

    from .tasks import notify_doctor_record_created

    transaction.on_commit(lambda: notify_doctor_record_created.delay(instance.pk))
    logger.info(f'Signal queued medical record notification task record_id={instance.pk}')

