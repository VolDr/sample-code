from flask import Flask
from flask import request
from flask_sslify import SSLify
from flask import jsonify
import random
from bs4 import BeautifulSoup as bs
import json
import time
import os
import requests
import re
from enum import Enum
from operator import attrgetter
from json import JSONEncoder

URL = 'https://api.telegram.org/bot922571702:AAEQfpasv5cZDmu8jnO4Lb8dfuQ9EPEuuSU/'
app = Flask(__name__)
sslify = SSLify(app)
general_folder = '/home/'
duel_folder = general_folder + 'duel/'
level_folder = general_folder + 'levels/'
activity_folder = general_folder + 'activity/'
log_msg = general_folder + 'logs/log_msg'
konf_id = [-1001230047111, -1001302039069, -1001202376846, -1001227751223, -1001341428897]

f = []
for (dir_path, dir_names, file_names) in os.walk(level_folder):
    f.extend(file_names)
    break
pass_ids = [int(re.findall('[0-9]{1,99}', file_name)[0]) for file_name in f]
levels_description = ['', '', '', '', '', '', '', '', '']
step_url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCg0Y6Q0m3A_5X0CPY-IG3Yg'
strel_url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCc7te9kr2fOVkkFay1ntCQQ'


class MyEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, LevelPhrases):
            return o.name
        else:
            return o.__dict__


class DuelPhrases(Enum):
    is_on = 'Дуэль все еще идет. {} - {}\n'
    not_start = 'Дуэль еще на началась.\n'
    not_your_turn = 'Ваш ход еще не наступил.\n'
    is_start = 'Дуэль началась! Выстрел: /vistrel Отменить: /pass\n'
    is_bad = 'Неправильно.\n'
    is_not_start = 'Дуэль еще на началась.\n'
    miss = 'Промах!\n'
    hit = 'Попал!\n'
    kill = '{} застрелен {}.\n'
    cancel = 'Дуэль отменена.\n'
    early_to_cancel = 'Еще слишком рано отменять дуэль.\n'
    can_not_cancel = 'Вы не можете отменить дуэль.\n'


class LevelPhrases(Enum):
    you_can_not = 'Слишком маленький уровень.\n'
    your_level_today = 'Твой уровень на сегодня:'
    already_roll_today = 'Возвращайтесь через'
    new_level = 'Теперь {} {} лвл {}.\n'
    you_do_not_roll_today = 'Ты еще не роллил сегодня. /roll\n'
    he_does_not_roll_today = 'Он еще не роллил сегодня. /roll\n'


class Gun(object):
    def __init__(self, accuracy, name='', damage=1):
        self.name = name
        self.accuracy = accuracy
        self.damage = damage

    def shot(self):
        return self.damage if random.randint(0, 99) in range(0, int(self.accuracy)) else 0


class Duelist(object):
    def __init__(self, id, name, hp, gun: Gun):
        self.id = id
        self.name = name
        self.hp = hp
        self.gun = gun
        self.score = Score(id=self.id, name=self.name, win=0, lose=0, rating=1200)

    def __eq__(self, other):
        return True if self.id == other.id else False

    def is_dead(self):
        return False if self.hp > 0 else True


