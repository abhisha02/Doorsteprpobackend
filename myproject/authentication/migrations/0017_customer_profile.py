# Generated by Django 5.0.7 on 2024-07-27 01:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0016_alter_jobprofile_profession'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='profile',
            field=models.ImageField(blank=True, null=True, upload_to='user/profile_pic/'),
        ),
    ]
