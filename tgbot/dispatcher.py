"""
    Telegram event handlers
      
"""
import sys
import logging
from typing import Dict
from queue import Queue
from threading import Thread

import telegram.error
from telegram import Bot, Update, BotCommand
from telegram.ext import (
    JobQueue,
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ChatMemberHandler,
    PreCheckoutQueryHandler,
    PollAnswerHandler
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


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
    get_gold_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(getgol_handlers.run_pay, pattern='^get_gold$', pass_job_queue=True)],
        states={
            PAYMENT_PREPARE: [
                CallbackQueryHandler(getgol_handlers.choose_payment_type, pattern='pay', pass_job_queue=True),
                CallbackQueryHandler(getgol_handlers.enter_promocode, pattern='enter_promocode', pass_job_queue=True),
            ],
            CATCH_PROMOCDE: [
                CallbackQueryHandler(getgol_handlers.choose_payment_type, pattern='pay', pass_job_queue=True),
                MessageHandler(Filters.text & ~Filters.command, getgol_handlers.catch_promocode, pass_job_queue=True)
            ],
            PAY: [
                CallbackQueryHandler(getgol_handlers.send_payment, pattern='^pmnt_type-(\d+)$', pass_job_queue=True),
                MessageHandler(Filters.successful_payment, getgol_handlers.successful_payment_callback, pass_job_queue=True)
            ],
        },
        fallbacks=[
            CommandHandler('stop', onboarding_handlers.stop, pass_job_queue=True), # -> STOPPING
            CallbackQueryHandler(profile_handlers.go_back, pattern='^back$', pass_job_queue=True), #  return END

        ],
        map_to_parent={
            END: SELECTING_LEVEL,
            STOPPING: STOPPING,
        },
        per_message=True
    )
    profile_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(profile_handlers.ask_input, pattern='^profile$')],
        states={
            EDIT_MSG: [CallbackQueryHandler(profile_handlers.edit_msg, pattern='(enter_name)|(enter_email)')],
            TYPING: [
                MessageHandler(Filters.regex("[^@]+@[^@]+\.[^@]+"), profile_handlers.save_email), 
                MessageHandler(Filters.regex(u"(\w+)\s(\w+)"), profile_handlers.save_name), 
                ]
        },
        fallbacks=[
            CallbackQueryHandler(profile_handlers.go_back, pattern=f'back'), #  return END
            CommandHandler('stop', onboarding_handlers.stop), #  return STOPPING
        ],
        map_to_parent={
            # Return to second level menu
            END: SELECTING_LEVEL,
            # End conversation altogether
            STOPPING: STOPPING,
        },
        per_message=True
    )
    run_test_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(runtest_handlers.run_test, pattern='^(run_first_test)|(run_test)$', pass_job_queue=True)
        ],
        states={
            INER: [CallbackQueryHandler(runtest_handlers.run_test, pattern='^run_test$', pass_job_queue=True)], 
            QUESTIONS: [CallbackQueryHandler(runtest_handlers.show_question, pattern='^q_id-(\d+)$', pass_job_queue=True)],
            CATCH_ANSWER: [
                CallbackQueryHandler(runtest_handlers.receive_callback_answer, pattern='^ans-(\d+)$', pass_job_queue=True),
                CallbackQueryHandler(runtest_handlers.show_question, pattern='^q_id-(\d+)$', pass_job_queue=True),
                MessageHandler(Filters.text & ~Filters.command, runtest_handlers.receive_text_answer, pass_job_queue=True),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(runtest_handlers.change_test_lvl, pattern='^change-lvl$', pass_job_queue=True), # -> END
            CallbackQueryHandler(runtest_handlers.change_test_theme, pattern='^themes$', pass_job_queue=True), # -> END
            CallbackQueryHandler(runtest_handlers.test_no_gold, pattern='^get_gold$', pass_job_queue=True), # -> END
            CallbackQueryHandler(runtest_handlers.need_profile, pattern='^profile$', pass_job_queue=True), # -> END
            CallbackQueryHandler(runtest_handlers.test_go_back, pattern='^back$', pass_job_queue=True), # -> END
            CallbackQueryHandler(runtest_handlers.finish_test, pattern='^finish_test$', pass_job_queue=True), # -> done -> END
            CommandHandler('stop', onboarding_handlers.stop, pass_job_queue=True), # -> STOPPING
        ],
        map_to_parent={
            END: SELECTING_LEVEL,
            STOPPING: STOPPING,
        },
        per_message=True
    )
    control_course_sett_handlers = [
        CallbackQueryHandler(courses_handlers.show_themes, pattern='^themes$', pass_job_queue=True), 
        CallbackQueryHandler(courses_handlers.show_test, pattern='^theme-(\d+)$', pass_job_queue=True),
        CallbackQueryHandler(courses_handlers.choose_lvl, pattern='^lvl-(\d+)$', pass_job_queue=True),
    ]
    courses_handler = ConversationHandler(
        entry_points=control_course_sett_handlers,
        states={
            CHOOSER: control_course_sett_handlers,
            CHOOSE_TEST: [MessageHandler(Filters.text & ~Filters.command, courses_handlers.choose_test, pass_job_queue=True)],  # получаем тест, открываем уровень
            GO: [run_test_handler],
        },
        fallbacks=[
            CallbackQueryHandler(onboarding_handlers.done, pattern=f'^back$', pass_job_queue=True), # -> END
            CommandHandler('stop', onboarding_handlers.stop, pass_job_queue=True), # -> STOPPING
        ],
        map_to_parent={
            END: SELECTING_LEVEL,
            SELECTING_LEVEL: SELECTING_LEVEL, 
            STOPPING: STOPPING,
        },
        per_message=True
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', onboarding_handlers.start, pass_job_queue=True)],
        states={
            SELECTING_LEVEL: [
                courses_handler,
                run_test_handler,
                profile_handler, 
                get_gold_handler,
                CallbackQueryHandler(onboarding_handlers.help, pattern=f'help', pass_job_queue=True),
            ],
            STOPPING: [
                CommandHandler('start', onboarding_handlers.start, pass_job_queue=True), 
                CommandHandler('help', onboarding_handlers.help, pass_job_queue=True), 
                CommandHandler('addfriend', onboarding_handlers.add_friend, pass_job_queue=True), 
            ],
        },
        fallbacks=[
            CallbackQueryHandler(onboarding_handlers.stop, pattern=f'^(done)|(exit)$', pass_job_queue=True),
            CommandHandler('stop', onboarding_handlers.stop, pass_job_queue=True)
        ],
        per_message=True
    )

    # main handle
    dp.add_handler(conv_handler)

    # track chat mabmer
    dp.add_handler(ChatMemberHandler(track_user.tack_chat_members, ChatMemberHandler.CHAT_MEMBER))
    # add friend command
    dp.add_handler(CommandHandler('addfriend', onboarding_handlers.add_friend))
    # payments handle
    dp.add_handler(PreCheckoutQueryHandler(getgol_handlers.precheckout_callback))
    # polls handle
    dp.add_handler(PollAnswerHandler(runtest_handlers.receive_poll_answer))

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

    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    updater.idle()


def set_up_commands(bot_instance: Bot) -> None:
    langs_with_commands: Dict[str, Dict[str, str]] = {
        'en': {
            'start': 'Start bot 🚀',
            'help': 'Need help ℹ️',
            'addfriend': 'Invite Friend!',
            'stop': 'Stop the process 📛',
        },
        'ru': {
            'start': 'Запустить бота 🚀',
            'help': 'Нужна помошь ℹ️',
            'addfriend': 'Пригласить друзей!',
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


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


# Global variable - best way I found to init Telegram bot
bot = Bot(TELEGRAM_TOKEN)
try:
    TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
except telegram.error.Unauthorized:
    logging.error(f"Invalid TELEGRAM_TOKEN.")
    sys.exit(1)

if not DEBUG:
    set_up_commands(bot)

n_workers = 0 if DEBUG else 4
queue = JobQueue()
dispatcher = setup_dispatcher(
    Dispatcher(
        bot,
        job_queue=queue,
        workers=n_workers, 
        update_queue=None, 
        use_context=True
    )
)
queue.set_dispatcher(dispatcher)
queue.start()
