# Бот-помощник онлайн-издательства "Игра слов"
Бот-помощник для VK и Telegram, который проводит викторину.\
Имя бота в Телеграм `@rs0x069_museum_quiz_bot`\
Бот работает на сервисе [Heroku](https://heroku.com/).


## Требования
* Python 3.8, 3.9 или 3.10.
* Redis

### Зависимые модули
* python-dotenv==0.20.0
* python-telegram-bot==13.12
* vk-api==11.9.8
* redis==4.3.4

## Предварительные требования
1. Для телеграм бота необходимо создать бота в Телеграм и получить токен. Разрешить боту отправлять вам уведомления.
2. Для бота в VK необходимо создать сообщество в VK. В настройках сообщества включить сообщения и создать ключ API. Пользователям нужно разрешить сообществу отправлять им сообщения.

## Установка
* Склонировать проект
```commandline
git clone https://github.com/rs0x069/museum_quiz.git
```
* Перейти в папку `museum_quiz`
* Установить пакеты
```commandline
pip install -r requirements.txt
```
* Создать файл `.env` со следующими переменными окружения:
  + `TELEGRAM_TOKEN` - токен телеграм бота.
  + `VK_TOKEN` - ключ API из VK.
  + `REDIS_HOST` - адрес базы данных Redis
  + `REDIS_PORT` - порт базы данных Redis
  + `REDIS_USERNAME` - имя пользователя для доступа к базе данных Redis
  + `REDIS_PASSWORD` - пароль для доступа к базе данных Redis

## Использование
* Для запуска телеграм бота запустить скрипт `bot_tg.py`
```commandline
python bot_tg.py
```
* Для запуска бота VK запустить скрипт `bot_vk.py`
```commandline
python bot_vk.py
```

## Примеры
#### Пример результата для Telegram:
![Пример результата для Telegram](https://raw.githubusercontent.com/rs0x069/museum_quiz/main/.github/images/examination_tg.gif)

#### Пример результата для ВКонтакте:
![Пример результата для ВКонтакте](https://raw.githubusercontent.com/rs0x069/museum_quiz/main/.github/images/examination_vk.gif)


***
Учебный проект для курсов web-разработчиков [dvmn](https://dvmn.org). 
