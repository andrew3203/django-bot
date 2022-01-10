from telegram.ext import ConversationHandler



# for deep linking
FROM_MY_CHANEL = 'from-my-chanel'
ADD_FRIEND = 'add-by-user'


# time then questions is avalible
DELAY = 50

# time for waiting user subsxribe
WAIT_FOR_SUBSCRIBE = 20

END = ConversationHandler.END

# main handler
SELECTING_LEVEL, CHECK_SUBSRIBE, STOPPING = map(chr, range(5, 8))

# profile handler
EDIT_MSG, TYPING = map(chr, range(8, 10))

# all courses handler
CHOOSER, CHOOSE_TEST, RUN_TEST = map(chr, range(10, 13))

# run test handler
QUESTIONS, CATCH_ANSWER, BACK = map(chr, range(13, 16))

# pay handler
PAYMENT_PREPARE, CATCH_PROMOCDE, PAY, TO_COURSES = map(chr, range(16, 20))