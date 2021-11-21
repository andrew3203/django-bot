from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render

from corporatum.settings import DEBUG

from tgbot.models import *
from tgbot.forms import BroadcastForm

from tgbot.tasks import broadcast_message
from tgbot.handlers.broadcast_message.utils import _send_message

from django_celery_beat.models import (
    PeriodicTask, ClockedSchedule,
    IntervalSchedule, CrontabSchedule,
    SolarSchedule
)



admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(PeriodicTask)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'username', 'first_name', 'last_name', 
        'language_code', 'deep_link',
        'created_at', 'updated_at', "is_blocked_bot",
    ]
    list_filter = ["is_blocked_bot", "is_moderator"]
    search_fields = ('username', 'user_id')

    actions = ['broadcast']

    def broadcast(self, request, queryset):
        """ Select users via check mark in django-admin panel, then select "Broadcast" to send message"""
        user_ids = queryset.values_list('user_id', flat=True).distinct().iterator()
        if 'apply' in request.POST:
            broadcast_message_text = request.POST["broadcast_text"]

            if DEBUG:  # for test / debug purposes - run in same thread
                for user_id in user_ids:
                    _send_message(
                        user_id=user_id,
                        text=broadcast_message_text,
                    )
                self.message_user(request, f"Just broadcasted to {len(queryset)} users")
            else:
                broadcast_message.delay(text=broadcast_message_text, user_ids=list(user_ids))
                self.message_user(request, f"Broadcasting of {len(queryset)} messages has been started")

            return HttpResponseRedirect(request.get_full_path())
        else:
            form = BroadcastForm(initial={'_selected_action': user_ids})
            return render(
                request, "admin/broadcast_message.html", {'form': form, 'title': u'Broadcast message'}
            )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ('short_name',)
    list_display = ('short_name', 'difficulty_lvl', 'get_test', 'get_theme')
    list_display_links = ('short_name', 'difficulty_lvl')
    list_filter = (
        ('difficulty_lvl', admin.ChoicesFieldListFilter),
        ('answer_type', admin.ChoicesFieldListFilter),
    )
    fieldsets = (
        (None, {
            'fields': (
                ("get_test", "get_theme"),
            ),
        }),
        ('Основное', {
            'fields': (
                ("short_name", "difficulty_lvl"),
                ("timer", "file"),
                ('text')
            ),
        }),
        ('Ответы', {
            'fields': (
                ('answer_type',),
                ("answer_variants",),
                ('right_answers',)
            ),
        }),
    )
    readonly_fields = ('get_test', 'get_theme')


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    search_fields = ['short_name']
    list_display = ['short_name', 'is_visible', 'get_theme']
    list_display_links = ('short_name',)
    list_filter = (
        ('is_visible', admin.BooleanFieldListFilter),
    )
    fieldsets = (
        ('Общая информация', {
            'fields': (
                ("short_name", "is_visible", 'get_theme'),
            ),
        }),
        ('Вопросы', {
            'fields': (
                ("questions",),
            ),
        }),
    )
    filter_horizontal = ('questions',)
    readonly_fields = ('get_theme',)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    search_fields = ['short_name']
    list_display = ['short_name', 'is_visible']
    list_display_links = ('short_name',)
    list_filter = (
        ('is_visible', admin.BooleanFieldListFilter),
    )
    fieldsets = (
        ('Общая информация', {
            'fields': (
                ("short_name", "is_visible"),
            ),
        }),
        ('Тесты', {
            'fields': (
                ("tests",),
            ),
        }),
    )
    filter_horizontal = ('tests',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    search_fields = ['question', 'user', 'date_created', 'is_correct']
    list_display = ['question', 'user', 'date_created', 'is_correct']
    list_display_links = ('question',)
    list_filter = (
        ('is_correct', admin.BooleanFieldListFilter),
        ('user', admin.RelatedFieldListFilter),
        ('question', admin.RelatedFieldListFilter),
    )
    fieldsets = (
        ('Информация об ответе', {
            'fields': (
                ("user", "question", 'is_correct'),
                ("date_created", "time_to_solve"),
            ),
        }),
        ('Ответ', {
            'fields': (
                ("answer_text",),
            ),
        }),
    )
    readonly_fields = (
        'answer_text', 
        'date_created', 
        'time_to_solve',
        'user',
        'question'
        )


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    search_fields = ['short_name', 'cost', 'gold_amount']
    list_display = ['short_name', 'cost', 'gold_amount']
    list_display_links = ('short_name',)
    list_filter = (
        ('cost', admin.AllValuesFieldListFilter),
        ('gold_amount', admin.AllValuesFieldListFilter),
    )
    fieldsets = (
        (None, {
            'fields': (
                ("short_name"),
                ("cost", "gold_amount"),
            ),
        }),
    )


@admin.register(Promocode)
class PromocodeAdmin(admin.ModelAdmin):
    search_fields = ['short_name', 'date_created', 'discount']
    list_display = ['short_name', 'discount', 'clics_amount']
    list_display_links = ('short_name', 'discount')
    list_filter = (
        ('discount', admin.AllValuesFieldListFilter),
        ('plan', admin.RelatedFieldListFilter)
    )
    fieldsets = (
        ('Основная информация', {
            'fields': (
                ("short_name", 'discount'),
                ('plan', "clics_amount",)
            ),
        }),
        ('Дополнительная информаци', {
            'fields': (
                ("date_created", "date_expire"),
                ('clics_left')
            ),
        }),
    )
    readonly_fields = (
        'date_created', 
        'clics_amount',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    search_fields = ['user', 'promocode', 'plan']
    list_display = ['user', 'plan', 'promocode', 'date_created']
    list_display_links = ('user', 'plan')
    list_filter = (
        ('plan', admin.RelatedFieldListFilter),
    )
    fieldsets = (
        ('Информация о платеже', {
            'fields': (
                ("user",),
                ('date_created'),
                ("plan", 'promocode')
            ),
        }),
    )
    readonly_fields = (
        'user', 
        'promocode',
        'plan',
        'date_created'
    )


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    search_fields = ['role', 'text']
    list_display = ['role', 'is_active']
    list_display_links = ('role',)
    list_filter = (
        ('is_active', admin.BooleanFieldListFilter),
    )
    fieldsets = (
        ('Информация о сообщении', {
            'fields': (
                ("role", 'is_active'),
                ('file'),
                ('text')
            ),
        }),
    )
    
    
admin.site.site_title = 'Управление курсами CORPORATUM'
admin.site.site_header = 'Управление курсами CORPORATUM'

