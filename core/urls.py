from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from . import views_api


class SessionInvalidatingPasswordResetConfirmView(PasswordResetConfirmView):
    """
    After a successful password reset, invalidate ALL existing sessions
    so the old password can no longer be used to stay logged in.
    """
    template_name = 'registration/password_reset_confirm.html'
    success_url = '/password-reset-complete/'

    def form_valid(self, form):
        user = form.save()
        # Rotate session auth hash so old sessions are invalidated
        update_session_auth_hash(self.request, user)
        # Explicitly redirect to complete page
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)

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
    path('profile/', views.user_profile, name='user_profile'),

    # ------------------------------------------
    # PASSWORD RESET
    # ------------------------------------------
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/password-reset/done/',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         SessionInvalidatingPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
    
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
    path('orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('orders/<int:pk>/update-payment/', views.update_payment_status, name='update_payment_status'),
    
    # ------------------------------------------
    # SALES & FORECASTING
    # ------------------------------------------
    path('sales/report/', views.sales_report, name='sales_report'),
    path('sales/export/', views.export_sales_report, name='export_sales_report'),
    path('sales/analytics/', views.production_cost_analytics, name='production_cost_analytics'),
    path('forecast/', views.forecast, name='forecast'),
    path('forecast/run/', views.run_forecast, name='run_forecast'),
    path('forecast/data/', views.forecast_data, name='forecast_data'),
    
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
    path('api/debug-order/', views.debug_order_request, name='debug_order_request'),
    
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
    # BUNDLES (app home screen bundle deals)
    # ------------------------------------------
    path('products/bundles/', views.bundle_list, name='bundle_list'),
    path('products/bundles/add/', views.bundle_add, name='bundle_add'),
    path('products/bundles/<int:pk>/toggle/', views.bundle_toggle, name='bundle_toggle'),
    path('products/bundles/<int:pk>/delete/', views.bundle_delete, name='bundle_delete'),
    path('products/bundles/<int:pk>/edit/', views.bundle_edit, name='bundle_edit'),
    path('api/bundles/', views.bundles_api, name='bundles_api'),

    # ------------------------------------------
    # ORDER WEBHOOK (called by Supabase on new order)
    # ------------------------------------------
    path('api/webhook/new-order/', views.order_webhook, name='order_webhook'),
    # ------------------------------------------
    path('products/app-features/', views.app_feature_list, name='app_feature_list'),
    path('products/app-features/add/', views.app_feature_add, name='app_feature_add'),
    path('products/app-features/<int:pk>/toggle/', views.app_feature_toggle, name='app_feature_toggle'),
    path('products/app-features/<int:pk>/delete/', views.app_feature_delete, name='app_feature_delete'),
    path('api/app-features/', views.app_features_api, name='app_features_api'),

    # ------------------------------------------
    # USER MANAGEMENT (admin/manager only)
    # ------------------------------------------
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),

    # ------------------------------------------
    # PUBLIC PAGES (no login required)
    # ------------------------------------------
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('privacy_policy.php', views.privacy_policy, name='privacy_policy_php'),
    path('privacy_policy.php/', views.privacy_policy, name='privacy_policy_php_slash'),

    # ------------------------------------------
    # API (includes all router URLs)
    # ------------------------------------------
    path('api/', include(router.urls)),
]