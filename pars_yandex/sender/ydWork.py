from pprint import pprint
from yadisk import YaDisk
from dotenv import load_dotenv
import postgreWork
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
            # self.pathMain='/Производственный отдел/ПРОЕКТЫ - собираем подборки под проекты, извлекаем отсюда новые/'
            self.pathMain='/Производственный отдел/ПРОЕКТЫ - собираем подборки под проекты, извлекаем отсюда новые/_АКТИВНЫЕ ТЕНДЕРЫ/'
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
        
        publickURL=None 
        try:
            folder_path, publickURL = self.create_folder(allPath)    
            postgreWork.update_project(projectID=projectID, folderURL=publickURL)

            
        except:
            logger.debug(f'Папка {folderName} уже существует')
            postgreWork.update_project(projectID=projectID, folderURL=publickURL)
            folder_path = allPath

        if fileURL.startswith('http'):
            self.upload_file_from_url(folder_path, fileURL, fileName)
        else:
            self.upload_file_from_local(fileURL, folder_path,nameFile=fileName)
        # self.upload_file_from_url(folder_path, fileURL, fileName)
        logger.info(f'Файл {fileName} загружен в папку {folder_path}')
        
        return folder_path, publickURL



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
    
if __name__ =='__main__':
    yadisk_manager = YandexDiskManager(APLICATION_ID=APLICATION_ID, APLICATION_SECRET=APLICATION_SECRET, TOKEN_YD=TOKEN_YD, isTest=True)
    # yadisk_manager.yadisk.p
    yadisk_manager.get_all_folders('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/')
    1/0
    a=yadisk_manager.yadisk.get_meta('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/test folder 12/test.jpg')
    # a=yadisk_manager.yadisk.get_public_resources('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/test folder 12/')
    # pprint(a.__dict__)

    # b=yadisk_manager.yadisk.get_meta('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/test folder 1/test.jpg')
    b=yadisk_manager.yadisk.get_meta('/Производственный отдел/ТЕСТИРОВАНИЕ/ТЕСТИРУЕМ БОТА - 1/')
    # b=yadisk_manager.yadisk.get_public_download_link(public_key=a.public_key)
    # pprint(b.__dict__)

    print(f"{a.md5=}\n{a.sha256}")
    print(f"{b.md5=}\n{b.sha256}")
    1/0

    public_link='https://disk.yandex.ru/d/RwxAt9uRuesdhQ'
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

