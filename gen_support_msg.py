from tgbot.models import SupportMessage

lines = 'BOT_ERROR--add_users_by_admin--add_users_by_user--all_themes--answer_correct--answer_incorrect--ask_profile--ask_subscribe--catch_data--choose_lvl--choose_pay--choose_test_error--choose_todo--close_question--email_error--enter_email--enter_name--enter_promocode--error_payment--error_promocode--finish_test--help_command--hide_question--name_error--no_answer--no_register--pay_help--payment_sucsess--promocode_correct--question_text--say_thanks--send_invoice--show_question--show_tests--show_user_choice--start_test--start_test_no_active--start_test_no_gold--start_test_no_gold--stop--whait_subscribe'

for line in lines.split('--'):
    print(line)
    text = f'command <b>{line}</b>\n\n some text'
    o = SupportMessage.objects.create(
        text=text, 
        role=line, 
        is_active=True
    )
    o.save()