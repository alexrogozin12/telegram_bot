import datetime
import json
import logging
import pymorphy2
import re
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from images import send_image
from poems import load_poems, send_poem

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
class SupaWeatherBot(object):
    def __init__(self):
        load_poems()
        with open('../data/bot_token.txt', 'r') as token_file:
            self.bot_token = token_file.readline()
        with open('../data/weather_header.txt', 'r') as header_file:
            prefix, api_key = header_file.read().split()
            self.header = {prefix: api_key}
        with open('../data/locations.txt', 'r') as locations_file:
            self.locations = json.loads(locations_file.readline())
            self.city_name_to_id = \
                {item['name'].lower(): item['geoid'] for item in self.locations}
            self.city_russian_to_english = \
                {item['name'].lower(): item['slug'] for item in self.locations}
        with open('../data/translations.txt', 'r') as translations_file:
            self.translations = json.loads(translations_file.readline())
        self.days_of_week = {
            'понедельник' : 0,
            'вторник': 1,
            'среда': 2,
            'четверг': 3,
            'пятница': 4,
            'суббота': 5,
            'воскресенье': 6,
            'воскресение': 6,
            'пн': 0,
            'вт': 1,
            'ср': 2,
            'чт': 3,
            'пт': 4,
            'сб': 5,
            'вс': 6
        }
        self.days_relative = {
            'сегодня': 0,
            'завтра': 1,
            'послезавтра': 2
        }
        self.wind_directions = {
            'c': 'штиль',
            'e': 'В',
            'n': 'С',
            'ne': 'СВ',
            'nw': 'СЗ',
            's': 'Ю',
            'se': 'ЮВ',
            'sw': 'ЮЗ',
            'w': 'З'
        }
        self.locations_short = {
            'мск': 'москва',
            'спб': 'санкт-петербург',
            'мгн': 'магнитогорск',
            'владик': 'владивосток',
            'челяб': 'челябинск',
            'крг': 'караганда'
        }
        self.morph = pymorphy2.MorphAnalyzer()

    def load_locations(self):
        url = 'https://api.weather.yandex.ru/v1/locations?lang=ru_RU'
        req = requests.get(url, headers=self.header)
        locations_data = json.loads(req.text)
        locations = {item['name']: item['geoid'] for item in locations_data}
        return locations

    def start(self, bot, update):
        """Send a message when the command /start is issued."""
        update.message.reply_text('Hi!')

    def help(self, bot, update):
        """Send a message when the command /help is issued."""
        update.message.reply_text('Help!')

    def error(self, bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)

    def weather(self, bot, update):
        handler = QueryHandler(self, update, bot)
        handler.reply()

    def run(self):
        """Start the bot."""
        # Create the EventHandler and pass it your bot's token.
        updater = Updater(self.bot_token)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))

        # on noncommand i.e message - echo the message on Telegram
        dp.add_handler(MessageHandler(Filters.text, self.weather))

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()


class QueryHandler(object):
    def __init__(self, bot, update, tbot):
        self.location = None
        self.day_of_week = None
        self.day_relative = None
        self.tbot = tbot
        self.bot = bot
        self.update = update

    def parse_query(self):
        words = re.findall(r'[\w]+', self.update.message.text.lower())
        for word in words:
            if word in bot.days_of_week:
                self.day_of_week = word
                continue

            if 'PREP' in bot.morph.parse(word)[0].tag:
                continue

            word = bot.morph.parse(word)[0].normal_form
            # print(word, word in bot.days_of_week)

            if word in bot.days_of_week:
                self.day_of_week = word
                continue

            if word in bot.days_relative:
                self.day_relative = word
                continue

            if word in bot.locations_short:
                self.location = bot.locations_short[word]
                continue

            if word in bot.city_name_to_id.keys():
                self.location = word
                continue

    def date_to_string(self, date):
        year = date.year
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)
        return '{}-{}-{}'.format(year, month, day)

    def string_to_date(self, string):
        year, month, day = (int(item) for item in string.split('-'))
        return datetime.date(year=year, month=month, day=day)

    def day_of_week_to_date(self, day_of_week):
        if day_of_week is None:
            # print('day of week unknown')
            return None
        now = datetime.date.today()
        now_weekday = now.weekday()
        needed_weekday = self.bot.days_of_week[day_of_week]

        delta_day = (needed_weekday - now_weekday) % 7
        # print('delta = {}'.format(delta_day))
        date = now + datetime.timedelta(days=delta_day)
        # print('day: {}'.format(self.date_to_string(date)))
        return date

    def reply(self):
        self.parse_query()

        if self.location is None:
            response = 'Не понимаю :( Что за город?'
            self.update.message.reply_text(response)
            return

        geoid = self.bot.city_name_to_id[self.location]
        geoid_query = 'geoid={}'.format(geoid)

        self.date = self.day_of_week_to_date(self.day_of_week)
        if self.date is None and self.day_relative is not None:
            self.date = datetime.date.today() + \
                        datetime.timedelta(days=self.bot
                                           .days_relative[self.day_relative])
        if self.date is None:
            self.date = datetime.date.today()
        # print(self.date)

        url = 'https://api.weather.yandex.ru/v1/forecast?geoid={}&extra=true'.format(geoid)
        req = json.loads(requests.get(url, headers=self.bot.header).text)

        if self.date <= datetime.date.today():
            weather_obj = req['fact']
        else:
            weather_obj = [wo for wo in req['forecasts'] if wo['date'] == self.date_to_string(self.date)][0]
            weather_obj = weather_obj['parts']['day']

        try:
            temp = weather_obj['temp']
        except KeyError:
            temp = weather_obj['temp_avg']
        humidity = weather_obj['humidity']
        feels_like = weather_obj['feels_like']
        pressure = weather_obj['pressure_mm']
        wind = weather_obj['wind_dir']
        wind = bot.wind_directions[wind]
        wind_speed = weather_obj['wind_speed']
        condition = weather_obj['condition']
        condition = self.bot.translations[condition].capitalize()
        response = 'Город: {}\n' \
                   'Дата: {}\n' \
                   'Температура: {}°C (ощущается как {}°C)\n' \
                   'Давление: {} мм рт.ст.\n' \
                   'Влажность: {}%\n' \
                   'Ветер: {}, {} м/с\n' \
                   '{}\n' \
                   .format(self.location.title(),
                           self.date_to_string(self.date),
                           temp,
                           feels_like,
                           pressure,
                           humidity,
                           wind,
                           wind_speed,
                           condition)

        self.update.message.reply_text(response)

        send_image(self, bot.city_russian_to_english[self.location], weather_obj['condition'])
        send_poem(self, weather_obj['condition'])


if __name__ == '__main__':
    bot = SupaWeatherBot()
    bot.run()
