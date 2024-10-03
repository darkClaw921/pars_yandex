from fast_bitrix24 import Bitrix
import os
from dataclasses import dataclass
from pprint import pprint
webHook = os.environ.get('webhook')

bit = Bitrix(webHook)




@dataclass
class Company:
    class StatusClient:
        id:str='UF_CRM_1727429789973'
        cool:int=104
        active:str=106

def prepare_body(event):
    import base64
    from urllib.parse import unquote
    body = event['body']
    print(body)
    body = str(base64.b64decode(body))
    print(body)
    body = str(unquote(body))
    body = body.split('&')
    body[0] = body[0].split("'")[1]
    print(body)
    return body

def get_deal(dealID):
    deal = bit.call('crm.deal.get', items={'ID': dealID})
    return deal

def get_company(companyID):
    company = bit.call('crm.company.get', items={'ID': companyID})
    return company

def update_company(companyID, fields):
    company = bit.call('crm.company.update', items={'ID': companyID, 'fields': fields})
    return company

 

def handler(event, context):

    body = prepare_body(event)
    dealID = body[2].split('DEAL_')[1]
    #получаем связную компанию
    deal = get_deal(dealID)
    pprint(deal)
    companyID = deal['order0000000000']['COMPANY_ID']
    # company = get_company(companyID)

    #устанавливаем статус клиента на активен
    company = update_company(companyID, {Company.StatusClient.id:Company.StatusClient.active})


    return {
        'statusCode': 200,
        'body': 'Hello World!',
    }

#функция обновления сделки если задача завершина 
def update_deal_for_task_done(taskID):
    task= bit.call('tasks.task.get', items={'ID': taskID})
    pprint(task)
    dealID = task['order0000000000']['DEAL_ID']
    #получаем связную компанию
    deal = get_deal(dealID)
    pprint(deal)
    companyID = deal['order0000000000']['COMPANY_ID']
    # company = get_company(companyID)


if __name__ == '__main__':
    dealID = 88
    deal = get_deal(dealID)
    pprint(deal)
    companyID = deal['order0000000000']['COMPANY_ID']
    # company = get_company(companyID)

    #устанавливаем статус клиента на активен
    company = update_company(companyID, {Company.StatusClient.id:Company.StatusClient.active}) 