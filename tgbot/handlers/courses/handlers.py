from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import CallbackContext

from tgbot.models import *
from tgbot.handlers.utils.conf import *
from tgbot.handlers.utils.handlers import _do_message



def show_themes(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    if update.callback_query:
        update.callback_query.answer('Выгрузка курсов')
    
    keyboard = []
    for theme in Theme.get_themes():
        keyboard.append([InlineKeyboardButton(theme.short_name, callback_data=f'theme-{theme.id}')])
    keyboard.append([InlineKeyboardButton('В меню', callback_data=f'back')])
    hcnt.to_top = True
    hcnt.role = 'all_themes'
    hcnt.action = 'edit_msg'
    hcnt = _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data['hcnt'] = hcnt
    return CHOOSER


def show_test(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Выгрузка тестов')
    query.delete_message()

    theme_id = query.data.split("-")[-1]
    navigation = Test.tests_of_theme(theme_id)
    markup =  ReplyKeyboardMarkup(
        [[KeyboardButton(t)] for t in navigation.keys()], 
        one_time_keyboard=True, 
        resize_keyboard=True
    )
    navigation['theme'] = theme_id
    hcnt = context.user_data['hcnt']
    hcnt.navigation = navigation
    hcnt.to_top = False
    hcnt.role = 'show_tests'
    hcnt.action = 'send_msg'

    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)
    return CHOOSE_TEST


def choose_test(update: Update, context: CallbackContext) -> str:
    test_name = update.message.text
    hcnt = context.user_data['hcnt']
    navigation = hcnt.navigation
    try:
        test_id = navigation.get(test_name)
        theme_id = navigation.get('theme')
    except:
        keyboard = [[KeyboardButton(t)] for t in navigation.keys]
        markup =  ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        hcnt.role = 'choose_test_error'
        hcnt.action = 'send_msg'
        hcnt = _do_message(hcnt, reply_markup=markup)
    else:
        hcnt.navigation= {
            'theme': theme_id,
            'test': test_id,  
        }
        update.message.reply_text('Принято', reply_markup=ReplyKeyboardRemove())
        context.user_data['hcnt'] = hcnt
        return send_lvl_choose(context)


def send_lvl_choose(context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    test_id = hcnt.navigation['test']
    theme_id = hcnt.navigation['theme']
    keyboard = []
    for l in Question.get_lvls_for_test(test_id):
        keyboard.append([
            InlineKeyboardButton(l[1], callback_data=f'lvl-{l[0]}')
        ])

    keyboard.append([
        InlineKeyboardButton('Темы', callback_data=f'theme-{theme_id}'),
        InlineKeyboardButton('Курсы', callback_data='themes'),
    ])
       
    hcnt.role = 'choose_lvl'
    hcnt.action = 'send_msg'
    hcnt = _do_message(hcnt, reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data['hcnt'] = hcnt
    return CHOOSER


def choose_lvl(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer('Готово')

    hcnt = context.user_data['hcnt']
    theme_id = hcnt.navigation.get('theme')
    test_id = hcnt.navigation.get('test')
    hcnt.navigation['lvl'] = query.data.split("-")[-1]

    test = Test.objects.get(id=test_id)
    theme = Theme.objects.get(id=theme_id)

    hcnt.keywords = {
        **hcnt.keywords, **theme.to_flashtext(), **test.to_flashtext()
    }
    reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton('Начать', callback_data=f'run_test'),
    ]])
    hcnt.role = 'show_user_choice'
    hcnt.action = 'edit_msg'
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=reply_markup)
    return GO

