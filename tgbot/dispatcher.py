"""
    Telegram event handlers
    TODO:
        - закончить finish_test
        - проверить, что везде нужное message_id
        - проверить, что везде нужное to_top
        - проверить, что везде есть keywords и navigation
        - проверить всю логику

        - get_gold
"""
import sys
import logging
from typing import Dict

import telegram.error
from telegram import Bot, Update, BotCommand
from telegram.ext import (
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ChatMemberHandler,
    PreCheckoutQueryHandler
)

from corporatum.celery import app  # event processing in async mode
from corporatum.settings import TELEGRAM_TOKEN, DEBUG

from tgbot.handlers.utils.conf import *
from tgbot.handlers.utils import track_user
from tgbot.handlers.utils import files, error

from tgbot.handlers.onboarding import handlers as onboarding_handlers
from tgbot.handlers.getgold import handlers as getgol_handlers
from tgbot.handlers.courses import handlers as courses_handlers
from tgbot.handlers.runtest import handlers as runtest_handlers
from tgbot.handlers.profile import handlers as profile_handlers



from tgbot.handlers.broadcast_message import handlers as broadcast_handlers
from tgbot.handlers.broadcast_message.static_text import broadcast_command
from tgbot.handlers.broadcast_message.manage_data import CONFIRM_DECLINE_BROADCAST




def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    get_gold_handler = ConversationHandler(
        entry_points=[
            CommandHandler('getgold', onboarding_handlers.get_gold),
            CallbackQueryHandler(getgol_handlers.run_pay, pattern='get_gold')
        ],
        states={
            PAYMENT_PREPARE: [
                CallbackQueryHandler(getgol_handlers.choose_payment_type, pattern='pay'),
                CallbackQueryHandler(getgol_handlers.enter_promocode, pattern='enter_promocode'),
            ],
            CATCH_PROMOCDE: [
                CallbackQueryHandler(getgol_handlers.choose_payment_type, pattern='pay'),
                MessageHandler(Filters.text & ~Filters.command, getgol_handlers.catch_promocode)
            ],
            PAY: [
                CallbackQueryHandler(getgol_handlers.send_payment, pattern='^pmnt_type-(\d)$'),
                PreCheckoutQueryHandler(getgol_handlers.precheckout_callback),
                MessageHandler(Filters.successful_payment, getgol_handlers.successful_payment_callback)
            ],

        },
        fallbacks=[
            CommandHandler('stop', onboarding_handlers.stop), # -> STOPPING
        ],
        map_to_parent={
            TO_COURSES: CHOOSER,
            STOPPING: STOPPING,
        },
    )
    run_test_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(runtest_handlers.run_test, pattern='run_first_test|run_test')
        ], # выводим смс с правилами, кнопка первый вопрос
        states={
            INER: [CallbackQueryHandler(runtest_handlers.run_test, pattern='run_test')], 
            QUESTIONS: [CallbackQueryHandler(runtest_handlers.show_question, pattern='^q_id-(\d)$')],
            CATCH_ANSWER: [MessageHandler(Filters.text & ~Filters.command, runtest_handlers.catch_answer)],
        },
        fallbacks=[
            CallbackQueryHandler(runtest_handlers.go_up, pattern='change-lvl|thems|get_gold|back'), # -> BACK|END
            CallbackQueryHandler(runtest_handlers.finish_test, pattern='finish_test'), # -> done -> end
            CommandHandler('stop', onboarding_handlers.stop), # -> STOPPING
        ],
        map_to_parent={
            # Return to choose level menu
            BACK: CHOOSER,
            # Return to top level menu
            END: SELECTING_LEVEL,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )
    profile_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(profile_handlers.ask_input, pattern='^profile$')],
        states={
            EDIT_MSG: [CallbackQueryHandler(profile_handlers.edit_msg, pattern='enter_name|enter_email')],
            TYPING: [
                MessageHandler(Filters.regex("[^@]+@[^@]+\.[^@]+"), profile_handlers.save_email), # будет вызывать ask_input
                MessageHandler(Filters.regex(u"(\w+)\s(\w+)"), profile_handlers.save_name), # будет вызывать ask_input
                ]
        },
        fallbacks=[
            CallbackQueryHandler(onboarding_handlers.done, pattern=f'back'), #  return END
            CommandHandler('stop', onboarding_handlers.stop), #  return STOPPING
        ],
        map_to_parent={
            # Return to second level menu
            END: SELECTING_LEVEL,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )
    courses_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(courses_handlers.show_thems, pattern='^thems$'),
            CommandHandler('gostudy', onboarding_handlers.go_study),
        ],
        states={
            CHOOSER: [
                CallbackQueryHandler(courses_handlers.show_thems, pattern='^thems$'), # показываем все темы
                CallbackQueryHandler(courses_handlers.show_test, pattern='^theme-(\d)$'), # получаем тему, открываем тесты
                CallbackQueryHandler(courses_handlers.choose_lvl, pattern='^lvl-(\d)$'), # кнопки сложность, начать кнопки назад, начать
            ], 
            CHOOSE_TEST: [MessageHandler(Filters.text & ~Filters.command, courses_handlers.choose_test)],  # получаем тест, открываем уровень
            GO: [run_test_handler],
        },
        fallbacks=[
            CallbackQueryHandler(onboarding_handlers.done, pattern=f'back'), # -> END
            CommandHandler('stop', onboarding_handlers.stop), # -> STOPPING
        ],
        map_to_parent={
            # Return to top level menu
            END: SELECTING_LEVEL,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )
    
    commands_handler = [
        CommandHandler('start', onboarding_handlers.start), # return SELECTING_LEVEL | CHECK_SUBSRIBE
        CommandHandler('gostudy', onboarding_handlers.go_study), # return RUN_TEST
        CommandHandler('getgold', onboarding_handlers.get_gold), # return GET_GOLD
        CommandHandler('help', onboarding_handlers.help), # STOPPING
    ]
    conv_handler = ConversationHandler(
        entry_points=commands_handler,
        states={
            SELECTING_LEVEL: [
                profile_handler, # done
                run_test_handler,
                get_gold_handler,
                courses_handler
            ],
            CHECK_SUBSRIBE: [ChatMemberHandler(track_user.check_subscribe, ChatMemberHandler.CHAT_MEMBER)],
            STOPPING: commands_handler,
        },
        fallbacks=[
            CallbackQueryHandler(onboarding_handlers.done, pattern=f'done|exit')
        ]
    )
    
    # main handle
    dp.add_handler(conv_handler)

    # broadcast message
    dp.add_handler(
        MessageHandler(Filters.regex(rf'^{broadcast_command}(/s)?.*'), broadcast_handlers.broadcast_command_with_message)
    )
    dp.add_handler(
        CallbackQueryHandler(broadcast_handlers.broadcast_decision_handler, pattern=f"^{CONFIRM_DECLINE_BROADCAST}")
    )
    # files
    dp.add_handler(MessageHandler(Filters.animation, files.show_file_id))

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)

    return dp