class Duel(object):
    def __init__(self, waiting_duelist: Duelist, current_duelist: Duelist):
        self.is_on = False
        self.last_result = None
        self.waiting_duelist = waiting_duelist
        self.current_duelist = current_duelist
        self.last_turn_timestamp = time.time()
        self.score = 100

    def update_last_turn_timestamp(self):
        self.last_turn_timestamp = time.time()

    def over(self):
        self.is_on = False
        current_duelist_delta_rating = self.current_duelist.score.get_delta_rating(self.waiting_duelist.score.rating)
        waiting_duelist_delta_rating = self.waiting_duelist.score.get_delta_rating(self.current_duelist.score.rating)
        self.current_duelist.score.set_rating(True, self.score, current_duelist_delta_rating)
        self.waiting_duelist.score.set_rating(False, self.score, waiting_duelist_delta_rating)
        self.current_duelist.score.set_win_rate(True)
        self.waiting_duelist.score.set_win_rate(False)

    def change_turn(self):
        self.current_duelist, self.waiting_duelist = self.waiting_duelist, self.current_duelist

    def get_turn_result(self, id, gun_name, gun=None):
        if gun != None:
            self.current_duelist.gun = gun
        else:
            if gun_name != None:
                self.current_duelist.gun.name = gun_name
            else:
                self.current_duelist.gun.name = ''
        damage = self.current_duelist.gun.shot()
        if self.waiting_duelist.name == 'stanislav' and 'славик' in self.current_duelist.gun.name:
            damage = 1
        if damage > 0:
            self.last_result = DuelPhrases.hit
            self.waiting_duelist.hp += -damage
            if self.waiting_duelist.is_dead():
                self.over()
                self.last_result = DuelPhrases.kill
        else:
            self.last_result = DuelPhrases.miss
        if self.is_on:
            self.change_turn()
        return self.last_result

    def make_shot(self, user_id, user_name, gun_name, gun=None):
        if self.is_on:
            self.update_last_turn_timestamp()
            if self.current_duelist.id == user_id:
                self.current_duelist.score.set_name(user_name)
                result = self.get_turn_result(user_id, gun_name, gun)
                if self.last_result == DuelPhrases.kill:
                    return DuelPhrases.kill.value.format(self.waiting_duelist.name,
                                                         self.current_duelist.gun.name) + duel.current_duelist.score.get_score_str() + duel.waiting_duelist.score.get_score_str()
                else:
                    return result.value
            elif self.waiting_duelist.id == user_id:
                return DuelPhrases.not_your_turn.value
            else:
                return DuelPhrases.is_on.value.format(self.current_duelist.name, self.waiting_duelist.name)
        else:
            return DuelPhrases.is_not_start.value

    def get_last_activity(self):
        with open(activity_folder + str(self.current_duelist.id) + '_activity.json', 'r') as f:
            return json.load(f)['message']['date']

    def get_cancel(self, id):
        if self.is_on:
            if id == self.waiting_duelist.id:
                if time.time() - self.last_turn_timestamp >= 60 and time.time() - self.get_last_activity() < 120 and self.get_last_activity() - self.last_turn_timestamp >= 0:
                    self.change_turn()
                    return self.make_shot(self.current_duelist.id, self.current_duelist.name, '',
                                          Gun(100, ' в анус', 1))
                elif time.time() - self.last_turn_timestamp >= 60 and time.time() - self.get_last_activity() >= 60:
                    self.over()
                    return DuelPhrases.cancel.value
                else:
                    return DuelPhrases.early_to_cancel.value
            elif time.time() - self.last_turn_timestamp >= 300 and id != self.current_duelist.id:
                self.over()
                return DuelPhrases.cancel.value
            else:
                return DuelPhrases.can_not_cancel.value
        else:
            return DuelPhrases.is_not_start.value

    def make_duel(self, user_id, user_name, reply_id, reply_name, is_bot):
        print('ss', user_id, user_name, reply_id, reply_name, is_bot)
        if self.is_on:
            return DuelPhrases.is_on.value.format(self.current_duelist.name, self.waiting_duelist.name)
        else:
            if reply_id is None:
                return DuelPhrases.is_bad.value
            else:
                if reply_id == user_id:
                    return DuelPhrases.is_bad.value
                else:
                    self.last_result = None
                    self.is_on = True
                    self.last_turn_timestamp = time.time()
                    self.waiting_duelist = Duelist(user_id, user_name, 1, Gun(62))
                    if is_bot:
                        self.current_duelist = Duelist(1000000, 'Нишка', 1, Gun(100, ' в анус', 1))
                        return DuelPhrases.is_start.value + self.make_shot(self.current_duelist.id, 'Нишка', '')
                    else:
                        self.current_duelist = Duelist(reply_id, reply_name, 1, Gun(38))
                        if -self.waiting_duelist.score.rating + self.current_duelist.score.rating >= 500:
                            self.is_on = False
                            return 'Ты не в его эло рейндже.'
                        else:
                            return DuelPhrases.is_start.value


