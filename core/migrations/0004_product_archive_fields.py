from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_order_payment_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
    ]

