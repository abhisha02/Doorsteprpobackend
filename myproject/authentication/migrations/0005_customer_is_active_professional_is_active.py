# Generated by Django 5.0.7 on 2024-07-18 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_alter_professional_earned_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='professional',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
