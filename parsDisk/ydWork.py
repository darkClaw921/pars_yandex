from pprint import pprint
from yadisk import YaDisk
from dotenv import load_dotenv
from tqdm import tqdm
# import postgreWork
import os
load_dotenv()
APLICATION_ID = os.getenv('APLICATION_ID')
APLICATION_SECRET = os.getenv('APLICATION_SECRET')
TOKEN_YD = os.getenv('TOKEN_YD')

from loguru import logger
logger.add("logs/ydWork_{time}.log",format="{time} - {level} - {message}", rotation="100 MB", retention="10 days", level="DEBUG")

class YandexDiskManager:
    def __init__(self, APLICATION_ID, APLICATION_SECRET, TOKEN_YD, isTest=True):
        self.yadisk = YaDisk(APLICATION_ID, APLICATION_SECRET, TOKEN_YD)
        
        if isTest:
            self.pathMain='/Производственный отдел/ТЕСТИРОВАНИЕ/'
        else:
            self.pathMain='/Производственный отдел/ПРОЕКТЫ - собираем подборки под проекты, извлекаем отсюда новые/'
        # url = self.yadisk.get_code_url()
        # print(url)
        # code=input('Введите код: ')
        # self.yadisk.get_token(code)
        print(self.yadisk.check_token())
  


    def upload_file_from_url(self, urlFolder, urlFile, nameFile) ->None:
        # meta=self.yadisk.get_public_meta(urlFolder)
        # meta.upload_url(urlFile, self.pathMain+meta.name+"/"+nameFile) 
        self.yadisk.upload_url(urlFile, urlFolder+"/"+nameFile) 

    def upload_file_from_local(self, path, folder_path,nameFile) ->None:
        self.yadisk.upload(path, folder_path+"/"+nameFile)

    def create_folder(self, folder_name)->str:
        urlFold=self.yadisk.mkdir(folder_name)
        publick=urlFold.publish()
        publick=urlFold.get_meta()
        

        publickURL=publick.public_url
        logger.info(f'Создана папка {folder_name}')
        return folder_name, publickURL

    def create_folder_and_upload_file(self,publickURL, folderName, fileName, fileURL, projectID=0):
        
        print(f'{publickURL=}, {folderName=}, {fileName=}, {fileURL=}')
        folderProject=self.yadisk.get_public_meta(publickURL).name
        allPath=self.pathMain+folderProject+'/'+folderName
        
        
        try:
            folder_path, publickURL = self.create_folder(allPath)    
            postgreWork.update_project(projectID=projectID, folderURL=publickURL)

            
        except:
            logger.debug(f'Папка {folderName} уже существует')
            folder_path = allPath

        if fileURL.startswith('http'):
            self.upload_file_from_url(folder_path, fileURL, fileName)
        else:
            self.upload_file_from_local(fileURL, folder_path,nameFile=fileName)
        # self.upload_file_from_url(folder_path, fileURL, fileName)
        logger.info(f'Файл {fileName} загружен в папку {folder_path}')
    #получаем список всех папок в директории 
    def get_all_folders(self, publickURL)->list:
        
        folderProject=self.yadisk.get_public_meta(publickURL).name
        allPath=self.pathMain+folderProject+'/'
        print(f'{allPath=}')
        path=allPath
        files=self.yadisk.get_meta(path).embedded.items
        folders=[]
        for file1 in files:
            if file1.file is None:
                pathFile=file1.path.replace('disk:'+path,'')
                folders.append(pathFile)
        pprint(folders)
        return folders 
    
    # получаем все файлы в папке
    def get_all_files(self, folderName)->list:
        # folderProject=self.yadisk.get_public_meta(folderName).name
        allPath=self.pathMain+folderName+''
        # print(f'{allPath=}')
        path=allPath
        files=self.yadisk.get_meta(path).embedded.items
        filesName=[]
        filesHash=[]
        for file1 in files:
            if file1.file is not None:
                hashFile=file1.md5
                pathFile=file1.path.replace('disk:'+path,'')
                filesName.append(pathFile)
                filesHash.append(hashFile)

        # pprint(filesName)
        # pprint(filesHash)
        return filesHash 

    #переносим файл из одной папки в другую 
    def move_file(mainFilePath, secondPath):


        pass

FOLDERS={}
def get_all_hash_files(publickURL):
    print('Получаем фото с диска')
    global FOLDERS
    yadisk1 = YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD, isTest=True)
    foldersNames=yadisk1.get_all_folders(publickURL=publickURL)
    folderProject=yadisk1.yadisk.get_public_meta(publickURL).name
    allPath=yadisk1.pathMain+folderProject+'/'
    print(f'{allPath=}')
    # path=allPath
    for folderName in tqdm(foldersNames):
        # print(f'Начинаем проверять папку "{folderName}"')
        allPathToFolder=allPath+f'ТЕСТИРУЕМ БОТА - 1/{folderName}'
        filesHash=yadisk1.get_all_files(f'ТЕСТИРУЕМ БОТА - 1/{folderName}')
       
        FOLDERS[allPathToFolder]={'photos':filesHash}
    # else:
    #     print(f'В этой дериктории {allPath} нет папок')
    #     filesHash=yadisk1.get_all_files(allPath) 
    #     FOLDERS[allPath]=filesHash

    pprint(FOLDERS)
    return FOLDERS



