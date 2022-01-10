from django.utils.timezone import now
from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
)
from telegram.ext import CallbackContext

from tgbot.models import Test, User, Question
from tgbot.handlers.utils.handlers import _do_message, _send_poll, remove_job_if_exists
from tgbot.handlers.courses.handlers import _get_lvl_markup, show_themes
from tgbot.handlers.onboarding.handlers import done
from tgbot.handlers.utils import conf
from utils.models import HelpContext



def run_test(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Готово')
    keyboard = [
        [InlineKeyboardButton('Выйти', callback_data=f'back')]
    ]
    hcnt = context.user_data['hcnt']
    if query.data == 'run_first_test':
        test_id = Test.get_test_id()
        hcnt.navigation['test'] = test_id
        lvl = 0
        user = User.get_user(update, context)
        test = Test.objects.get(id=test_id)
    else:
        test_id = hcnt.navigation.get('test')
        lvl = hcnt.navigation.get('question_lvl')
        keyboard.insert(0, [
            InlineKeyboardButton('К курсам', callback_data=f'themes'),
            InlineKeyboardButton('Другая сложность', callback_data=f'change-lvl')
        ])

    user = User.get_user(update, context)
    if user.is_active or query.data == 'run_first_test':
        if user.gold - int(lvl) >= 0:
            q_id = Test.get_question_id(test_id)
            role = 'start_test'
            data = f'q_id-{q_id}'
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
    hcnt.keywords[lvl] = ['question_lvl']
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
    hcnt = context.user_data['hcnt']
    if u.gold < q.difficulty_lvl:
        hcnt.role = 'start_test_no_gold'
        hcnt.action = 'edit_msg'
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('Получить золото', callback_data='get_gold')],
            [InlineKeyboardButton('Выйти', callback_data=f'back')]
        ])
        context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)  
        return None
    else:
        u.gold -= q.difficulty_lvl
        u.save()
    remove_job_if_exists(f'{hcnt.user_id}-trackquestion', context)
    hcnt = _del_kb_message_if_exists(context, hcnt, q)

    hcnt.keywords = {**u.to_flashtext(), **q.to_flashtext()}
    hcnt.role = 'show_question'
    hcnt.action = 'edit_msg'
    hcnt.navigation['q_id'] = q_id
    hcnt.navigation['start_time'] = now()

    new_q_id = Test.get_question_id(test_id=hcnt.navigation['test'], last_q_id=q_id)
    call = ('Пропустить вопрос', f'q_id-{new_q_id}') if new_q_id else ('Закончить тест', 'back')
    keyboard = [[InlineKeyboardButton(call[0], callback_data=call[1])]]

    if q.answer_type == q.AnswerType.FLY_BTN:
        keyboard1 = [[InlineKeyboardButton(v, callback_data=f'ans-{k}')] for k, v in enumerate(q.get_ans_variants())]
        keyboard1.append(keyboard[0])
        hcnt = _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keyboard1))

    elif q.answer_type == q.AnswerType.KB_BTN:
        hcnt = _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keyboard))

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
    
    context.user_data['hcnt'] = hcnt
    context.job_queue.run_once(
        no_answer, q.get_total_seconds(), context=hcnt, 
        name=f'{hcnt.user_id}-trackquestion'
    )
    return conf.CATCH_ANSWER

def no_answer(context: CallbackContext) -> str:
    hcnt = context.job.context
    q_id, test_id = hcnt.navigation['q_id'],  hcnt.navigation['test']
    questions = list(Question.objects.filter(test__id=test_id).values_list('id', flat=True))

    q = Question.objects.get(id=q_id)
    u = User.objects.get(user_id=hcnt.user_id )
    d_N = {1 + questions.index(q_id): 'question_position'}
    hcnt.keywords = {**u.to_flashtext(), **q.to_flashtext(), **d_N}

    hcnt.action == 'edit_msg'; hcnt.role = 'hide_question'
    hcnt = _do_message(hcnt)

    hcnt.action = 'send_msg'; hcnt.role = 'no_answer'
    hcnt = _do_message(hcnt)
    
    remove_job_if_exists(f'{hcnt.user_id}-{q_id}-delaymessageedit', context)
    hcnt = _del_kb_message_if_exists(context, hcnt, q)
  
def receive_callback_answer(update: Update, context: CallbackContext) -> str:
    hcnt =  context.user_data['hcnt']
    q = Question.objects.get(id=hcnt.navigation['q_id'])
    ans_num = int(update.callback_query.data.split('-')[-1])
    answer_text = q.get_ans_variants()[ans_num]
    hcnt, markup, _, re = _check_answer(context, answer_text, q)
    hcnt.action = 'edit_msg' 
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
    return re

