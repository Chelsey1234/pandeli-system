from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_performance_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200)),
                ('subtitle', models.CharField(blank=True, max_length=300)),
                ('image', models.ImageField(upload_to='app_features/')),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['order', '-created_at'],
            },
        ),
    ]
