from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_order_product_image_order_product_name_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS core_bundle (
                    id bigserial PRIMARY KEY,
                    name varchar(200) NOT NULL,
                    description text NOT NULL DEFAULT '',
                    subtitle varchar(200) NOT NULL DEFAULT '',
                    item_count integer NOT NULL DEFAULT 1,
                    category varchar(20) NOT NULL DEFAULT '',
                    is_active boolean NOT NULL DEFAULT true,
                    "order" integer NOT NULL DEFAULT 0,
                    created_at timestamptz NOT NULL DEFAULT now(),
                    updated_at timestamptz NOT NULL DEFAULT now()
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS core_bundle;",
            state_operations=[
                migrations.CreateModel(
                    name='Bundle',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=200)),
                        ('description', models.TextField(blank=True)),
                        ('subtitle', models.CharField(blank=True, max_length=200)),
                        ('item_count', models.PositiveIntegerField(default=1)),
                        ('category', models.CharField(blank=True, max_length=20)),
                        ('is_active', models.BooleanField(default=True)),
                        ('order', models.PositiveIntegerField(default=0)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={'ordering': ['order', '-created_at']},
                ),
            ],
        ),
    ]
