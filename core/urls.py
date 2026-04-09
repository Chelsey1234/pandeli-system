from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from . import views_api

# ========== API ROUTER CONFIGURATION ==========
# Remove 'api/' from these prefixes - they'll be added by the include below
router = DefaultRouter()
router.register(r'products', views_api.ProductViewSet)  # Changed: removed 'api/'
router.register(r'orders', views_api.OrderViewSet)      # Changed: removed 'api/'
router.register(r'customers', views_api.CustomerViewSet) # Changed: removed 'api/'
router.register(r'raw-materials', views_api.RawMaterialViewSet)  # Changed: removed 'api/'
router.register(r'suppliers', views_api.SupplierViewSet)  # Changed: removed 'api/'
router.register(r'dashboard', views_api.DashboardViewSet, basename='dashboard')  # Changed: removed 'api/'

# ========== URL PATTERNS ==========
urlpatterns = [
    # ------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------
    path('', views.login_view, name='login'),           # Root URL goes to login
    path('login/', views.login_view, name='login'),     # Explicit login URL
    path('logout/', views.logout_view, name='logout'),
    
    # ------------------------------------------
    # CORE FEATURES
    # ------------------------------------------
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('inventory/', views.inventory_status, name='inventory_status'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('messages/', views.messages_view, name='messages'),
    
    # ------------------------------------------
    # ORDERS
    # ------------------------------------------
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/confirm/', views.confirm_order, name='confirm_order'),
    
    # ------------------------------------------
    # SALES & FORECASTING
    # ------------------------------------------
    path('sales/report/', views.sales_report, name='sales_report'),
    path('sales/export/', views.export_sales_report, name='export_sales_report'),
    path('sales/analytics/', views.production_cost_analytics, name='production_cost_analytics'),
    path('forecast/', views.forecast, name='forecast'),
    path('forecast/run/', views.run_forecast, name='run_forecast'),
    
    # ------------------------------------------
    # IMPORT / EXPORT
    # ------------------------------------------
    path('import/', views.import_data, name='import_data'),
    path('import/history/', views.import_history, name='import_history'),
    path('import/template/<str:import_type>/', views.download_import_template, name='download_import_template'),
    path('export/', views.export_data, name='export_data'),
    
    # ------------------------------------------
    # POINT OF SALE (POS)
    # ------------------------------------------
    path('pos/', views.pos_view, name='pos'),
    path('pos/create-order/', views.pos_create_order, name='pos_create_order'),
    path('pos/product/<int:product_id>/', views.pos_get_product, name='pos_get_product'),
    path('api/order-modal-products/', views.order_modal_products, name='order_modal_products'),
    path('pos/search-products/', views.pos_search_products, name='pos_search_products'),
    path('pos/receipt/<int:order_id>/', views.pos_receipt, name='pos_receipt'),

    # ------------------------------------------
    # API AUTH (for Android / external clients)
    # ------------------------------------------
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    
    # ------------------------------------------
    # NOTIFICATION API
    # ------------------------------------------
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/count/', views.notification_count, name='notification_count'),
    path('api/notifications/<int:notification_id>/read/', 
         views.mark_notification_read, 
         name='mark_notification_read'),
    path('api/notifications/mark-all-read/', 
         views.mark_all_notifications_read, 
         name='mark_all_notifications_read'),
    
    # ------------------------------------------
    # NOTIFICATION MANAGEMENT
    # ------------------------------------------
    path('notifications/check-stock/', 
         views.trigger_low_stock_check, 
         name='trigger_low_stock_check'),
    path('notifications/create-bulk/', 
         views.create_bulk_notification, 
         name='create_bulk_notification'),
    
    # ------------------------------------------
    # API (includes all router URLs)
    # This will create endpoints like:
    # /api/products/
    # /api/orders/
    # /api/customers/
    # etc.
    # ------------------------------------------
    path('api/', include(router.urls)),
]