class DuelWithLevels(Duel):

    def get_cancel(self, id):
        status = super().get_cancel(id)

        return status

    def change_level(self):
        waiting_moder = ModerWithLevels(id=self.waiting_duelist.id, name=self.waiting_duelist.name, level=None,
                                        level_timestamp=0)
        current_moder = ModerWithLevels(id=self.current_duelist.id, name=self.current_duelist.name, level=None,
                                        level_timestamp=0)
        if not waiting_moder.is_time_is_up() and not waiting_moder.level is None:
            if not current_moder.is_time_is_up() and not current_moder.level is None:
                if waiting_moder.level > 0:
                    waiting_moder.level -= 1
                    waiting_moder.save_to_file()
                if current_moder.level < 8:
                    current_moder.level += 1
                    current_moder.save_to_file()
                return LevelPhrases.new_level.value.format(current_moder.name, current_moder.level, levels_description[
                    current_moder.level]) + LevelPhrases.new_level.value.format(waiting_moder.name, waiting_moder.level,
                                                                                levels_description[waiting_moder.level])
            else:
                return DuelPhrases.is_bad.value
        else:
            return DuelPhrases.is_bad.value

    def make_shot(self, user_id, user_name, gun_name, gun=None):
        if self.is_on:
            shot = super().make_shot(user_id, user_name, gun_name, gun)
            if self.last_result == DuelPhrases.kill:
                return shot + self.change_level()
            else:
                return shot
        else:
            return DuelPhrases.is_not_start.value

    def make_duel(self, user_id, user_name, reply_id, reply_name, is_bot):
        status = super().make_duel(user_id, user_name, reply_id, reply_name, is_bot)
        if status == DuelPhrases.is_bad.value:
            return status
        if not is_bot:
            waiting_moder = ModerWithLevels(id=self.waiting_duelist.id, name=self.waiting_duelist.name, level=None,
                                            level_timestamp=0)
            current_moder = ModerWithLevels(id=self.current_duelist.id, name=self.current_duelist.name, level=None,
                                            level_timestamp=0)
            if waiting_moder.is_time_is_up() or waiting_moder.level is None:
                self.is_on = False
                return LevelPhrases.you_do_not_roll_today.value
            elif current_moder.is_time_is_up() or current_moder.level is None:
                self.is_on = False
                return LevelPhrases.he_does_not_roll_today.value
            else:
                return status
        else:
            return status


