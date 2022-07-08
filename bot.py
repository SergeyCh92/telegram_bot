from references import PERSONAL_ACCOUNT_BUTTONS, PROFILE_MANAGEMENT_BUTTONS, RequestPhrases, ResponsePhrases, \
    PROFILE_ELEMENTS, COMMUNITES, TYPES_ACTIVITES, CHOICE_BUTTONS_PARAMS, SEARCH_MANAGEMENT_BUTTONS, ELEMENT_PLACE, \
    SEARCH_MANAGEMENT_BUTTONS_LAST_EL
from telebot import TeleBot
from telebot.types import Message
from typing import List, Optional, Any, Tuple
from storage_db import DbClient, UserDb, MatchesResult
import json
from base_bot import BaseBot
from profile_bot import ProfileBot
from references import TARGETS


class Bot(BaseBot, ProfileBot):
    def __init__(self, bot: TeleBot, db_client: DbClient):
        BaseBot.__init__(self, db_client)
        self.bot: TeleBot = bot

    # TODO разделить функционал по разным классам
    def handler_personal_account(self, message: Message):
        if not message.text or message.text not in PROFILE_MANAGEMENT_BUTTONS:
            self.create_keyboard(message.chat.id, PROFILE_MANAGEMENT_BUTTONS)
            msg = self.bot.send_message(message.chat.id, 'Выберите один из вариантов ниже',
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.handler_personal_account)
        elif message.text == PROFILE_MANAGEMENT_BUTTONS[0]:
            self.create_keyboard(message.chat.id, PROFILE_ELEMENTS)
            self.add_button(self.source_markup, 'В главное меню', message.chat.id)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_change,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_changes)
        elif message.text == PROFILE_MANAGEMENT_BUTTONS[1]:
            pass
        elif message.text == PROFILE_MANAGEMENT_BUTTONS[2]:
            pass

    def processing_changes(self, message: Message):
        if message.text == 'В главное меню':
            self.create_keyboard(message.chat.id, PERSONAL_ACCOUNT_BUTTONS)
            msg = self.bot.send_message(message.chat.id, ResponsePhrases.select_button,
                                        reply_markup=self.source_markup[message.chat.id])
        elif message.text not in PROFILE_ELEMENTS:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_change_repeat,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_changes)
        elif message.text == PROFILE_ELEMENTS[0]:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_fullname)
            self.bot.register_next_step_handler(msg, self.change_text_field, 'fullname',
                                                ResponsePhrases.fullname_changed_success,
                                                RequestPhrases.request_fullname)
        elif message.text == PROFILE_ELEMENTS[1]:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_photo)
            self.bot.register_next_step_handler(msg, self.change_photo_field)
        elif message.text == PROFILE_ELEMENTS[2]:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_age)
            self.bot.register_next_step_handler(msg, self.change_text_field, 'age', ResponsePhrases.age_added_success,
                                                RequestPhrases.request_age, self._validation_integer)
        elif message.text == PROFILE_ELEMENTS[3]:
            self.create_keyboard(message.chat.id, TYPES_ACTIVITES[:-1], True)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_type_activity,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.change_list_field, TYPES_ACTIVITES, 'types_activity')
        elif message.text == PROFILE_ELEMENTS[4]:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_interests)
            self.bot.register_next_step_handler(msg, self.change_text_field, 'interests',
                                                ResponsePhrases.interests_changed_success,
                                                RequestPhrases.request_interests)
        elif message.text == PROFILE_ELEMENTS[5]:
            self.create_keyboard(message.chat.id, COMMUNITES[:-1], True)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_community,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.change_list_field, COMMUNITES, 'community')
        elif message.text == PROFILE_ELEMENTS[6]:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_personal_info)
            self.bot.register_next_step_handler(msg, self.change_text_field, 'personal_info',
                                                ResponsePhrases.personal_info_changed_success,
                                                RequestPhrases.request_personal_info)
        elif message.text == PROFILE_ELEMENTS[7]:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_city)
            self.bot.register_next_step_handler(msg, self.change_text_field, 'city',
                                                ResponsePhrases.city_changed_success,
                                                RequestPhrases.request_city)

    def change_text_field(self, message: Message, field: str, response_text_success: str,
                          response_text_invalid: str, validation: Any = None):
        if message.text:
            if validation:
                is_valid = validation(message.text)
                if not is_valid:
                    msg = self.bot.send_message(message.chat.id, response_text_invalid)
                    self.bot.register_next_step_handler(msg, self.change_text_field, field,
                                                        response_text_success, response_text_invalid,
                                                        self._validation_integer)
                    return
            self.db_client.update_field(UserDb, field, message.text, message.chat.id)
            # del self.user.person[message.chat.id]
            msg = self.bot.send_message(message.chat.id, response_text_success,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_changes)
        else:
            msg = self.bot.send_message(message.chat.id, response_text_invalid)
            self.bot.register_next_step_handler(msg, self.change_text_field, field,
                                                response_text_success, response_text_invalid,
                                                self._validation_integer)

    def change_photo_field(self, message: Message):
        if message.content_type == 'photo':
            photo = self.bot.get_file(message.photo[-1].file_id)
            download_file = self.bot.download_file(photo.file_path)
            self.db_client.update_field(UserDb, 'photo', download_file, message.chat.id)
            # del self.user.person[message.chat.id]
            msg = self.bot.send_message(message.chat.id, ResponsePhrases.photo_changed_success,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_changes)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_photo)
            self.bot.register_next_step_handler(msg, self.change_photo_field)

    def change_list_field(self, message: Message, button_source: List[str], field: str):
        if message.text in button_source[:-1]:
            self.user.add_attribute(message.chat.id, field, message.text)
            button_name = message.text
            self.add_button(self.temp_source_markup, button_source[-1], message.chat.id)
            self.delete_button(message.chat.id, button_name, True)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_is_selection_completed,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.change_list_field, button_source, field)
        elif message.text == button_source[-1]:
            data = self.user.extract_one_attribute(message.chat.id, field)
            types_activites = json.dumps(data, ensure_ascii=False)
            self.db_client.update_field(UserDb, field, types_activites, message.chat.id)
            del self.user.person[message.chat.id][field]
            msg = self.bot.send_message(message.chat.id, ResponsePhrases.type_activity_changed_success,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_changes)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_photo)
            self.bot.register_next_step_handler(msg, self.change_list_field, button_source, field)

    def _validation_integer(self, age: Any):
        try:
            age = int(age)
            return True
        except ValueError:
            return False

    # функционал поиска. Тоже крайне желательно вынести в отдельный класс
    def start_search(self, message: Message, targets: List[str], location: int, communities: List[str]):
        if message.text not in CHOICE_BUTTONS_PARAMS:
            msg = self.bot.send_message(message.chat.id, ResponsePhrases.no_button_selected)
            self.bot.register_next_step_handler(msg, self.start_search)
        elif message.text == CHOICE_BUTTONS_PARAMS[0]:
            self.bot.send_message(message.chat.id, ResponsePhrases.start_search)
            relevant_users = self.search_matches(message.chat.id, targets, location, communities)
            quantity_results = len(relevant_users)
            if quantity_results == 0:
                self.create_keyboard(message.chat.id, PERSONAL_ACCOUNT_BUTTONS)
                msg = self.bot.send_message(message.chat.id, ResponsePhrases.unsuccessful_search,
                                            reply_markup=self.source_markup[message.chat.id])
            else:
                # user_id = relevant_users[0]
                text, photo = self.prepare_data_for_response(message.chat.id, 0)
                self.db_client.update_field(MatchesResult, 'cursor', 1, message.chat.id)
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS[1:])
                msg = self.bot.send_photo(message.chat.id, photo, caption=text,
                                          reply_markup=self.source_markup[message.chat.id])
                self.bot.register_next_step_handler(msg, self.processing_search)
        elif message.text == CHOICE_BUTTONS_PARAMS[1]:
            self.create_keyboard(message.chat.id, COMMUNITES, True)
            self.processing_community(message, True)

    def matches_attributes(self, users_data: List[Any], targets: List[str], communities: List[str]) -> \
            List[Optional[int]]:
        relevant_users = []
        for user in users_data:
            match_community = set(json.loads(user.community)) & set(communities)
            match_targets = set(json.loads(user.targets)) & set(targets)
            if match_community and match_targets:
                relevant_users.append(user.id_telegram)
        return relevant_users

    def search_matches(self, user_id: int, targets: List[str], location: int, communities: List[int]) -> \
            List[Optional[int]]:
        # TODO убрать из списка релевантных юзеров id пользователя, который начал поиск
        users = self.db_client.get_matching_users(UserDb, location)
        relevant_users = self.matches_attributes(users, targets, communities)
        relevant_users_json = json.dumps(relevant_users, ensure_ascii=False)
        matches = MatchesResult(
            id=user_id,
            matches=relevant_users_json
        )
        self.db_client.add_matches(matches, user_id)
        return relevant_users

    def prepare_text_profile(self, user_data: UserDb) -> str:
        interests = user_data.interests if not user_data.interests else user_data.interests[1:-1]
        text = f'ФИО: {user_data.fullname}\n' \
               f'Сообщества: {user_data.community[1:-1]}\nemail: {user_data.email}\nВозраст: {user_data.age}\n' \
               f'Виды деятельности: {user_data.types_activity[1:-1]}\nИнтересы: {interests}\n' \
               f'Город постоянного проживания: {user_data.city}\nПара слов о себе: {user_data.personal_info}'
        return text

    def processing_search(self, message: Message):
        if not message.text or message.text not in SEARCH_MANAGEMENT_BUTTONS:
            msg = self.bot.send_message(message.chat.id, 'Выберите один из вариантов ниже',
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_search)
        elif message.text == SEARCH_MANAGEMENT_BUTTONS[4]:
            self.create_keyboard(message.chat.id, PERSONAL_ACCOUNT_BUTTONS)
            self.bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=self.source_markup[message.chat.id])
        elif message.text == SEARCH_MANAGEMENT_BUTTONS[3]:
            cursor = self.db_client.get_cursor(message.chat.id)
            element_place = self.check_is_boundary(message.chat.id, cursor)
            if element_place == ELEMENT_PLACE[0]:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS[1:])
            elif element_place == ELEMENT_PLACE[1]:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS_LAST_EL)
            else:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS)
            text, photo = self.prepare_data_for_response(message.chat.id, cursor)
            self.db_client.update_field(MatchesResult, 'cursor', cursor + 1, message.chat.id)
            msg = self.bot.send_photo(message.chat.id, photo, caption=text,
                                      reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_search)
        elif message.text == SEARCH_MANAGEMENT_BUTTONS[0]:
            cursor = self.db_client.get_cursor(message.chat.id)
            cursor -= 2
            if cursor < 0:
                pass
            element_place = self.check_is_boundary(message.chat.id, cursor)
            if element_place == ELEMENT_PLACE[0]:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS[1:])
            elif element_place == ELEMENT_PLACE[1]:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS_LAST_EL)
            else:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS)
            text, photo = self.prepare_data_for_response(message.chat.id, cursor)
            self.db_client.update_field(MatchesResult, 'cursor', cursor + 1, message.chat.id)
            msg = self.bot.send_photo(message.chat.id, photo, caption=text,
                                      reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_search)
        elif message.text == SEARCH_MANAGEMENT_BUTTONS[1]:
            last = False
            cursor = self.db_client.get_cursor(message.chat.id)
            cursor -= 1
            users_ids = self.db_client.get_matching_list_user_id(message.chat.id)
            favourite_user_id = users_ids[cursor]
            users_ids.remove(users_ids[cursor])
            if not users_ids:
                self.create_keyboard(message.chat.id, ['В главное меню'])
                self.bot.send_message(message.chat.id, 'К сожалению подходящих анкет больше нет! Попробуйте начать новый поиск и изменить его параметры.', reply_markup=self.source_markup[message.chat.id])
                return
            if cursor == len(users_ids):
                self.db_client.update_field(MatchesResult, 'cursor', cursor, message.chat.id)
            users_ids = json.dumps(users_ids)
            self.db_client.update_field(MatchesResult, 'matches', users_ids, message.chat.id)
            element_place = self.check_is_boundary(message.chat.id, cursor)
            if element_place == ELEMENT_PLACE[0]:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS[1:])
            elif element_place == ELEMENT_PLACE[1]:
                last = True
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS_LAST_EL)
                text, photo = self.prepare_data_for_response(message.chat.id, cursor - 1)
            elif element_place == ELEMENT_PLACE[3]:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS_LAST_EL[1:])
            else:
                self.create_keyboard(message.chat.id, SEARCH_MANAGEMENT_BUTTONS)
            if not last:
                text, photo = self.prepare_data_for_response(message.chat.id, cursor)
            msg = self.bot.send_photo(message.chat.id, photo, caption=text,
                                      reply_markup=self.source_markup[message.chat.id])
            self.send_like(message.chat.id, favourite_user_id)
            self.bot.register_next_step_handler(msg, self.processing_search)

    def prepare_data_for_response(self, chat_id: int, cursor: Optional[int] = None) -> Tuple[str, bytes]:
        if cursor or cursor == 0:
            match_user_id = self.db_client.get_matching_user_id(chat_id, cursor)
            match_user = self.db_client.get_user(match_user_id)
            text = self.prepare_text_profile(match_user)
            photo = match_user.photo
        elif not cursor:
            match_user = self.db_client.get_user(chat_id)
            text = self.prepare_text_profile(match_user)
            photo = match_user.photo
        return text, photo

    def get_contact(self, chat_id: int):
        user_data = self.db_client.get_user(chat_id)
        if user_data.telegram_name:
            return user_data.telegram_name
        else:
            return user_data.phone

    def check_is_boundary(self, user_id: int, cursor: int) -> str:
        users_ids = self.db_client.get_matching_list_user_id(user_id)
        if len(users_ids) == 1:
            return ELEMENT_PLACE[3]
        if cursor == 0:
            return ELEMENT_PLACE[0]
        if cursor + 1 >= len(users_ids):
            return ELEMENT_PLACE[1]
        else:
            return ELEMENT_PLACE[2]

    def send_like(self, user_id: int, favourite_user_id: int):
        text, photo = self.prepare_data_for_response(user_id)
        contact = self.get_contact(favourite_user_id)
        callback_data = [user_id, contact]
        callback_data = json.dumps(callback_data)
        self.create_inline_keyboard(user_id, {'Лайкнуть \U00002764': 'like_' + callback_data,
                                    'Отклонить \U0001F6AB': 'reject_' + callback_data}, True)
        self.bot.send_photo(favourite_user_id, photo, caption=text, reply_markup=self.temp_source_markup[user_id])
