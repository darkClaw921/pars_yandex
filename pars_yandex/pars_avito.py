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

# Настройка драйвера
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
# driver = webdriver.Chrome()
# Открываем нужный URL (замените на фактический URL)
# driver.get("https://www.avito.ru/mihnevo/doma_dachi_kottedzhi/dom_1067_m_na_uchastke_10_sot._3039447988?utm_campaign=native&utm_medium=item_page_ios&utm_source=soc_sharing&guests=2")  # Замените на URL, где находится ваш элемент
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
    image_frame = WebDriverWait(driver, 1).until(
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
    actions.move_to_element(image_frame).perform()

    # Ожидание появления целевого элемента
    time.sleep(1)
    scroll_down(image_frame)


    

def get_adress():
    global driver
     # Ожидание загрузки элемента с адресом
    address_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@itemprop="address"]//span'))
    )

    # Получаем полный текст адреса
    full_address = address_element.text

    # Выводим полный адрес
    print(f'Полный адрес: {full_address}')

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
        image_frame = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "image-frame-wrapper")]'))
        )

        img_src = image_frame.find_element(By.TAG_NAME, 'img').get_attribute('src')

        # Вывод данных
        # print(f'SRC изображения: {img_src}')
        urls.append(img_src)
        target_element.click()
    
    pprint(urls)
    
    driver.quit()

def get_info_avito(url:str):
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

    get_main_photo()
    adress=get_adress()
    photo=get_all_photo()
    # try:
    #     adress=get_adress()
    # except:
    #     adress=None
    # try:
    #     photo=get_all_photo()
    # except:
    #     photo=None

    return adress, photo

if __name__ == '__main__':
    get_info_avito("https://www.avito.ru/mihnevo/doma_dachi_kottedzhi/dom_1067_m_na_uchastke_10_sot._3039447988?utm_campaign=native&utm_medium=item_page_ios&utm_source=soc_sharing&guests=2")
# get_main_photo()
# get_adress()
# get_all_photo()