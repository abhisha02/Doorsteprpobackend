# Generated by Django 5.0.7 on 2024-07-26 13:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Services', '0004_service_duration'),
        ('authentication', '0015_remove_professional_groups_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobprofile',
            name='profession',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Services.category'),
        ),
    ]
