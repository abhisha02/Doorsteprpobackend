# Generated by Django 5.0.7 on 2024-07-19 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_rename_name_professional_first_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='otpstore',
            name='encrypted_otp',
        ),
        migrations.RemoveField(
            model_name='otpstore',
            name='encryption_key',
        ),
        migrations.AddField(
            model_name='otpstore',
            name='otp',
            field=models.IntegerField(null=True),
        ),
    ]