def receive_text_answer(update: Update, context: CallbackContext) -> str:
    hcnt =  context.user_data['hcnt']
    q = Question.objects.filter(id=hcnt.navigation.get('q_id', None)).first()
    answer_text = update.message.text
    hcnt, markup, is_correct, re = _check_answer(context, answer_text, q)

    if is_correct:
        _set_delay_edit(context, hcnt.copy(), q.id)
        hcnt = _del_kb_message_if_exists(context, hcnt, q)
        hcnt.action = 'send_msg' 
        context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
           
    else:
        hcnt.action = 'edit_msg' 
        context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
    return re

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
    hcnt.role = 'question_text' 
    hcnt = _do_message(hcnt, reply_markup=None)
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

def _del_kb_message_if_exists(context: CallbackContext, hcnt: HelpContext, q: Question) -> HelpContext:
    kb = hcnt.navigation.get('KB_BTN_message_id', None)
    if q and kb and q.answer_type == q.AnswerType.KB_BTN:
        context.bot.delete_message(
            chat_id=hcnt.user_id, 
            message_id=kb,
        )
        del hcnt.navigation['KB_BTN_message_id']
    return hcnt

def _check_answer(context: CallbackContext, answer_text: str, q: Question) -> str:
    hcnt =  context.user_data['hcnt']
    user = User.objects.get(user_id=hcnt.user_id)

    is_correct, ans = q.save_and_check_answer(answer_text, user, hcnt.navigation['start_time'])
    cc = 'Ответ верный' if is_correct else 'Ответ не верный'
    hcnt.keywords[cc] = ['is_correct']
    hcnt.keywords[ans] = ['answer']
    hcnt.keywords = {**user.to_flashtext(), **q.to_flashtext()}
    new_q_id = Test.get_question_id(test_id=hcnt.navigation['test'], last_q_id=q.id)

    if is_correct:
        remove_job_if_exists(f'{hcnt.user_id}-trackquestion', context)
        hcnt.role = 'answer_correct'
        re = conf.QUESTIONS
    else:
        hcnt.role = 'answer_incorrect'
        time_left_dict = q.get_time_left(hcnt.navigation['start_time'])
        hcnt.keywords = {**hcnt.keywords, **time_left_dict}
        re =  None

    keybord = [[InlineKeyboardButton('Выйти', callback_data='back')]]
    if new_q_id:
        btn_text = 'Следующий вопрос'; data = f'q_id-{new_q_id}'
    else:
        btn_text = 'Закончить тест'; data = f'finish_test'
        keybord = []
    keybord.append([InlineKeyboardButton(btn_text, callback_data=data)])
    return hcnt, InlineKeyboardMarkup(keybord), is_correct, re

def _go_up(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Готово')
    remove_job_if_exists(f'{query.message.chat_id}-trackquestion', context)
    hcnt = context.user_data['hcnt']
    q = Question.objects.filter(id=hcnt.navigation.get('q_id', None)).first()
    hcnt = _del_kb_message_if_exists(context, hcnt, q)
    return hcnt

def change_test_lvl(update: Update, context: CallbackContext) -> str:
    hcnt = _go_up(update, context)
    test_id = hcnt.navigation['test']
    hcnt.action = 'edit_msg'; hcnt.role = 'choose_lvl'  
    hcnt = _do_message(hcnt, reply_markup=_get_lvl_markup(test_id))
    context.user_data['hcnt'] = hcnt
    return conf.CHOOSER

def change_test_theme(update: Update, context: CallbackContext) -> str:
    context.user_data['hcnt'] = _go_up(update, context)
    show_themes(update, context)
    return conf.CHOOSER

def test_no_gold(update: Update, context: CallbackContext) -> str:
    hcnt = _go_up(update, context)
    hcnt.action = 'edit_msg'
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(u'Получить золото', callback_data='get_gold')],
    ])
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
    return conf.END  

def need_profile(update: Update, context: CallbackContext) -> str:
    hcnt = _go_up(update, context)
    hcnt.action = 'edit_msg'
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(hcnt.profile_status, callback_data='profile')],
    ])
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
    return conf.END

def test_go_back(update: Update, context: CallbackContext) -> str:
    hcnt = _go_up(update, context)
    hcnt.action = 'edit_msg'
    context.user_data['hcnt'] = hcnt
    done(update, context)
    return conf.END

def finish_test(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    remove_job_if_exists(f'{hcnt.user_id}-trackquestion', context)
    hcnt = context.user_data['hcnt']
    q = Question.objects.get(id=hcnt.navigation['q_id'])
    hcnt = _del_kb_message_if_exists(context, hcnt, q)
    hcnt.role = 'finish_test'
    hcnt.action = 'edit_msg'
    res = Test.get_results(hcnt.navigation['test'], hcnt.user_id)
    hcnt.keywords = {**hcnt.keywords, **res}
    hcnt = _do_message(hcnt)
   
    hcnt.action = 'send_msg'
    context.user_data['hcnt'] = hcnt
    done(update, context)
    return conf.END
