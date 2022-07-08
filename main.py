import os
import random
import re

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


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

    update.message.reply_text('Привет! Я бот для викторин!:', reply_markup=reply_markup)


def echo_message(update, context):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    quiz_questions = load_questions()
    random_number_questions = random.randint(0,  len(quiz_questions)-1)

    if update.message.text == 'Новый вопрос':
        quiz_question = quiz_questions[random_number_questions]['Вопрос']
    else:
        quiz_question = 'Вопрос не определён'

    update.message.reply_text(quiz_question, reply_markup=reply_markup)


def main():
    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_TOKEN")

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
