import os
import random
import re
import redis

from enum import Enum, unique
from functools import partial

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

reply_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
reply_markup = ReplyKeyboardMarkup(reply_keyboard)


@unique
class Quiz(Enum):
    NEW_QUESTION = 1
    ANSWER = 2
    GIVING_UP = 3
    SCORE = 4


def load_questions():
    files_folder = 'quiz-questions'

    try:
        quiz_files = [
            os.path.join(files_folder, filename)
            for filename in os.listdir(files_folder)
            if os.path.isfile(os.path.join(files_folder, filename))
        ]
        quiz_files.sort()
    except OSError as err:
        print(f'OSError: {err}')
        return False

    quiz_questions = []
    try:
        for quiz_file in quiz_files[:1]:
            with open(quiz_file, 'r', encoding='KOI8-R') as readable_file:
                for line in readable_file:
                    if re.search(r'^Вопрос\s\d+:$', line):
                        search_pattern = ''
                        question = ''
                        while search_pattern != '\n':
                            search_pattern = readable_file.readline()
                            question += search_pattern.replace('\n', ' ')
                        question = question.rstrip()

                        # Method 1 to find answer
                        # while readable_file.readline() != 'Ответ:\n':
                        #     next(readable_file)
                        # answer = readable_file.readline().rstrip()

                    # Method 2 to find answer
                    if re.search(r'^Ответ:$', line):
                        answer = readable_file.readline().rstrip()
                        answer_lowercase = answer.translate({ord(c): None for c in '."[]'}).strip().lower()

                        quiz_questions.append({
                            'Вопрос': question,
                            'Ответ': answer_lowercase
                        })
    except OSError as err:
        print(f'OSError: {err}')
    else:
        return quiz_questions


def get_random_quiz_question():
    quiz_questions = load_questions()
    random_number_questions = random.randint(0, len(quiz_questions) - 1)
    return quiz_questions[random_number_questions]['Вопрос']


def get_correct_answer(wished_question):
    for quiz_question in load_questions():
        if quiz_question['Вопрос'] == wished_question:
            return quiz_question['Ответ']
    return None


def start_command(update, context):
    update.message.reply_text('Привет! Я бот для викторин!', reply_markup=reply_markup)
    return Quiz.NEW_QUESTION


def handle_new_question_request(update, context, db_redis):
    user_id = update.message.from_user.id

    wished_question = db_redis.get(user_id)
    if wished_question:
        update.message.reply_markdown(f'Нужно ответить на загаданный вопрос. Сдаёшься?\n`{wished_question}`',
                                      reply_markup=reply_markup)
        return Quiz.ANSWER

    random_quiz_question = get_random_quiz_question()
    db_redis.set(user_id, random_quiz_question)

    update.message.reply_text(random_quiz_question, reply_markup=reply_markup)

    return Quiz.ANSWER


def handle_solution_attempt(update, context, db_redis):
    user_id = update.message.from_user.id

    wished_question = db_redis.get(user_id)
    if not wished_question:
        update.message.reply_text('Для следующего вопроса нажми "Новый вопрос"', reply_markup=reply_markup)
        return Quiz.NEW_QUESTION

    user_answer = ''.join(update.message.text).lower()
    correct_answer = get_correct_answer(wished_question)

    if user_answer == correct_answer:
        quiz_response = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        db_redis.delete(user_id)
        update.message.reply_text(quiz_response, reply_markup=reply_markup)
        return Quiz.NEW_QUESTION
    else:
        quiz_response = 'Неправильно… Попробуешь ещё раз?'
        update.message.reply_text(quiz_response, reply_markup=reply_markup)
        return Quiz.ANSWER


def handle_giving_up(update, context, db_redis):
    user_id = update.message.from_user.id

    wished_question = db_redis.get(user_id)
    if not wished_question:
        update.message.reply_text('Вопрос не задан. Для следующего вопроса нажми "Новый вопрос"',
                                  reply_markup=reply_markup)
        return Quiz.NEW_QUESTION

    correct_answer = get_correct_answer(wished_question)
    update.message.reply_text(f'Правильный ответ: {correct_answer}', reply_markup=reply_markup)

    random_quiz_question = get_random_quiz_question()
    db_redis.set(user_id, random_quiz_question)
    update.message.reply_text(f'Новый вопрос: {random_quiz_question}', reply_markup=reply_markup)

    return Quiz.ANSWER


def quiz(update, context, db_redis):
    user_id = update.message.from_user.id

    if update.message.text == 'Новый вопрос':
        wished_question = db_redis.get(user_id)

        if wished_question:
            return update.message.reply_markdown(
                f'Нужно ответить на загаданный вопрос. Сдаёшься?\n`{wished_question}`',
                reply_markup=reply_markup)

        quiz_questions = load_questions()
        random_number_questions = random.randint(0, len(quiz_questions) - 1)
        random_quiz_question = quiz_questions[random_number_questions]['Вопрос']

        db_redis.set(user_id, random_quiz_question)
        quiz_response = random_quiz_question

    elif update.message.text == 'Сдаться':
        quiz_response = 'Не сдавайся, попробуй ещё раз'

    elif update.message.text == 'Мой счёт':
        quiz_response = 'Ваш счёт'

    else:
        wished_question = db_redis.get(user_id)

        if not wished_question:
            return update.message.reply_text('Для следующего вопроса нажми "Новый вопрос"', reply_markup=reply_markup)

        user_answer = ''.join(update.message.text).lower()
        correct_answer = get_correct_answer(wished_question)

        if user_answer == correct_answer:
            quiz_response = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
            db_redis.delete(user_id)
        else:
            quiz_response = 'Неправильно… Попробуешь ещё раз?'

    update.message.reply_text(quiz_response, reply_markup=reply_markup)


def cancel_command(update, context):
    update.message.reply_text(
        'До свидания! Попробуйте пройти викторину ещё раз.', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_TOKEN")
    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    redis_username = os.getenv("REDIS_USERNAME")
    redis_password = os.getenv("REDIS_PASSWORD")

    db_redis = redis.Redis(
        host=redis_host,
        port=int(redis_port),
        db=0,
        username=redis_username,
        password=redis_password,
        decode_responses=True
    )

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    # quiz_redis = partial(quiz, db_redis=db_redis)
    handle_new_question_request_redis = partial(handle_new_question_request, db_redis=db_redis)
    handle_solution_attempt_redis = partial(handle_solution_attempt, db_redis=db_redis)
    handle_giving_up_redis = partial(handle_giving_up, db_redis=db_redis)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            Quiz.NEW_QUESTION: [MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request_redis)],
            Quiz.ANSWER: [
                MessageHandler(
                    Filters.text &
                    ~(Filters.command | Filters.regex('^Сдаться$') | Filters.regex('^Мой счёт$') | Filters.regex(
                        '^Новый вопрос$')), handle_solution_attempt_redis),
                MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request_redis),
                MessageHandler(Filters.regex('^Сдаться$'), handle_giving_up_redis)
            ],
            # Quiz.GIVING_UP: [MessageHandler(Filters.regex('^Сдаться$'), handle_giving_up_redis)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)]
    )
    dispatcher.add_handler(conv_handler)

    # dispatcher.add_handler(CommandHandler('start', start_command))
    # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, quiz_redis))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
