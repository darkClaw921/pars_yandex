import random
from fast_bitrix24 import Bitrix
import os
from dotenv import load_dotenv
from pprint import pprint
from dataclasses import dataclass
from datetime import datetime, timedelta


load_dotenv()
webhook = os.getenv('WEBHOOK')
bit = Bitrix(webhook)



@dataclass
class Deal:
    urlFolder:str='UF_CRM_1665135345460'
    sheetUrl:str='UF_CRM_1718109141725'
#полуаем все активные сделки у которых заполнено поле UF_CRM_1665135345460 и все пользовательские поля
def get_active_deals()->list:
    deals = bit.get_all('crm.deal.list', params={'filter': {'CLOSE': 'N', f'!={Deal.urlFolder}': None}, 'select': ['*', 'UF_*']})
    return deals

def prepare_deal_to_text(deals:list)->str:
    """
    1. Название сделки
    2. Название сделки
    """
    text=''
    for i,deal in enumerate(deals):
        text+=f"""{i}. {deal['TITLE']}\n"""
        
        
    return text

def get_prepare_active_deals()->str:
    deals = get_active_deals()
    text=prepare_deal_to_text(deals)
    return text

if __name__ == '__main__':
    deals = get_active_deals()
    text=prepare_deal_to_text(deals)
    print(text)
    # pprint(deals)
    # print(len(deals))
    # print('end')