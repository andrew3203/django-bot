from django.utils.timezone import now
from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)
from telegram.ext import CallbackContext

from tgbot.models import Test, User, Question
from tgbot.handlers.utils.handlers import _do_message, _send_poll, remove_job_if_exists
from tgbot.handlers.courses.handlers import send_lvl_choose, show_themes
from tgbot.handlers.onboarding.handlers import done
from tgbot.handlers.utils import conf
from utils.models import HelpContext



def run_test(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Готово')
    keyboard = [
        [InlineKeyboardButton('К курсам', callback_data=f'themes')],
        [InlineKeyboardButton('Выйти', callback_data=f'back')]
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
            InlineKeyboardButton('Другая сложность', callback_data=f'change-lvl')
        )

    user = User.get_user(update, context)
    if user.is_active or query.data == 'run_first_test':
        if user.gold - int(lvl) >= 0:
            hcnt.navigation['q_num'] = 0
            q_id = Test.get_question_id(hcnt.navigation['q_num'], test_id)
            role = 'start_test'
            data = f'q_id-{q_id}'
            print(role, data)
            btn_name = 'Первый вопрос'
            new_q_id = Test.get_new_question_id(user.user_id, test_id)
            if new_q_id and new_q_id != q_id:
                keyboard[-1].append(InlineKeyboardButton('Начать c последнего', callback_data=f'q_id-{new_q_id}'))
        else:
            role = 'start_test_no_gold'
            data = f'get_gold'
            btn_name = 'Получить золото'
    else:
        role = 'start_test_no_active'
        data = f'profile'
        btn_name = 'Регистрация'
        hcnt.profile_status = btn_name

    hcnt.role = role
    hcnt.keywords[lvl] = ['lvl']
    hcnt.action = 'edit_msg'
    keyboard[-1].append(InlineKeyboardButton(btn_name, callback_data=data))
    markup = InlineKeyboardMarkup(keyboard)
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)    
    return conf.QUESTIONS


def show_question(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    q_id = query.data.split("-")[-1]
               
    u = User.get_user(update, context)        
    q = Question.objects.get(id=q_id)
    u.gold -= q.difficulty_lvl

    hcnt = context.user_data['hcnt']
    if remove_job_if_exists(f'{hcnt.user_id}-trackquestion', context):
        if q.answer_type == q.AnswerType.KB_BTN:
            context.bot.delete_message(
                    chat_id=hcnt.user_id, 
                    message_id=hcnt.navigation['KB_BTN_message_id'],
            )

    hcnt.keywords = {**hcnt.keywords, **u.to_flashtext(), **q.to_flashtext()}
    hcnt.role = 'show_question'
    hcnt.action = 'edit_msg'
    hcnt.navigation['q_id'] = q_id
    hcnt.navigation['start_time'] = now()

    test_id, q_num = hcnt.navigation['test'], hcnt.navigation['q_num']
    q_id = Test.get_question_id(q_num + 1, test_id)
    call = ('Пропустить вопрос', f'q_id-{q_id}') if q_id else ('Закончить тест', 'back')
    keyboard = [[InlineKeyboardButton(call[0], callback_data=call[1])]]
    print('current question: ', q.answer_type, q.id)
    print('next question: ', call[1])

    if q.answer_type == q.AnswerType.FLY_BTN:
        keyboard1 = [[InlineKeyboardButton(v, callback_data=f'ans-{k}')] for k, v in enumerate(q.get_ans_variants())]
        keyboard1.append(keyboard[0])
        hcnt = _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keyboard1))

    elif q.answer_type == q.AnswerType.KB_BTN:
        hcnt = _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keyboard))
        print(hcnt.message_id)

        keyboard1 = [[KeyboardButton(v)] for v in q.get_ans_variants()]
        markup = ReplyKeyboardMarkup(keyboard1, one_time_keyboard=True, resize_keyboard=True)
        m = query.message.reply_text(text='Выберете выриант на клавиатуре', reply_markup=markup)
        hcnt.navigation['KB_BTN_message_id'] = m.message_id

    elif q.answer_type == q.AnswerType.POLL:
        hcnt = _do_message(hcnt,  reply_markup=InlineKeyboardMarkup(keyboard))
        text = 'Выбирите вариант ответа:'
        payload = _send_poll(text, user_id=hcnt.user_id, options=q.get_ans_variants(), poll_type='poll')
        context.bot_data.update(payload)

    elif q.answer_type == q.AnswerType.QUIZ:
        hcnt = _do_message(hcnt,  reply_markup=InlineKeyboardMarkup(keyboard))
        text = 'Выбирите вариант ответа:'
        correct_option = q.correct_option_id()
        payload = _send_poll(text, user_id=hcnt.user_id, options=q.get_ans_variants(), correct_option_id=correct_option, poll_type='quiz')
        context.bot_data.update(payload)

    elif q.answer_type in [q.AnswerType.SENTENSE, q.AnswerType.WORD]:
        hcnt = _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keyboard))
    
    hcnt.prev_answer_type = q.answer_type
    cnt = {'hcnt': hcnt, 'bot': context.bot}
    name = f'{hcnt.user_id}-trackquestion'
    context.user_data['hcnt'] = hcnt
    context.job_queue.run_once(no_answer, q.get_total_seconds(), context=cnt, name=name)
    return conf.CATCH_ANSWER

