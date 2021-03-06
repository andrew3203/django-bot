# Generated by Django 3.2.12 on 2022-03-17 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0019_auto_20220122_1441'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_sub_question',
            field=models.BooleanField(default=False, help_text='Поставьте галочку, чтобы использовать как промежуточный вопрос', verbose_name='Под вопрос'),
        ),
        migrations.AddField(
            model_name='question',
            name='need_answer',
            field=models.BooleanField(default=False, help_text='Поставьте галочку, чтобы бот отвечал пользователю на этот под вопрос', verbose_name='Давать обратную связь на подвопрос'),
        ),
    ]
