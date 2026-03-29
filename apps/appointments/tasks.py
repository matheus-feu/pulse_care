import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from core.utils import format_datetime_br, send_notification_email

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='appointments.send_appointment_reminder',
)
def send_appointment_reminder(self, appointment_id: int) -> dict:
    """
    Send an email reminder to the patient N hours before their appointment.
    Configured via APPOINTMENT_REMINDER_HOURS_BEFORE setting.
    """
    from apps.appointments.models import Appointment

    logger.info(f'Task start appointments.send_appointment_reminder task_id={self.request.id} appointment_id={appointment_id}')
    try:
        appointment = (
            Appointment.objects
            .select_related('patient', 'doctor')
            .get(pk=appointment_id)
        )
    except Appointment.DoesNotExist:
        logger.info(f'Task skip appointments.send_appointment_reminder appointment_id={appointment_id} reason=not_found')
        return {'status': 'skipped', 'reason': 'not_found'}

    if appointment.status != Appointment.Status.CONFIRMED:
        logger.info(f'Task skip appointments.send_appointment_reminder appointment_id=%s reason=not_confirmed status=%s', appointment_id, appointment.status)
        return {'status': 'skipped', 'reason': 'not_confirmed'}

    patient = appointment.patient
    if not patient.email:
        logger.info('Task skip appointments.send_appointment_reminder appointment_id=%s reason=no_patient_email', appointment_id)
        return {'status': 'skipped', 'reason': 'no_patient_email'}

    formatted_dt = format_datetime_br(appointment.scheduled_at)
    subject = f'[PulseCare] Appointment reminder — {formatted_dt}'
    body = (
        f'Hello, {patient.first_name}!\n\n'
        f'This is a reminder that you have an appointment scheduled for:\n\n'
        f'  Date/Time : {formatted_dt}\n'
        f'  Doctor    : {appointment.doctor.get_full_name()}\n'
        f'  Type      : {appointment.get_appointment_type_display()}\n\n'
        f'If you need to reschedule or cancel, please contact us as soon as possible.\n\n'
        f'PulseCare Team'
    )

    send_notification_email(
        subject=subject,
        body=body,
        recipient_list=[patient.email],
        log_context=f'appointments.send_appointment_reminder appointment_id={appointment_id}',
    )

    logger.info('Task success appointments.send_appointment_reminder appointment_id=%s email=%s', appointment_id, patient.email)
    return {'status': 'sent', 'appointment_id': appointment_id, 'email': patient.email}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='appointments.send_appointment_confirmation',
)
def send_appointment_confirmation(self, appointment_id: int) -> dict:
    """
    Send a booking confirmation email to the patient right after scheduling.
    """
    from apps.appointments.models import Appointment

    logger.info('Task start appointments.send_appointment_confirmation task_id=%s appointment_id=%s', self.request.id, appointment_id)

    try:
        appointment = (
            Appointment.objects
            .select_related('patient', 'doctor')
            .get(pk=appointment_id)
        )
    except Appointment.DoesNotExist:
        logger.info('Task skip appointments.send_appointment_confirmation appointment_id=%s reason=not_found', appointment_id)
        return {'status': 'skipped', 'reason': 'not_found'}

    patient = appointment.patient
    if not patient.email:
        logger.info('Task skip appointments.send_appointment_confirmation appointment_id=%s reason=no_patient_email', appointment_id)
        return {'status': 'skipped', 'reason': 'no_patient_email'}

    formatted_dt = format_datetime_br(appointment.scheduled_at)
    subject = f'[PulseCare] Appointment confirmed — {formatted_dt}'
    body = (
        f'Hello, {patient.first_name}!\n\n'
        f'Your appointment has been successfully scheduled.\n\n'
        f'  Date/Time : {formatted_dt}\n'
        f'  Doctor    : {appointment.doctor.get_full_name()}\n'
        f'  Type      : {appointment.get_appointment_type_display()}\n'
        f'  Reason    : {appointment.reason}\n\n'
        f'Please arrive 10 minutes early.\n\n'
        f'PulseCare Team'
    )

    send_notification_email(
        subject=subject,
        body=body,
        recipient_list=[patient.email],
        log_context=f'appointments.send_appointment_confirmation appointment_id={appointment_id}',
    )

    logger.info('Task success appointments.send_appointment_confirmation appointment_id=%s', appointment_id)
    return {'status': 'sent', 'appointment_id': appointment_id}


@shared_task(name='appointments.cancel_no_show_appointments')
def cancel_no_show_appointments() -> dict:
    """
    Periodic task (run by Celery Beat) that marks appointments as NO_SHOW
    when they are still CONFIRMED/SCHEDULED and their time has passed by
    more than 2 hours without being completed.
    """
    from apps.appointments.models import Appointment

    logger.info('Task start appointments.cancel_no_show_appointments')

    threshold = timezone.now() - timedelta(hours=2)
    pending_statuses = [Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]

    updated = (
        Appointment.objects
        .filter(status__in=pending_statuses, scheduled_at__lte=threshold)
        .update(status=Appointment.Status.NO_SHOW)
    )

    logger.info(f'Task success appointments.cancel_no_show_appointments marked_no_show={updated}')
    return {'status': 'ok', 'marked_no_show': updated}
