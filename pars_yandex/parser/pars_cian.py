from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.chrome.options import Options
import random
import requests
from fake_useragent import UserAgent
# Настройка драйвера
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
# driver = webdriver.Chrome()
# Открываем нужный URL (замените на фактический URL)
# driver.get("https://www.avito.ru/mihnevo/doma_dachi_kottedzhi/dom_1067_m_na_uchastke_10_sot._3039447988?utm_campaign=native&utm_medium=item_page_ios&utm_source=soc_sharing&guests=2")  # Замените на URL, где находится ваш элемент
# options = Options()
# user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ' \
#             'Chrome/123.0.0.0 Safari/537.36'
# options = webdriver.ChromeOptions()
# options.add_argument("--start-maximized")
# options.add_argument('--headless')
# options.add_argument(f'user-agent={user_agent}')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # driver = webdriver.Chrome()
# Список прокси
proxies = [
    # "http://proxy1:port",
    # "http://proxy2:port",
    # "http://proxy3:port",
    # Добавьте свои прокси
"http://45.138.87.238:1080"
]

def scroll_down(element):
    # Прокручиваем страницу вниз
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    
    # iframe = driver.find_element(By.TAG_NAME, "iframe")
    scroll_origin = ScrollOrigin.from_element(element)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 700)\
        .perform()

    scroll_origin = ScrollOrigin.from_element(element, 0, -50)
    try:
        ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 5000)\
        .perform()
    except Exception as e: 
        print("error: ", e)

    scroll_origin = ScrollOrigin.from_viewport(10, 10)
    try:    
        ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 700)\
        .perform()
    except Exception as e:
        print("error2: ", e)


    time.sleep(1)  # Ждем, чтобы страница успела загрузить новые элементы

def get_main_photo():
    # try:
    global driver
    # Ожидание загрузки элемента
    image_frame = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "image-frame-wrapper")]'))
    )

    # Извлечение данных
    title = image_frame.get_attribute('data-title')
    image_url = image_frame.get_attribute('data-url')
    img_src = image_frame.find_element(By.TAG_NAME, 'img').get_attribute('src')

    # Вывод данных
    print(f'Название: {title}')
    print(f'URL изображения: {image_url}')
    print(f'SRC изображения: {img_src}')

    actions = ActionChains(driver)

    # Наводим курсор на родительский элемент
    time.sleep(2)
    a=actions.move_to_element(image_frame)
    time.sleep(3) 
    a.perform()


    # Ожидание появления целевого элемента
    # time.sleep(1)
    scroll_down(image_frame)
   

def get_adress():
    global driver
        # Ожидание загрузки контейнера с адресом
    address_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@data-name="AddressContainer"]'))
    )

    # Получаем все элементы <a> внутри контейнера
    address_items = address_container.find_elements(By.XPATH, './/a[@data-name="AddressItem"]')

    # Собираем адрес
    address_parts = []
    for item in address_items:
        address_parts.append(item.text if item.text else " ")

    # Формируем полный адрес
    full_address = ', '.join(address_parts)

    # Выводим полный адрес
    print(f'Полный адрес: {full_address}')

def get_all_photo():
    global driver
    urls=[]
    # Ожидание загрузки контейнера с изображениями
    gallery_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@data-name="OfferGallery"]'))
    )

    # Получаем все элементы <img> внутри контейнера
    images = gallery_container.find_elements(By.TAG_NAME, 'img')

    # Извлекаем URL изображений
    image_urls = [img.get_attribute('src') for img in images]

    # Выводим все URL изображений
    for url in image_urls:
        print(url)

def get_valid_proxy():
    # prox=random.choice(proxies)
     # Получаем список прокси-серверов
    # proxies_list = get_proxies_list()
    proxies_list = proxies
    for proxy in proxies_list:
        try:
            # Проверяем прокси, отправляя запрос через него
            response = requests.get('https://httpbin.io/ip', proxies={"http": proxy, "https": proxy}, timeout=1)
            if response.status_code == 200:
                # Если прокси работает, возвращаем его
                return proxy
        except requests.RequestException:
            # Если прокси не работает, пробуем следующий
            continue
    return None

# from selenium_stealth import stealth  
def random_mouse_movement(driver, element, num_moves=30):
    """
    Функция для случайного перемещения курсора по элементу.
    
    :param driver: Экземпляр веб-драйвера Selenium.
    :param element: Элемент, по которому будет перемещаться курсор.
    :param num_moves: Количество перемещений курсора.
    """
    actions = ActionChains(driver)
    
    # Получаем размеры элемента
    element_location = element.location
    element_size = element.size
    
    for _ in range(num_moves):
        # Генерируем случайные координаты внутри элемента
        x_offset = random.randint(0, element_size['width'])
        y_offset = random.randint(0, element_size['height'])
        
        # Перемещаем курсор к сгенерированным координатам
        actions.move_to_element_with_offset(element, x_offset, y_offset).perform()
        
        # Случайная задержка между перемещениями (от 0.5 до 2 секунд)
        time.sleep(random.uniform(0.5, 2.0))

def get_info_cian(url:str):
    global driver
    

    # proxy=get_valid_proxy()
    # print(proxy)
    proxy=None

    ua = UserAgent()
    user_agent = ua.random
    options = Options()
    # user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ' \
    #             'Chrome/123.0.0.0 Safari/537.36'
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument("--disable-infobars")  # Отключить инфобары
    options.add_argument("--disable-extensions")  # Отключить расширения
    if proxy is not None:
        options.add_argument(f'--proxy-server={proxy}')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver = webdriver.Chrome()
    # driver.get("https://yandex.ru/navi/org/chaykhana_mayiz/232322945673")
    # stealth(driver,
    #     languages=["en-US", "en"],
    #     vendor="Google Inc.",
    #     platform="Win32",
    #     webgl_vendor="Intel Inc.",
    #     fix_hairline=True,
    #     run_on_insecure=True,
    # )
    
    driver.get(url)
    
    # Ожидание загрузки элемента с логотипом
    # logo_element = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.XPATH, '//header[@class="logo"]//img'))
    # )

    # Получаем URL логотипа
    # logo_url = logo_element.get_attribute('src')

    # Выводим URL логотипа
    # print(f'URL логотипа: {logo_url}')
    time.sleep(20)
    # Вызов функции для случайного перемещения курсора
    # random_mouse_movement(driver, logo_element)

    a=driver.page_source
    
    with open('cian.html', 'w') as f:
        f.write(a)

    # # navigate to the target webpage
    # driver.get("https://httpbin.io/ip")

    # # print the body content of the target webpage
    # print(driver.find_element(By.TAG_NAME, "body").text)

    # # release the resources and close the browser
    # driver.quit()




    # get_main_photo()
    # adress=get_adress()
    # photo=get_all_photo()
    adress=get_adress()
    # print(adress)
    try:
        adress=get_adress()
        print(adress)
    except:
        adress=None
    try:
        photo=get_all_photo()
    except:
        photo=None

    driver.close()

    return adress, photo

if __name__ == '__main__':
    # import cloudscraper
    # url="https://www.cian.ru/sale/suburban/303820116/"
    # scraper = cloudscraper.create_scraper(browser={
    #     'browser': 'chrome',
    #     'platform': 'android',
    #     'desktop': False
    # },interpreter='nodejs')  # returns a CloudScraper instance
    # # Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
    # html=scraper.get(url).text  # => "<!DOCTYPE html><html><head>..."
    

    get_info_cian("https://www.cian.ru/sale/suburban/303820116/")
# get_main_photo()
# get_adress()
# get_all_photo()