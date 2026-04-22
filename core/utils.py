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
    Generate forecast using weighted moving average with day-of-week adjustment.
    Accurate, deterministic, and fast (single DB query + bulk upsert).
    """
    try:
        end_date = timezone.now().date()
        # Pull 90 days of history for better day-of-week patterns
        start_date = end_date - timedelta(days=90)

        daily_sales = list(OrderItem.objects.filter(
            product=product,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        ).values('order__created_at__date').annotate(
            total=Sum('quantity')
        ).order_by('order__created_at__date'))

        # Build full 90-day series (fill missing days with 0)
        sales_map = {row['order__created_at__date']: int(row['total']) for row in daily_sales}
        full_series = []
        for i in range(90):
            d = start_date + timedelta(days=i)
            full_series.append((d, sales_map.get(d, 0)))

        # Day-of-week average (0=Mon … 6=Sun)
        dow_totals = [0] * 7
        dow_counts = [0] * 7
        for d, qty in full_series:
            dow = d.weekday()
            dow_totals[dow] += qty
            dow_counts[dow] += 1
        dow_avg = [
            dow_totals[i] / dow_counts[i] if dow_counts[i] else 0
            for i in range(7)
        ]

        # Weighted moving average of last 30 days (more recent = higher weight)
        recent = [qty for _, qty in full_series[-30:]]
        weights = list(range(1, 31))  # 1..30
        wma = sum(v * w for v, w in zip(recent, weights)) / sum(weights) if sum(weights) else 0

        # Overall daily average for scaling
        overall_avg = sum(qty for _, qty in full_series) / 90 if full_series else 0

        # Build forecast objects in memory, then bulk upsert
        to_upsert = []
        for i in range(days):
            forecast_date = end_date + timedelta(days=i + 1)
            dow = forecast_date.weekday()

            # Blend WMA with day-of-week pattern
            if overall_avg > 0:
                dow_factor = dow_avg[dow] / overall_avg
            else:
                dow_factor = 1.0

            predicted = max(0, round(wma * dow_factor))
            margin = max(1, round(predicted * 0.25))  # 25% confidence interval

            to_upsert.append(SalesForecast(
                product=product,
                forecast_date=forecast_date,
                predicted_quantity=predicted,
                confidence_lower=max(0, predicted - margin),
                confidence_upper=predicted + margin,
                model_used='WMA'
            ))

        # Bulk upsert — single query instead of N round trips
        SalesForecast.objects.bulk_create(
            to_upsert,
            update_conflicts=True,
            unique_fields=['product', 'forecast_date'],
            update_fields=['predicted_quantity', 'confidence_lower', 'confidence_upper', 'model_used'],
        )

        return to_upsert

    except Exception as e:
        logger.error(f"Error generating forecast for {product.name}: {str(e)}")
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
    Calculate profit analysis for a given period.
    Uses OrderItem if available, falls back to product_name stored in Order.
    """
    if not end_date:
        end_date = timezone.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    total_revenue = float(orders.aggregate(total=Sum('total'))['total'] or 0)
    total_cost = 0
    product_costs = {}

    # Try OrderItem first
    has_items = False
    for order in orders:
        items = list(order.items.all())
        if items:
            has_items = True
            for item in items:
                cost = float(item.product.cost) * item.quantity
                total_cost += cost
                name = item.product.name
                if name not in product_costs:
                    product_costs[name] = {'revenue': 0, 'cost': 0, 'quantity': 0}
                product_costs[name]['revenue'] += float(item.subtotal)
                product_costs[name]['cost'] += cost
                product_costs[name]['quantity'] += item.quantity

    # Fallback: use product_name stored directly in order
    if not has_items:
        for order in orders:
            if order.product_name:
                name = order.product_name
                revenue = float(order.total)
                # Try to get cost from Product table
                product = Product.objects.filter(name__iexact=name).first()
                cost = float(product.cost) if product else 0
                if name not in product_costs:
                    product_costs[name] = {'revenue': 0, 'cost': 0, 'quantity': 0}
                product_costs[name]['revenue'] += revenue
                product_costs[name]['cost'] += cost
                product_costs[name]['quantity'] += 1
                total_cost += cost

    gross_profit = total_revenue - total_cost
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

    for name, data in product_costs.items():
        data['profit'] = data['revenue'] - data['cost']
        data['margin'] = (data['profit'] / data['revenue'] * 100) if data['revenue'] > 0 else 0

    return {
        'period': {'start': start_date, 'end': end_date},
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'gross_profit': gross_profit,
        'profit_margin': profit_margin,
        'products': product_costs,
    }