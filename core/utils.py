import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .models import OrderItem, Product, SalesForecast, Order, Notification, RawMaterial
from django.db.models import Sum, F
from django.utils import timezone
import logging as _logging
import logging

logger = _logging.getLogger(__name__)

def generate_sales_forecast(product, days=30):
    """
    Generate sales forecast for a product.
    Uses Prophet if available, otherwise ARIMA via statsmodels, else simple moving average.
    """
    try:
        # Get historical sales data (last 90 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=90)
        
        sales_data = OrderItem.objects.filter(
            product=product,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        ).values(
            'order__created_at__date'
        ).annotate(
            total=Sum('quantity')
        ).order_by('order__created_at__date')
        
        if len(sales_data) < 7:
            return generate_simple_forecast(product, days)
        
        df = pd.DataFrame(list(sales_data))
        df.columns = ['ds', 'y']
        df['ds'] = pd.to_datetime(df['ds'])
        df = df.set_index('ds').resample('D').sum().fillna(0).reset_index()
        
        # Try Prophet first (optional dependency)
        try:
            from prophet import Prophet
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False,
            )
            model.fit(df)
            future = model.make_future_dataframe(periods=days)
            forecast = model.predict(future)
            forecasts = []
            for _, row in forecast.tail(days).iterrows():
                forecast_date = row['ds'].date()
                predicted = max(0, int(round(row['yhat'])))
                lower = max(0, int(round(row.get('yhat_lower', predicted - 2))))
                upper = max(0, int(round(row.get('yhat_upper', predicted + 2))))
                forecast_obj, _ = SalesForecast.objects.update_or_create(
                    product=product, forecast_date=forecast_date,
                    defaults={'predicted_quantity': predicted, 'confidence_lower': lower,
                              'confidence_upper': upper, 'model_used': 'Prophet'}
                )
                forecasts.append(forecast_obj)
            return forecasts
        except ImportError:
            pass
        
        # Try statsmodels ARIMA
        try:
            from statsmodels.tsa.arima.model import ARIMA
            ts = df.set_index('ds')['y']
            model = ARIMA(ts, order=(1, 0, 1))
            fitted = model.fit()
            forecast_vals = fitted.forecast(steps=days)
            forecasts = []
            for i, val in enumerate(forecast_vals):
                forecast_date = end_date + timedelta(days=i + 1)
                predicted = max(0, int(round(val)))
                forecast_obj, _ = SalesForecast.objects.update_or_create(
                    product=product, forecast_date=forecast_date,
                    defaults={'predicted_quantity': predicted, 'confidence_lower': max(0, predicted - 3),
                              'confidence_upper': predicted + 3, 'model_used': 'ARIMA'}
                )
                forecasts.append(forecast_obj)
            return forecasts
        except ImportError:
            pass
        
        return generate_simple_forecast(product, days)
    except Exception as e:
        logger.error(f"Error generating forecast for {product.name}: {str(e)}")
        return generate_simple_forecast(product, days)

def generate_simple_forecast(product, days=30):
    """
    Generate simple forecast using moving average.
    Always generates forecasts even with no order history.
    """
    try:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        total_qty = OrderItem.objects.filter(
            product=product,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Average daily sales — minimum 1 to always produce a forecast
        avg_sales = max(1, round(total_qty / 30))
        
        forecasts = []
        for i in range(days):
            forecast_date = end_date + timedelta(days=i + 1)
            # Small deterministic variation based on day of week
            dow_factor = [0, 1, 1, 0, 1, 2, 2][forecast_date.weekday()]
            predicted = max(0, avg_sales + dow_factor)
            
            forecast_obj, _ = SalesForecast.objects.update_or_create(
                product=product,
                forecast_date=forecast_date,
                defaults={
                    'predicted_quantity': predicted,
                    'confidence_lower': max(0, predicted - 2),
                    'confidence_upper': predicted + 2,
                    'model_used': 'Moving Average'
                }
            )
            forecasts.append(forecast_obj)
        
        return forecasts
        
    except Exception as e:
        logger.error(f"Error generating simple forecast for {product.name}: {str(e)}")
        return []

def check_low_stock_alerts():
    """
    Check for low stock items and create notifications
    """
    # Check products
    low_stock_products = Product.objects.filter(
        stock__lte=F('low_stock_threshold'),
        is_available=True
    )
    
    from .notifications import NotificationService
    for product in low_stock_products:
        NotificationService.notify_admins(
            title=f"Low Stock Alert: {product.name}",
            message=f"Product {product.name} has only {product.stock} units left (threshold: {product.low_stock_threshold})",
            notification_type='stock',
            priority='high' if product.stock == 0 else 'medium'
        )
    
    # Check raw materials
    low_stock_materials = RawMaterial.objects.filter(
        stock_quantity__lte=F('low_stock_threshold')
    )
    
    for material in low_stock_materials:
        NotificationService.notify_admins(
            title=f"Low Material Alert: {material.name}",
            message=f"Raw material {material.name} has only {material.stock_quantity} {material.unit} left",
            notification_type='stock',
            priority='high' if material.stock_quantity == 0 else 'medium'
        )
    
    return len(low_stock_products) + len(low_stock_materials)

def calculate_profit_analysis(start_date=None, end_date=None):
    """
    Calculate profit analysis for a given period
    """
    if not end_date:
        end_date = timezone.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Include all orders in the selected period (regardless of payment status)
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )
    
    total_revenue = orders.aggregate(total=Sum('total'))['total'] or 0
    
    # Calculate cost of goods sold
    total_cost = 0
    product_costs = {}
    
    for order in orders:
        for item in order.items.all():
            cost = item.product.cost * item.quantity
            total_cost += cost
            
            if item.product.name not in product_costs:
                product_costs[item.product.name] = {
                    'revenue': 0,
                    'cost': 0,
                    'quantity': 0
                }
            
            product_costs[item.product.name]['revenue'] += float(item.subtotal)
            product_costs[item.product.name]['cost'] += float(cost)
            product_costs[item.product.name]['quantity'] += item.quantity
    
    gross_profit = total_revenue - total_cost
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Calculate profit by product
    for product_name, data in product_costs.items():
        data['profit'] = data['revenue'] - data['cost']
        data['margin'] = (data['profit'] / data['revenue'] * 100) if data['revenue'] > 0 else 0
    
    return {
        'period': {
            'start': start_date,
            'end': end_date
        },
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'gross_profit': gross_profit,
        'profit_margin': profit_margin,
        'products': product_costs
    }