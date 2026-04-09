from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_notification_action_text_notification_expires_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[("cash", "Cash"), ("gcash", "Gcash")],
                default="cash",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="amount_received",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="order",
            name="change_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]