class FileSaver(object):
    def __init__(self, file_name):
        self.file_name = file_name
        dir_name = os.path.dirname(file_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if os.path.exists(self.file_name):
            with open(self.file_name, 'r') as f:
                self.data = json.load(f)

    def save_to_file(self):  # overwrite file
        with open(self.file_name, 'w') as f:
            json.dump(self.__dict__, f, indent=4, ensure_ascii=False, cls=MyEncoder)


class Score(FileSaver):
    def __init__(self, **data):
        super().__init__(duel_folder + str(data['id']) + '.json')
        try:
            self.data
        except AttributeError:
            self.data = data
        self.id = self.data['id']
        self.name = self.data['name']
        self.win = self.data['win']
        self.lose = self.data['lose']
        self.rating = self.data['rating']
        del self.data
        self.save_to_file()

    def set_name(self, name):
        self.name = name
        self.save_to_file()

    def set_win_rate(self, is_win):
        if is_win:
            self.win += 1
        else:
            self.lose += 1
        self.save_to_file()

    def get_score_str(self):
        return self.name + ': TG: ' + str(self.win + self.lose) + ' Elo: ' + str(self.rating) + '.\n'

    def get_win_rate(self):
        try:
            return int(100 * self.win / (self.win + self.lose))
        except ZeroDivisionError:
            return 100

    def set_rating(self, is_win, score, delta_rating):
        if is_win:
            if int(delta_rating / 10) + score >= 5:
                self.rating += int(delta_rating / 10) + score
            else:
                self.rating += 5
        else:
            if int(delta_rating / 10) - score <= -5:
                self.rating += int(delta_rating / 10) - score
            else:
                self.rating -= 5
        self.save_to_file()

    def get_delta_rating(self, other_rating):
        return other_rating - self.rating

    def get_delta_win_rate(self, other_win_rate):
        return other_win_rate - self.get_win_rate()


class BoardLoader(object):
    def __init__(self, folder_name, class_name):
        self.score_list = list()
        f = []
        for (dir_path, dir_names, file_names) in os.walk(folder_name):
            f.extend(file_names)
            break
        for file_name in f:
            self.score_list.append(eval('{}(id=int({}))'.format(class_name, re.findall('[0-9]{1,99}', file_name)[0])))


class Scoreboard(BoardLoader):
    def __init__(self, folder_name):
        super().__init__(folder_name, Score.__name__)

    def get(self):
        format_str = ''
        for score in [elem for elem in sorted(self.score_list, key=attrgetter('rating'), reverse=True) if
                      elem.id != 1000000]:
            format_str += score.get_score_str()
        return format_str


class Levelboard(BoardLoader):
    def __init__(self, folder_name):
        super().__init__(folder_name, Moder.__name__)

    def get(self):
        format_str = ''
        for moder in sorted([elem for elem in self.score_list if not elem.is_time_is_up()], key=attrgetter('level'),
                            reverse=True):
            format_str += moder.get_level_str()
        return format_str


class Moder(FileSaver):
    def __init__(self, **data):
        super().__init__(level_folder + str(data['id']) + '.json')
        try:
            self.data
        except AttributeError:
            self.data = data
        self.id = self.data['id']
        self.name = self.data['name']
        self.level = self.data['level']
        self.level_timestamp = self.data['level_timestamp']
        self.roll_cool_down = 12
        self.pic_limit = 3
        del self.data
        self.save_to_file()

    def set_name(self, name):
        self.name = name
        self.save_to_file()

    def roll_level(self):
        if self.level is None or self.is_time_is_up():
            random_value = random.randint(0, 99)
            if random_value in range(0, 10):
                self.level = 1
            elif random_value in range(10, 25):
                self.level = 2
            elif random_value in range(25, 50):
                self.level = 3
            elif random_value in range(50, 65):
                self.level = 4
            elif random_value in range(65, 85):
                self.level = 5
            elif random_value in range(85, 95):
                self.level = 6
            elif random_value in range(95, 99):
                self.level = 7
            elif random_value in range(99, 100):
                self.level = 8
            self.level_timestamp = time.time()
            self.save_to_file()
            self.pic_limit = 3
            return '{} {} лвл {}.'.format(LevelPhrases.your_level_today.value, self.level,
                                          levels_description[int(self.level)]) + \
                   (' Доступны команды: /plus_lvl /minus_lvl' if self.level >= 6 else '')
        else:
            h, m = self.get_time_to_next_h_m()
            return '{} {} ч. {} м.'.format(LevelPhrases.already_roll_today.value, h, m)

    def get_level_str(self):
        return '{}: {} лвл {}. \n'.format(self.name, self.level, levels_description[self.level])

    def change_level(self, other_id, other_name, is_lower: bool):
        if other_id is not None and other_name is not None:
            other = Moder(id=other_id, name=other_name, level=None, level_timestamp=0)
            if not self.is_time_is_up() and not self.level is None:
                if not other.is_time_is_up() and not other.level is None:
                    if self.level >= 6:
                        if is_lower:
                            high_level = 3
                            low_level = 1
                            if self.level == 7: high_level = 6
                            if self.level == 8: high_level = 8
                        else:
                            high_level = 2
                            low_level = 0
                            if self.level == 7: high_level = 5
                            if self.level == 8: high_level = 7
                        if low_level <= other.level <= high_level:
                            other.level += -1 if is_lower else +1
                            other.save_to_file()
                            return LevelPhrases.new_level.value.format(other.name, other.level,
                                                                       levels_description[other.level])
                        elif other.level == 0:
                            return 'Уменьшаять уже некуда.'
                        else:
                            return LevelPhrases.you_can_not.value
                    else:
                        return LevelPhrases.you_can_not.value
                else:
                    return LevelPhrases.he_does_not_roll_today.value
            else:
                return LevelPhrases.you_do_not_roll_today.value
        else:
            return DuelPhrases.is_bad.value

    def is_time_is_up(self):
        return True if self.get_time_to_next_roll() < 0 else False

    def get_time_to_next_roll(self):
        return 60 * 60 * self.roll_cool_down - int(time.time()) + int(self.level_timestamp)

    def get_time_to_next_h_m(self):
        seconds = self.get_time_to_next_roll()
        h = seconds / 3600
        m = (seconds / 60) % 60
        return int(h), int(m)


class ModerWithLevels(Moder):
    def change_level(self, other_id, other_name, is_lower: bool, duel):
        if duel.is_on and (duel.current_duelist.id == self.id or duel.waiting_duelist.id == self.id):
            return 'Стреляй, чепушила.'
        else:
            return super().change_level(other_id, other_name, is_lower)


def send_random_img(file_name, moder, level, chat_id, reply_to_message_id):
    if not moder.is_time_is_up():
        if moder.level >= level:
            if moder.pic_limit > 0:
                send_photo(chat_id, choose_ranom_img_from_file(file_name), reply_to_message_id)
                moder.pic_limit -= 1
        else:
            send_message(chat_id, LevelPhrases.you_can_not.value, reply_to_message_id)
    else:
        send_message(chat_id, LevelPhrases.you_do_not_roll_today.value, reply_to_message_id)


def choose_ranom_img_from_file(file_name):
    with open(general_folder + file_name, 'r') as f:
        return random.choice(list(f))


def seconds_to_hms(seconds):
    seconds = int(seconds)
    h = seconds / 3600
    m = (seconds / 60) % 60
    return int(h), int(m)


def send_message(chat_id, text, reply_to_message_id):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id,
              'text': text,
              'reply_to_message_id': reply_to_message_id}
    r = requests.post(url, json=answer)
    return r.json()


