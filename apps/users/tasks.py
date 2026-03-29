import logging

from celery import shared_task

from core.utils import send_notification_email

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    name='users.send_welcome_email',
)
def send_welcome_email(self, user_id: int) -> dict:
    """
    Send a welcome / onboarding email to a newly created staff member.
    """
    from apps.users.models import User

    logger.info('Task start users.send_welcome_email task_id=%s user_id=%s', self.request.id, user_id)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.info('Task skip users.send_welcome_email user_id=%s reason=not_found', user_id)
        return {'status': 'skipped', 'reason': 'not_found'}

    if not user.email:
        logger.info('Task skip users.send_welcome_email user_id=%s reason=no_email', user_id)
        return {'status': 'skipped', 'reason': 'no_email'}

    subject = '[PulseCare] Welcome to the team!'
    body = (
        f'Hello, {user.first_name}!\n\n'
        f'Your PulseCare account has been created successfully.\n\n'
        f'  Role   : {user.get_role_display()}\n'
        f'  Email  : {user.email}\n\n'
        f'Please log in and change your password on first access.\n\n'
        f'PulseCare Team'
    )

    send_notification_email(
        subject=subject,
        body=body,
        recipient_list=[user.email],
        log_context=f'users.send_welcome_email user_id={user_id}',
    )

    logger.info('Task success users.send_welcome_email user_id=%s email=%s', user_id, user.email)
    return {'status': 'sent', 'user_id': user_id, 'email': user.email}
