import requests
from bs4 import BeautifulSoup

image_url = 'https://www.bing.com/images/search?q='

def do_image_request_with_keywords(request_keywords):
    links = []
    print("request keywords", request_keywords)
    req = requests.get(image_url+request_keywords+"&FORM=HDRSC2")
    print(req.url)

    soup = BeautifulSoup(req.text, "lxml")
    headers = soup.find_all('a', class_="thumb")
    for image in headers:
        for line in str(image).split():
            if 'href' in line:
                links.append(line[6:len(line)-1])
    return links

def simplify_weather(complex_weather):
    complex_weather = set(complex_weather.split('-'))
    simple_weathers = ['clear', 'snow', 'rain', 'cloudy']
    for condition in simple_weathers:
        if condition in complex_weather:
            return condition
    if 'overcast' in complex_weather:
        return 'cloudy'
      
    image_url = 'https://www.bing.com/images/search?q='

def get_image_links(city_data):
    """
    find images for city and weather
    keywords = {'weather': 'weather-f}
    """
#     print("I'm in images")
    weather = city_data['condition_english']
#     print(weather)
    weather = simplify_weather(weather)
    print("simplified weather", weather)
        
    request_keywords = weather + "+" + city_data['slug']
    print("request keywords:", request_keywords)
    
    image_links = do_image_request_with_keywords(request_keywords)

    if len(image_links) == 0:
        print("Shit! Such a rare request!")
        image_links = do_image_request_with_keywords(city_data['slug'])
    if len(image_links) == 0:
        image_links.append('http://cs617424.vk.me/v617424318/68a0/GT6qv13kjz4.jpg')
        
    return image_links
