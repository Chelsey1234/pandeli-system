from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.utils import timezone
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST  # <-- ADD THIS LINE
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.cache import never_cache
from datetime import timedelta, datetime
from django.http import JsonResponse, HttpResponse
from functools import wraps
from .models import *


def login_required_json(view_func):
    """For AJAX requests, return 401 JSON instead of redirecting to login."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        # Prefer JSON response for AJAX so frontend can show "log in" message
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({'error': 'Login required', 'products': []}, status=401)
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    return _wrapped
from .utils import *
from .notifications import NotificationService, check_low_stock_and_notify  # If you created this
import json
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.chart import BarChart, Reference, LineChart
import csv

# ========== AUTHENTICATION VIEWS ==========

@never_cache
@csrf_protect
def login_view(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', request.GET.get('next', 'dashboard'))
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'registration/login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Check if "Remember me" is checked
                if not request.POST.get('remember_me'):
                    # Session expires on browser close
                    request.session.set_expiry(0)
                
                # Check if next_url is safe
                if next_url and next_url != 'None' and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account is disabled.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'registration/login.html')
@never_cache
@login_required
def logout_view(request):
    # Explicitly clear auth/session state and force a new anonymous session.
    logout(request)
    request.session.flush()

    response = redirect('login')
    response.delete_cookie('sessionid')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def is_admin_or_manager(user):
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role in ['admin', 'production_admin', 'manager'])

# ========== DASHBOARD VIEWS ==========

@login_required
def dashboard(request):
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    week_start = today - timedelta(days=6)

    # Run all aggregates in as few queries as possible
    from django.db.models import Count

    # Single query for today's stats
    today_stats = Order.objects.filter(created_at__date=today).aggregate(
        daily_sales=Sum('total'),
        total_orders=Count('id'),
    )
    daily_sales = today_stats['daily_sales'] or 0
    total_orders = today_stats['total_orders'] or 0

    monthly_sales = Order.objects.filter(
        created_at__date__gte=start_of_month,
    ).aggregate(total=Sum('total'))['total'] or 0

    pending_orders = Order.objects.filter(status='pending').count()

    # Low stock
    low_stock_products = Product.objects.filter(
        stock__lte=F('low_stock_threshold'),
        is_available=True
    ).only('name', 'stock', 'low_stock_threshold')[:10]

    # Best sellers
    best_sellers = OrderItem.objects.values(
        'product__name', 'product__id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum('subtotal')
    ).order_by('-total_quantity')[:5]

    # Sales graph — single query for last 7 days
    sales_qs = (
        Order.objects.filter(created_at__date__gte=week_start)
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Sum('total'))
        .order_by('day')
    )
    sales_by_day = {}
    for row in sales_qs:
        if row['day']:
            sales_by_day[row['day'].date()] = float(row['total'] or 0)

    last_7_days = []
    sales_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        last_7_days.append(date.strftime('%Y-%m-%d'))
        sales_data.append(sales_by_day.get(date, 0))

    # Recent orders
    recent_orders = Order.objects.select_related('customer').only(
        'order_number', 'order_type', 'status', 'total', 'created_at',
        'customer__name'
    ).order_by('-created_at')[:5]

    # Products and customers for modal
    products = Product.objects.filter(is_archived=False).only(
        'id', 'name', 'price', 'stock', 'category'
    ).order_by('name')[:100]
    customers = Customer.objects.only('id', 'name').order_by('name')[:50]

    context = {
        'daily_sales': daily_sales,
        'monthly_sales': monthly_sales,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'low_stock_products': low_stock_products,
        'best_sellers': best_sellers,
        'recent_orders': recent_orders,
        'sales_labels': json.dumps(last_7_days),
        'sales_data': json.dumps(sales_data),
        'products': products,
        'customers': customers,
    }

    return render(request, 'core/dashboard.html', context)

# ========== PRODUCT VIEWS ==========

@login_required
def product_list(request):
    products = Product.objects.filter(is_archived=False)
    archived_products = Product.objects.filter(is_archived=True).order_by('-archived_at', '-updated_at')
    categories = Category.objects.all()
    raw_materials = RawMaterial.objects.all().order_by('name')
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        products = products.filter(category=category)
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(code__icontains=search) |
            Q(description__icontains=search)
        )
    
    context = {
        'products': products,
        'archived_products': archived_products,
        'categories': categories,
        'raw_materials': raw_materials,
    }
    return render(request, 'core/product_list.html', context)

# ========== INVENTORY VIEWS ==========

@login_required
def inventory_status(request):
    products = Product.objects.filter(is_archived=False).order_by('-stock')
    raw_materials = RawMaterial.objects.all()
    
    # Pre-calculate inventory values for template
    for product in products:
        product.inventory_value = product.stock * product.price
    
    for material in raw_materials:
        material.inventory_value = material.stock_quantity * material.cost_per_unit
    
    # Low stock items
    low_stock_products = products.filter(stock__lte=F('low_stock_threshold'))
    low_stock_materials = raw_materials.filter(stock_quantity__lte=F('low_stock_threshold'))
    
    # Recent transactions
    recent_transactions = InventoryTransaction.objects.select_related('product', 'created_by').order_by('-created_at')[:20]
    
    context = {
        'products': products,
        'raw_materials': raw_materials,
        'low_stock_products': low_stock_products,
        'low_stock_materials': low_stock_materials,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'core/inventory_status.html', context)

# ========== ORDER VIEWS ==========

@login_required
def order_list(request):
    orders = Order.objects.all().select_related('customer').prefetch_related('items')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by date
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    context = {
        'orders': orders,
        'status_choices': Order.ORDER_STATUS,
    }
    return render(request, 'core/order_list.html', context)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Safely get customer — customer_id may be a UUID string from mobile app
    customer = None
    try:
        customer = order.customer
    except Exception:
        pass
    context = {
        'order': order,
        'customer': customer,
    }
    return render(request, 'core/order_detail.html', context)

@login_required
def confirm_order(request, pk):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        
        if order.status == 'pending':
            # Check stock availability
            insufficient_stock = []
            for item in order.items.all():
                if item.product.stock < item.quantity:
                    insufficient_stock.append(f"{item.product.name} (available: {item.product.stock}, needed: {item.quantity})")
            
            if insufficient_stock:
                messages.error(request, f"Insufficient stock for: {', '.join(insufficient_stock)}")
                return redirect('order_detail', pk=pk)
            
            # Deduct stock
            for item in order.items.all():
                old_stock = item.product.stock
                item.product.stock -= item.quantity
                item.product.save()
                
                # Record transaction
                InventoryTransaction.objects.create(
                    product=item.product,
                    transaction_type='out',
                    quantity=item.quantity,
                    previous_stock=old_stock,
                    new_stock=item.product.stock,
                    reference=order.order_number,
                    notes=f"Order confirmation",
                    created_by=request.user
                )
                
                # Deduct raw materials if recipe exists
                for recipe in item.product.recipe.all():
                    material = recipe.raw_material
                    needed_qty = recipe.quantity * item.quantity
                    
                    if material.stock_quantity >= needed_qty:
                        old_material_stock = material.stock_quantity
                        material.stock_quantity -= needed_qty
                        material.save()
                        
                        RawMaterialTransaction.objects.create(
                            raw_material=material,
                            transaction_type='out',
                            quantity=needed_qty,
                            previous_stock=old_material_stock,
                            new_stock=material.stock_quantity,
                            reference=order.order_number,
                            notes=f"Used for {item.product.name}",
                            created_by=request.user
                        )
            
            order.status = 'confirmed'
            order.save()
            
            # Create notification — safely handle UUID customer_id from mobile app
            try:
                if order.customer and order.customer.user:
                    Notification.objects.create(
                        title=f"Order #{order.order_number} Confirmed",
                        message=f"Your order has been confirmed and is being prepared.",
                        notification_type='order',
                        recipient_type='customer',
                        recipient_user=order.customer.user
                    )
            except Exception:
                pass
            
            messages.success(request, f'Order #{order.order_number} confirmed successfully.')
    
    return redirect('order_detail', pk=pk)

# ========== SALES VIEWS ==========

@login_required
def sales_report(request):
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        try:
            date_from = datetime.strptime(str(date_from), '%Y-%m-%d').date()
        except ValueError:
            date_from = (timezone.now() - timedelta(days=30)).date()
    if not date_to:
        date_to = timezone.now().date()
    else:
        try:
            date_to = datetime.strptime(str(date_to), '%Y-%m-%d').date()
        except ValueError:
            date_to = timezone.now().date()
    
    # Include all orders in the selected date range (regardless of payment status)
    orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )
    
    # Summary statistics
    total_sales = orders.aggregate(total=Sum('total'))['total'] or 0
    total_orders = orders.count()
    average_order = total_sales / total_orders if total_orders > 0 else 0
    
    # Sales by category
    sales_by_category = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'product__category'
    ).annotate(
        total=Sum('subtotal'),
        quantity=Sum('quantity')
    ).order_by('-total')
    
    # Daily sales for graph
    daily_sales = orders.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total=Sum('total')
    ).order_by('day')
    
    sales_dates = [item['day'].strftime('%Y-%m-%d') for item in daily_sales]
    sales_amounts = [float(item['total']) for item in daily_sales]
    
    # Top products
    top_products = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'product__name'
    ).annotate(
        quantity=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-revenue')[:10]
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'average_order': average_order,
        'sales_by_category': sales_by_category,
        'sales_dates': json.dumps(sales_dates),
        'sales_amounts': json.dumps(sales_amounts),
        'top_products': top_products,
    }
    return render(request, 'core/sales_report.html', context)


@login_required
def production_cost_analytics(request):
    """Production cost analytics and profit margin analysis."""
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        try:
            date_from = datetime.strptime(str(date_from), '%Y-%m-%d').date()
        except ValueError:
            date_from = (timezone.now() - timedelta(days=30)).date()
    if not date_to:
        date_to = timezone.now().date()
    else:
        try:
            date_to = datetime.strptime(str(date_to), '%Y-%m-%d').date()
        except ValueError:
            date_to = timezone.now().date()

    analysis = calculate_profit_analysis(start_date=date_from, end_date=date_to)
    analysis['date_from'] = date_from
    analysis['date_to'] = date_to

    # Product-level margins
    product_margins = []
    for name, data in analysis.get('products', {}).items():
        product_margins.append({
            'name': name,
            'revenue': data['revenue'],
            'cost': data['cost'],
            'profit': data['profit'],
            'margin': data['margin'],
            'quantity': data['quantity'],
        })
    product_margins.sort(key=lambda x: -x['revenue'])

    context = {
        'analysis': analysis,
        'product_margins': product_margins,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'core/production_analytics.html', context)


@login_required
def export_sales_report(request):
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    if not date_to:
        date_to = timezone.now().date()
    
    # Create Excel workbook
    wb = Workbook()
    
    # Sales Summary Sheet
    ws1 = wb.active
    ws1.title = "Sales Summary"
    
    # Headers
    headers = ['Date', 'Order Number', 'Customer', 'Items', 'Subtotal', 'Tax', 'Discount', 'Total', 'Payment Status']
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True)
    
    # Get orders
    orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        payment_status='paid'
    ).order_by('-created_at')
    
    # Write data
    row = 2
    for order in orders:
        items_count = order.items.count()
        try:
            customer_name = order.customer.name if order.customer else 'Walk-in'
        except Exception:
            customer_name = 'Walk-in'
        ws1.cell(row=row, column=1, value=order.created_at.strftime('%Y-%m-%d'))
        ws1.cell(row=row, column=2, value=order.order_number)
        ws1.cell(row=row, column=3, value=customer_name)
        ws1.cell(row=row, column=4, value=items_count)
        ws1.cell(row=row, column=5, value=float(order.subtotal))
        ws1.cell(row=row, column=6, value=float(order.tax))
        ws1.cell(row=row, column=7, value=float(order.discount))
        ws1.cell(row=row, column=8, value=float(order.total))
        ws1.cell(row=row, column=9, value=order.payment_status)
        row += 1
    
    # Add totals row
    totals_row = row + 1
    ws1.cell(row=totals_row, column=5, value=f"=SUM(E2:E{row-1})")
    ws1.cell(row=totals_row, column=8, value=f"=SUM(H2:H{row-1})")
    ws1.cell(row=totals_row, column=5).font = Font(bold=True)
    ws1.cell(row=totals_row, column=8).font = Font(bold=True)
    
    # Create chart
    chart = LineChart()
    chart.title = "Daily Sales Trend"
    chart.style = 13
    chart.y_axis.title = 'Sales Amount'
    chart.x_axis.title = 'Date'
    
    data = Reference(ws1, min_col=8, min_row=1, max_row=row-1, max_col=8)
    dates = Reference(ws1, min_col=1, min_row=2, max_row=row-1)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(dates)
    
    ws1.add_chart(chart, "K2")
    
    # Products Sheet
    ws2 = wb.create_sheet("Top Products")
    
    headers = ['Product', 'Category', 'Quantity Sold', 'Revenue']
    for col, header in enumerate(headers, 1):
        cell = ws2.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
    
    top_products = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'product__name', 'product__category'
    ).annotate(
        quantity=Sum('quantity'),
        revenue=Sum('subtotal')
    ).order_by('-revenue')[:20]
    
    row = 2
    for item in top_products:
        ws2.cell(row=row, column=1, value=item['product__name'])
        ws2.cell(row=row, column=2, value=item['product__category'])
        ws2.cell(row=row, column=3, value=item['quantity'])
        ws2.cell(row=row, column=4, value=float(item['revenue']))
        row += 1
    
    # Set column widths
    for ws in [ws1, ws2]:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = min(adjusted_width, 50)
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="sales_report_{date_from}_to_{date_to}.xlsx"'
    
    wb.save(response)
    return response

# ========== FORECAST VIEWS ==========

@login_required
def forecast(request):
    # Include all products so forecasting still works even if stock is 0
    products = Product.objects.all().order_by('name')
    
    # Get forecasts
    forecasts = SalesForecast.objects.filter(
        forecast_date__gte=timezone.now().date()
    ).select_related('product').order_by('forecast_date')[:30]
    
    # Prepare chart data
    forecast_dates = []
    forecast_values = []
    for forecast in forecasts:
        forecast_dates.append(forecast.forecast_date.strftime('%Y-%m-%d'))
        forecast_values.append(forecast.predicted_quantity)
    
    # Get historical data for comparison
    historical_data = OrderItem.objects.filter(
        order__created_at__date__gte=timezone.now().date() - timedelta(days=30)
    ).values(
        'order__created_at__date'
    ).annotate(
        total=Sum('quantity')
    ).order_by('order__created_at__date')
    
    historical_dates = [item['order__created_at__date'].strftime('%Y-%m-%d') for item in historical_data]
    historical_values = [item['total'] for item in historical_data]
    
    context = {
        'products': products,
        'forecasts': forecasts,
        'forecast_dates': json.dumps(forecast_dates),
        'forecast_values': json.dumps(forecast_values),
        'historical_dates': json.dumps(historical_dates),
        'historical_values': json.dumps(historical_values),
    }
    return render(request, 'core/forecast.html', context)

@login_required
def run_forecast(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        days = min(int(request.POST.get('days', 30)), 30)  # cap at 30 days

        created_count = 0
        try:
            if product_id:
                product = get_object_or_404(Product, id=product_id)
                result = generate_sales_forecast(product, days)
                created_count = len(result or [])
            else:
                # Limit to 20 products max to avoid timeout
                products = Product.objects.filter(is_archived=False)[:20]
                for product in products:
                    try:
                        result = generate_sales_forecast(product, days)
                        created_count += len(result or [])
                    except Exception:
                        continue
        except Exception as e:
            messages.error(request, f'Forecast error: {str(e)}')
            return redirect('forecast')

        if created_count > 0:
            messages.success(request, f'Forecast generated successfully! ({created_count} forecast rows)')
        else:
            messages.warning(request, 'No forecast rows were generated. Add order history first, then try again.')
        return redirect('forecast')

    return redirect('forecast')

# ========== IMPORT/EXPORT VIEWS ==========

def _process_import_rows(import_type, df, file_name, request, errors_list):
    """Process import rows - returns (success_count, error_count, error_rows for report)"""
    success_count = 0
    error_count = 0
    error_rows = []  # List of dicts for error report: {row_num, data, error}
    
    if import_type == 'product':
        required = ['code', 'name', 'category', 'price']
        for index, row in df.iterrows():
            row_num = index + 2  # 1-based, +1 for header
            row_data = row.to_dict()
            try:
                code = row.get('code')
                if pd.isna(code) or not str(code).strip():
                    raise ValueError("Code is required")
                category = str(row.get('category', '')).strip().lower()
                valid_cats = ['bread', 'pastries', 'croissants', 'beverages', 'spread']
                if category not in valid_cats:
                    raise ValueError(f"Invalid category. Use: {', '.join(valid_cats)}")
                Product.objects.update_or_create(
                    code=str(code).strip(),
                    defaults={
                        'name': str(row.get('name', '')).strip() or 'Unknown',
                        'category': category,
                        'price': float(row.get('price', 0)),
                        'cost': float(row.get('cost', 0)),
                        'stock': int(row.get('stock', 0)),
                        'description': str(row.get('description', '')),
                    }
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                error_rows.append({'row': row_num, 'data': row_data, 'error': str(e)})
                errors_list.append(f"Row {row_num}: {str(e)}")
    
    elif import_type == 'customer':
        for index, row in df.iterrows():
            row_num = index + 2
            row_data = row.to_dict()
            try:
                email = row.get('email')
                if pd.isna(email) or not str(email).strip():
                    raise ValueError("Email is required")
                Customer.objects.update_or_create(
                    email=str(email).strip(),
                    defaults={
                        'name': str(row.get('name', '')).strip() or 'Unknown',
                        'phone': str(row.get('phone', '')),
                        'address': str(row.get('address', '')),
                    }
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                error_rows.append({'row': row_num, 'data': row_data, 'error': str(e)})
                errors_list.append(f"Row {row_num}: {str(e)}")
    
    elif import_type == 'inventory':
        for index, row in df.iterrows():
            row_num = index + 2
            row_data = row.to_dict()
            try:
                product = Product.objects.get(code=str(row.get('product_code', '')).strip())
                new_stock = int(row.get('new_stock', 0))
                old_stock = product.stock
                InventoryTransaction.objects.create(
                    product=product,
                    transaction_type='adjustment',
                    quantity=new_stock - old_stock,
                    previous_stock=old_stock,
                    new_stock=new_stock,
                    notes=f"Bulk import from {file_name}",
                    created_by=request.user
                )
                product.stock = new_stock
                product.save()
                success_count += 1
            except Exception as e:
                error_count += 1
                error_rows.append({'row': row_num, 'data': row_data, 'error': str(e)})
                errors_list.append(f"Row {row_num}: {str(e)}")
    
    elif import_type == 'sales':
        for index, row in df.iterrows():
            row_num = index + 2
            row_data = row.to_dict()
            try:
                product_code = str(row.get('product_code', '')).strip()
                product = Product.objects.get(code=product_code)
                qty = int(row.get('quantity', 0))
                if qty <= 0:
                    success_count += 1
                    continue
                order = Order.objects.create(
                    order_type='walk_in',
                    status='confirmed',
                    payment_status='paid',
                    subtotal=product.price * qty,
                    tax=0,
                    total=product.price * qty,
                    created_by=request.user
                )
                OrderItem.objects.create(order=order, product=product, quantity=qty, price=product.price, subtotal=product.price * qty)
                old_stock = product.stock
                product.stock -= qty
                product.save()
                InventoryTransaction.objects.create(
                    product=product, transaction_type='out', quantity=qty,
                    previous_stock=old_stock, new_stock=product.stock,
                    reference=order.order_number, notes="Historical sales import",
                    created_by=request.user
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                error_rows.append({'row': row_num, 'data': row_data, 'error': str(e)})
                errors_list.append(f"Row {row_num}: {str(e)}")
    
    return success_count, error_count, error_rows


def _create_error_report_file(error_rows, import_type, file_name):
    """Create Excel error report and return HttpResponse or None"""
    if not error_rows:
        return None
    wb = Workbook()
    ws = wb.active
    ws.title = "Import Errors"
    ws.cell(row=1, column=1, value="Row #")
    ws.cell(row=1, column=2, value="Error Message")
    for c, col in enumerate(error_rows[0].get('data', {}).keys(), 3):
        ws.cell(row=1, column=c, value=str(col))
    for idx, er in enumerate(error_rows[:500], 2):
        ws.cell(row=idx, column=1, value=er['row'])
        ws.cell(row=idx, column=2, value=er['error'])
        for c, (k, v) in enumerate(er.get('data', {}).items(), 3):
            ws.cell(row=idx, column=c, value=str(v) if pd.notna(v) else '')
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    base = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
    response['Content-Disposition'] = f'attachment; filename="import_errors_{import_type}_{base}.xlsx"'
    wb.save(response)
    return response


@login_required
@user_passes_test(is_admin_or_manager)
def import_data(request):
    if request.method == 'POST':
        import_type = request.POST.get('import_type')
        files = request.FILES.getlist('files') or request.FILES.getlist('file')
        if not files:
            single = request.FILES.get('file')
            if single:
                files = [single]
        if not files or not import_type:
            messages.error(request, 'Please select import type and at least one file.')
            return redirect('import_data')
        
        all_errors = []
        total_success = 0
        total_failed = 0
        all_error_rows = []
        file_names = []
        
        with transaction.atomic():
            for file in files:
                if not file.name:
                    continue
                try:
                    if file.name.lower().endswith('.csv'):
                        df = pd.read_csv(file)
                    elif file.name.lower().endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file)
                    else:
                        messages.warning(request, f'Skipped {file.name}: unsupported format.')
                        continue
                except Exception as e:
                    messages.error(request, f'Could not read {file.name}: {e}')
                    continue
                
                file_names.append(file.name)
                success, failed, error_rows = _process_import_rows(import_type, df, file.name, request, all_errors)
                total_success += success
                total_failed += failed
                for er in error_rows:
                    er['file'] = file.name
                    all_error_rows.append(er)
            
            # Create import history record
            ImportHistory.objects.create(
                import_type=import_type,
                file_name=', '.join(file_names),
                status='success' if total_failed == 0 else 'partial' if total_success > 0 else 'failed',
                total_records=total_success + total_failed,
                success_records=total_success,
                failed_records=total_failed,
                error_log='\n'.join(all_errors[:200]),
                imported_by=request.user
            )
        
        if total_failed > 0 and all_error_rows:
            err_resp = _create_error_report_file(all_error_rows, import_type, file_names[0] if file_names else 'import')
            if err_resp:
                messages.warning(request, f'Import completed: {total_success} success, {total_failed} errors. Download error report below.')
                request.session['import_error_report'] = None
                return err_resp
        if total_success > 0:
            messages.success(request, f'Successfully imported {total_success} records from {len(file_names)} file(s).')
        elif total_failed > 0:
            messages.error(request, f'Import failed. {total_failed} errors. Check file format and data.')
        
        return redirect('import_history')
    
    return render(request, 'core/import_data.html')

@login_required
def import_history(request):
    imports = ImportHistory.objects.all().order_by('-created_at')
    return render(request, 'core/import_history.html', {'imports': imports})


@login_required
@user_passes_test(is_admin_or_manager)
def download_import_template(request, import_type):
    """Download CSV template for import."""
    templates = {
        'product': (['code', 'name', 'category', 'price', 'cost', 'stock', 'description'], 'products_template.csv'),
        'customer': (['name', 'email', 'phone', 'address'], 'customers_template.csv'),
        'inventory': (['product_code', 'new_stock'], 'inventory_template.csv'),
        'sales': (['product_code', 'quantity'], 'sales_template.csv'),
    }
    if import_type not in templates:
        return redirect('import_data')
    headers, filename = templates[import_type]
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')  # BOM for Excel UTF-8
    writer = csv.writer(response)
    writer.writerow(headers)
    if import_type == 'product':
        writer.writerow(['BREAD001', 'Sample Bread', 'bread', '50.00', '25.00', '100', 'Description'])
    return response


@login_required
def export_data(request):
    export_type = request.GET.get('type', 'products')
    
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    
    if export_type == 'products':
        ws.title = "Products"
        headers = ['Code', 'Name', 'Category', 'Price', 'Cost', 'Stock', 'Low Stock Threshold', 'Created At']
        data = Product.objects.all().values_list(
            'code', 'name', 'category', 'price', 'cost', 'stock', 'low_stock_threshold', 'created_at'
        )
    
    elif export_type == 'customers':
        ws.title = "Customers"
        headers = ['Name', 'Email', 'Phone', 'Address', 'Loyalty Points', 'Created At']
        data = Customer.objects.all().values_list(
            'name', 'email', 'phone', 'address', 'loyalty_points', 'created_at'
        )
    
    elif export_type == 'orders':
        ws.title = "Orders"
        headers = ['Order Number', 'Customer', 'Date', 'Items', 'Subtotal', 'Tax', 'Discount', 'Total', 'Status']
        data = []
        for order in Order.objects.all().select_related('customer'):
            try:
                customer_name = order.customer.name if order.customer else 'Walk-in'
            except Exception:
                customer_name = 'Walk-in'
            data.append((
                order.order_number,
                customer_name,
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.items.count(),
                order.subtotal,
                order.tax,
                order.discount,
                order.total,
                order.status
            ))
    
    elif export_type == 'inventory':
        ws.title = "Inventory"
        headers = ['Product', 'Current Stock', 'Low Stock Threshold', 'Status']
        data = Product.objects.all().values_list('name', 'stock', 'low_stock_threshold')
    
    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
    
    # Write data
    for row_idx, row_data in enumerate(data, 2):
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    wb.save(response)
    return response

# ========== SUPPLIER VIEWS ==========

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    
    # Search
    search = request.GET.get('search')
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) | 
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    context = {
        'suppliers': suppliers,
    }
    return render(request, 'core/supplier_list.html', context)

# ========== MESSAGES/NOTIFICATIONS VIEWS ==========

@login_required
def messages_view(request):
    notifications = Notification.objects.filter(
        Q(recipient_user=request.user) |
        Q(recipient_type='admin')
    ).order_by('-created_at')
    
    # Mark as read
    notification_id = request.GET.get('read')
    if notification_id:
        notification = get_object_or_404(Notification, id=notification_id)
        notification.is_read = True
        notification.save()
    
    # Get unread count
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'core/messages.html', context)

# ========== POINT OF SALE (POS) VIEWS ==========

@login_required
def pos_view(request):
    """
    Point of Sale interface for walk-in customers
    """
    # Get all available products
    # Show all products in POS so the cashier can see items even when temporarily out of stock.
    # Ordering/checkout is still blocked server-side by `pos_create_order` when stock is insufficient.
    products = Product.objects.filter(is_archived=False).order_by('category', 'name')
    
    # Get categories for filtering
    categories = Product.CATEGORY_CHOICES
    
    # Get recent orders (last 10)
    recent_orders = Order.objects.filter(
        order_type='walk_in'
    ).select_related('customer').order_by('-created_at')[:10]
    
    # Get customers for quick selection
    customers = Customer.objects.all().order_by('name')[:20]
    
    context = {
        'products': products,
        'categories': categories,
        'recent_orders': recent_orders,
        'customers': customers,
    }
    return render(request, 'core/pos.html', context)


@login_required
@transaction.atomic
def pos_create_order(request):
    """
    AJAX view to create a new POS order
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            customer_id = data.get('customer_id')
            payment_method = (data.get('payment_method') or 'cash').lower()
            tax_percent = data.get('tax_percent', 0)
            discount = data.get('discount', 0)
            amount_received = data.get('amount_received', 0)
            notes = data.get('notes', '')
            
            if not items:
                return JsonResponse({'error': 'No items in cart'}, status=400)

            if payment_method not in ('cash', 'gcash'):
                return JsonResponse({'error': 'Invalid payment method'}, status=400)
            
            # Calculate totals
            subtotal = 0
            order_items_data = []
            
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                quantity = int(item['quantity'])
                
                if product.stock < quantity:
                    return JsonResponse({
                        'error': f'Insufficient stock for {product.name}. Available: {product.stock}'
                    }, status=400)
                
                item_subtotal = product.price * quantity
                subtotal += item_subtotal
                
                order_items_data.append({
                    'product': product,
                    'quantity': quantity,
                    'price': product.price,
                    'subtotal': item_subtotal
                })

            # Validate required raw materials for all items before creating/updating anything.
            material_requirements = {}
            for item_data in order_items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                for recipe in product.recipe.select_related('raw_material').all():
                    material_id = recipe.raw_material_id
                    needed_qty = float(recipe.quantity) * quantity
                    if material_id not in material_requirements:
                        material_requirements[material_id] = {
                            'material': recipe.raw_material,
                            'needed': 0.0,
                        }
                    material_requirements[material_id]['needed'] += needed_qty

            insufficient_materials = []
            for data_item in material_requirements.values():
                material = data_item['material']
                needed = data_item['needed']
                if float(material.stock_quantity) < needed:
                    insufficient_materials.append(
                        f"{material.name} (available: {material.stock_quantity}, needed: {needed:.2f})"
                    )

            if insufficient_materials:
                return JsonResponse({
                    'error': f"Insufficient raw materials: {', '.join(insufficient_materials)}"
                }, status=400)
            
            # Tax/discount
            try:
                tax_percent = float(tax_percent or 0)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'Invalid tax percent'}, status=400)

            if tax_percent < 0 or tax_percent > 100:
                return JsonResponse({'error': 'Tax percent must be between 0 and 100'}, status=400)

            try:
                discount = float(discount or 0)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'Invalid discount'}, status=400)

            if discount < 0:
                return JsonResponse({'error': 'Discount cannot be negative'}, status=400)

            tax = float(subtotal) * (tax_percent / 100.0)
            total = float(subtotal) + tax - discount

            if total < 0:
                return JsonResponse({'error': 'Total cannot be negative'}, status=400)

            # Payment validation
            try:
                amount_received = float(amount_received or 0)
            except (TypeError, ValueError):
                return JsonResponse({'error': 'Invalid amount received'}, status=400)

            if payment_method == 'cash':
                if amount_received < total:
                    return JsonResponse({'error': 'Insufficient cash amount received'}, status=400)
                change_amount = amount_received - total
            else:
                # Gcash: usually exact amount, but allow >= total; no change returned
                if amount_received and amount_received < total:
                    return JsonResponse({'error': 'Insufficient Gcash amount'}, status=400)
                amount_received = total
                change_amount = 0
            
            # Create order
            customer = None
            if customer_id:
                customer = Customer.objects.get(id=customer_id)
            
            order = Order.objects.create(
                customer=customer,
                order_type='walk_in',
                status='confirmed',  # POS orders are auto-confirmed
                payment_status='paid',
                payment_method=payment_method,
                amount_received=amount_received,
                change_amount=change_amount,
                subtotal=subtotal,
                tax=tax,
                discount=discount,
                total=total,
                notes=notes,
                created_by=request.user
            )
            
            # Create order items and update stock
            for item_data in order_items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                    subtotal=product.price * quantity
                )
                
                # Update stock
                old_stock = product.stock
                product.stock -= quantity
                product.save()
                
                # Record inventory transaction
                InventoryTransaction.objects.create(
                    product=product,
                    transaction_type='out',
                    quantity=quantity,
                    previous_stock=old_stock,
                    new_stock=product.stock,
                    reference=order.order_number,
                    notes=f"POS sale",
                    created_by=request.user
                )

                # Deduct raw materials based on recipe
                for recipe in product.recipe.select_related('raw_material').all():
                    material = recipe.raw_material
                    needed_qty = float(recipe.quantity) * quantity
                    old_material_stock = float(material.stock_quantity)
                    material.stock_quantity = old_material_stock - needed_qty
                    material.save()

                    RawMaterialTransaction.objects.create(
                        raw_material=material,
                        transaction_type='out',
                        quantity=needed_qty,
                        previous_stock=old_material_stock,
                        new_stock=material.stock_quantity,
                        reference=order.order_number,
                        notes=f"Used for POS sale: {product.name}",
                        created_by=request.user
                    )
            
            # Update customer loyalty points (optional)
            if customer:
                customer.loyalty_points += int(total / 10)  # 1 point per $10 spent
                customer.save()
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'order_number': order.order_number,
                'total': float(total),
                'change_amount': float(change_amount),
            })
            
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=400)
        except Customer.DoesNotExist:
            return JsonResponse({'error': 'Customer not found'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@login_required
def pos_get_product(request, product_id):
    """
    AJAX view to get product details
    """
    try:
        product = Product.objects.get(id=product_id, is_available=True)
        data = {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'stock': product.stock,
            'code': product.code,
            'category': product.get_category_display(),
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


@login_required_json
def order_modal_products(request):
    """
    AJAX: return all products for the Create New Order modal (no is_available filter).
    """
    try:
        products = Product.objects.all().order_by('name')[:200]
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'name': p.name or '',
                'price': float(p.price) if p.price is not None else 0,
                'stock': int(p.stock) if p.stock is not None else 0,
                'code': getattr(p, 'code', '') or '',
            })
        return JsonResponse({'products': data})
    except Exception as e:
        return JsonResponse({'error': str(e), 'products': []}, status=500)


@login_required
def pos_search_products(request):
    """
    AJAX view to search products
    """
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    products = Product.objects.filter(is_available=True, stock__gt=0)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )
    
    if category:
        products = products.filter(category=category)
    
    products = products.order_by('name')[:50]
    
    data = [{
        'id': p.id,
        'name': p.name,
        'price': float(p.price),
        'stock': p.stock,
        'code': p.code,
        'category': p.get_category_display(),
    } for p in products]
    
    return JsonResponse({'products': data})


