# Generated by Django 5.1 on 2024-08-21 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0013_booking_temp_professional'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='pro_flag',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
