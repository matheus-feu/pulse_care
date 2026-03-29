import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Appointment, dispatch_uid='appointments.appointment_pre_save_track_status')
def appointment_pre_save_track_status(sender, instance: Appointment, **kwargs):
    """Cache previous status so we can react to status transitions in post_save."""
    if not instance.pk:
        instance._previous_status = None
        return
    instance._previous_status = (
        sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    )


@receiver(post_save, sender=Appointment, dispatch_uid='appointments.appointment_post_save_notifications')
def appointment_post_save_notifications(sender, instance: Appointment, created: bool, **kwargs):
    """Queue confirmation and reminder tasks for appointment lifecycle events."""
    from .tasks import send_appointment_confirmation, send_appointment_reminder

    if created:
        transaction.on_commit(lambda: send_appointment_confirmation.delay(instance.pk))
        logger.info(f'Signal queued confirmation task appointment_id={instance.pk}')

    previous_status = getattr(instance, '_previous_status', None)
    became_confirmed = instance.status == Appointment.Status.CONFIRMED and previous_status != Appointment.Status.CONFIRMED
    if not became_confirmed:
        return

    hours_before = getattr(settings, 'APPOINTMENT_REMINDER_HOURS_BEFORE', 24)
    eta = instance.scheduled_at - timedelta(hours=hours_before)
    if eta <= timezone.now():
        logger.info(f'Signal skipped reminder scheduling appointment_id={instance.pk} reason=eta_in_past eta={eta}')
        return

    transaction.on_commit(lambda: send_appointment_reminder.apply_async(args=[instance.pk], eta=eta))
    logger.info(f'Signal queued reminder task appointment_id={instance.pk} eta={eta}')
