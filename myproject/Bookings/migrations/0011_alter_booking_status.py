# Generated by Django 5.0.7 on 2024-08-05 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bookings', '0010_booking_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('created', 'Created'), ('professional_assigned', 'Professional Assigned'), ('professional_none', 'Professional None'), ('rescheduled', 'Rescheduled'), ('task_done', 'Task Done'), ('payment_done', 'Payment Done'), ('completed', 'Completed'), ('review_done', 'Review Done')], default='pending', max_length=200),
        ),
    ]
