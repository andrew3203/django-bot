from __future__ import annotations
from typing import Union, Optional, Tuple
from flashtext import KeywordProcessor
import math
import unicodedata
import random
from datetime import time, timedelta, datetime

from django.db import models
from django.contrib import admin
from django.db.models import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from telegram import Update

from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, HelpContext


def get_deadline(days=30):
    return now() + timedelta(days=days)


def _normalize_text(text):
    return unicodedata.normalize("NFKD", text.casefold())


class User(CreateUpdateTracker):
    user_id = models.IntegerField(_('Chat id'), primary_key=True)  # telegram_id
    email = models.EmailField(_('Почта'), unique=True, blank=True, null=True)
    username = models.CharField(_('Никнейн'), max_length=32, **nb)
    first_name = models.CharField(_('Имя'), max_length=256, default='Гость')
    last_name = models.CharField(_('Фамилия'), max_length=256, **nb)

    gold = models.IntegerField(_('Золото'), blank=True, default=1)
    date_joined = models.DateTimeField(_('Дата регистрации'), auto_now_add=True, blank=True)
    language_code = models.CharField(_('Язык'), max_length=8, **nb)
    deep_link = models.CharField(max_length=64, **nb)

    is_blocked_bot = models.BooleanField(_('Заблокировал бота'), default=False)
    is_banned = models.BooleanField(_('Забанин'), default=False)

    is_active = models.BooleanField(_('Активный'), default=False)
    is_admin = models.BooleanField(_('Администратор'), default=False)
    is_moderator = models.BooleanField(_('Модератор'), default=False)
    
    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.username}'

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-date_joined']
        unique_together = [['user_id', 'email']]

    def to_flashtext(self):
        return {
            str(self.email): ['user_email'],
            self.username: ['username'],
            self.first_name: ['first_name'],
            self.last_name: ['last_name'],
            str(self.gold): ['user_gold'],
        }

    def add_gold(self, plan,):
        self.gold += plan.gold_amount

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"

    @classmethod
    def get_user_and_created(cls, update: Update, context) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user(cls, update: Update, context) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()


class Question(models.Model):
    short_name = models.CharField(_('Название'),max_length=30, unique=True)
    text = models.TextField(_('Текст вопроса'), max_length=1200)
    timer = models.TimeField(_('Время на решение'), blank=True)
    file = models.FileField(_('Файл'), upload_to='question/', blank=True)
    answer_variants = models.TextField(_('Варианты ответа'), max_length=500, blank=True)
    right_answers = models.TextField(_('Правильные варианты'), max_length=1000, blank=True)

    class AnswerType(models.TextChoices):
        WORD = 'Word', _('Слово')
        FLY_BTN = 'FlyButtons', _('Летающие кнопки')
        SENTENSE = 'Sentence', _('Предложение')
        POLL = 'Poll', _('Опрос')
        QUIZ = 'Quiz', _('Квиз')
        KB_BTN = 'KBButtons', _('Доп. Клавиатура')

    class DifficultyLvl(models.IntegerChoices):
        TEST = 0, _('Пробный')
        FIRST = 1, _('Начальный')
        SECOND = 2, _('Средний')
        THIRD = 3, _('Сложный')
        FOURTH = 4, _('Особый')

    answer_type = models.CharField(
        _('Тип ответа'),
        max_length=15,
        choices=AnswerType.choices,
        default=AnswerType.FLY_BTN
    )
    difficulty_lvl = models.IntegerField(
        _('Уровень сложности'), 
        choices=DifficultyLvl.choices,
        default=DifficultyLvl.FIRST
    )

    class Meta:
        verbose_name = _('Вопрос')
        verbose_name_plural = _('Вопросы')

    def __str__(self):
        return self.short_name

    

    def to_flashtext(self):
        return {
            self.short_name: ['question_name'],
            self.text: ['question_text'],
            self.timer.strftime("%H:%M:%S"): ['time_to_question'],
            self.get_difficulty_lvl_name(): ['question_lvl'],
        }

    def get_time_left(self, start_time):
        end_time = self.timer + start_time
        time_left = (datetime.min + (end_time - now())).time()
        return {'time_left': time_left.strftime("%H:%M:%S")}

    def is_answer_correct(self, ans, user, start_time) -> bool:
        answers = self.right_answers.split(';')
        answers = list(map(_normalize_text, answers))

        if self.answer_type == self.AnswerType.FLY_BTN:
            ans = _normalize_text(ans)
            is_correct = True if ans in answers else False

        elif self.answer_type == self.AnswerType.POLL:
            ans = list(map(_normalize_text, ans))
            is_correct = True if len(set(ans) and set(answers)) > 0 else False

        elif self.answer_type in [self.AnswerType.WORD, self.AnswerType.KB_BTN]:
            ans = _normalize_text(ans.replace(' ', ''))
            is_correct = True if ans in answers else False

        elif self.answer_type == self.AnswerType.SENTENSE:
            is_correct = True if len(ans) > 0 else False

        elif self.answer_type == self.AnswerType.QUIZ:
            is_correct, ans = ans

        time_to_solve = (datetime.min + (now() - start_time)).time()
        ans = Answer.objects.create(
            question=self,
            user=user,
            time_to_solve=time_to_solve,
            answer_text=ans,
            is_correct=is_correct,
        )
        ans.save()

        return is_correct

    def get_difficulty_lvl_name(self):
        return str(dict(self.DifficultyLvl.choices).get(self.difficulty_lvl))

    @staticmethod
    def get_lvls_for_test(test_id):
        s = set()
        for q in Question.objects.filter(test__id=test_id):
            s.add((q.difficulty_lvl, q.get_difficulty_lvl_name()))
        return sorted(s, key=lambda x: x[0])
    
    @admin.display(description='Тест')
    def get_test(self):
        obj = Test.objects.filter(questions=self).first()
        return str(obj)

    @admin.display(description='Тема')
    def get_theme(self):
        obj = Test.objects.filter(questions=self).first()
        re = Theme.objects.filter(tests=obj).first()
        return str(re)
    

