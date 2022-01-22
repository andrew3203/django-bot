# Generated by Django 3.2.9 on 2022-01-22 11:41

import cloudinary.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0018_auto_20220122_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, default=None, help_text='Чтобы добавить файл/аудио/большое видео используйте ссылку в сообщении', max_length=255, null=True, verbose_name='Фото (png, jpeg) / Видео (mp4)'),
        ),
        migrations.AlterField(
            model_name='supportmessage',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, default=None, help_text='Чтобы добавить файл/аудио/большое видео используйте ссылку в сообщении', max_length=255, null=True, verbose_name='Фото (png, jpeg) / Видео (mp4)'),
        ),
    ]
