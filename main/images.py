import random
import requests
from bs4 import BeautifulSoup
from transliterate import translit

def send_image(handler, location, condition):
    sender = ImageSender(handler, location, condition)
    sender.build_query()
    sender.send_image()


class ImageSender(object):
    def __init__(self, handler, location, condition):
        self.handler = handler
        self.url_template = 'http://www.bing.com/images/search?q='
        self.url_ending = '&FORM=HDRSC2'
        self.image_urls = []
        self.query = None
        self.location = location
        self.possible_conditions = ['rain', 'snow', 'cloudy', 'synop', 'overcast', 'clear']
        self.condition = self.get_condition(condition)
        self.subscription_key = 'b53cb2d7c63f4ed1a7e47b5648489539'
        self.image_not_found = [
            'http://cft2.igromania.ru/upload/iblock/1008/4c4859/panoramic.jpg',
            'http://igra-prestolov.com/uploads/images/2015/626/rjda77.jpg',
            'https://memepedia.ru/wp-content/uploads/2017/08/3640869.jpg',
            'https://memepedia.ru/wp-content/uploads/2017/08/3640869.jpg'
        ]
        print(self.condition)

    def get_condition(self, condition):
        print(condition)
        conditions = condition.split('-')
        for cond in conditions:
            if cond in self.possible_conditions:
                if cond == 'clear':
                    cond = 'clear weather'
                if cond == 'overcast':
                    cond = 'cloudy'
                return cond
        return None

    def build_query(self):
        if self.condition is None:
            return
        location = translit(self.handler.location, 'ru', reversed=True)
        # info = '+'.join([self.location, self.condition])
        info = '+'.join([location, self.condition])
        print('info = {}'.format(info))
        url = ''.join([self.url_template, info, self.url_ending])
        req = requests.get(url, headers={'Ocp-Apim-Subscription-Key': self.subscription_key})
        soup = BeautifulSoup(req.text, 'lxml')

        image_headers = soup.find_all('a', class_="thumb")
        for image in image_headers:
            for item in str(image).split():
                if 'href' in item:
                    new_url = item.replace('href=', '')[1:-1]
                    self.image_urls.append(new_url)
        self.image_urls[:] = self.image_urls[:4]

    def send_image(self):
        if len(self.image_urls) == 0:
            url = self.image_not_found[random.randint(0, len(self.image_not_found) - 1)]
            self.handler.update.message.reply_text('Подходящего фото не нашлось...')
        else:
            url_num = random.randint(0, len(self.image_urls) - 1)
            url = self.image_urls[url_num]
        self.handler.tbot.send_photo(chat_id=self.handler.update.message.chat_id,
                                     photo=url)
        print(url)
