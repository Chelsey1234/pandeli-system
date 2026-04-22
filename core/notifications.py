from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import F
from .models import Notification, Product, Order, RawMaterial
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service class for creating and managing notifications"""
    
    @staticmethod
    def create_notification(title, message, notification_type, recipient_type, 
                           recipient_user=None, recipient_customer=None, 
                           recipient_supplier=None, priority='medium', 
                           link='', action_text='', expires_in_days=7):
        """
        Create a new notification
        """
        try:
            expires_at = timezone.now() + timedelta(days=expires_in_days) if expires_in_days else None
            
            notification = Notification.objects.create(
                title=title,
                message=message,
                notification_type=notification_type,
                recipient_type=recipient_type,
                recipient_user=recipient_user,
                recipient_customer=recipient_customer,
                recipient_supplier=recipient_supplier,
                priority=priority,
                link=link,
                action_text=action_text,
                expires_at=expires_at
            )
            logger.info(f"Notification created: {title}")
            return notification
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    def notify_admins(title, message, notification_type='system', priority='medium', link='', action_text=''):
        """Send notification to all admin/manager/staff users who manage the web dashboard"""
        from .models import UserProfile
        from django.contrib.auth.models import User

        # Collect all users who should see admin notifications:
        # superusers + users with admin/production_admin/manager/cashier roles
        user_ids = set()

        # Superusers
        for uid in User.objects.filter(is_superuser=True).values_list('id', flat=True):
            user_ids.add(uid)

        # Staff roles
        for uid in UserProfile.objects.filter(
            role__in=['admin', 'production_admin', 'manager', 'cashier', 'staff']
        ).values_list('user_id', flat=True):
            user_ids.add(uid)

        for user in User.objects.filter(id__in=user_ids, is_active=True):
            NotificationService.create_notification(
                title=title,
                message=message,
                notification_type=notification_type,
                recipient_type='admin',
                recipient_user=user,
                priority=priority,
                link=link,
                action_text=action_text
            )

    @staticmethod
    def notify_staff(title, message, notification_type='system', priority='medium', link='', action_text=''):
        """Send notification to all staff users (alias for notify_admins for system messages)"""
        NotificationService.notify_admins(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            link=link,
            action_text=action_text
        )
    
    @staticmethod
    def notify_customer(customer, title, message, notification_type='order', priority='medium', link='', action_text=''):
        """Send notification to a specific customer"""
        if customer and customer.user:
            NotificationService.create_notification(
                title=title,
                message=message,
                notification_type=notification_type,
                recipient_type='customer',
                recipient_user=customer.user,
                recipient_customer=customer,
                priority=priority,
                link=link,
                action_text=action_text
            )
    
    @staticmethod
    def notify_supplier(supplier, title, message, notification_type='order', priority='medium', link='', action_text=''):
        """Send notification to a specific supplier"""
        NotificationService.create_notification(
            title=title,
            message=message,
            notification_type=notification_type,
            recipient_type='supplier',
            recipient_supplier=supplier,
            priority=priority,
            link=link,
            action_text=action_text
        )


def check_low_stock_and_notify():
    """
    Check for low stock items and create notifications
    Run this periodically via cron job or Celery
    """
    notifications_created = 0
    
    # Check products
    low_stock_products = Product.objects.filter(
        stock__lte=F('low_stock_threshold'),
        is_available=True
    )
    
    for product in low_stock_products:
        title = f"Low Stock Alert: {product.name}"
        message = f"Product '{product.name}' has only {product.stock} units left (threshold: {product.low_stock_threshold})"
        link = f"/products/?search={product.code}"
        
        NotificationService.notify_admins(
            title=title,
            message=message,
            notification_type='stock',
            priority='high' if product.stock == 0 else 'medium',
            link=link,
            action_text='View Product'
        )
        notifications_created += 1
    
    # Check raw materials
    low_stock_materials = RawMaterial.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    )
    
    for material in low_stock_materials:
        title = f"Low Material Alert: {material.name}"
        message = f"Raw material '{material.name}' has only {material.stock_quantity} {material.unit} left"
        link = f"/inventory/?material={material.id}"
        
        NotificationService.notify_admins(
            title=title,
            message=message,
            notification_type='stock',
            priority='high' if material.stock_quantity == 0 else 'medium',
            link=link,
            action_text='View Material'
        )
        notifications_created += 1
    
    return notifications_created


def create_order_notification(order, event_type='created'):
    """
    Create notifications for order events
    event_type: 'created', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled'
    """
    status_messages = {
        'created': f"New order #{order.order_number} has been placed",
        'confirmed': f"Order #{order.order_number} has been confirmed",
        'preparing': f"Order #{order.order_number} is being prepared",
        'ready': f"Order #{order.order_number} is ready for pickup",
        'delivered': f"Order #{order.order_number} has been delivered",
        'cancelled': f"Order #{order.order_number} has been cancelled",
    }
    
    status_titles = {
        'created': "New Order Received",
        'confirmed': "Order Confirmed",
        'preparing': "Order Preparation Started",
        'ready': "Order Ready for Pickup",
        'delivered': "Order Delivered",
        'cancelled': "Order Cancelled",
    }
    
    title = status_titles.get(event_type, "Order Update")
    message = status_messages.get(event_type, f"Order #{order.order_number} status updated to {event_type}")
    link = f"/orders/{order.id}/"
    
    # Notify admins/staff
    NotificationService.notify_admins(
        title=title,
        message=message,
        notification_type='order',
        priority='high' if event_type in ['created', 'cancelled'] else 'medium',
        link=link,
        action_text='View Order'
    )
    
    # Notify customer if exists
    if order.customer:
        NotificationService.notify_customer(
            customer=order.customer,
            title=title,
            message=message,
            notification_type='order',
            priority='medium',
            link=link,
            action_text='Track Order'
        )


def create_system_notification(message, title="System Notification", priority='medium'):
    """Create a system-wide notification"""
    NotificationService.notify_admins(
        title=title,
        message=message,
        notification_type='system',
        priority=priority
    )
    NotificationService.notify_staff(
        title=title,
        message=message,
        notification_type='system',
        priority=priority
    )