def no_answer(context: CallbackContext) -> str:
    bot = context.job.context['bot']
    hcnt = context.job.context['hcnt']
    q = Question.objects.get(id=hcnt.navigation['q_id'])
    remove_job_if_exists(f'{hcnt.user_id}-{q.id}-delaymessageedit', context)
    bot.edit_message_text(
        f'Вопрос: {hcnt.navigation["q_num"]}', 
        message_id=hcnt.message_id,
        chat_id=hcnt.user_id
    )
    if q.answer_type == q.AnswerType.KB_BTN:
        context.bot.delete_message(
                chat_id=hcnt.user_id, 
                message_id=hcnt.navigation['KB_BTN_message_id'],
        )
    u = User.objects.get(user_id=hcnt.user_id )
    hcnt.keywords = {**hcnt.keywords, **u.to_flashtext(), **q.to_flashtext()}
    hcnt.role = 'no_answer'
    hcnt.action = 'send_msg'
    hcnt = _do_message(hcnt)
  
def receive_callback_answer(update: Update, context: CallbackContext) -> str:
    hcnt =  context.user_data['hcnt']
    q = Question.objects.get(id=hcnt.navigation['q_id'])
    print('receive callback answer: ', q.id, q.answer_type)
    ans_num = int(update.callback_query.data.split('-')[-1])
    answer_text = q.get_ans_variants()[ans_num]
    hcnt, markup, _, re = _check_answer(context, answer_text, q)
    print('answer checked:', update.callback_query.data, ans_num, _, re)
    hcnt.action = 'edit_msg' 
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
    return re

def receive_text_answer(update: Update, context: CallbackContext) -> str:
    hcnt =  context.user_data['hcnt']
    print(hcnt.message_id)
    q = Question.objects.filter(id=hcnt.navigation['q_id']).first()
    print('receive text answer: ', q.id, q.answer_type)
    answer_text = update.message.text

    if q and q.answer_type in [q.AnswerType.WORD, q.AnswerType.KB_BTN, q.AnswerType.SENTENSE]:
        hcnt, markup, is_correct, re = _check_answer(context, answer_text, q)
        print(hcnt.message_id)
        print('answer checked:', answer_text, is_correct, re)

        if is_correct:
            if q.answer_type == q.AnswerType.KB_BTN:
                context.bot.delete_message(
                    chat_id=hcnt.user_id, 
                    message_id=hcnt.navigation['KB_BTN_message_id'],
                )
            # set timer to delete question text
            _set_delay_edit(context, hcnt.copy(), q.id)

            hcnt.action = 'send_msg' 
            context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
           
        else:
            hcnt.action = 'edit_msg' 
            context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
        return re
    else:
        return conf.CATCH_ANSWER

def receive_poll_answer(update: Update, context: CallbackContext) -> None:
    answer = update.poll_answer
    poll_id = answer.poll_id
    poll_data = context.bot_data[poll_id]
    hcnt =  context.user_data['hcnt']
    q = Question.objects.get(id=hcnt.navigation['q_id'])

    selected_options = answer.option_ids
    answers = poll_data["answers"]
    if q.answer_type == q.AnswerType.POLL:
        answer_text = [answers[i] for i in selected_options]
    elif q.answer_type == q.AnswerType.QUIZ:
        ans = True if poll_data['correct_option_id'] == selected_options[0] else False
        answer_text = (ans, answers[0])
    else:
        context.bot.stop_poll(poll_data["chat_id"], poll_data["message_id"])
        return

    hcnt, markup, is_correct, re = _check_answer(context, answer_text, q)
    _set_delay_edit(context, hcnt.copy(), q.id)
    if is_correct or q.answer_type == q.AnswerType.QUIZ:
        context.bot.stop_poll(poll_data["chat_id"], poll_data["message_id"])
        hcnt.action = 'send_msg' 
    else:
        hcnt.action = 'edit_msg' 
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)

