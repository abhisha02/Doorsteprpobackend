# Generated by Django 5.0.7 on 2024-08-05 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0009_alter_professionalrating_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='review',
            field=models.TextField(blank=True, null=True),
        ),
    ]
