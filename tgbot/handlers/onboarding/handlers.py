from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext


from tgbot.handlers.utils.handlers import _do_message, send_selecting_lvl
from tgbot.handlers.utils.track_user import subscribe_faild
from tgbot.handlers.profile.handlers import ask_input
from tgbot.handlers.getgold.handlers import run_pay
from tgbot.handlers.courses.handlers import show_thems

from tgbot.handlers.utils.conf import *

from tgbot.models import User
from utils.models import HelpContext



def start(update: Update, context: CallbackContext) -> str:
    u, created = User.get_user_and_created(update, context)
    hcnt = HelpContext(
        action='send_msg',
        role='ask_subscribe',
        user_id=u.user_id,
        keywords=u.to_flashtext(),
        profile_status=u'Регистрация',
        to_top=False,
        navigation=dict()
    )
    if created:
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton('Подписаться на канал!', url="tg://resolve?domain=corporatum")
        ]])
        hcnt = _do_message(hcnt, reply_markup=reply_markup, disable_web_page_preview=True)        
        context.job_queue.run_once(subscribe_faild, 500, context=hcnt)
        context.user_data['hcnt'] = hcnt
        return CHECK_SUBSRIBE
    else:
        hcnt.profile_status = u'Мой профиль'
        hcnt.role  = 'choose_todo'
        context.user_data['hcnt'] = hcnt
        send_selecting_lvl(update, context)
        return SELECTING_LEVEL


def help(update: Update, context: CallbackContext) -> str:
    u = User.get_user(update, context)
    hcnt = HelpContext(
        action='send_msg',
        role='help_command',
        user_id=u.user_id,
        keywords=u.to_flashtext(),
        profile_status=u'Профиль' if u.is_active else u'Регистрация',
        to_top=False,
        navigation=dict()
    )
    context.user_data['hcnt'] = _do_message(hcnt)
    return STOPPING


def go_study(update: Update, context: CallbackContext) -> str:
    return show_thems(update, context)
    

def get_gold(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    context.user_data['hcnt'] = HelpContext(
        action='send_msg',
        role='pay_help',
        user_id=u.user_id,
        keywords=u.to_flashtext(),
        profile_status=u'Профиль',
        to_top=False,
        navigation=dict()
    )
    if not u.is_active:
        return ask_input(update, context)
    else:
        return run_pay(update, context)


def done(update: Update, context: CallbackContext) ->str:
    hcnt = context.user_data['hcnt']
    if hcnt.to_top:
         send_selecting_lvl(update, context)
         hcnt.to_top = False
    context.user_data['hcnt'] = hcnt
    return END


def stop(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    hcnt.role = 'stop'
    hcnt.action = 'edit_msg'
    context.user_data['hcnt'] = _do_message(hcnt)
    return STOPPING
