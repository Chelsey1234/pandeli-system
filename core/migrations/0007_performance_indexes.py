from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_product_featured_flags'),
    ]

    operations = [
        # Product indexes
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_archived', 'is_available'], name='core_product_archived_avail_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category'], name='core_product_category_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_best_seller'], name='core_product_best_seller_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_new_arrival'], name='core_product_new_arrival_idx'),
        ),
        # OrderItem indexes
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['product'], name='core_orderitem_product_idx'),
        ),
        migrations.AddIndex(
            model_name='orderitem',
            index=models.Index(fields=['order'], name='core_orderitem_order_idx'),
        ),
        # InventoryTransaction indexes
        migrations.AddIndex(
            model_name='inventorytransaction',
            index=models.Index(fields=['product', '-created_at'], name='core_invtrans_product_date_idx'),
        ),
    ]
