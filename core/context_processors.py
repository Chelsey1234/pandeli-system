import logging
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

def safe_context_processor(func):
    """Decorator to safely handle errors in context processors"""
    def wrapper(request):
        try:
            return func(request)
        except Exception as e:
            logger.error(f"Error in context processor {func.__name__}: {e}")
            return {}
    return wrapper


@safe_context_processor
def notifications(request):
    """
    Context processor to add notification data to all templates
    """
    context = {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            from .models import Notification
            unread_count = Notification.objects.filter(
                recipient_user=request.user,
                is_read=False
            ).count()
            recent_notifications = Notification.objects.filter(
                recipient_user=request.user
            ).only('id', 'title', 'message', 'notification_type', 'is_read', 'created_at', 'link'
            ).order_by('-created_at')[:5]
            context = {
                'unread_notifications_count': unread_count,
                'recent_notifications': recent_notifications,
            }
        except Exception as e:
            logger.warning(f"Could not load notifications: {e}")
    
    return context


@safe_context_processor
def products_context(request):
    """
    Context processor to add products to all templates for the New Order modal
    """
    context = {
        'products': [],
        'customers': [],  # Also add customers for the order modal
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            from .models import Product, Customer
            context = {
                'products': Product.objects.filter(
                    is_archived=False, is_available=True
                ).only('id', 'name', 'price', 'stock', 'category').order_by('name')[:50],
                'customers': Customer.objects.only('id', 'name').order_by('name')[:30],
            }
        except Exception as e:
            logger.warning(f"Could not load products/customers: {e}")
    
    return context


@safe_context_processor
def user_role(request):
    """
    Context processor for user role information
    """
    context = {
        'is_admin': False,
        'is_manager': False,
        'is_staff': False,
        'is_cashier': False,
        'is_production_admin': False,
        'user_role': 'guest',
        'user_display_name': 'Guest',
        'profile_picture_url': None,
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            context['user_display_name'] = request.user.get_full_name() or request.user.username

            try:
                profile = request.user.profile
            except ObjectDoesNotExist:
                profile = None

            if profile is not None:
                role = profile.role if profile.role else 'staff'
                context.update({
                    'is_admin': role == 'admin',
                    'is_manager': role == 'manager',
                    'is_cashier': role == 'cashier',
                    'is_production_admin': role == 'production_admin',
                    'is_staff': role in ['staff', 'cashier', 'production_admin'],
                    'user_role': role,
                })
                if profile.profile_picture:
                    context['profile_picture_url'] = profile.profile_picture.url
            else:
                context.update({
                    'is_admin': request.user.is_superuser,
                    'is_staff': request.user.is_staff,
                    'user_role': 'superuser' if request.user.is_superuser else 'staff' if request.user.is_staff else 'user',
                })
        except Exception as e:
            logger.warning(f"Could not determine user role: {e}")
    
    return context


@safe_context_processor
def site_settings(request):
    """
    Context processor for site-wide settings
    """
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'Pandeli System'),
        'site_version': getattr(settings, 'SITE_VERSION', '1.0.0'),
        'debug': settings.DEBUG,
        'current_year': 2026,
    }