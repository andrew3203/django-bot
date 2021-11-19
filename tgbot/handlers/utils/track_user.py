from telegram import (
    Update,
    ChatMember, ChatMemberUpdated,

)
from telegram.ext import CallbackContext
from tgbot.handlers.utils.conf import *
from tgbot.models import User
from tgbot.handlers.utils.handlers import _do_message



def is_new_member(chat_member_update: ChatMemberUpdated) -> bool:
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))
    if status_change is not None:
        old_status, new_status = status_change
        was_member = (old_status == ChatMember.RESTRICTED and old_is_member is True)
        is_member = (new_status == ChatMember.RESTRICTED and new_is_member is True)
        if not was_member and is_member:
            return True
    return False


def check_subscribe(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    user = User.objects.filter(user_id=hcnt.user_id).first()
    if user is None:
        return END
    elif is_new_member(update.chat_member):
        member_name = update.chat_member.new_chat_member.user.mention_html()
        if member_name in context.user_data['msg']['new_user']:
            hcnt.role = 'say_thanks'
            _do_message(hcnt)
            hcnt.role = 'choose_todo'
            _do_message(hcnt)
            user.last_name = 'JustSubscribed'
            user.save()
            return SELECTING_LEVEL

    return CHECK_SUBSRIBE


def subscribe_faild(context: CallbackContext):
    hcnt = context.job.context
    user = User.objects.filter(user_id=hcnt.user_id).first()
    if user.last_name == '':
        user.delete()
        hcnt.role = 'whait_subscribe'
        _do_message(hcnt)