class Test(models.Model):
    short_name = models.CharField(_('Название'), max_length=50)
    questions = models.ManyToManyField(
        Question,
        related_name=_('tests'),
        related_query_name=_('test'),
        verbose_name=_(u'Вопросы'),
        help_text= _(u'Выпросы этого теста'),
        blank=True
    )
    is_visible = models.BooleanField(_('Виден'), default=False)

    class Meta:
        verbose_name = _('Тест')
        verbose_name_plural = _('Тесты')
        ordering = ['short_name']

    def __str__(self):
        return f'{self.short_name}'

    def to_flashtext(self):
        return {
            self.short_name: ['test_name'],
        }

    def get_difficulty_lvl(self):
         ans = [q.difficulty_lvl for q in Question.objects.filter(tests=self)]
         return math.mean(ans)

    @staticmethod
    def get_test_id():
        re = [o.id for o in Test.objects.filter(questions__difficulty_lvl=0)]
        N = len(re)
        return re[random.randint(0, N)]  if N > 1 else re[0]

    @staticmethod
    def tests_of_theme(theme_id):
        d = {}
        for t in Test.objects.filter(theme__id=theme_id):
                d[t.short_name] = t.id
        return d

    @staticmethod
    def get_question(num, test_id) -> Optional[bool]:
        questions = Question.objects.filter(tests___id=test_id)
        if len(questions) > num:
            return questions[num]
        else:
            return False

    @staticmethod
    def get_new_question(user_id, test_id): # показать следующий не сделанный вопрос
        questions = Question.objects.filter(tests___id=test_id)
        questions_closed = Question.objects.filter(answers__is_correct=True, answers__user__user_id=user_id)

        ans = sorted(set(questions) - set(questions_closed))
        return ans[0] if len(ans) > 0 else 0

    @admin.display(description='Тема')
    def get_theme(self):
        obj = Theme.objects.filter(tests=self).first()
        if obj is None:
            return 'Нет'
        else:
            return str(obj)


class Theme(models.Model):
    short_name = models.CharField(_('Название'), max_length=50, blank=True)
    is_visible = models.BooleanField(_('Видна'), default=False)
    
    tests = models.ManyToManyField(
        Test,
        related_name=_('themes'),
        related_query_name=_('theme'),
        verbose_name=_(u'Тесты'),
        help_text=_(u'Тесты этой темы'),
        blank=True
    )

    class Meta:
        verbose_name = _('Тема')
        verbose_name_plural = _('Темы')
        ordering = ['short_name']
    
    def __str__(self) -> str:
        return f'{self.short_name}'

    def to_flashtext(self):
        return {
            self.short_name: ['theme_name'],
        }

    @staticmethod
    def get_thems():
        return Theme.objects.filter(is_visible=True)


