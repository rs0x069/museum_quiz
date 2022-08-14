import os
import random

import redis
import vk_api as vk

from dotenv import load_dotenv
from vk_api.exceptions import VkApiError
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from questions_management import get_random_quiz_question, get_correct_answer, load_questions


def handle_new_question(event, vk_api, db_redis, keyboard, questions):
    user_id = event.user_id

    wished_question = db_redis.get(user_id)

    if wished_question:
        return vk_api.messages.send(
            user_id=user_id,
            message=f'Нужно ответить на загаданный вопрос. Сдаёшься?\n{wished_question}',
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )

    random_quiz_question = get_random_quiz_question(questions)
    db_redis.set(user_id, random_quiz_question)

    vk_api.messages.send(
        user_id=event.user_id,
        message=random_quiz_question,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def handle_surrender(event, vk_api, db_redis, keyboard, questions):
    user_id = event.user_id

    wished_question = db_redis.get(user_id)

    if not wished_question:
        return vk_api.messages.send(
            user_id=user_id,
            message='Вопрос не задан. Для следующего вопроса нажми "Новый вопрос"',
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )

    correct_answer = get_correct_answer(questions, wished_question)
    vk_api.messages.send(
        user_id=user_id,
        message=f'Вот тебе правильный ответ: {correct_answer}',
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )

    random_quiz_question = get_random_quiz_question(questions)
    db_redis.set(user_id, random_quiz_question)

    vk_api.messages.send(
        user_id=event.user_id,
        message=f'Новый вопрос: {random_quiz_question}',
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def handle_user_answer(event, vk_api, db_redis, keyboard, questions):
    user_id = event.user_id

    wished_question = db_redis.get(user_id)

    if not wished_question:
        return vk_api.messages.send(
            user_id=user_id,
            message='Для следующего вопроса нажми "Новый вопрос"',
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )

    user_answer = ''.join(event.text).lower()
    correct_answer = get_correct_answer(questions, wished_question)

    if user_answer == correct_answer:
        quiz_response = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        db_redis.delete(user_id)
    else:
        quiz_response = 'Неправильно… Попробуешь ещё раз?'

    vk_api.messages.send(
        user_id=user_id,
        message=quiz_response,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def main():
    load_dotenv()

    quiz_questions = []
    try:
        quiz_questions = load_questions()
    except OSError as err:
        print(f'OSError: {err}')

    vk_token = os.getenv("VK_TOKEN")
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

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    vk_keyboard = VkKeyboard(one_time=True)
    vk_keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    vk_keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    for vk_event in longpoll.listen():
        if vk_event.type == VkEventType.MESSAGE_NEW and vk_event.to_me:
            try:
                if vk_event.text == 'Новый вопрос':
                    handle_new_question(vk_event, vk_api, db_redis, vk_keyboard, quiz_questions)
                elif vk_event.text == 'Сдаться':
                    handle_surrender(vk_event, vk_api, db_redis, vk_keyboard, quiz_questions)
                else:
                    handle_user_answer(vk_event, vk_api, db_redis, vk_keyboard, quiz_questions)
            except VkApiError as err:
                print(f'VkApiError: {err}')
            except ValueError as err:
                print(f'ValueError: {err}')


if __name__ == '__main__':
    main()
