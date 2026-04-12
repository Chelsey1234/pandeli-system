# api/views.py
from rest_framework import viewsets, permissions, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from core.models import *
from .serializers import *
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta

# User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# UserProfile ViewSet
class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['role']
    search_fields = ['user__username', 'user__email', 'phone']

# Category ViewSet
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

# Product ViewSet
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['price', 'stock', 'created_at']
    
    def get_permissions(self):
        """
        Allow anyone to view products, but require authentication
        for creating/updating/deleting.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock_products = self.queryset.filter(stock__lte=models.F('low_stock_threshold'))
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def recipe(self, request, pk=None):
        product = self.get_object()
        recipe = ProductRecipe.objects.filter(product=product)
        serializer = ProductRecipeSerializer(recipe, many=True)
        return Response(serializer.data)

# RawMaterial ViewSet
class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all()
    serializer_class = RawMaterialSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'supplier']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock = self.queryset.filter(stock_quantity__lte=models.F('reorder_point'))
        serializer = self.get_serializer(low_stock, many=True)
        return Response(serializer.data)

# Customer ViewSet
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        customer = self.get_object()
        orders = Order.objects.filter(customer=customer)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

# Order ViewSet
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'order_type']
    search_fields = ['order_number', 'customer__name']
    ordering_fields = ['-created_at', 'total']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status in dict(Order.ORDER_STATUS).keys():
            order.status = new_status
            order.save()
            
            # Create notification
            try:
                if order.customer and order.customer.user:
                    Notification.objects.create(
                        title=f'Order {order.order_number} Status Updated',
                        message=f'Your order is now: {order.get_status_display()}',
                        notification_type='order',
                        recipient_user=order.customer.user,
                        link=f'/orders/{order.id}'
                    )
            except Exception:
                pass
            
            return Response({'status': 'updated'})
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        data = {
            'today_orders': self.queryset.filter(created_at__date=today).count(),
            'today_revenue': self.queryset.filter(
                created_at__date=today, 
                payment_status='paid'
            ).aggregate(Sum('total'))['total__sum'] or 0,
            'pending_orders': self.queryset.filter(status='pending').count(),
            'recent_orders': OrderSerializer(
                self.queryset.order_by('-created_at')[:10], 
                many=True
            ).data,
            'weekly_sales': self.queryset.filter(
                created_at__date__gte=week_ago,
                payment_status='paid'
            ).extra({'date': 'date(created_at)'}).values('date').annotate(
                total=Sum('total'),
                count=Count('id')
            ).order_by('date')
        }
        return Response(data)

# InventoryTransaction ViewSet
class InventoryTransactionViewSet(viewsets.ModelViewSet):
    queryset = InventoryTransaction.objects.all()
    serializer_class = InventoryTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['transaction_type', 'product']
    search_fields = ['reference', 'notes']
    ordering = ['-created_at']

# Supplier ViewSet
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']

# PurchaseOrder ViewSet
class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'supplier']
    search_fields = ['po_number']

# Promotion ViewSet
class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['promo_type', 'is_active']
    search_fields = ['name', 'description']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        now = timezone.now()
        active_promos = self.queryset.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        serializer = self.get_serializer(active_promos, many=True)
        return Response(serializer.data)

# Notification ViewSet
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            Q(recipient_user=self.request.user) |
            Q(recipient_type='all')
        ).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.mark_all_as_read(request.user)
        return Response({'status': 'all marked as read'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

# SalesForecast ViewSet
class SalesForecastViewSet(viewsets.ModelViewSet):
    queryset = SalesForecast.objects.all()
    serializer_class = SalesForecastSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'forecast_date']