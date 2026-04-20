from rest_framework import viewsets, status, filters, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDay
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal  # <-- IMPORTANT: Add this import
from .models import *
from .serializers import *
import json

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_archived=False)
    serializer_class = ProductSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'price', 'stock', 'created_at']

    def get_queryset(self):
        qs = Product.objects.all()
        archived = self.request.query_params.get('archived')
        if archived in ('1', 'true', 'True'):
            return qs.filter(is_archived=True)
        if archived in ('all',):
            return qs
        return qs.filter(is_archived=False)

    def _parse_recipes(self, request):
        recipes_raw = request.data.get('recipes', '[]')
        if isinstance(recipes_raw, list):
            recipes = recipes_raw
        else:
            try:
                recipes = json.loads(recipes_raw or '[]')
            except (TypeError, ValueError):
                raise ValueError('Invalid recipes payload')

        cleaned = []
        for item in recipes:
            try:
                raw_material_id = int(item.get('raw_material_id'))
                quantity = Decimal(str(item.get('quantity')))
            except Exception:
                raise ValueError('Invalid recipe item format')

            if raw_material_id <= 0 or quantity <= 0:
                raise ValueError('Recipe raw material and quantity must be valid')

            cleaned.append({
                'raw_material_id': raw_material_id,
                'quantity': quantity
            })
        return cleaned

    def _sync_product_recipes(self, product, recipes):
        ProductRecipe.objects.filter(product=product).delete()
        for item in recipes:
            ProductRecipe.objects.create(
                product=product,
                raw_material_id=item['raw_material_id'],
                quantity=item['quantity']
            )

    def create(self, request, *args, **kwargs):
        try:
            recipes = self._parse_recipes(request)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.pop('recipes', None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            product = serializer.save()
            self._sync_product_recipes(product, recipes)

        output = self.get_serializer(product)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        try:
            recipes = self._parse_recipes(request)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.pop('recipes', None)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            product = serializer.save()
            self._sync_product_recipes(product, recipes)

        output = self.get_serializer(product)
        return Response(output.data)

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        product.is_archived = True
        product.archived_at = timezone.now()
        product.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        try:
            product = Product.objects.get(pk=pk, is_archived=True)
        except Product.DoesNotExist:
            return Response({'error': 'Archived product not found'}, status=status.HTTP_404_NOT_FOUND)

        product.is_archived = False
        product.archived_at = None
        product.save()
        serializer = self.get_serializer(product)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        products = self.get_queryset().filter(
            stock__lte=F('low_stock_threshold'),
            is_available=True
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        notes = request.data.get('notes', '')
        
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_stock = product.stock
        product.stock += quantity
        product.save()
        
        InventoryTransaction.objects.create(
            product=product,
            transaction_type='adjustment',
            quantity=quantity,
            previous_stock=old_stock,
            new_stock=product.stock,
            notes=notes,
            created_by=request.user
        )
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_new_arrival(self, request, pk=None):
        product = self.get_object()
        product.is_new_arrival = not product.is_new_arrival
        product.save(update_fields=['is_new_arrival'])
        return Response({'is_new_arrival': product.is_new_arrival})

    @action(detail=True, methods=['post'])
    def toggle_best_seller(self, request, pk=None):
        product = self.get_object()
        product.is_best_seller = not product.is_best_seller
        product.save(update_fields=['is_best_seller'])
        return Response({'is_best_seller': product.is_best_seller})


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related('items__product')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'customer__name']
    ordering_fields = ['created_at', 'total', 'status']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return queryset
        return queryset.filter(created_by=user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create to handle order items"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Start a transaction to ensure data consistency
        with transaction.atomic():
            # Create the order - pass order_type and notes from request
            order_type = request.data.get('order_type', 'walk_in')
            notes = request.data.get('notes', '')
            order = serializer.save(
                created_by=request.user,
                order_type=order_type,
                notes=notes or ''
            )
            
            # Get items from request
            items_data = request.data.get('items', [])
            
            if not items_data:
                return Response(
                    {'error': 'No items provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use Decimal for calculations
            subtotal = Decimal('0.00')
            
            # Create order items
            for item_data in items_data:
                try:
                    product = Product.objects.get(id=item_data['product_id'])
                    quantity = int(item_data['quantity'])
                    
                    # Check stock
                    if product.stock < quantity:
                        return Response(
                            {'error': f'Insufficient stock for {product.name}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Calculate item total - convert to Decimal
                    item_total = product.price * quantity
                    subtotal += item_total
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=product.price,
                        subtotal=item_total
                    )
                    
                    # Update stock
                    product.stock -= quantity
                    product.save()
                    
                except Product.DoesNotExist:
                    return Response(
                        {'error': f'Product with id {item_data["product_id"]} not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                except Exception as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # No tax - use original price as total
            tax = Decimal('0')
            total = subtotal
            
            # Update order with calculated values
            order.subtotal = subtotal
            order.tax = tax
            order.total = total
            order.save()
        
        # Return the updated order
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        
        if order.status != 'pending':
            return Response(
                {'error': f'Order cannot be confirmed - current status: {order.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check stock
        insufficient_stock = []
        for item in order.items.all():
            if item.product.stock < item.quantity:
                insufficient_stock.append({
                    'product': item.product.name,
                    'available': item.product.stock,
                    'requested': item.quantity
                })
        
        if insufficient_stock:
            return Response(
                {'error': 'Insufficient stock', 'details': insufficient_stock},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deduct stock
        for item in order.items.all():
            item.product.stock -= item.quantity
            item.product.save()
        
        order.status = 'confirmed'
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Order.ORDER_STATUS):
            order.status = new_status
            order.save()
            
            # Create notification
            try:
                if order.customer and order.customer.user:
                    Notification.objects.create(
                        title=f"Order #{order.order_number} Status Updated",
                        message=f"Your order status is now: {order.get_status_display()}",
                        notification_type='order',
                        recipient_type='customer',
                        recipient_user=order.customer.user
                    )
            except Exception:
                pass
            
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'loyalty_points', 'created_at']


class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all()
    serializer_class = RawMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'stock_quantity', 'cost_per_unit']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        materials = self.get_queryset().filter(
            stock_quantity__lte=F('low_stock_threshold')
        )
        serializer = self.get_serializer(materials, many=True)
        return Response(serializer.data)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get dashboard summary data"""
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        daily_sales = Order.objects.filter(
            created_at__date=today,
            payment_status='paid'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        monthly_sales = Order.objects.filter(
            created_at__date__gte=start_of_month,
            payment_status='paid'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        total_orders = Order.objects.filter(created_at__date=today).count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        low_stock_count = Product.objects.filter(
            stock__lte=F('low_stock_threshold'),
            is_available=True
        ).count()
        
        best_sellers = OrderItem.objects.values(
            'product__name'
        ).annotate(
            total=Sum('quantity')
        ).order_by('-total')[:5]
        
        return Response({
            'daily_sales': daily_sales,
            'monthly_sales': monthly_sales,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'low_stock_count': low_stock_count,
            'best_sellers': best_sellers
        })
    
    @action(detail=False, methods=['get'])
    def sales_chart(self, request):
        """Get sales chart data"""
        days = int(request.GET.get('days', 7))
        today = timezone.now().date()
        
        data = []
        for i in range(days-1, -1, -1):
            date = today - timedelta(days=i)
            total = Order.objects.filter(
                created_at__date=date,
                payment_status='paid'
            ).aggregate(total=Sum('total'))['total'] or 0
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'total': float(total)
            })
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def sales_by_category(self, request):
        """Get sales by category for bar chart"""
        days = int(request.GET.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        sales_by_category = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__payment_status='paid'
        ).values('product__category').annotate(
            total_sales=Sum('subtotal'),
            total_quantity=Sum('quantity')
        ).order_by('-total_sales')
        
        categories = []
        sales_data = []
        quantity_data = []
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#7BC225', '#00A8B5'
        ]
        
        for item in sales_by_category:
            category_name = dict(Product.CATEGORY_CHOICES).get(
                item['product__category'], 
                item['product__category'].title()
            )
            categories.append(category_name)
            sales_data.append(float(item['total_sales']))
            quantity_data.append(item['total_quantity'])
        
        return Response({
            'labels': categories,
            'sales': sales_data,
            'quantities': quantity_data,
            'colors': colors[:len(categories)]
        })
    
    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """Get top selling products for bar chart"""
        limit = int(request.GET.get('limit', 10))
        start_date = timezone.now().date() - timedelta(days=30)
        
        top_products = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__payment_status='paid'
        ).values('product__name', 'product__id').annotate(
            total_sales=Sum('subtotal'),
            total_quantity=Sum('quantity')
        ).order_by('-total_sales')[:limit]
        
        products = []
        sales_data = []
        quantity_data = []
        
        for item in top_products:
            products.append(item['product__name'][:20] + ('...' if len(item['product__name']) > 20 else ''))
            sales_data.append(float(item['total_sales']))
            quantity_data.append(item['total_quantity'])
        
        return Response({
            'labels': products,
            'sales': sales_data,
            'quantities': quantity_data
        })