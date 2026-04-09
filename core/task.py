from celery import shared_task
from django.utils import timezone
from .notifications import check_low_stock_and_notify, create_system_notification
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_low_stock_periodically():
    """
    Celery task to check for low stock every hour
    """
    try:
        count = check_low_stock_and_notify()
        logger.info(f"Low stock check completed. {count} notifications created.")
        return f"Created {count} notifications"
    except Exception as e:
        logger.error(f"Error in low stock check: {e}")
        return f"Error: {e}"


@shared_task
def cleanup_old_notifications(days=30):
    """
    Archive or delete notifications older than specified days
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    old_notifications = Notification.objects.filter(
        created_at__lt=cutoff_date,
        is_archived=False
    )
    
    count = old_notifications.update(is_archived=True)
    logger.info(f"Archived {count} old notifications")
    return f"Archived {count} notifications"