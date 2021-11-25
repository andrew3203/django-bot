from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import CallbackContext
from tgbot.handlers.utils.conf import *
from tgbot.models import User
from tgbot.handlers.utils.handlers import _do_message, send_selecting_lvl, remove_job_if_exists



def is_user_subscribed(context: CallbackContext):
    hcnt = context.job.context
    user = User.objects.filter(user_id=hcnt.user_id).first()
    if user and not user.is_subscribed:
        hcnt.role = 'whait_subscribe'
        _do_message(hcnt)

def extract_status_change(chat_member_update: ChatMemberUpdated):
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = (
        old_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    )
    is_member = (
        new_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    )
    return was_member, is_member

def tack_chat_members(update: Update, context: CallbackContext) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is not None:
        was_member, is_member = result
        cause_name = update.chat_member.from_user.mention_html()
        member_name = update.chat_member.new_chat_member.user.username
        u = User.objects.filter(username=member_name).first()

        if u and not was_member and is_member:
            u.is_subscribed = True
            u.save()
            if remove_job_if_exists(f'{u.user_id}-checksubscribe', context):       
                context.user_data['hcnt'].role = 'choose_todo'
                send_selecting_lvl(update, context)
            #update.effective_chat.send_message(f"{member_name} was added by {cause_name}. Welcome!")
            
        elif u and was_member and not is_member:
            u.is_subscribed = False
            u.save()
            #update.effective_chat.send_message(f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...")