@login_required
def pos_receipt(request, order_id):
    """
    View to display/print receipt
    """
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/pos_receipt.html', {'order': order})

@login_required
def notifications_api(request):
    """
    API endpoint for notifications (AJAX)
    """
    notification_type = request.GET.get('type', 'all')
    limit = int(request.GET.get('limit', 20))
    
    notifications = Notification.objects.filter(recipient_user=request.user)
    
    if notification_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif notification_type != 'all':
        notifications = notifications.filter(notification_type=notification_type)
    
    notifications = notifications[:limit]
    
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message[:100] + ('...' if len(n.message) > 100 else ''),
        'type': n.notification_type,
        'priority': n.priority,
        'is_read': n.is_read,
        'link': n.link,
        'action_text': n.action_text,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'time_ago': timesince(n.created_at),
    } for n in notifications]
    
    return JsonResponse({'notifications': data})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient_user=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    count = Notification.objects.filter(recipient_user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True, 'count': count})


@login_required
def notification_count(request):
    """Get unread notification count"""
    count = Notification.objects.filter(recipient_user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@user_passes_test(is_admin_or_manager)
def trigger_low_stock_check(request):
    """Manually trigger low stock check (admin only)"""
    if request.method == 'POST':
        count = check_low_stock_and_notify()
        messages.success(request, f'Low stock check completed. {count} notifications created.')
        return redirect('inventory_status')
    return redirect('inventory_status')


@login_required
@user_passes_test(is_admin_or_manager)
def create_bulk_notification(request):
    """Create a notification for multiple users (admin only)"""
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type', 'system')
        recipient_type = request.POST.get('recipient_type', 'admin')
        
        if recipient_type == 'all_admins':
            NotificationService.notify_admins(title, message, notification_type)
            messages.success(request, f'Notification sent to all admins')
        elif recipient_type == 'all_staff':
            NotificationService.notify_staff(title, message, notification_type)
            messages.success(request, f'Notification sent to all staff')
        
        return redirect('messages')
    
    return render(request, 'core/create_notification.html')

def index(request):
    """Simple index view that redirects to login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