def run_pooling():
    """ Run bot in pooling mode """
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp = setup_dispatcher(dp)

    bot_info = Bot(TELEGRAM_TOKEN).get_me()
    bot_link = f"https://t.me/" + bot_info["username"]

    print(f"Pooling of '{bot_link}' started")
    # it is really useful to send '👋' emoji to developer
    # when you run local test
    # bot.send_message(text='👋', chat_id=<YOUR TELEGRAM ID>)

    updater.start_polling()
    updater.idle()


# Global variable - best way I found to init Telegram bot
bot = Bot(TELEGRAM_TOKEN)
try:
    TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
except telegram.error.Unauthorized:
    logging.error(f"Invalid TELEGRAM_TOKEN.")
    sys.exit(1)


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def set_up_commands(bot_instance: Bot) -> None:
    langs_with_commands: Dict[str, Dict[str, str]] = {
        'en': {
            'start': 'Start bot 🚀',
            'help': 'Need help ℹ️',
            'gostudy': 'Start test ✅',
            'getgold': 'Get gold 💎',
            'stop': 'Stop the process 📛',
        },
        'ru': {
            'start': 'Запустить бота 🚀',
            'help': 'Нужна помошь ℹ️',
            'gostudy': 'Пройти тест ✅',
            'getgold': 'Получить золото 💎',
            'stop': 'Остановить процесс 📛',
        }
    }

    bot_instance.delete_my_commands()
    for language_code in langs_with_commands:
        bot_instance.set_my_commands(
            language_code=language_code,
            commands=[
                BotCommand(command, description) for command, description in langs_with_commands[language_code].items()
            ]
        )


# WARNING: it's better to comment the line below in DEBUG mode.
# Likely, you'll get a flood limit control error, when restarting bot too often
#set_up_commands(bot)

n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True))
