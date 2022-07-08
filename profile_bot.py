import json
from telebot import TeleBot
from telebot.types import Message
from references import CHOICE_BUTTONS_PARAMS, RequestPhrases, ResponsePhrases, PROFILE_ELEMENTS, TYPES_ACTIVITES, \
    COMMUNITES, TARGETS, LOCATIONS, PERSONAL_ACCOUNT_BUTTONS
from storage_db import UserDb


class ProfileBot:
    def __init__(self, bot: TeleBot):
        self.bot: TeleBot = bot

    def confirm_name(self, message: Message):
        if message.text and message.text.lower() == 'да':
            self.bot.send_message(message.chat.id, 'Запомню \U0001F60A')
            if message.chat.username:
                self.user.add_attribute(message.chat.id, 'telegram_name', message.chat.username)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_number)
            self.bot.register_next_step_handler(msg, self.get_number)
        elif message.text.lower() == 'нет':
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_name)
            self.bot.register_next_step_handler(msg, self.remember_name)
        else:
            msg = self.bot.send_message(message.chat.id, 'Введите "да" или "нет".')
            self.bot.register_next_step_handler(msg, self.confirm_name)

    def get_number(self, message: Message):
        if message.text:
            self.user.add_attribute(message.chat.id, 'phone', message.text)
            self.bot.send_message(message.chat.id, 'Отлично! Записал Ваш телефон \U0000260E')
            self.create_keyboard(message.chat.id, ['У меня нет почты'])
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_post,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.get_post)
        else:
            msg = self.bot.send_message(message.chat.id, 'Похоже Вы где-то ошиблись, перепроверьте номер \U0001F609')
            self.bot.register_next_step_handler(msg, self.get_number)

    def remember_name(self, message: Message):
        if message.text:
            self.bot.send_message(message.chat.id, 'Запомню \U0001F60A')
            if message.chat.username:
                self.user.add_attribute(message.chat.id, 'telegram_name', message.chat.username)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_number)
            self.bot.register_next_step_handler(msg, self.get_number)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_name)
            self.bot.register_next_step_handler(msg, self.remember_name)

    def get_post(self, message: Message):
        if not message.text:
            self.create_keyboard(message.chat.id, PROFILE_ELEMENTS)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_post,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.get_post)
        elif message.text.lower() == 'у меня нет почты':
            self.user.add_attribute(message.chat.id, 'email', message.text)
            self.bot.send_message(message.chat.id, ResponsePhrases.no_post_reponse)
            self.create_keyboard(message.chat.id, PROFILE_ELEMENTS)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_photo)
            self.bot.register_next_step_handler(msg, self.processing_photo)
        elif '@' not in message.text or len(message.text) < 4:
            msg = self.bot.send_message(message.chat.id, 'Похоже Вы где-то ошиблись, перепроверьте почту \U0001F609')
            self.bot.register_next_step_handler(msg, self.get_post)
        else:
            self.user.add_attribute(message.chat.id, 'email', message.text)
            self.bot.send_message(message.chat.id, 'Супер! Почта в базе данных! \U00002709')
            self.create_keyboard(message.chat.id, PROFILE_ELEMENTS)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_photo)
            self.bot.register_next_step_handler(msg, self.processing_photo)

    def processing_photo(self, message: Message):
        if message.content_type == 'photo':
            photo = self.bot.get_file(message.photo[-1].file_id)
            download_file = self.bot.download_file(photo.file_path)
            self.user.add_attribute(message.chat.id, 'photo', download_file)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_fullname)
            self.bot.register_next_step_handler(msg, self.processing_fullname)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.repeat_request_photo)
            self.bot.register_next_step_handler(msg, self.processing_photo)

    def processing_fullname(self, message: Message):
        if message.text:
            self.user.add_attribute(message.chat.id, 'fullname', message.text)
            # self.bot.send_message(message.chat.id, ResponsePhrases.fullname_added_success)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_age)
            self.bot.register_next_step_handler(msg, self.processing_age)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_fullname)
            self.bot.register_next_step_handler(msg, self.processing_fullname)

    def processing_age(self, message: Message):
        if message.text and message.text.strip().isdigit():
            self.user.add_attribute(message.chat.id, 'age', int(message.text))
            self.create_keyboard(message.chat.id, TYPES_ACTIVITES[:-1], True)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_type_activity,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_type_activity)
        else:
            msg = self.bot.send_message(message.chat.id, ResponsePhrases.no_digit)
            self.bot.register_next_step_handler(msg, self.processing_age)

    def processing_type_activity(self, message: Message):
        if message.text and message.text.lower().capitalize() in TYPES_ACTIVITES[:-1]:
            self.user.add_attribute(message.chat.id, 'types_activity', message.text)
            button_name = message.text.lower().capitalize()
            self.add_button(self.temp_source_markup, TYPES_ACTIVITES[-1], message.chat.id)
            self.delete_button(message.chat.id, button_name, True)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_is_selection_completed,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_type_activity)
        elif message.text and message.text.lower().capitalize() == TYPES_ACTIVITES[-1]:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_interests)
            self.bot.register_next_step_handler(msg, self.processing_interests)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_type_activity,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_type_activity)

    def processing_interests(self, message: Message):
        if message.text:
            self.user.add_attribute(message.chat.id, 'interests', message.text)
            self.create_keyboard(message.chat.id, COMMUNITES[:-1], True)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_community,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_community)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_interests)
            self.bot.register_next_step_handler(msg, self.processing_interests)

    def processing_community(self, message: Message, one_time_use: bool = False):
        if message.text in COMMUNITES[:-1]:
            self.user.add_attribute(message.chat.id, 'community', message.text)
            button_name = message.text
            self.add_button(self.temp_source_markup, COMMUNITES[-1], message.chat.id)
            self.delete_button(message.chat.id, button_name, True)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_is_selection_community_completed,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_community, one_time_use)
        elif message.text and message.text.lower().capitalize() == COMMUNITES[-1]:
            if one_time_use:
                self.create_keyboard(message.chat.id, TARGETS)
                community = self.user.extract_one_attribute(message.chat.id, 'community')
                community = json.dumps(community)
                self.db_client.update_field(UserDb, 'community', community, message.chat.id)
                msg = self.bot.send_message(message.chat.id, RequestPhrases.request_target, reply_markup=self.source_markup[message.chat.id])
                self.bot.register_next_step_handler(msg, self.processing_targets, True)
                return
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_personal_info)
            self.bot.register_next_step_handler(msg, self.processing_personal_info)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_community,
                                        reply_markup=self.temp_source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_community, one_time_use)

    def processing_personal_info(self, message: Message):
        if message.text:
            self.user.add_attribute(message.chat.id, 'personal_info', message.text)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_city)
            self.bot.register_next_step_handler(msg, self.processing_city)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_personal_info)
            self.bot.register_next_step_handler(msg, self.processing_personal_info)

    def processing_city(self, message: Message):
        if message.text:
            self.user.add_attribute(message.chat.id, 'city', message.text)
            self.create_keyboard(message.chat.id, TARGETS)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_target,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_targets)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_personal_info)
            self.bot.register_next_step_handler(msg, self.processing_personal_info)

    def processing_targets(self, message: Message, one_time_use: bool = False):
        if message.text == 'Завершить выбор целей':
            self.create_keyboard(message.chat.id, LOCATIONS)
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_location,
                                        reply_markup=self.source_markup[message.chat.id])
            if one_time_use:
                targets = self.user.extract_one_attribute(message.chat.id, 'targets')
                targets = json.dumps(targets)
                self.db_client.update_field(UserDb, 'targets', targets, message.chat.id)
                self.bot.register_next_step_handler(msg, self.processing_location, True)
        elif message.text in TARGETS:
            self.increase_quantity_targets(message.chat.id)
            self.user.add_attribute(message.chat.id, 'targets', message.text)
            button_name = message.text
            self.add_button(self.source_markup, 'Завершить выбор целей', message.chat.id)
            self.delete_button(message.chat.id, button_name)
            if len(self.user.person[message.chat.id]['targets']) == 3:
                if one_time_use:
                    targets = self.user.extract_one_attribute(message.chat.id, 'targets')
                    targets = json.dumps(targets)
                    self.db_client.update_field(UserDb, 'targets', targets, message.chat.id)
                self.create_keyboard(message.chat.id, LOCATIONS)
                msg = self.bot.send_message(message.chat.id, RequestPhrases.request_location,
                                            reply_markup=self.source_markup[message.chat.id])
                self.bot.register_next_step_handler(msg, self.processing_location, True)
            else:
                msg = self.bot.send_message(message.chat.id, RequestPhrases.request_target,
                                            reply_markup=self.source_markup[message.chat.id])
                self.bot.register_next_step_handler(msg, self.processing_targets, one_time_use)
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_target,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_targets, one_time_use)

    def processing_location(self, message: Message, one_time_use: bool = False):
        if message.text in LOCATIONS:
            if one_time_use:
                self.user.add_attribute(message.chat.id, 'location', int(message.text[-1]))
                location = self.user.extract_one_attribute(message.chat.id, 'location')
                location = json.dumps(location)
                self.db_client.update_field(UserDb, 'location', int(location), message.chat.id)
                del self.user.person[message.chat.id]
                self.create_keyboard(message.chat.id, CHOICE_BUTTONS_PARAMS)
                communities = self.db_client.get_community(UserDb, message.chat.id)
                text_communities = ', '.join(communities)
                targets = self.db_client.get_targets(UserDb, message.chat.id)
                text_targets = ', '.join(targets)
                location = self.db_client.get_location(UserDb, message.chat.id)
                text = f'Сообщества: {text_communities}\nЦели поиска: {text_targets}\nЛокация поиска: {location}'
                self.bot.send_message(message.chat.id, text)
                msg = self.bot.send_message(message.chat.id, RequestPhrases.request_change_params, reply_markup=self.source_markup[message.chat.id])
                self.bot.register_next_step_handler(msg, self.start_search, targets, location, communities)
                return
            self.record_information(message)
            del self.user.person[message.chat.id]
            self.create_keyboard(message.chat.id, PERSONAL_ACCOUNT_BUTTONS)
            self.bot.send_message(message.chat.id, ResponsePhrases.profile_filled_success,
                                  reply_markup=self.source_markup[message.chat.id])
        else:
            msg = self.bot.send_message(message.chat.id, RequestPhrases.request_location,
                                        reply_markup=self.source_markup[message.chat.id])
            self.bot.register_next_step_handler(msg, self.processing_location, one_time_use)

    def record_information(self, message: Message):
        self.user.add_attribute(message.chat.id, 'location', int(message.text[-1]))
        self.user.enter_data_to_database(message.chat.id)
