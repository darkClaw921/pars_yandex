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
    button=driver.find_element(By.XPATH, '//button[span[text()="Interior"]]')
    #button=driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[8]/div[1]/div[1]/div[1]/div/div[1]/div/div[3]/div/div[3]/div/div/div[5]/div/div/div[2]/div[2]/div/div/div/div/div[2]/button')
    # Кликаем по кнопке
    button.click()
    time.sleep(5)
    # photos=driver.find_elements(By.CLASS_NAME, 'media-gallery _mode_preview _columns_3')
    # pprint(photos)
    images = driver.find_elements(By.CSS_SELECTOR, 'div.media-wrapper._loaded img.media-wrapper__media')
    image_urls = [img.get_attribute('src') for img in images[:20]]  # Получаем только первые 10 изображений
    pprint(image_urls)
    return image_urls

def get_photo_outside():
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[span[text()="Exterior"]]'))
    )
    # Кликаем по кнопке
    button.click()

    time.sleep(5)
    # photos=driver.find_elements(By.CLASS_NAME, 'media-gallery _mode_preview _columns_3')
    # pprint(photos)
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
    # driver.get("https://yandex.ru/navi/org/chaykhana_mayiz/232322945673")
    driver.get(url)
    title=driver.title
    print(title)
    time.sleep(5)    
    phone=get_phone()
    imgInside=get_photo_inside()
    imgOutside=get_photo_outside()

    driver.close()
    return phone, imgInside, imgOutside