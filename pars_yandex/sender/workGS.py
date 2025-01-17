import gspread
from oauth2client.service_account import ServiceAccountCredentials
from loguru import logger
from pprint import pprint

class Sheet():

    @logger.catch
    def __init__(self, jsonPath: str, sheetName: str, workSheetName, servisName: str = None, sheetDealUrl: str = None):

        self.scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']  # что то для чего-то нужно Костыль
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            jsonPath, self.scope)  # Секретынй файл json для доступа к API
        self.client = gspread.authorize(self.creds)
        if sheetDealUrl:
            self.sheet = self.client.open_by_url(sheetDealUrl).worksheet(workSheetName)
        else:
            self.sheet = self.client.open(sheetName).worksheet(
                workSheetName)  # Имя таблицы
        # self.sheet = self.client.open(workSheetName)  # Имя таблицы

    def send_cell(self, position: str, value):
        #self.sheet.update_cell(position, value=value)
        self.sheet.update(position, value)

    def update_cell(self, r, c, value):
        self.sheet.update_cell(int(r), int(c), value)
        # sheet.update_cell(1, 1, "I just wrote to a spreadsheet using Python!")0

    def find_cell(self, value):
        cell = self.sheet.find(value)
        return cell

    def get_cell(self, row: str):
        # A1
        cell = self.sheet.acell(row).value
        return cell

    def get_value_in_column(self, column: int):
        # 3
        cell = self.sheet.col_values(column)
        return cell

    def insert_cell(self,data:list):
        """Записывает в последнуюю пустую строку"""
        nextRow = len(self.sheet.get_all_values()) + 1
        self.sheet.insert_row(data,nextRow, value_input_option='USER_ENTERED')
    
    def get_last_clear_row_for_column(self, column: str='ЛОКАЦИЯ'):
        """Находит последнюю пустую строку в колонке и возвращает ее номер и номер колонки"""
        colLocation=self.find_cell(column).col
        valuesLocation=self.get_value_in_column(colLocation)
        # pprint(valuesLocation)
        lastClearRowLocation=len(valuesLocation)+1

        #or
        # Находим индекс колонки "ЛОКАЦИЯ"
        # header = worksheet.row_values(1)  # Получаем первую строку (заголовки)
        # location_index = header.index("ЛОКАЦИЯ") + 1  # Индекс колонки (начинается с 1)

        return lastClearRowLocation, colLocation
        
    def add_new_location(self,
                         name: str,
                         address: str,
                         phone: str,
                         email: str,
                         folderURL: str,
                         timeWork: str,
                         status: str=None,):
        
        # lastClearRowLocation, colIndexLocation=self.get_last_clear_row_for_column('ЛОКАЦИЯ')
        lastClearRowLocation, colIndexLocation=self.get_last_clear_row_for_column('ОБЪЕКТ')
        self.update_cell(lastClearRowLocation, colIndexLocation, name)

        #ССЫЛКА НА ФОТО В НАШЕЙ БАЗЕ
        lastClearRowPhoto, colIndexPhoto=self.get_last_clear_row_for_column('ССЫЛКА НА ФОТО В НАШЕЙ БАЗЕ')
        self.update_cell(lastClearRowLocation, colIndexPhoto, folderURL)

        #АДРЕС
        lastClearRowAddress, colIndexAddress=self.get_last_clear_row_for_column('АДРЕС')
        self.update_cell(lastClearRowLocation, colIndexAddress, address)

        #КОНТАКТ
        lastClearRowPhone, colIndexPhone=self.get_last_clear_row_for_column('КОНТАКТ')
        self.update_cell(lastClearRowLocation, colIndexPhone, phone)

        #Часы работы
        lastClearRowTimeWork, colIndexTimeWork=self.get_last_clear_row_for_column('Часы работы')
        self.update_cell(lastClearRowLocation, colIndexTimeWork, timeWork)

        #Из базы / новый
        lastClearRowStatus, colIndexStatus=self.get_last_clear_row_for_column('Из базы / новый')
        self.update_cell(lastClearRowLocation, colIndexStatus, status)


if __name__ == '__main__':
    s=Sheet('profzaboru-5f6f677a3cd8.json','Объекты тест','Объекты')
    
    

    s.add_new_location(name='стадион',
                       address='ул. Ленина 1',
                    phone='8-800-555-35-35',
                    email='asd@asd.tu',
                    folderURL='https://drive.google.com/drive/folders/1Q3Km3Z2Y9z7H3k0Tb9l6Jc5Ue1b4Z8XZ',
                    timeWork='с 9 до 18',
                    status='Новый'
                       )

    # # valuesLocation=s.get_value_in_column(colLocation)
    # lastClearRowLocation, colIndex=s.get_last_clear_row_for_column(col)
    # # pprint(valuesLocation)
    # print(lastClearRowLocation)
    # print(colIndex)

    # s.update_cell(lastClearRowLocation, colIndex, 'test')
    # s.update_cell(2, 1, 'Новый')
    pass