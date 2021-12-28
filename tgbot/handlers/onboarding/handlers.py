from telegram import (
    Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext
from telegram.utils import helpers

from tgbot.handlers.utils.handlers import _do_message, send_selecting_lvl, remove_job_if_exists
from tgbot.handlers.utils.track_user import is_user_subscribed

from tgbot.handlers.utils.conf import *

from tgbot.models import User, SupportMessage
from utils.models import HelpContext

    


def start(update: Update, context: CallbackContext) -> str:
    u, created = User.get_user_and_created(update, context)
    payload = context.args
    hcnt = HelpContext(
        action='send_msg',
        role='ask_subscribe',
        user_id=u.user_id,
        keywords=u.to_flashtext(),
        profile_status=u'Регистрация',
        to_top=False,
        navigation=dict()
    )
    if payload == FROM_MY_CHANEL:
        if not created: hcnt.profile_status = u'Мой профиль'
        u.deep_link = payload
        send_selecting_lvl(update, context)
    else:
        if created:
            u.deep_link = payload
            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton('Подписаться на канал!', url="tg://resolve?domain=corporatum")
            ]])
            hcnt.role = 'ask_subscribe'
            hcnt = _do_message(hcnt, reply_markup=reply_markup, disable_web_page_preview=True)
            name = f'{u.user_id}-checksubscribe'
            context.job_queue.run_once(is_user_subscribed, 15, context=hcnt, name=name)
            context.user_data['hcnt'] = hcnt
        else:
            hcnt.profile_status = u'Мой профиль'
            hcnt.role  = 'choose_todo'
            context.user_data['hcnt'] = hcnt
            send_selecting_lvl(update, context)
        return SELECTING_LEVEL

def start_deep_linked(update: Update, context: CallbackContext) -> str:
    # Filters.regex(DEEP_LINKED) regueried
    pass

def help(update: Update, context: CallbackContext) -> str:
    u = User.get_user(update, context)
    hcnt = HelpContext(
        action='edit_msg',
        role='help_command',
        user_id=u.user_id,
        keywords=u.to_flashtext(),
        profile_status=u'Профиль' if u.is_active else u'Регистрация',
        to_top=False,
        navigation=dict()
    )
    hcnt = context.user_data.get('hcnt', hcnt)
    context.user_data['hcnt'] = _do_message(hcnt)
    return STOPPING

def done(update: Update, context: CallbackContext) ->str:
    hcnt = context.user_data['hcnt']
    if hcnt.to_top:
        hcnt.role = 'choose_todo'
        hcnt.to_top = False
        context.user_data['hcnt'] = hcnt
        send_selecting_lvl(update, context)
        
    context.user_data['hcnt'] = hcnt
    return END

def stop(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    hcnt.role = 'stop'
    hcnt.action = 'edit_msg'
    remove_job_if_exists(f'{hcnt.user_id}-trackquestion', context)
    context.user_data['hcnt'] = _do_message(hcnt)
    return STOPPING

def add_friend(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    u, c = User.get_user_and_created(update, context)
    if u.is_admin:
        rearg = f'{FROM_MY_CHANEL}'
        role = 'add_users_by_admin'
    else:
        rearg = f'{ADD_FRIEND}-{u.user_id}'
        role = 'add_users_by_user'
    hcnt = context.user_data.get('hcnt', HelpContext(role=role, user_id=u.user_id, action='send_msg'))
    hcnt.role = role
    url = helpers.create_deep_linked_url(bot.username, rearg)
    msg = SupportMessage.get_message(hcnt)
    keyboard = InlineKeyboardMarkup.from_button(InlineKeyboardButton(text="Запустить бота", url=url))
    update.message.reply_text(msg.text, reply_markup=keyboard)
    return STOPPING

