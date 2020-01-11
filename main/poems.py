import os
import random
import requests

weathers = ['rain', 'snow', 'clear', 'cloudy']
poems = {weather: [] for weather in weathers}

def load_poems():
    for filename in os.listdir('../poems/'):
        with open('../poems/{}'.format(filename), 'r') as file:
            text = file.read()
        weather = None
        for item in weathers:
            if filename.startswith(item):
                weather = item
        poems[weather].append(text)

    print(poems['rain'][0])

def get_condition(condition):
    possible_conditions = ['rain', 'snow', 'cloudy', 'synop', 'overcast', 'clear']
    conditions = condition.split('-')
    for cond in conditions:
        if cond in possible_conditions:
            if cond == 'overcast':
                cond = 'cloudy'
            return cond
    return None

def send_poem(handler, condition):
    condition = get_condition(condition)
    poem_num = random.randint(0, len(poems[condition]) - 1)
    handler.update.message.reply_text(poems[condition][poem_num])
