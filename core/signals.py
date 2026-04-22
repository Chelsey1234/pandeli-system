import logging

logger = logging.getLogger(__name__)

# Signals file intentionally left minimal.
# New-order notifications are handled by the notification_count poll
# in views.py (_create_missing_order_notifications) which is idempotent.
