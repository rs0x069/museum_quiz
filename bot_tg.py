import os

import redis

from enum import Enum, unique
from functools import partial

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from questions_management import get_random_quiz_question, get_correct_answer, load_questions


@unique
class Quiz(Enum):
    NEW_QUESTION = 1
    ANSWER = 2
    GIVING_UP = 3
    SCORE = 4


def start_command(update, context):
    reply_keyboard = [['Новый вопрос', 'Сдаться']]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    update.message.reply_text('Привет! Нажми "Новый вопрос" для начала викторины\n /cancel - для отмены',
                              reply_markup=reply_markup)
    return Quiz.NEW_QUESTION


def handle_new_question_request(update, context, db_conn, questions):
    user_id = update.message.from_user.id

    wished_question = db_conn.get(user_id)
    if wished_question:
        update.message.reply_markdown(f'Нужно ответить на загаданный вопрос. Сдаёшься?\n`{wished_question}`')
        return Quiz.ANSWER

    random_quiz_question = get_random_quiz_question(questions)
    db_conn.set(user_id, random_quiz_question)

    update.message.reply_text(random_quiz_question)

    return Quiz.ANSWER


def handle_solution_attempt(update, context, db_conn, questions):
    user_id = update.message.from_user.id

    wished_question = db_conn.get(user_id)
    if not wished_question:
        update.message.reply_text('Для следующего вопроса нажми "Новый вопрос"')
        return Quiz.NEW_QUESTION

    user_answer = ''.join(update.message.text).lower()
    correct_answer = get_correct_answer(questions, wished_question)

    if user_answer == correct_answer:
        quiz_response = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        db_conn.delete(user_id)
        update.message.reply_text(quiz_response)
        return Quiz.NEW_QUESTION
    else:
        quiz_response = 'Неправильно… Попробуешь ещё раз?'
        update.message.reply_text(quiz_response)
        return Quiz.ANSWER


def handle_giving_up(update, context, db_conn, questions):
    user_id = update.message.from_user.id

    wished_question = db_conn.get(user_id)
    if not wished_question:
        update.message.reply_text('Вопрос не задан. Для следующего вопроса нажми "Новый вопрос"')
        return Quiz.NEW_QUESTION

    correct_answer = get_correct_answer(questions, wished_question)
    update.message.reply_text(f'Вот тебе правильный ответ: {correct_answer}')

    random_quiz_question = get_random_quiz_question(questions)
    db_conn.set(user_id, random_quiz_question)
    update.message.reply_text(f'Новый вопрос: {random_quiz_question}')

    return Quiz.ANSWER


def cancel_command(update, context):
    update.message.reply_text(
        'До свидания! Попробуйте пройти викторину ещё раз.', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    load_dotenv()
    quiz_questions = load_questions()

    telegram_token = os.getenv("TELEGRAM_TOKEN")
    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    redis_username = os.getenv("REDIS_USERNAME")
    redis_password = os.getenv("REDIS_PASSWORD")

    redis_conn = redis.Redis(
        host=redis_host,
        port=int(redis_port),
        db=0,
        username=redis_username,
        password=redis_password,
        decode_responses=True
    )

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    handle_new_question_request_redis = partial(handle_new_question_request,
                                                db_conn=redis_conn,
                                                questions=quiz_questions)
    handle_solution_attempt_redis = partial(handle_solution_attempt,
                                            db_conn=redis_conn,
                                            questions=quiz_questions)
    handle_giving_up_redis = partial(handle_giving_up,
                                     db_conn=redis_conn,
                                     questions=quiz_questions)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            Quiz.NEW_QUESTION: [
                MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request_redis),
                MessageHandler(Filters.regex('^Сдаться$'), handle_giving_up_redis)
            ],
            Quiz.ANSWER: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Сдаться$') | Filters.regex('^Новый вопрос$')),
                    handle_solution_attempt_redis
                ),
                MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request_redis),
                MessageHandler(Filters.regex('^Сдаться$'), handle_giving_up_redis)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