def send_photo(chat_id, text, reply_to_message_id):
    url = URL + 'sendPhoto'
    answer = {'chat_id': chat_id,
              'photo': text,
              'reply_to_message_id': reply_to_message_id}
    r = requests.post(url, json=answer)
    return r.json()


def write_json(data, filename='_activity.json'):
    print(data)
    with open(activity_folder + str(data['message']['from']['id']) + filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=MyEncoder)


def get_new_video(url):
    session = requests.Session()
    r = session.get(url)
    if r.status_code == 200:
        soup = bs(r.content)
        return 'https://www.youtube.com/watch?v=' + soup.find('yt:videoid').text
    else:
        return None

duel = DuelWithLevels(Duelist(1000000, 'test', 1, Gun(0)),
                      Duelist(1000000, 'test', 1, Gun(0)))
duel.is_on = False


@app.route('/', methods=['POST', 'GET'])
def index():
    global duel
    if request.method == 'POST':
        r = request.get_json()
        try:
            is_bot = r['message']['from']['is_bot']
            chat_id = r['message']['chat']['id']
            user_id = r['message']['from']['id']
            reply_to_message_id = r['message']['message_id']
            user_name = r['message']['from']['first_name']
            if not is_bot:
                message = r['message']['text']
                moder = ModerWithLevels(id=user_id, name=user_name, level=None, level_timestamp=0)
                moder.set_name(user_name)
                if chat_id in konf_id:
                    if 'duel' in message or '\\дуэль' in message:
                        try:
                            reply_id = r['message']['reply_to_message']['from']['id']
                            reply_name = r['message']['reply_to_message']['from']['first_name']
                            is_bot = r['message']['reply_to_message']['from']['is_bot']
                        except KeyError:
                            reply_id = None
                            reply_name = None
                            is_bot = None
                        send_message(chat_id, duel.make_duel(user_id, user_name, reply_id, reply_name, is_bot),
                                     reply_to_message_id)

                    if 'pass' in message or '\\отменить' in message:
                        send_message(chat_id, duel.get_cancel(user_id), reply_to_message_id)

                    if 'vistrel' in message or '\\выстрел' in message:
                        send_message(chat_id, duel.make_shot(user_id, user_name, message[8:]), reply_to_message_id)

                if (chat_id in konf_id and user_id in pass_ids) or (chat_id == user_id and user_id in pass_ids):
                    write_json(r, '_activity.json')
                    with open(log_msg, 'a') as f:
                        try:
                            f.write(
                                f"from: {r['message']['from']['id']} to: {r['message']['reply_to_message']['from']['id']} [[from {r['message']['from']['first_name']} ({r['message']['from']['username']}) to {r['message']['reply_to_message']['from']['first_name']} ({r['message']['reply_to_message']['from']['username']}) ({r['message']['chat']['title']})]]:\n{' '.join(r['message']['text'].split())}\n")
                        except KeyError:
                            f.write(
                                f"from: {r['message']['from']['id']} to: none [[from {r['message']['from']['first_name']} ({r['message']['from']['username']}) ({r['message']['chat']['title']})]]:\n{' '.join(r['message']['text'].split())}\n")
                    if 'help' in message:
                        send_message(chat_id, '/roll - получить уровень\n'
                                              '/my_lvl - посмотреть уровень\n'
                                              '/list_lvl - список уровней\n'
                                              '/duel - дуэль\n'
                                              '/stata - статистика дуэлей\n'
                                              '/neformalka /kare', reply_to_message_id)
                    if 'roll' in message:
                        send_message(chat_id, moder.roll_level(), reply_to_message_id)

                    if 'plus_lvl' in message or 'minus_lvl' in message:
                        try:
                            reply_id = r['message']['reply_to_message']['from']['id']
                            reply_name = r['message']['reply_to_message']['from']['first_name']
                        except KeyError:
                            reply_id = None
                            reply_name = None
                        send_message(chat_id,
                                     moder.change_level(reply_id, reply_name, True if 'minus_lvl' in message else False,
                                                        duel),
                                     reply_to_message_id)

                    if 'list_lvl' in message or 'lvl_list' in message:
                        levelboard = Levelboard(level_folder)
                        send_message(chat_id, levelboard.get(), reply_to_message_id=reply_to_message_id)

                    if 'my_lvl' in message:
                        send_message(chat_id, moder.get_level_str(), reply_to_message_id)

                    if 'stata' in message or '\\стата' in message:
                        scoreboard = Scoreboard(duel_folder)
                        send_message(chat_id, scoreboard.get(), reply_to_message_id=reply_to_message_id)

                    if 'neformalka' in message or '\\неформалка' in message:
                        send_random_img('neformalki.txt', moder, 3, chat_id, reply_to_message_id)
                    if 'kare' in message or '\\каре' in message:
                        send_random_img('kare.txt', moder, 5, chat_id, reply_to_message_id)

                    if 'vanga' in message or '\\ванга' in message:
                        try:
                            vanga = re.findall(' (.{1,99}) (или) (.{1,99})', message)[0]
                            if vanga[1] != 'или' and vanga[1] != 'or':
                                send_message(chat_id, DuelPhrases.is_bad.value, reply_to_message_id)
                            else:
                                send_message(chat_id, vanga[0] if random.randint(0, 1) == 0 else vanga[2],
                                             reply_to_message_id)
                        except IndexError or KeyError:
                            send_message(chat_id, DuelPhrases.is_bad.value, reply_to_message_id)

                    if 'step' in message:
                        send_message(chat_id, get_new_video(step_url), reply_to_message_id)
                    if 'strel' in message:
                        if not ('vistrel' in message):
                            send_message(chat_id, get_new_video(strel_url), reply_to_message_id)
        except KeyError as e:
            print(e)
        return jsonify(r)
    elif request.method == 'GET':
        return '<h1>>.</h1>'

def main():
    pass

if __name__ == '__main__':
    app.run()
