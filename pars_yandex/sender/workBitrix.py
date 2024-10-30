import random
from fast_bitrix24 import Bitrix
import os
from dotenv import load_dotenv
from pprint import pprint
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

load_dotenv()
webhook = os.getenv('WEBHOOK')
bit = Bitrix(webhook)



@dataclass
class Deal:
    urlFolder:str='UF_CRM_1665135345460'
    sheetUrl:str='UF_CRM_1718109141725'
#полуаем все активные сделки у которых заполнено поле UF_CRM_1665135345460 и все пользовательские поля
# async def get_active_deals()->list:
async def get_active_deals()->dict:
    deals = await bit.get_all('crm.deal.list', params={'filter': {'CLOSED': 'N', f'!={Deal.urlFolder}': None}, 'select': ['*', 'UF_*']})
    deals=deals[:30]
    # pprint(deals[0])
    # pprint(deals)

    dealsDict={}
    for deal in deals:
        dealsDict[deal["ID"]]=deal

    # return deals
    return dealsDict

def prepare_deal_to_text(deals:list)->str:
    """
    1. Название сделки
    2. Название сделки
    """
    text=''
    for i,deal in enumerate(deals):
        text+=f"""{i}. {deal['TITLE']}\n"""
        
        
    return text

async def get_prepare_active_deals()->str:
    deals = await get_active_deals()
    # text=prepare_deal_to_text(deals)
    text='' 
    return text, deals

if __name__ == '__main__':
    deals = get_active_deals()
    text=prepare_deal_to_text(deals)
    print(text)
    # pprint(deals)
    # print(len(deals))
    # print('end')