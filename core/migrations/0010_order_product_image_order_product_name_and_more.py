from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_inventorytransaction_core_invtrans_product_date_idx_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE core_order ADD COLUMN IF NOT EXISTS product_image text NULL;
                ALTER TABLE core_order ADD COLUMN IF NOT EXISTS product_name text NULL;
            """,
            reverse_sql="""
                ALTER TABLE core_order DROP COLUMN IF EXISTS product_image;
                ALTER TABLE core_order DROP COLUMN IF EXISTS product_name;
            """,
            state_operations=[
                migrations.AddField(
                    model_name='order',
                    name='product_image',
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='order',
                    name='product_name',
                    field=models.TextField(blank=True, null=True),
                ),
            ],
        ),
        migrations.AlterField(
            model_name='order',
            name='order_type',
            field=models.CharField(
                choices=[('online', 'Online'), ('walk_in', 'Walk-in'), ('pickup', 'Pickup'), ('delivery', 'Delivery')],
                default='walk_in',
                max_length=10,
            ),
        ),
    ]
