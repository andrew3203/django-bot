# Generated by Django 3.2.9 on 2021-11-25 14:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0009_auto_20211122_0902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='plan',
            field=models.ForeignKey(blank=True, help_text='Вариант оплаты', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', related_query_name='payment', to='tgbot.paymentplan', verbose_name='Вариант оплаты'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='promocode',
            field=models.ForeignKey(blank=True, default=None, help_text='Промокод', null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='payments', related_query_name='payment', to='tgbot.promocode', verbose_name='Промокод'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(blank=True, default='DELETED', help_text='Пользователь', on_delete=django.db.models.deletion.SET_DEFAULT, related_name='payments', related_query_name='payment', to='tgbot.user', verbose_name='Пользователь'),
        ),
    ]
