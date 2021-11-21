from corporatum.settings import PROVIDER_TOKEN
from telegram import (
    Update, LabeledPrice,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext
from tgbot.handlers.utils.handlers import _do_message
from tgbot.handlers.utils.conf import *
from tgbot.models import SupportMessage, PaymentPlan, Promocode, do_payment



def run_pay(update: Update, context: CallbackContext) ->str:
    hcnt = context.user_data['hcnt']
    hcnt.navigation['message_id'] =  hcnt.navigation.get(
        'message_id', 
        update.callback_query.message.message_id
    )
    hcnt.role = 'pay_help'
    hcnt.action='edit_msg'
    markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('У меня есть промокод', callback_data='enter_promocode')],
            [InlineKeyboardButton('Перейти к оплате', callback_data='pay')]
    ])
    _do_message(hcnt, message_id=hcnt.navigation['message_id'], reply_markup=markup)
    return PAYMENT_PREPARE


def enter_promocode(update: Update, context: CallbackContext) ->str:
    query = update.callback_query
    hcnt = context.user_data['hcnt']
    hcnt.action = 'edit_msg'
    hcnt.role = 'enter_promocode'
    hcnt.navigation['message_id'] = query.message.message_id
    _do_message(hcnt, message_id=query.message.message_id)
    context.user_data['hcnt'] = hcnt
    return CATCH_PROMOCDE


def catch_promocode(update: Update, context: CallbackContext) -> str:
    promocode  = update.message.text
    hcnt = context.user_data['hcnt']
    hcnt.action = 'edit_msg'
    valid_promocode = Promocode.is_promocode_valid(promocode, user_id=int(hcnt.user_id))
    if valid_promocode:
        hcnt.keywords = {
            **hcnt.keywords, **valid_promocode.to_flashtext()
        }
        hcnt.role = 'promocode_correct'
        hcnt.navigation['promocode_id'] = valid_promocode.id
        _do_message(hcnt, message_id=hcnt.navigation['message_id'])
        context.user_data['hcnt'] = hcnt
        return choose_payment_type(update, context)

    else:
        hcnt.role = 'error_promocode'
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('Оплатить без промокода', callback_data=f"pay")]
        ])
        _do_message(hcnt, message_id=hcnt.navigation['message_id'], reply_markup=markup)
        context.user_data['hcnt'] = hcnt
        return CATCH_PROMOCDE


def choose_payment_type(update: Update, context: CallbackContext) -> str:
    hcnt = context.user_data['hcnt']
    promocode_id = hcnt.navigation.get('promocode_id', None)
    p, names  = PaymentPlan.get_plans(promocode_id)
   
    hcnt.role = 'choose_pay'
    hcnt.action = 'send_msg' if promocode_id else 'edit_msg'
    hcnt.keywords = {**hcnt.keywords, **p}
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(n['name'], callback_data=f"pmnt_type-{n['id']}")] for n in names
    ])
    _do_message(hcnt, reply_markup=markup, message_id=hcnt.navigation['message_id'])

    context.user_data['hcnt'] = hcnt
    return PAY


def send_payment(update: Update, context: CallbackContext) ->str:
    query = update.callback_query
    plan_id = query.data.split('-')[-1]
    query.message.edit_text(text=f'Вы выбрали: {str(PaymentPlan.objects.get(id=plan_id))}')
    
    hcnt = context.user_data['hcnt']
    hcnt.navigation['plan_id'] = plan_id

    p, n = PaymentPlan.payment_details(hcnt.navigation.get('promocode_id', None), plan_id)
    hcnt.keywords = {**hcnt.keywords, **p}
    hcnt.role = 'send_invoice'
    msg = SupportMessage.get_message(hcnt)
    prices = [LabeledPrice(f'{n["gold_amount"]} едениц золота:', 100*n['cost'])]
    context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=f'Покупка {n["gold_amount"]} едениц золота:',
        description=msg.text,
        payload="GetGold",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
    )
    context.user_data['hcnt'] = hcnt
    return PAY


def precheckout_callback(update: Update, context: CallbackContext) -> str:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    if query.invoice_payload != 'GetGold':
        query.answer(ok=False, error_message="Возникла какая то ошибка...")
        hcnt = context.user_data['hcnt']
        hcnt.role = 'error_payment'
        hcnt.action = 'error_payment' 
        _do_message(hcnt)
        run_pay(update, context)
        return PAYMENT_PREPARE
    else:
        query.answer(ok=True)
        return PAY


def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    hcnt = context.user_data['hcnt']
    payment_plan_id = hcnt.navigation['plan_id']
    promocode_id = hcnt.navigation['promocode_id']
    do_payment(hcnt.user_id, payment_plan_id, promocode_id)

    hcnt.navigation['promocode_id'] = None
    hcnt.action = 'send_msg'
    hcnt.role = 'payment_sucsess'
    markup = InlineKeyboardMarkup([
            [InlineKeyboardButton('К курсам', callback_data='thems')]
    ])
    _do_message(hcnt, reply_markup=markup)
    context.user_data['hcnt'] = hcnt
    return END