#Проверка на похожие файлы 
#для одной
def check_files(data:dict):

    # Получаем все ключи
    keys = list(data.keys())

    # Словарь для хранения результатов
    results = {}

    # Проходим по всем ключам
    for i in tqdm(range(len(keys))):
        current_key = keys[i]
        current_photos = set(data[current_key]['photos'])
        
        # Получаем фотографии из текущего ключа
        for j in range(len(keys)):
            if i == j:
                continue  # Пропускаем сам себя

            compare_key = keys[j]
            compare_photos = set(data[compare_key]['photos'])
            
            # Находим совпадения
            common_photos = current_photos.intersection(compare_photos)
            
            if common_photos:
                # Если есть совпадения, проверяем, какие фотографии отсутствуют
                missing_photos = current_photos - compare_photos
                if missing_photos:
                    if compare_key not in results:
                        results[compare_key] = {
                            'missing_count': 0,
                            'missing_photos': [],
                            'missing_from': []
                        }
                    pprint(results)
                    results[compare_key]['missing_count'] += len(missing_photos)
                    results[compare_key]['missing_photos'].extend(list(missing_photos))
                    results[compare_key]['missing_from'].append(current_key)
            # else:
            #     # Если нет совпадений, считаем папку готовой
            #     results[compare_key] = 'Полностью готовая папка'
    
    pprint(results)
    1/0
    # Выводим результат
    for key, value in results.items():
        if isinstance(value, dict):
            print(f"{key}: {value['missing_count']} недостающих фото: {value['missing_photos']} (от: {', '.join(value['missing_from'])})")
            
        else:
            print(f"{key}: {value}")
        pass


#для 2х папок 
def compare_photo_dicts(dict1, dict2):
    # Получаем все ключи из обоих словарей
    keys1 = list(dict1.keys())
    keys2 = list(dict2.keys())
    
    # Словарь для хранения результатов
    results = {}

    # Проходим по всем ключам первого словаря
    for i in range(len(keys1)):
        current_key = keys1[i]
        current_photos = set(dict1[current_key]['photos'])
        
        # Сравниваем с ключами второго словаря
        for j in range(len(keys2)):
            compare_key = keys2[j]
            compare_photos = set(dict2[compare_key]['photos'])
            
            # Находим совпадения
            common_photos = current_photos.intersection(compare_photos)
            
            if common_photos:
                # Если есть совпадения, проверяем, какие фотографии отсутствуют
                missing_photos = current_photos - compare_photos
                if missing_photos:
                    if compare_key not in results:
                        results[compare_key] = {
                            'missing_count': 0,
                            'missing_photos': [],
                            'missing_from': []
                        }
                    results[compare_key]['missing_count'] += len(missing_photos)
                    results[compare_key]['missing_photos'].extend(list(missing_photos))
                    results[compare_key]['missing_from'].append(current_key)
            # else:
            #     # Если нет совпадений, считаем папку готовой
            #     results[compare_key] = 'Полностью готовая папка'

    # Выводим результат
    pprint(results)
    # for key, value in results.items():
    #     if isinstance(value, dict):
    #         print(f"{key}: {value['missing_count']} недостающих фото: {value['missing_photos']} (от: {', '.join(value['missing_from'])})")
    #     else:
    #         print(f"{key}: {value}")

if __name__ =='__main__':
    yadisk_manager = YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD, isTest=True)
    public_link='https://disk.yandex.ru/d/RwxAt9uRuesdhQ'
    data=get_all_hash_files(public_link)
    
    check_files(data)
    1/0
    # yadisk_manager.yadisk.p
    # yadisk_manager.get_all_folders('https://disk.yandex.ru/d/RwxAt9uRuesdhQ')
    yadisk_manager.get_all_files('ТЕСТИРУЕМ БОТА - 1/Березовая роща')
    1/0
    a=yadisk_manager.yadisk.get_meta('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/test folder 12/test.jpg')
    # a=yadisk_manager.yadisk.get_public_resources('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/test folder 12/')
    # pprint(a.__dict__)

    b=yadisk_manager.yadisk.get_meta('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/test folder 1/test.jpg')
    # b=yadisk_manager.yadisk.get_meta('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/')
    # b=yadisk_manager.yadisk.get_public_download_link(public_key=a.public_key)
    # pprint(b.__dict__)

    print(f"{a.md5=}\n{a.sha256}")
    print(f"{b.md5=}\n{b.sha256}")
    1/0

   
    fileUrl='https://images.cdn-cian.ru/images/dom-aladino-mayskaya-ulica-2202794273-2.jpg'
    fileName='test.jpg'
    folderName='test folder 12'


    # path=yadisk_manager.create_folder('test folder 1')
    # print(path)
    # yadisk_manager.upload_file_from_url(urlFolder=path, urlFile=fileUrl, nameFile=fileName)
   
    yadisk_manager.create_folder_and_upload_file(
        publickURL=public_link,
        folderName=folderName,
        fileName=fileName,
        fileURL=fileUrl
    )

# и='/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/ТЕСТИРУЕМ БОТА - 1/джим': {
#     'missing_count': 3,
#     'missing_from': ['/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/ТЕСТИРУЕМ БОТА - 1/фитнес'],
#     'missing_photos': ['f7dcef74c8287edac8591dff1f67ab27',
#                     '5f20942e0ca60a33e4f68453d839c292',
#                     '55086e01867500dc1ddcecbc436336e8']},