class Answer(models.Model):
    question = models.OneToOneField(
        Question,
        related_name=_('answers'),
        related_query_name=_('answer'),
        verbose_name=_(u'Вопрос'),
        help_text= _(u'Вопрос этого ответа'),
        on_delete=models.CASCADE, blank=True, null=True
    )
    user = models.OneToOneField(
        User,
        related_name=_(u'answer'),
        related_query_name=_('answer'),
        verbose_name=_(u'Автор ответа'),
        help_text= _(u'Автор этого ответа'),
        on_delete=models.CASCADE, blank=True, null=True
    )
    date_created = models.DateTimeField(_('Дата ответа'), auto_now_add=True)
    time_to_solve = models.TimeField(_('Время, потраченное на решение'))
    answer_text = models.TextField(_('Текст ответа'), max_length=500, blank=True)
    is_correct = models.BooleanField(_('Правильность'), blank=True, default=False)

    class Meta:
        verbose_name = _('Ответ')
        verbose_name_plural = _('Ответы')
        ordering = ['-date_created']

    def __str__(self) -> str:
        return f'Ответ от: {str(self.user)}'

    def to_flashtext(self):
        is_correct = 'Да' if self.is_correct else 'Нет'
        d1 =  {
            is_correct: ['is_correct', 'is_answer_correct'],
            self.time_to_solve.strftime("%H:%M:%S"): ['time_to_solve'],
        }
        d2 = self.question.to_flashtext()
        d3 = self.user.to_flashtext()
        return {**d1, **d2, **d3}


class PaymentPlan(models.Model):
    short_name = models.CharField(_(u'Название'), max_length=50, unique=True)
    cost = models.IntegerField(_(u'Цена в рублях'))
    gold_amount = models.IntegerField(_(u'Количество золотых'))

    class Meta:
        verbose_name = _('Вариант оплаты')
        verbose_name_plural = _('Варианты оплаты')
        ordering = ['cost']

    def __str__(self) -> str:
        return f'{self.short_name}'

    def to_flashtext(self):
        return  {
            self.short_name: ['paymen_plan_name'],
            str(self.cost): ['paymen_plan_cost'],
            str(self.gold_amount): ['paymen_plan_gold_amount'],
        }

    @staticmethod
    def get_plans(promocode_id):
        if promocode_id:
            p = Promocode.objects.get(id=promocode_id)
            discount = 1 - p.discount / 100
            query = PaymentPlan.objects.filter(promocode__id=promocode_id)
        else:
            discount = 1
            query = PaymentPlan.objects.all()

        ans = ''; names = []
        for plan in query:
            cost = plan.cost * discount
            names.append({
                'id': plan.id,
                'gold_amount': plan.gold_amount, 
                'name': plan.short_name, 
                'cost': cost}
            )
            ans += f'<bold>{plan.short_name}:</bold>\n'
            ans += f' - <bold>{plan.gold_amount}</bold> золотых\n'
            ans += f' - <bold>{cost}</bold> стоимость\n'
            ans += '----------'

        return {ans[:-11]: ['plans'] }, names

    @staticmethod
    def payment_details(promocode_id, plan_id):
        p = PaymentPlan.objects.get(id=plan_id)
        d = p.to_flashtext()
        c = 'Применен' if promocode_id else 'Нет'
        d[c] = ['is_promocode']
        n = {
            'name': p.short_name,
            'cost': p.cost,
            'gold_amount': p.gold_amount,
        }
        return d, n


