import logging

from celery import shared_task

from core.utils import format_datetime_br, send_notification_email

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    name='records.notify_doctor_record_created',
)
def notify_doctor_record_created(self, record_id: int) -> dict:
    """
    Notify the responsible doctor that a new medical record has been registered.
    """
    from apps.records.models import MedicalRecord

    logger.info(f'Task start records.notify_doctor_record_created task_id={self.request.id} record_id={record_id}')

    try:
        record = (
            MedicalRecord.objects
            .select_related('patient', 'doctor')
            .get(pk=record_id)
        )
    except MedicalRecord.DoesNotExist:
        logger.info(f'Task skip records.notify_doctor_record_created record_id={record_id} reason=not_found')
        return {'status': 'skipped', 'reason': 'not_found'}

    if not record.doctor or not record.doctor.email:
        logger.info(f'Task skip records.notify_doctor_record_created record_id={record_id} reason=no_doctor_email')
        return {'status': 'skipped', 'reason': 'no_doctor_email'}

    subject = f'[PulseCare] New medical record — {record.patient.full_name}'
    body = (
        f'Hello, Dr. {record.doctor.last_name}!\n\n'
        f'A new medical record has been registered for:\n\n'
        f'  Patient   : {record.patient.full_name}\n'
        f'  Complaint : {record.chief_complaint}\n'
        f'  Diagnosis : {record.diagnosis}\n'
        f'  Created   : {format_datetime_br(record.created_at)}\n\n'
        f'Log in to PulseCare to review the full record.\n\n'
        f'PulseCare Team'
    )

    send_notification_email(
        subject=subject,
        body=body,
        recipient_list=[record.doctor.email],
        log_context=f'records.notify_doctor_record_created record_id={record_id}',
    )

    logger.info(
        f'Task success records.notify_doctor_record_created record_id={record_id} doctor_email={record.doctor.email}')
    return {'status': 'sent', 'record_id': record_id}
