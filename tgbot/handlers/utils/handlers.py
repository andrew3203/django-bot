from datetime import datetime
from django.utils.timezone import now

import io
import csv
from typing import Optional, Dict, List

import telegram
from telegram import (
    Update, Poll,
    MessageEntity, 
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext
from django.db.models import QuerySet

from corporatum.settings import TELEGRAM_TOKEN
from tgbot.models import User, SupportMessage
from utils.models import HelpContext



def _export_users(update: Update, context) -> None:
    u = User.get_user(update, context)

    # in values argument you can specify which fields should be returned in output csv
    users = User.objects.all().values()
    csv_users = _get_csv_from_qs_values(users)
    context.bot.send_document(chat_id=u.user_id, document=csv_users)


def _get_csv_from_qs_values(queryset: QuerySet, filename: str = 'users'):
    keys = queryset[0].keys()

    # csv module can write data in io.StringIO buffer only
    s = io.StringIO()
    dict_writer = csv.DictWriter(s, fieldnames=keys)
    dict_writer.writeheader()
    dict_writer.writerows(queryset)
    s.seek(0)

    # python-telegram-bot library can send files only from io.BytesIO buffer
    # we need to convert StringIO to BytesIO
    buf = io.BytesIO()

    # extract csv-string, convert it to bytes and write to buffer
    buf.write(s.getvalue().encode())
    buf.seek(0)

    # set a filename with file's extension
    buf.name = f"{filename}__{datetime.now().strftime('%Y.%m.%d.%H.%M')}.csv"

    return buf


def _from_celery_entities_to_entities(celery_entities: Optional[List[Dict]] = None) -> Optional[List[MessageEntity]]:
    entities = None
    if celery_entities:
        entities = [
            MessageEntity(
                type=entity['type'],
                offset=entity['offset'],
                length=entity['length'],
                url=entity.get('url'),
                language=entity.get('language'),
            )
            for entity in celery_entities
        ]
    return entities


def _send_poll(
    text: str,
    user_id: int,
    poll_type: None,
    options: list,
    correct_option_id: None = 0,
    tg_token: str = TELEGRAM_TOKEN,
) -> dict:

    bot = telegram.Bot(tg_token)

    try:
        if poll_type == 'poll':
            m = bot.send_poll(
                chat_id=user_id,
                question=text,
                options=options,
                is_anonymous=False,
                type=Poll.REGULAR, 
                explanation='Test exsplanation',
                allows_multiple_answers=True,
            )
        else:
            m = bot.send_poll(
                chat_id=user_id,
                question=text,
                options=options,
                is_anonymous=False,
                type=Poll.QUIZ, 
                explanation='Test exsplanation',
                correct_option_id=correct_option_id
            )
     
    except telegram.error.Unauthorized:
        print(f"Can't send message to {user_id}. Reason: Bot was stopped.")
        User.objects.filter(user_id=user_id).update(is_blocked_bot=True)
        payload = {}
    else:
        payload = {
            m.poll.id: {
                "answers": options,
                "message_id": m.message_id,
                'poll_id': m.poll.id,
                "chat_id": user_id,
                "correct_option_id": correct_option_id
            },
            user_id: {"message_id": m.message_id}
        }
        User.objects.filter(user_id=user_id).update(is_blocked_bot=False)
    return payload




def _do_message(
    help_context: HelpContext,
    parse_mode: Optional[str] = telegram.ParseMode.HTML,
    reply_markup: Optional[List[List[Dict]]] = None,
    disable_web_page_preview: Optional[bool] = None,
    entities: Optional[List[MessageEntity]] = None,
    tg_token: str = TELEGRAM_TOKEN,
) -> HelpContext:
    
    action = help_context.action
    message_id = help_context.message_id
    user_id = help_context.user_id
    
    bot = telegram.Bot(tg_token)
    msg = SupportMessage.get_message(help_context)

    try:
        if action == 'send_msg':
             m = bot.send_message(
                chat_id=user_id,
                text=msg.text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
                entities=entities,
            )
        elif action == 'edit_msg':
            m = bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=msg.text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
                entities=entities,
            )
        elif action == 'delete_msg':
            m = bot.delete_message(
                chat_id=user_id,
                message_id=message_id,
            )
    except telegram.error.Unauthorized:
        print(f"Can't send message to {user_id}. Reason: Bot was stopped.")
        User.objects.filter(user_id=user_id).update(is_blocked_bot=True)
        help_context.message_id = None
    else:
        help_context.message_id = m.message_id if not action == 'delete_msg' else None
        User.objects.filter(user_id=user_id).update(is_blocked_bot=False)
    return help_context


def send_selecting_lvl(update: Update, context: CallbackContext):
    hcnt = context.user_data['hcnt']
    u = User.get_user(update, context)
    hcnt.profile_status = 'Профиль' if u.is_active else 'Регистрация'
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(u'Пробный тест', callback_data='run_first_test'),
            InlineKeyboardButton(hcnt.profile_status, callback_data='profile')
        ],
        [InlineKeyboardButton(u'Все курсы', callback_data='themes')],
        [InlineKeyboardButton(u'Получить золото', callback_data='get_gold')],
        [InlineKeyboardButton(u'Помошь', callback_data='help')],
    ])
    if update.callback_query is not None:
        update.callback_query.answer('Готово')
    context.user_data['hcnt'] = _do_message(hcnt, reply_markup=markup)

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True