class Promocode(models.Model):
    short_name = models.CharField(_(u'Название'), max_length=50, unique=True)
    text = models.TextField(_(u'Текст'), max_length=250)
    date_created = models.DateTimeField(_(u'Дата создания'), auto_now_add=True)
    date_expire = models.DateTimeField(_(u'Дата окончания действия'), default=get_deadline)
    clics_left = models.IntegerField(_(u'Оставшееся количество использований'), default=100)
    clics_amount = models.IntegerField(_(u'Общее количество использований'), default=0)
    discount = models.IntegerField(_(u'Скидка, %'), default=10)

    plan = models.OneToOneField(
        PaymentPlan,
        related_name=_(u'promocode'),
        verbose_name=_(u'Вариант оплаты'),
        help_text= _(u'Вариант оплаты'),
        on_delete=models.SET_NULL, blank=True, null=True
    )

    class Meta:
        verbose_name = _('Промокод')
        verbose_name_plural = _('Промокоды')
        ordering = ['-date_created']

    def __str__(self) -> str:
        return f'{self.short_name}'

    def to_flashtext(self):
        is_valid = 'Просрочен' if self.is_expired() else 'Действует'
        return  {
            self.short_name: ['promocode_name'],
            is_valid: ['is_valid'],
            self.text: ['promocode_text'],
            str(self.discount): ['promocode_discount']
        }

    def is_expired(self):
        if self.date_expire >= now() and self.clics_left > 0:
            return False
        else:
            return True
   
    @staticmethod
    def is_promocode_valid(promocode: str, user_id: int) -> Optional[bool]:
        promocode = promocode.replace(' ', '')
        valid_promocode = Promocode.objects.filter(
            short_name=promocode,
            date_expire__gte=now(),
            clics_left__gt=0
        ).first()
        print(user_id, promocode, valid_promocode)
        payments = Payment.objects.filter(user__user_id=user_id, promocode__short_name=promocode).count()
        print(payments)
        if payments > 0:
            valid_promocode = None
        return valid_promocode
       
    def use_promocode(self) -> None:
        self.clics_left -= 1
        self.clics_amount += 1


class Payment(models.Model):
    user = models.OneToOneField(
        User,
        related_name=_('payments'),
        related_query_name=_('payment'),
        verbose_name=_(u'Пользователь'),
        help_text= _(u'Пользователь'),
        on_delete=models.SET_DEFAULT, blank=True, default='DELETED'
    )
    promocode = models.OneToOneField(
        Promocode,
        related_name=_('payments'),
        related_query_name=_('payment'),
        verbose_name=_(u'Промокод'),
        help_text= _(u'Промокод'),
        on_delete=models.SET_DEFAULT, blank=True, default=None, null=True
    )
    plan = models.OneToOneField(
        PaymentPlan,
        related_name=_('payments'),
        related_query_name=_('payment'),
        verbose_name=_(u'Вариант оплаты'),
        help_text= _(u'Вариант оплаты'),
        on_delete=models.SET_NULL, blank=True, null=True
    )
    date_created = models.DateTimeField(_('Дата платежа'), auto_now_add=True)

    class Meta:
        verbose_name = _('Платеж')
        verbose_name_plural = _('Платежи')
        ordering = ['-date_created']

    def __str__(self) -> str:
        return f'Платеж от: {str(self.user)}'

    def to_flashtext(self):
        d1 =  self.promocode.to_flashtext()
        d2 = self.user.to_flashtext()
        d3 = self.plan.to_flashtext()
        return {**d1, **d2, **d3}


class SupportMessage(models.Model):
    text = models.TextField(_(u'Текст сообщения'), max_length=300, blank=True)
    role = models.CharField(_(u'Роль'), max_length=20)
    file = models.FileField(_(u'Файл'), upload_to='message/', blank=True)
    is_active= models.BooleanField(_(u'Использовать в качестве ответа'), default=False)

    class Meta:
        verbose_name = _('Служебное сообщение')
        verbose_name_plural = _('Служебные сообщения')
        ordering = ['role']

    def __str__(self) -> str:
        return f'Сообщение в: {self.role}'

    @staticmethod
    def get_message(cnt: HelpContext) -> SupportMessage:
        re = SupportMessage.objects.filter(role=cnt.role, is_active=True)
        N = len(re) - 1
        msq = re[random.randint(0, N)]  if N > 0 else re[0]

        if cnt.keywords:
            keyword_processor = KeywordProcessor()
            keyword_processor.add_keywords_from_dict(cnt.keywords)
            msq.text = keyword_processor.replace_keywords(msq.text)
        
        return msq

    @staticmethod
    def replace_user_keywords(text, user_id):
        u = User.objects.get(user_id=user_id)
        keyword_processor = KeywordProcessor()
        keyword_processor.add_keywords_from_dict(u.to_flashtext())
        return keyword_processor.replace_keywords(text)




def do_payment(u_id, payment_plan_id, promocode_id):
    user = User.objects.get(user_id=u_id)
    plan = PaymentPlan.objects.get(id=payment_plan_id)
    promocode = Promocode.objects.filter(id=promocode_id).first()

    Payment.objects.create(
        user=user,
        promocode=promocode,
        plan=plan
    ).save()
    if promocode:
        promocode.use_promocode()

    user.add_gold(plan)
   
    