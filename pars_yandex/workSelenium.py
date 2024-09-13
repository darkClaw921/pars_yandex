from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin

options = Options()
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ' \
            'Chrome/123.0.0.0 Safari/537.36'
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument('--headless')
options.add_argument(f'user-agent={user_agent}')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scroll_down(element):
    # Прокручиваем страницу вниз
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    
    # iframe = driver.find_element(By.TAG_NAME, "iframe")
    scroll_origin = ScrollOrigin.from_element(element)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 400)\
        .perform()

    scroll_origin = ScrollOrigin.from_element(element, 0, -50)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 5000)\
        .perform()
    
    scroll_origin = ScrollOrigin.from_viewport(10, 10)

    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 200)\
        .perform()


    time.sleep(5)  # Ждем, чтобы страница успела загрузить новые элементы

def get_phone():
    try:
        phone_div = driver.find_element(By.CLASS_NAME, 'orgpage-phones-view__phone-number').text
    except: 
        phone_div = driver.find_element(By.CLASS_NAME, 'card-phones-view__phone-number').text

    print(phone_div)
    # photo_div = driver.find_elements(By.CLASS_NAME, 'tabs-select-view__title _name_gallery') #кнопка фото
    # photo_div = driver.find_elements(By.XPATH, '/html/body/div[1]/div[2]/div[8]/div[1]/div[1]/div[1]/div/div[1]/div/div[3]/div/div[17]/div/div/div[2]/div[2]/div/div/div/div[1]/div[3]/div') #кнопка фото
    photo_button = driver.find_element(By.XPATH, '//div[@aria-selected="false" and @class="tabs-select-view__title _name_gallery"]')
    photo_button.click()    
    return phone_div

#time.sleep(10)
def get_photo_inside():
    time.sleep(5)
#    with open('index.html', 'w') as file:
#        file.write(driver.page_source) 
    
    button=driver.find_element(By.XPATH, '//button[span[text()="Exterior"]]')
    # button=driver.find_element(By.XPATH, '//button[span[text()="Снаружи"]]')
    button.click()
    
    button=driver.find_element(By.XPATH, '//button[span[text()="Interior"]]')
    # button=driver.find_element(By.XPATH, '//button[span[text()="Внутри"]]')

    #button=driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[8]/div[1]/div[1]/div[1]/div/div[1]/div/div[3]/div/div[3]/div/div/div[5]/div/div/div[2]/div[2]/div/div/div/div/div[2]/button')
    # Кликаем по кнопке
    button.click()
    time.sleep(3)
    # photos=driver.find_elements(By.CLASS_NAME, 'media-gallery _mode_preview _columns_3')
    # pprint(photos)
    # Прокручиваем страницу вниз несколько раз
    # for _ in range(10):  # Прокручиваем 3 раза
    scroll_down(button)

    images = driver.find_elements(By.CSS_SELECTOR, 'div.media-wrapper._loaded img.media-wrapper__media')
    image_urls = [img.get_attribute('src') for img in images[:20]]  # Получаем только первые 10 изображений
    pprint(image_urls)
    return image_urls

def get_photo_outside():

    button=driver.find_element(By.XPATH, '//button[span[text()="Exterior"]]')
    # button=driver.find_element(By.XPATH, '//button[span[text()="Снаружи"]]')
    
    # Кликаем по кнопке
    button.click()

    time.sleep(5)
    # photos=driver.find_elements(By.CLASS_NAME, 'media-gallery _mode_preview _columns_3')
    # pprint(photos)
    # Прокручиваем страницу вниз несколько раз
    # for _ in range(5):  # Прокручиваем 3 раза
    #     scroll_down()
    images = driver.find_elements(By.CSS_SELECTOR, 'div.media-wrapper._loaded img.media-wrapper__media')
    image_urls = [img.get_attribute('src') for img in images[:20]]  # Получаем только первые 10 изображений
    pprint(image_urls)
    return image_urls

def get_info(url:str):
    global driver
    options = Options()
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                'Chrome/123.0.0.0 Safari/537.36'
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--headless')
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # driver = webdriver.Chrome()
    # driver.get("https://yandex.ru/navi/org/chaykhana_mayiz/232322945673")
    driver.get(url)
    title=driver.title
    print(title)
    time.sleep(5)   
    try:
        phone=get_phone() 
    except:
        phone=None
    # phone=get_phone()

    try:
        imgInside=get_photo_inside()
    except:
        imgInside=None
    
    try:
        imgOutside=get_photo_outside()
    except:
        imgOutside=None

    driver.close()
    return phone, imgInside, imgOutside