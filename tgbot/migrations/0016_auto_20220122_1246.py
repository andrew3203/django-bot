# Generated by Django 3.2.9 on 2022-01-22 09:46

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0015_auto_20220121_0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='Файл'),
        ),
        migrations.AlterField(
            model_name='supportmessage',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, max_length=255, verbose_name='Файл'),
        ),
    ]
