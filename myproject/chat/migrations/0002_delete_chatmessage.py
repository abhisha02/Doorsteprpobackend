# Generated by Django 5.0.7 on 2024-08-08 06:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChatMessage',
        ),
    ]
