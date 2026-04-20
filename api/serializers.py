# api/serializers.py
from rest_framework import serializers
from core.models import *
from django.contrib.auth.models import User

# User Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'phone', 'address', 'profile_picture', 
                 'username', 'password', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

    def create(self, validated_data):
        # Create user first
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', '')
        }
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**user_data, password=password)
        
        # Create profile
        profile = UserProfile.objects.create(user=user, **validated_data)
        return profile

# Category Serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category', read_only=True)
    profit_margin = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

# RawMaterial Serializer
class RawMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMaterial
        fields = '__all__'

# ProductRecipe Serializer
class ProductRecipeSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    material_name = serializers.CharField(source='raw_material.name', read_only=True)
    
    class Meta:
        model = ProductRecipe
        fields = '__all__'

# Customer Serializer
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

# OrderItem Serializer (nested)
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'subtotal']
        read_only_fields = ['subtotal']

# Order Serializer
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'subtotal', 'tax', 'total']

class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['customer', 'order_type', 'notes', 'items', 'discount']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        validated_data['created_by'] = self.context['request'].user
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['price'] for item in items_data)
        validated_data['subtotal'] = subtotal
        validated_data['tax'] = subtotal * 0.1  # 10% tax example
        validated_data['total'] = subtotal + validated_data['tax'] - validated_data.get('discount', 0)
        
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
            
            # Update inventory
            product = item_data['product']
            product.stock -= item_data['quantity']
            product.save()
            
            # Create inventory transaction
            InventoryTransaction.objects.create(
                product=product,
                transaction_type='out',
                quantity=item_data['quantity'],
                previous_stock=product.stock + item_data['quantity'],
                new_stock=product.stock,
                reference=order.order_number,
                created_by=validated_data['created_by']
            )
        
        return order

# InventoryTransaction Serializer
class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = InventoryTransaction
        fields = '__all__'

# Supplier Serializer
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

# PurchaseOrder Serializer
class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

# Promotion Serializer
class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'

# Notification Serializer
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

# SalesForecast Serializer
class SalesForecastSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SalesForecast
        fields = '__all__'
         