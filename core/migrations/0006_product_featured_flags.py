from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_order_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_new_arrival',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='is_best_seller',
            field=models.BooleanField(default=False),
        ),
    ]
