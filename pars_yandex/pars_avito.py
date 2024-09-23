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
"http://45.138.87.238:1080",
"http://111.59.4.88:9002",
"http://212.127.93.44:8081",
"http://185.49.31.207:8081",
"http://129.159.67.33:80",
"http://193.26.157.224:80",
"http://103.18.77.50:1111",
"http://34.124.190.108:8080",
"http://202.179.184.66:8080",
"http://31.11.143.83:80",
"http://52.117.160.219:8081",
"http://103.35.153.74:8080",
"http://37.187.73.7:43381",
"http://82.165.198.169:41569",
"http://188.165.223.183:55572",
"http://58.246.58.150:9002",
"http://5.75.200.249:80",
"http://45.231.11.220:8080",
"http://45.90.89.20:80",
"http://52.172.55.7:80",
"http://213.230.124.108:8088",
"http://119.235.114.242:3128",
"http://58.22.61.222:57981",
"http://45.56.96.113:3128",
"http://103.155.191.60:7777",
"http://8.209.255.13:3128",
"http://82.165.198.169:48285",
"http://49.13.9.253:80",
"http://116.203.50.3:3128",
"http://8.213.156.191:9080",
"http://185.43.220.45:4008",
"http://167.71.250.32:51378",
"http://66.228.33.190:49117",
"http://116.111.124.175:46919",
"http://5.189.158.162:3128",
"http://91.121.88.53:80",
"http://185.138.123.25:1080",
"http://181.129.183.19:53281",
"http://61.129.2.212:8080",
"http://182.16.8.42:80",
"http://23.134.91.168:3128",
"http://154.94.5.241:7001",
"http://34.140.150.176:3128",
"http://47.122.45.221:3128",
"http://54.38.70.138:80",
"http://203.153.121.131:8080",
"http://91.65.103.3:80",
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
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 5000)\
        .perform()
    
    scroll_origin = ScrollOrigin.from_viewport(10, 10)

    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 700)\
        .perform()


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
     # Ожидание загрузки элемента с адресом
    address_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '//div[@itemprop="address"]//span'))
    )

    # Получаем полный текст адреса
    full_address = address_element.text

    # Выводим полный адрес
    print(f'Полный адрес: {full_address}')
    return full_address

def get_all_photo():
    global driver
    urls=[]
    # Ожидание загрузки родительского элемента
    parent_element = driver.find_element(By.XPATH, '//div[contains(@class, "image-frame-wrapper")]')  # Замените на XPath родительского элемента
    

    # Создаем объект ActionChains
    actions = ActionChains(driver)

    # Наводим курсор на родительский элемент
    actions.move_to_element(parent_element).perform()

    # Ожидание появления целевого элемента
    time.sleep(1)
    target_element = WebDriverWait(driver, 1).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@data-marker="image-frame/right-button"]//button'))  # Замените на XPath целевого элемента
    )

    # Нажимаем на целевой элемент
    target_element.click()

    # Ожидание загрузки списка изображений
    image_list = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '//ul[@data-marker="image-preview/preview-wrapper"]'))
    )

    # Получаем все элементы <li> внутри <ul>
    images = image_list.find_elements(By.XPATH, './/li[@data-marker="image-preview/item"]')

    # Получаем количество изображений
    image_count = len(images)
    print(f'Количество изображений: {image_count}')
    for _ in range(image_count - 1):
        image_frame = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "image-frame-wrapper")]'))
        )

        img_src = image_frame.find_element(By.TAG_NAME, 'img').get_attribute('src')

        # Вывод данных
        # print(f'SRC изображения: {img_src}')
        urls.append(img_src)
        target_element.click()
    
    pprint(urls)
    return urls
    # driver.quit()

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
    

def get_info_avito(url:str):
    global driver
    

    proxy=get_valid_proxy()
    print(proxy)


    options = Options()
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                'Chrome/123.0.0.0 Safari/537.36'
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_argument(f'user-agent={user_agent}')
    
    if proxy is not None:
        options.add_argument(f'--proxy-server={proxy}')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # driver = webdriver.Chrome()
    # driver.get("https://yandex.ru/navi/org/chaykhana_mayiz/232322945673")
    driver.get(url)

    # # navigate to the target webpage
    # driver.get("https://httpbin.io/ip")

    # # print the body content of the target webpage
    # print(driver.find_element(By.TAG_NAME, "body").text)

    # # release the resources and close the browser
    # driver.quit()




    get_main_photo()
    # adress=get_adress()
    # photo=get_all_photo()
    
    try:
        adress=get_adress()
    except:
        adress=None
    try:
        photo=get_all_photo()
    except:
        photo=None

    driver.close()

    return adress, photo

if __name__ == '__main__':
    get_info_avito("https://www.avito.ru/mihnevo/doma_dachi_kottedzhi/dom_1067_m_na_uchastke_10_sot._3039447988?utm_campaign=native&utm_medium=item_page_ios&utm_source=soc_sharing&guests=2")
# get_main_photo()
# get_adress()
# get_all_photo()