from typing import Union, Optional, Dict, List

import telegram
from telegram import (
    MessageEntity, 
    InlineKeyboardButton, InlineKeyboardMarkup,
)

from corporatum.settings import TELEGRAM_TOKEN
from tgbot.models import User, SupportMessage


def _from_celery_markup_to_markup(celery_markup: Optional[List[List[Dict]]]) -> Optional[InlineKeyboardMarkup]:
    markup = None
    if celery_markup:
        markup = []
        for row_of_buttons in celery_markup:
            row = []
            for button in row_of_buttons:
                row.append(
                    InlineKeyboardButton(
                        text=button['text'],
                        callback_data=button.get('callback_data'),
                        url=button.get('url'),
                    )
                )
            markup.append(row)
        markup = InlineKeyboardMarkup(markup)
    return markup


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


def _send_message(
    user_id: Union[str, int],
    keywords: dict,
    parse_mode: Optional[str] = telegram.ParseMode.HTML,
    reply_markup: Optional[List[List[Dict]]] = None,
    reply_to_message_id: Optional[int] = None,
    disable_web_page_preview: Optional[bool] = None,
    entities: Optional[List[MessageEntity]] = None,
    tg_token: str = TELEGRAM_TOKEN,
) -> bool:
    bot = telegram.Bot(tg_token)
    msg = SupportMessage.get_message(keywords)
    try:
        m = bot.send_message(
            chat_id=user_id,
            text=msg.text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            reply_to_message_id=reply_to_message_id,
            disable_web_page_preview=disable_web_page_preview,
            entities=entities,
        )
    except telegram.error.Unauthorized:
        print(f"Can't send message to {user_id}. Reason: Bot was stopped.")
        User.objects.filter(user_id=user_id).update(is_blocked_bot=True)
        success = False
    else:
        success = True
        User.objects.filter(user_id=user_id).update(is_blocked_bot=False)
    return success


def _do_message(
    user_id: Union[str, int],
    action: str,
    keywords: Optional[dict] = None,
    message_id: Optional[int] = None,
    parse_mode: Optional[str] = telegram.ParseMode.HTML,
    reply_markup: Optional[List[List[Dict]]] = None,
    disable_web_page_preview: Optional[bool] = None,
    entities: Optional[List[MessageEntity]] = None,
    tg_token: str = TELEGRAM_TOKEN,
) -> bool:
    
    if action in ['send', 'edit'] and keywords is None:
        return False
    else:
        bot = telegram.Bot(tg_token)
        msg = SupportMessage.get_message(keywords)

    try:
        if action == 'send':
             m = bot.send_message(
                chat_id=user_id,
                text=msg.text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
                entities=entities,
            )
        elif action == 'edit':
            m = bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=msg.text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
                entities=entities,
            )
        elif action == 'delete':
            m = bot.delete_message(
                chat_id=user_id,
                message_id=message_id,
            )
    except telegram.error.Unauthorized:
        print(f"Can't send message to {user_id}. Reason: Bot was stopped.")
        User.objects.filter(user_id=user_id).update(is_blocked_bot=True)
        success = False
    else:
        success = True
        User.objects.filter(user_id=user_id).update(is_blocked_bot=False)
    return success
