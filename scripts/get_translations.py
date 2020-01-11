import requests

if __name__ == '__main__':
    with open('../data/weather_header.txt', 'r') as header_file:
        prefix, api_key = header_file.read().split()
        header = {prefix: api_key}
    url = 'https://api.weather.yandex.ru/v1/translations'
    req = requests.get(url, headers=header)
    with open('../data/translations.txt', 'w') as output:
        output.write(req.text)
