from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    profit_margin = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()
    recipe_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return obj.image.url
        return None

    def get_recipe_details(self, obj):
        return [
            {
                'id': recipe.id,
                'raw_material_id': recipe.raw_material_id,
                'raw_material_name': recipe.raw_material.name,
                'quantity': recipe.quantity,
            }
            for recipe in obj.recipe.select_related('raw_material').all()
        ]

class RawMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMaterial
        fields = '__all__'

class ProductRecipeSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    material_name = serializers.ReadOnlyField(source='raw_material.name')
    
    class Meta:
        model = ProductRecipe
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'subtotal']
        read_only_fields = ['price', 'subtotal']

# SINGLE OrderSerializer (removed the duplicate)
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.ReadOnlyField(source='customer.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'order_type',
            'status', 'payment_status', 'subtotal', 'tax', 'discount', 'total',
            'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at',
            'items'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at', 'created_by']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='raw_material.name')
    
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.ReadOnlyField(source='supplier.name')
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class SalesForecastSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = SalesForecast
        fields = '__all__'

class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = InventoryTransaction
        fields = '__all__'

class ImportHistorySerializer(serializers.ModelSerializer):
    imported_by_name = serializers.ReadOnlyField(source='imported_by.username')
    
    class Meta:
        model = ImportHistory
        fields = '__all__'

