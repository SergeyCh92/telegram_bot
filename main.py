import telebot
import logging
from dotenv import load_dotenv
import os
from telebot import logger, TeleBot
from references import PROFILE_MANAGEMENT_BUTTONS, RequestPhrases, PERSONAL_ACCOUNT_BUTTONS, CHOICE_BUTTONS_PARAMS
from bot import Bot
from storage_db import DbClient, UserDb
from utils import connect_to_db
import json


load_dotenv()
TOKEN = os.getenv('TOKEN')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
NAME_BD = os.getenv('NAME_BD')
PASSWORD = os.getenv('PASSWORD')
PG_DSN = f'postgresql://postgres:{PASSWORD}@{HOST}:{PORT}/{NAME_BD}'

db_client = DbClient(PG_DSN)

logging.basicConfig(filename='filename.log', format=' %(asctime)s - %(levelname)s - %(message)s')
logger = logger
telebot.logger.setLevel(logging.DEBUG)
telebot.apihelper.SESSION_TIME_TO_LIVE = 4 * 60

bot = Bot(TeleBot(TOKEN), db_client)
connect_to_db(bot)


@bot.bot.message_handler(commands=['start'])
def message_start(message):
    if bot.db_client.session.query(UserDb).filter(
        UserDb.id_telegram == message.chat.id
    ).first():
        pass
    elif message.chat.first_name:
        name = message.chat.first_name
        bot.create_keyboard(message.chat.id, ['Да', 'Нет'])
        msg = bot.bot.send_message(message.chat.id, f'Приветствую! Вас зовут {name}, верно?',
                                   reply_markup=bot.source_markup[message.chat.id])
        bot.bot.register_next_step_handler(msg, bot.confirm_name)
    else:
        bot.bot.send_message(message.chat.id, RequestPhrases.greeting)


@bot.bot.message_handler(content_types=['text'])
def profile_management(message):
    if not bot.db_client.session.query(UserDb).filter(
        UserDb.id_telegram == message.chat.id
    ).first():
        pass
    elif message.text in PERSONAL_ACCOUNT_BUTTONS:
        if message.text == 'Личный кабинет':
            bot.create_keyboard(message.chat.id, PROFILE_MANAGEMENT_BUTTONS)
            msg = bot.bot.send_message(message.chat.id, 'Выберите интересущий вариант',
                                       reply_markup=bot.source_markup[message.chat.id])
            bot.bot.register_next_step_handler(msg, bot.handler_personal_account)
        elif message.text == 'Продолжить поиск':
            pass
        elif message.text == 'Новый поиск':
            bot.create_keyboard(message.chat.id, CHOICE_BUTTONS_PARAMS)
            communities = bot.db_client.get_community(UserDb, message.chat.id)
            text_communities = ', '.join(communities)
            targets = bot.db_client.get_targets(UserDb, message.chat.id)
            text_targets = ', '.join(targets)
            location = bot.db_client.get_location(UserDb, message.chat.id)
            text = f'Сообщества: {text_communities}\nЦели поиска: {text_targets}\nЛокация поиска: {location}'
            bot.bot.send_message(message.chat.id, text)
            msg = bot.bot.send_message(message.chat.id, RequestPhrases.request_change_params,
                                       reply_markup=bot.source_markup[message.chat.id])
            bot.bot.register_next_step_handler(msg, bot.start_search, targets, location, communities)
    else:
        bot.create_keyboard(message.chat.id, PERSONAL_ACCOUNT_BUTTONS)
        bot.bot.send_message(message.chat.id, 'Пожалуйста, воспользуйтесь одной из кнопок ниже',
                             reply_markup=bot.source_markup[message.chat.id])


@bot.bot.callback_query_handler(func=lambda call: True)
def callback_response_profile(call):
    if call.data[:4] == 'like':
        data = call.data[5:]
        data = json.loads(data)
        user_id = data[0]
        contact = data[1]
        photo = bot.bot.get_file(call.message.photo[-1].file_id)
        download_file = bot.bot.download_file(photo.file_path)
        bot.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        bot.bot.send_photo(user_id, download_file, f'Вас лайкнули!\nКонтакт для связи: {contact}\nАнкета лайкнувшего:\n{call.message.caption}')
    elif call.data[:6] == 'reject':
        data = call.data[7:]
        data = json.loads(data)
        user_id = data[0]
        contact = data[1]
        photo = bot.bot.get_file(call.message.photo[-1].file_id)
        download_file = bot.bot.download_file(photo.file_path)
        bot.bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=None)
        bot.bot.send_photo(user_id, download_file, f'К сожалению Вас не лайкнули!\nАнкета по которой пришел отказ:\n{call.message.caption}')


if __name__ == '__main__':
    bot.bot.infinity_polling()
