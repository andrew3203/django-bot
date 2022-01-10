import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corporatum.settings')
django.setup()

from tgbot.models import SupportMessage


def generate():
    data = [
        ('BOT_ERROR', 'Что-то сломалось внутри бота.\r\nЭто потому, что мы постоянно улучшаем наш сервис, но иногда мы можем забыть протестировать некоторые базовые вещи.\r\nМы уже получили все подробности по устранению проблемы.\r\nНажмите, чтобы /stop остановить, а затем /start', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'), 
        ('add_users_by_admin', 'Приглашаю использовать бота (для канала)', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'), 
        ('add_users_by_user', 'Приглашаю использовать бота', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'),
        ('all_themes', 'Список всех доступных тем', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'), 
        ('answer_correct', 'Ответ получен!\r\nТекст вопроса: question_text\r\n\r\nПроверка: is_correct\r\nОтвет получен: answer', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nquestion_name - Название вопроса\r\nquestion_text - Текст вопроса\r\ntime_to_question - Время, отведенное на решение вопроса\r\nquestion_lvl - Уровень сложности\r\n\r\nanswer - Полученный ответ'), ('answer_incorrect', 'Ответ получен\r\nТекст вопроса: question_text\r\n\r\nПроверка: is_correct\r\nОтвет получен: answer\r\nНе решение осталсоь time_left', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nquestion_name - Название вопроса\r\nquestion_text - Текст вопроса\r\ntime_to_question - Время, отведенное на решение вопроса\r\nquestion_lvl - Уровень сложности\r\n\r\ntime_left - Оставшееся время для решения вопроса'),
        ('ask_profile', 'Давайте зарегистрируемся', 'username - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя'),
        ('ask_subscribe', 'Подпишись пожайлуста на канал, first_name', 'username - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя'), 
        ('catch_data', 'Получено, first_name!', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'), 
        ('choose_lvl', 'Выберите пожалуйста уровень сложности', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\ntheme_name - Название темы\r\ntest_name - Название теста'),
        ('choose_pay', 'Выберете вариант оплаты из доступных, first_name!\r\n\r\nplans', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nplans - Список доступных вариантов оплаты'),
        ('choose_test_error', 'Ошибка в выборе теста, пожалуйста попробуйте еще раз', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\ntheme_name - Название темы'),
        ('choose_todo', 'Добро пожаловать в главное меню first_name!\r\n\r\nУ вас на счете  <b> username</b> золотых', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nusername - Количество золотых монет у пользователя'),
        ('close_question', 'Вопрос: question_name', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\nquestion_name - Название вопроса\r\nquestion_text - Текст вопроса\r\ntime_to_question - Время для решения вопроса\r\nquestion_lvl - Сложность вопроса'),
        ('email_error', 'Вы не верно ввели почту, введите пожалуйста заново в формате \r\n\r\nexample@domain.path', 'username - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'),
        ('enter_email', 'Введите пожалуйста почту в формате\r\n\r\nexample@domain.path', 'username - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'),
        ('enter_name', 'Введите пожалуйста ваше имя и фамилию ф формате \r\n\r\nИмя Фамилия', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nuser_gold - Количество золотых монет у пользователя'),
        ('enter_promocode', 'Введите промокод', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'),
        ('error_payment', 'Ошибка оплаты', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'),
        ('error_promocode', 'Такого промокода не существует, он просрочен или вы уже им воспользовались', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'),
        ('finish_test', 'Ура, вы прошли тест! \r\nВот Ваши результаты\r\n\r\n<b>right_amount </b> -  Количество правильных ответов\r\n<b>right_percent</b> - Процент правильных ответов', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nright_amount - Количество правильных ответов\r\nquestions_amount - Количество вопросов в тесте\r\nright_percent - Процент правильных ответов\r\nwrong_percent - Процент неправильных ответов'),
        ('help_command', 'Команда подсказка \r\n\r\nчто можно делать с ботом\r\nкому написать в случае чего\r\n\r\nЧтобы продолжить использовать бота нажмите\r\n/start', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'),
        ('hide_question', 'Вопрос question_position', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nquestion_position - Номер вопроса в тесте\r\nquestion_name - Название вопроса\r\nquestion_text - Текст вопроса\r\nquestion_lvl - Сложность вопроса\r\ntime_to_question - Время на решение вопроса'), ('name_error', 'Вы не верно ввели имя \r\nпожалуйста введите его в формате  \r\n\r\nИмя Фамилия', 'username - Никнейм пользователя в Телеграм'), 
        ('no_answer', 'Ответ не был получен, вопрос:\r\nquestion_name\r\nскрыт', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nquestion_position - Номер вопроса в тесте\r\nquestion_name - Название вопроса\r\nquestion_text - Текст вопроса\r\nquestion_lvl - Сложность вопроса\r\ntime_to_question - Время на решение вопроса'), 
        ('no_register', 'Для начала необходимо зарегистрироваться!', 'username - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя'), ('pay_help', 'Краткая инструкция к оплате', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'), 
        ('payment_sucsess', 'Ура, оплата прошла!\r\nТеперь у вас <b>user_gold</b> на счете', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'), 
        ('promocode_correct', 'Промокод принят!\r\n\r\npromocode_text\r\n\r\nВаша скидка - promocode_discount', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя\r\n\r\npromocode_name - Название промокода\r\nis_valid - Дейсвителен ли промокод\r\npromocode_text- Текст промокода\r\npromocode_discount - Скидка, %'),('question_text', 'Вопрос:\r\nquestion_text\r\n\r\ntime_to_question', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nquestion_position - Номер вопроса в тесте\r\nquestion_name - Название вопроса\r\nquestion_text - Текст вопроса\r\nquestion_lvl - Сложность вопроса\r\ntime_to_question - Время на решение вопроса'), ('say_thanks', 'Спасибо что подписались, username!', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя'), ('send_invoice', 'Вы выбрали:\r\nТип оплаты  - paymen_plan_name\r\nЦена - paymen_plan_cost\r\nВы получите paymen_plan_gold_amount\r\nПромокод: is_promocode', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nplans - Доступные планы\r\npaymen_plan_name - Название типа оплаты\r\npaymen_plan_cost - Стоимость золотых (в рублях)\r\npaymen_plan_gold_amount - Количество золотых, которое упадет на счет при покупке\r\nis_promocode-Использовал ли пользователя промокод'), 
        ('show_question', '<b>show_question</b>\r\nquestion_name\r\nquestion_text\r\n\r\nquestion_text\r\n\r\nВремЯ на решение: <b>time_to_question</b>', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\nquestion_name - Название вопроса\r\nquestion_text - Текст вопроса\r\ntime_to_question - Время, отведенное на решение вопроса\r\nquestion_lvl - Уровень сложности'), 
        ('show_tests', 'Список тестов', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\ntheme_name - Название темы'), 
        ('show_user_choice', 'show_user_choice', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\ntheme_name - Название темы\r\ntest_name - Названия тесты\r\n\r\nquestion_lvl - Сложность вопросов'), 
        ('start_test', 'start_test', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\ntest_name - Названия тесты\r\nquestion_lvl - Сложность вопросов'), 
        ('start_test_no_active', 'Увы, чтобы начать проходить тесты Вам необходимо зарегистрироваться', 'username - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя'), 
        ('start_test_no_gold', 'Недостаточно средств на счете', 'user_email - Почта пользователя\r\nusername - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя\r\nuser_gold - Количество золотых монет у пользователя \r\n\r\ntest_name - Названия тесты\r\nquestion_lvl - Сложность вопросов'), 
        ('stop', 'Процесс прерван, теперь нажмите  /start', 'user_email username first_name last_name user_gold'), 
        ('whait_subscribe', 'Ждем пока вы подпишитесь на канал', 'username - Никнейм пользователя в Телеграм\r\nfirst_name - Имя пользователя\r\nlast_name - Фамилия пользователя')
    ]
    for m in data:
        print(m[0])
        o = SupportMessage.objects.create(
            text=m[1], 
            role=m[0], 
            available_words=m[3],
            is_active=True
        )
        o.save()

if __name__ == "__main__":
    generate()