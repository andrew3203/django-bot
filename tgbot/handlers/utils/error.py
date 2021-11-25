import logging
import traceback
import html

import telegram
from telegram import Update

from corporatum.settings import TELEGRAM_LOGS_CHAT_ID
from tgbot.models import User, HelpContext
from tgbot.handlers.utils.handlers import _do_message


def send_stacktrace_to_tg_chat(update: Update, context) -> None:
    logging.error("Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    hcnt = context.user_data['hcnt']
    hcnt.role = 'BOT_ERROR'
    hcnt.action = 'delete_msg'
    _do_message(hcnt)
    hcnt.action = 'send_msg'
    context.user_data['hcnt'] = _do_message(hcnt)

    u = User.objects.get(user_id=hcnt.user_id)
    message = (
        f'<b>Возникло исключение при обработке обновления</b>\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )
    admin_message = f"⚠️⚠️⚠️ for {u.tg_str}:\n{message}"[:4090]
    if TELEGRAM_LOGS_CHAT_ID:
        context.bot.send_message(
            chat_id=TELEGRAM_LOGS_CHAT_ID,
            text=admin_message,
            parse_mode=telegram.ParseMode.HTML,
        )
    else:
        logging.error(admin_message)
