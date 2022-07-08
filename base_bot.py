from storage_db import DbClient, UserDb
from typing import Dict, Optional, List, Tuple, Union
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import json


class BaseBot:
    def __init__(self, db_client: DbClient):
        self.source_markup: Dict[str, ReplyKeyboardMarkup] = {}
        self.temp_source_markup: Dict[str, ReplyKeyboardMarkup] = {}
        self.db_client: DbClient = db_client
        self.user: User = User(self.db_client)
        self.quantity_targets: Dict[Optional[int], int] = dict()

    def increase_quantity_targets(self, chat_id: int):
        if self.quantity_targets.get(chat_id):
            self.quantity_targets[chat_id] += 1
        else:
            self.quantity_targets[chat_id] = 1

    def create_keyboard(self, chat_id: int, names: List[str], temp_keyboard: bool = False):
        source_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for name in names:
            btn = KeyboardButton(name)
            source_markup.add(btn)

        if temp_keyboard:
            self.temp_source_markup[chat_id] = source_markup
        else:
            self.source_markup[chat_id] = source_markup

    def create_inline_keyboard(self, chat_id: int, names: Dict[str, str], temp_keyboard: bool = False):
        source_markup = InlineKeyboardMarkup()
        for name, callback_data in names.items():
            btn = InlineKeyboardButton(text=name, callback_data=callback_data)
            source_markup.add(btn)

        if temp_keyboard:
            self.temp_source_markup[chat_id] = source_markup
        else:
            self.source_markup[chat_id] = source_markup

    def delete_button(self, chat_id: int, button_name: str, temp_keyboard: bool = False):
        if temp_keyboard:
            self.temp_source_markup[chat_id].keyboard = [button for button in self.temp_source_markup[chat_id].keyboard
                                                         if button[0]['text'].lower() != button_name.lower()]
        else:
            self.source_markup[chat_id].keyboard = [button for button in self.source_markup[chat_id].keyboard if
                                                    button[0]['text'].lower() != button_name.lower()]

    def add_button(self, source: Dict[str, ReplyKeyboardMarkup], button_name: str, chat_id):
        list_names_btn = [name[0]['text'] for name in source[chat_id].keyboard]
        if button_name in list_names_btn:
            return
        btn = KeyboardButton(button_name)
        source[chat_id].add(btn)


class User:
    def __init__(self, db_client: DbClient):
        self.person: Dict[str, Dict[str, str]] = dict()
        self.db_client: DbClient = db_client

    def add_attribute(self, chat_id: int, attr_name: str, value: Union[str, bytes]):
        multivalue_attrs = ['types_activity', 'interests', 'community', 'targets']
        if attr_name in multivalue_attrs:
            if self.person.get(chat_id):
                if self.person[chat_id].get(attr_name):
                    self.person[chat_id][attr_name].append(value)
                else:
                    self.person[chat_id][attr_name] = [value]
            else:
                self.person[chat_id] = {attr_name: [value]}
        elif self.person.get(chat_id):
            self.person[chat_id][attr_name] = value
        else:
            self.person[chat_id] = {attr_name: value}

    def extract_one_attribute(self, chat_id: int, attr_name: str):
        if self.person.get(chat_id):
            if self.person[chat_id].get(attr_name) or self.person[chat_id].get(attr_name) == 0:
                result = self.person[chat_id].get(attr_name)
                return result
        else:
            return None

    def prepare_data_to_database(self, chat_id: int) -> UserDb:
        fullname, photo, age, types_activites, interests, communities, personal_info, city, \
            phone, email, telegram_name, targets, location = self.extract_data(chat_id)
        user = UserDb(
            fullname=fullname,
            photo=photo,
            age=age,
            types_activity=types_activites,
            interests=interests,
            community=communities,
            personal_info=personal_info,
            city=city,
            phone=phone,
            email=email,
            telegram_name=telegram_name,
            id_telegram=chat_id,
            targets=targets,
            location=location
        )
        return user

    def enter_data_to_database(self, chat_id: str):
        user = self.prepare_data_to_database(chat_id)
        self.db_client.add_user(user)

    def extract_data(self, chat_id: str) -> Tuple[str, bytes, int, str, str, str, str, str, str, str, int]:
        fullname = self.person[chat_id]['fullname']
        photo = self.person[chat_id]['photo']
        age = self.person[chat_id]['age']
        types_activites = self.person[chat_id]['types_activity']
        interests = self.person[chat_id]['interests']
        communities = self.person[chat_id]['community']
        personal_info = self.person[chat_id]['personal_info']
        city = self.person[chat_id]['city']
        phone = self.person[chat_id]['phone']
        email = self.person[chat_id]['email']
        targets = self.person[chat_id]['targets']
        location = self.person[chat_id]['location']
        if self.person[chat_id].get('telegram_name'):
            telegram_name = self.person[chat_id]['telegram_name']
        else:
            telegram_name = ''

        types_activites = json.dumps(types_activites, ensure_ascii=False)
        interests = json.dumps(interests, ensure_ascii=False)
        communities = json.dumps(communities, ensure_ascii=False)
        targets = json.dumps(targets, ensure_ascii=False)

        return fullname, photo, age, types_activites, interests, communities, personal_info, city, \
            phone, email, telegram_name, targets, location
