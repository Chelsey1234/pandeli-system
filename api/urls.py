# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'raw-materials', views.RawMaterialViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'inventory-transactions', views.InventoryTransactionViewSet)
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'promotions', views.PromotionViewSet)
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'forecasts', views.SalesForecastViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('token/', obtain_auth_token, name='api_token_auth'),
]