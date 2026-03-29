import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str:
    """Return the real client IP, respecting X-Forwarded-For from proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '-')


def get_actor_email(user) -> str:
    return getattr(user, 'email', None) or 'anonymous'


def send_notification_email(
        *,
        subject: str,
        body: str,
        recipient_list: list[str],
        log_context: str = '',
) -> None:
    """
    Send an email using Django's send_mail with standardised logging.

    Raises the original exception on failure (so Celery can auto-retry).

    Args:
        subject: Email subject line.
        body: Plain-text email body.
        recipient_list: List of recipient email addresses.
        log_context: Short string appended to log messages for traceability
                     (e.g. "appointment_id=42").
    """
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception:
        logger.exception(f'Email send error {log_context}')
        raise

    logger.info('Email sent to=%s %s', recipient_list, log_context)


def format_datetime_br(dt) -> str:
    """
    Format a datetime to the Brazilian pattern ``dd/mm/YYYY às HH:MM``.

    Automatically converts to the local timezone defined in settings.
    Returns an empty string if *dt* is None.
    """
    if dt is None:
        return ''
    local_dt = timezone.localtime(dt)
    return local_dt.strftime('%d/%m/%Y às %H:%M')


def calculate_age(date_of_birth: date) -> int:
    """
    Calculate the age in full years from a date of birth.

    Can be reused by models, serializers, and filters that need the same logic.
    """
    today = date.today()
    return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def age_cutoff_date(years: int) -> date:
    """
    Return the date-of-birth cutoff to filter people who are at least
    *years* old (``dob <= cutoff``) or at most *years* old (``dob >= cutoff``).

    Example usage in filters:
        queryset.filter(date_of_birth__lte=age_cutoff_date(18))  # 18+
    """
    return date.today() - relativedelta(years=years)