def _set_delay_edit(context: CallbackContext, hcnt: HelpContext, q_id: int) -> None:
    hcnt.action = 'edit_msg' 
    hcnt = _do_message(hcnt, reply_markup=None)
    print(hcnt.message_id, '12 -- deleted\n\n')
    context.job_queue.run_once(
        _delay_message_edit, conf.DELAY, 
        context=hcnt, 
        name=f'{hcnt.user_id}-{q_id}-delaymessageedit'
    )

def _delay_message_edit(context: CallbackContext):
    hcnt = context.job.context
    hcnt.action = 'edit_msg' 
    hcnt.role = 'close_question'
    _do_message(hcnt, reply_markup=None)

def _check_answer(context: CallbackContext, answer_text: str, q: Question) -> str:
    hcnt =  context.user_data['hcnt']
    user = User.objects.get(user_id=hcnt.user_id)

    is_correct, ans = q.save_and_check_answer(answer_text, user, hcnt.navigation['start_time'])
    cc = 'Да' if is_correct else 'Нет'
    hcnt.keywords[cc] = ['is_correct']
    hcnt.keywords[ans] = ['answer']
    hcnt.keywords = {**hcnt.keywords, **user.to_flashtext(), **q.to_flashtext()}

    if is_correct:
        remove_job_if_exists(f'{hcnt.user_id}-trackquestion', context)
        hcnt.role = 'answer_correct'
    else:
        hcnt.role = 'answer_incorrect'
        time_left_dict = q.get_time_left(hcnt.navigation['start_time'])
        hcnt.keywords = { **hcnt.keywords, **time_left_dict}
        re =  conf.CATCH_ANSWER

    keybord = [[InlineKeyboardButton('Выйти', callback_data='back')]]
    new_q_id = Test.get_question_id(hcnt.navigation['q_num'] + 1,  hcnt.navigation['test'])
    if new_q_id:
        hcnt.navigation['q_num'] += 1
        btn_text = 'Следующий вопрос'; data = f'q_id-{new_q_id}'
        re = conf.QUESTIONS
    else:
        btn_text = 'Закончить тест'; data = f'finish_test'
        keybord = []
        re = conf.INER
    keybord.append([InlineKeyboardButton(btn_text, callback_data=data)])

    hcnt.navigation['last_q'] = q.id
    return hcnt, InlineKeyboardMarkup(keybord), is_correct, re

def go_up(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Готово')
    remove_job_if_exists(f'{query.message.chat_id}-trackquestion', context)
    hcnt = context.user_data['hcnt']
    q = Question.objects.get(id=hcnt.navigation.get('q_id', 1))
    if q.answer_type == q.AnswerType.KB_BTN:
        context.bot.delete_message(
            chat_id=hcnt.user_id, 
            message_id=hcnt.navigation['KB_BTN_message_id'],
        )


    if query.data == 'change-lvl':
        send_lvl_choose(context)
        return conf.CHOOSER

    elif query.data == 'themes':
        show_themes(update, context)
        return conf.CHOOSER

    elif query.data == 'back':
        hcnt.to_top = True
        hcnt.action = 'edit_msg'
        context.user_data['hcnt'] = hcnt
        return done(update, context)

def finish_test(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    remove_job_if_exists(f'{hcnt.user_id}-trackquestion', context)
    hcnt = context.user_data['hcnt']
    q = Question.objects.get(id=hcnt.navigation['q_id'])
    if q.answer_type == q.AnswerType.KB_BTN:
        context.bot.delete_message(
            chat_id=hcnt.user_id, 
            message_id=hcnt.navigation['KB_BTN_message_id'],
        ) 

    hcnt.role = 'finish_test'
    hcnt.action = 'edit_msg'
    hcnt = _do_message(hcnt)
   
    hcnt.to_top = True
    hcnt.action = 'send_msg'
    context.user_data['hcnt'] = hcnt
    return done(update, context)
