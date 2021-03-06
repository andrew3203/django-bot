# Generated by Django 3.2.9 on 2022-01-22 11:16

import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0016_auto_20220122_1246'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='sticker',
            field=models.CharField(blank=True, help_text='Отправьте стикер боту, чтобы узнать его ID, затем вставьте его сюда без лишних символов', max_length=250, verbose_name='Id стикера в телеграм'),
        ),
        migrations.AddField(
            model_name='supportmessage',
            name='sticker',
            field=models.CharField(blank=True, help_text='Отправьте стикер боту, чтобы узнать его ID, затем вставьте его сюда без лишних символов', max_length=250, verbose_name='Id стикера в телеграм'),
        ),
        migrations.AlterField(
            model_name='question',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, help_text='Чтобы добавить файл/аудио/большое видео используйте ссылку в сообщении', max_length=255, verbose_name='Фото (png, jpeg) / Видео (mp4)'),
        ),
        migrations.AlterField(
            model_name='supportmessage',
            name='file',
            field=cloudinary.models.CloudinaryField(blank=True, help_text='Чтобы добавить файл/аудио/большое видео используйте ссылку в сообщении', max_length=255, verbose_name='Фото (png, jpeg) / Видео (mp4)'),
        ),
        migrations.AlterField(
            model_name='supportmessage',
            name='text',
            field=models.TextField(blank=True, max_length=450, verbose_name='Текст сообщения'),
        ),
    ]
