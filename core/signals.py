import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='core.Order')
def order_post_save(sender, instance, created, **kwargs):
    """
    Fire a notification to all staff whenever a new order is created,
    regardless of how it was created (app, REST API, POS, webhook, admin).
    """
    if not created:
        return

    try:
        from .notifications import NotificationService
        NotificationService.notify_admins(
            title=f"🛒 New Order #{instance.order_number}",
            message=f"New {instance.get_order_type_display()} order received. Total: ₱{instance.total}",
            notification_type='order',
            priority='high',
            link=f'/orders/{instance.pk}/',
            action_text='View Order',
        )
        logger.info(f"New order notification sent for {instance.order_number}")
    except Exception as e:
        logger.error(f"Failed to send new order notification: {e}")
