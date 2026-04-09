from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import *

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role')
    
    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else 'N/A'
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'price', 'stock', 'is_available')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('code', 'name')
    list_editable = ('price', 'stock', 'is_available')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'order_type', 'created_at')
    search_fields = ('order_number', 'customer__name')
    readonly_fields = ('order_number', 'subtotal', 'total')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'subtotal')
    list_filter = ('order__status',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'loyalty_points', 'created_at')
    search_fields = ('name', 'email', 'phone')

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'stock_quantity', 'low_stock_threshold', 'cost_per_unit')
    list_filter = ('unit',)
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone')
    search_fields = ('name', 'email')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'recipient_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'recipient_type', 'is_read')

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'previous_stock', 'new_stock', 'created_at')
    list_filter = ('transaction_type', 'created_at')

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'promo_type', 'discount_value', 'start_date', 'end_date', 'is_active')
    list_filter = ('promo_type', 'is_active')

@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    list_display = ('import_type', 'file_name', 'status', 'total_records', 'success_records', 'created_at')
    list_filter = ('import_type', 'status')