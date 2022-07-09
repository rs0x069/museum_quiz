import os
import random
import re
import redis

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler


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
                        answer = answer.translate({ord(c): None for c in '."[]'}).strip().lower()

                        quiz_questions.append({
                            'Вопрос': question,
                            'Ответ': answer
                        })
    except OSError as err:
        print(f'OSError: {err}')
    else:
        return quiz_questions


def start_command(update, context):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    update.message.reply_text('Привет! Я бот для викторин!', reply_markup=reply_markup)


def quiz(update, context):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

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

    user_id = update.message.from_user.id

    if update.message.text == 'Новый вопрос':
        wished_question = db_redis.get(user_id)

        if wished_question:
            return update.message.reply_text('Нужно ответить на загаданный вопрос. Сдаёшься?',
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

        correct_answer = ''
        for quiz_question in load_questions():
            if quiz_question['Вопрос'] == wished_question:
                correct_answer = quiz_question['Ответ']
                break

        if user_answer == correct_answer:
            quiz_response = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
            db_redis.delete(user_id)
        else:
            quiz_response = 'Неправильно… Попробуешь ещё раз?'

    update.message.reply_text(quiz_response, reply_markup=reply_markup)


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

    for item in load_questions():
        print(item['Ответ'])

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, quiz))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
