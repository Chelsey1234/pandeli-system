from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_bundle'),
    ]

    operations = [
        # Order: date-based filtering is the most common query pattern
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['created_at', 'status'], name='core_order_created_status_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_type'], name='core_order_type_idx'),
        ),
        # OrderItem: joining to order by date is very common in reports
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['order', 'product'], name='core_orderitem_order_product_idx'),
        ),
        # Product: stock-level queries
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['stock', 'is_archived'], name='core_product_stock_archived_idx'),
        ),
        # Notification: per-user unread lookup on every page
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient_user', 'is_read', '-created_at'], name='core_notif_user_read_date_idx'),
        ),
    ]
