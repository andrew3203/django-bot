from django.utils.timezone import now
from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)
from telegram.ext import CallbackContext

from tgbot.models import Test, User, Question
from tgbot.handlers.utils.handlers import _do_message
from tgbot.handlers.courses.handlers import send_lvl_choose, show_thems
from tgbot.handlers.onboarding.handlers import done, get_gold
from tgbot.handlers.utils.conf import *
from utils.models import HelpContext



def run_test(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Готово')
    keyboard = [
        [InlineKeyboardButton('Курсы', callback_data=f'thems')],
        [InlineKeyboardButton('Прервать', callback_data=f'back')]
    ]
    hcnt = context.user_data['hcnt']
    if query.data == 'run_first_test':
        test_id = Test.get_test_id()
        hcnt.navigation['test'] = test_id
        lvl = 0
    else:
        test_id = hcnt.navigation.get('test')
        lvl = hcnt.navigation.get('lvl')
        keyboard[0].append(
            InlineKeyboardButton('Изменить сложность', callback_data=f'change-lvl')
        )

    user = User.get_user(update, context)
    if user.is_active or query.data == 'run_first_test':
        if user.gold - int(lvl) >= 0:
            hcnt.navigation['q_num'] = 0
            q_id = Test.get_question(hcnt.navigation['q_num'], test_id)
            role = 'start_test'
            data = f'q_id-{q_id}'
            btn_name = 'Первый вопрос'
            new_q_id = Test.get_new_question(user.user_id, test_id)
            if new_q_id > 0:
                print(role, new_q_id)
                keyboard.append(
                    [InlineKeyboardButton('Начать c последнего места', callback_data=f'q_id-{new_q_id}')]
                )
            print(role)
        else:
            role = 'start_test_no_gold'
            data = f'get_gold'
            btn_name = 'Получить золото'
            print(role)
    else:
        role = 'start_test_no_active'
        data = f'profile'
        btn_name = 'Регистрация'
        hcnt.profile_status = btn_name
        print(role)

    hcnt.role = role
    hcnt.navigation['message_id'] = query.message.message_id
    hcnt.keywords[lvl] = ['lvl']
    hcnt.action = 'edit_msg'
    keyboard[-1].append(InlineKeyboardButton(btn_name, callback_data=data))
    markup = InlineKeyboardMarkup(keyboard)
    context.user_data['hcnt'] = hcnt
    _do_message(hcnt, message_id=query.message.message_id, reply_markup=markup)    
    return QUESTIONS


def show_question(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    q_id = query.data.split("-")[-1]
    message_id = query.message.message_id
               
    u = User.get_user(update, context)
    q = Question.objects.get(id=q_id)
    u.gold -= q.difficulty_lvl

    hcnt = context.user_data['hcnt']
    hcnt.role = 'show_question'
    hcnt.action = 'edit_msg'
    hcnt.navigation['q_id'] = q_id
    hcnt.navigation['message_id'] = message_id 
    hcnt.navigation['start_time'] = now()
    context.user_data['hcnt'] = hcnt

    test_id, q_num = hcnt.navigation['test'], hcnt.navigation['q_num'] + 1
    q_id = q.get_question(q_num, test_id)
    if q_id:
        keybord = [[InlineKeyboardButton('Пропустить вопрос', callback_data=f'q_id-{q_id}')]]
    else:
        keybord = [[InlineKeyboardButton('Выйти', callback_data='back')]]

    if q.answer_type == 'FLY_BTN':
        for d, a in q.get_answer_variants():
            keybord.append([InlineKeyboardButton(a, callback_data=d)])
        _do_message(hcnt, message_id=message_id, reply_markup=InlineKeyboardMarkup(keybord))

    elif q.answer_type == 'KB_BTN':
        _do_message(hcnt, message_id=message_id, reply_markup=InlineKeyboardMarkup(keybord))
        markup = ReplyKeyboardMarkup(
            [[KeyboardButton(a)] for _, a in q.get_answer_variants()], one_time_keyboard=True
        )
        query.message.reply_text(
            text='Выберете выриант на клавиатуре',
            reply_markup=markup
        )
    elif q.answer_type == 'Poll':
        _do_message(hcnt, message_id=message_id, reply_markup=InlineKeyboardMarkup(keybord))
         # send poll
    elif q.answer_type == 'Quiz':
        _do_message(hcnt, message_id=message_id, reply_markup=InlineKeyboardMarkup(keybord))
        # send quiz
    else:
        _do_message(hcnt, message_id=message_id)
        
    context.job_queue.run_once(catch_answer, q.timer.total_seconds(), context={'runtime': True, 'hcnt': hcnt})
    return CATCH_ANSWER


def _get_markum(hcnt: HelpContext, keybord: list, q: Question, text: str) -> tuple:
    test_id, q_num = hcnt.navigation['test'], hcnt.navigation['q_num']
    q_id = q.get_question(q_num + 1, test_id)
    if q_id:
        hcnt.navigation['q_num'] += 1
        keybord[-1].append(InlineKeyboardButton('Следующий вопрос', callback_data=f'q_id-{q_id}'))
        re = QUESTIONS
    else:
        keybord[-1].append(InlineKeyboardButton('Закончить тест', callback_data=f'finish_test'))

        re = INER
    return hcnt, keybord, re


def catch_answer(update: Update, context: CallbackContext, job_queue=None) -> str:
    if job_queue.context.get('runtime', False):
        hcnt = job_queue.context.get('hcnt')
        q = Question.objects.get(id=hcnt.navigation['q_id'])
        u = User.objects.get(iser_id=hcnt.user_id )
        hcnt.keywords = {**u.to_flashtext(), **q.to_flashtext()}
        hcnt.role = 'no_answer'
        hcnt.action = 'edit_msg'
        _do_message(hcnt, message_id=hcnt.navigation['message_id'])
        return STOPPING
    else:
        hcnt =  context.user_data['hcnt']
        q = Question.objects.get(id=hcnt.navigation['q_id'])
        if q.answer_type in [q.AnswerType.WORD, q.AnswerType.KB_BTN, q.AnswerType.SENTENSE]:
            answer_text = update.message.text
        elif q.answer_type == q.AnswerType.FLY_BTN:
            answer_text = update.callback_query.message.text
        elif q.answer_type == q.AnswerType.POLL:
            answer_text = None
        elif q.answer_type == q.AnswerType.QUIZ:
            answer_text = (True, None)
        
        user = User.get_user(update, context)
        hcnt.role = 'show_answer'
        hcnt.keywords = {**user.to_flashtext(), **q.to_flashtext()}
        is_correct = q.is_answer_correct(answer_text, user, hcnt.navigation['start_time'])
        cc = 'Да' if is_correct else 'Нет'
        hcnt.keywords[cc] = [is_correct]
        keybord = [[InlineKeyboardButton('Выйти', callback_data='back')]]
        if is_correct:
            job_queue.stop()
            hcnt.action = 'edit_msg'
            hcnt.role = 'show_answer'
            hcnt, keybord, re = _get_markum(hcnt, keybord, q)
            context.user_data['hcnt'] = hcnt
            _do_message(hcnt, message_id=hcnt.navigation['message_id'], reply_markup=InlineKeyboardMarkup(keybord))
            return re
        else:
            hcnt.role = 'answer_incorrect'
            hcnt.action = 'send_msg' 
            hcnt, keybord, _ = _get_markum(hcnt, keybord, q)

            time_left_dict = q.get_time_left(hcnt.navigation['start_time'])
            hcnt.keywords = { **hcnt.keywords, **time_left_dict}
            context.user_data['hcnt'] = hcnt
            _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keybord))
            return CATCH_ANSWER


def go_up(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Готово')
    if query.data == 'change-lvl':
        send_lvl_choose(context)
        return BACK

    elif query.data == 'get_gold':
        get_gold(update, context)
        return END

    elif query.data == 'thems':
        show_thems(update, context)
        return BACK

    elif query.data == 'back':
        context.user_data['hcnt'].to_top = True
        context.user_data['hcnt'].action = 'edit_msg'
        context.user_data['hcnt'].navigation['message_id'] = update.callback_query.message.message_id
        return done(update, context)


def finish_test(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    msg_id1 = hcnt.navigation['message_id']
    msg_id2 = update.callback_query.message.message_id
    if msg_id1 < msg_id2:
        hcnt.role = 'no_answer'
        hcnt.action = 'edti_msg'
        _do_message(hcnt, message_id=msg_id1)

    hcnt.role = 'finish_test'
    hcnt.action = 'send_msg'
    _do_message(hcnt)
   
    hcnt.to_top = True
    hcnt.action = 'send_msg'
    return done(update, context)