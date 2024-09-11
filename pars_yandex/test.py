import requests
from pprint import pprint
from bs4 import BeautifulSoup

url='https://yandex.ru/navi/org/chaykhana_mayiz/232322945673'
# url=''



# def get_html(url):
#     response = requests.get(url)
#     #save_html
#     with open('index.html', 'w') as file:
#         file.write(response.text)
#     return response.text
# html = get_html(url)
# print(html)

html= open('index.html').read()
# html = requests.get(url).text
soup = BeautifulSoup(html, 'html.parser')
# Находим элемент div с нужным классом
phone_div = soup.find('div', class_='orgpage-phones-view__phone-number').get_text(strip=True)
pprint(phone_div)

photo_div = soup.find_all('div', class_='tabs-select-view__title _name_gallery') #кнопка фото
pprint(photo_div)