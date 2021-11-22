from django.core.exceptions import ValidationError
from django.core.validators import validate_email


from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext

from tgbot.models import User
from tgbot.handlers.utils.handlers import _do_message
from tgbot.handlers.onboarding import handlers as onboarding_handlers
from tgbot.handlers.utils.conf import *



def ask_input(update: Update, context: CallbackContext) -> str:
    keyboard = [[
        InlineKeyboardButton('Имя и Фаммилию', callback_data=f'enter_name'),
        InlineKeyboardButton('Почту', callback_data=f'enter_email'),
    ]]
    u = User.get_user(update, context)
    hcnt = context.user_data['hcnt']
    hcnt.user_id = u.user_id
    hcnt.role = 'ask_profile'
    hcnt.to_top = False

    if u.is_active:
        hcnt.to_top = True
        keyboard[-1].append(InlineKeyboardButton('Готово', callback_data=f'back'))
        
    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        update.callback_query.answer("Получено")
        hcnt.action = 'edit_msg'
    else:
        hcnt.action = 'send_msg'
    
    context.user_data['hcnt'] = _do_message(hcnt,reply_markup=markup)  
    return EDIT_MSG


def edit_msg(update: Update, context: CallbackContext) -> str:
    update.callback_query.answer('Введите данные')
    hcnt = context.user_data['hcnt']
    hcnt.action = 'edit_msg'
    hcnt.to_top = False
    hcnt.role = update.callback_query.data

    context.user_data['hcnt'] = _do_message(hcnt)
    return TYPING


def save_email(update: Update, context: CallbackContext) -> str:
    email = update.message.text.replace(" ", '').lower()
    hcnt = context.user_data['hcnt']
    hcnt.action = 'send_msg'
    try:
        validate_email(email)
    except ValidationError as e:
        hcnt.role = 'email_error'
        context.user_data['hcnt'] = _do_message(hcnt)
        return TYPING
    else:
        user = User.get_user(update, context)
        user.email = email
        if user.last_name:
            user.is_active = True
        user.save()
        hcnt.role = 'catch_data'

        context.user_data['hcnt'] = _do_message(hcnt)
        return ask_input(update, context)


def save_name(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    hcnt.action = 'send_msg'
    try:
        name = update.message.text
        for c in name:
            if c.isdigit():
                raise ValidationError
        first_name, last_name = name.split(' ')
    except:
        hcnt.role = 'name_error'
        context.user_data['hcnt'] = _do_message(hcnt)
        return TYPING
    else:
        user = User.get_user(update, context)
        user.first_name = first_name
        user.last_name = last_name
        if user.email:
            user.is_active = True
        user.save()
        hcnt.role = 'catch_data'
        context.user_data['hcnt'] = _do_message(hcnt)
        return ask_input(update, context)

def go_back(update: Update, context: CallbackContext) -> str:
    context.user_data['hcnt'].role = 'choose_todo'
    context.user_data['hcnt'].action = 'edit_msg'
    return onboarding_handlers.done(update, context)