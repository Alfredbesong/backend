import logging

from firebase_admin import initialize_app, messaging

from apps.users.models import DeviceToken

logger = logging.getLogger(__name__)


_firebase_initialized = False


def _ensure_firebase_app() -> bool:
    global _firebase_initialized

    if _firebase_initialized:
        return True

    try:
        initialize_app()
        _firebase_initialized = True
        return True
    except Exception as error:
        logger.warning('Firebase admin was not initialized: %s', error)
        return False


def send_report_status_notification(report) -> None:
    if not _ensure_firebase_app():
        return

    tokens = list(
        DeviceToken.objects.filter(user=report.user, is_active=True).values_list('token', flat=True)
    )
    if not tokens:
        return

    title = 'Waste report updated'
    body = f'Your report #{report.id} is now {report.get_status_display()}.'

    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
            data={
                'report_id': str(report.id),
                'status': report.status,
            },
        )

        try:
            messaging.send(message)
        except Exception as error:
            logger.warning('Failed to send notification to %s: %s', token, error)
