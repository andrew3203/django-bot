# Generated by Django 3.2.9 on 2022-01-18 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0012_supportmessage_available_words'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='file_tg_id',
            field=models.CharField(blank=True, default=None, max_length=100, verbose_name='Id файла в телеграм'),
        ),
        migrations.AddField(
            model_name='supportmessage',
            name='file_tg_id',
            field=models.CharField(blank=True, default=None, max_length=100, verbose_name='Id файла в телеграм'),
        ),
    ]
