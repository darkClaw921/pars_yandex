from sqlalchemy import (create_engine, Column, 
                        Integer, Float, String,
                        DateTime, JSON, ARRAY, 
                        BigInteger, func, text, 
                        BOOLEAN, URL, ForeignKey, cast)
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship, declarative_base
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pprint import pprint


load_dotenv()
userName = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')
db = os.environ.get('POSTGRES_DB')
url = os.environ.get('POSTGRES_URL')
url='postgres-ys'
url='localhost'


# Создаем подключение к базе данных
engine = create_engine(f'postgresql://{userName}:{password}@{url}:5433/{db}')
# engine = create_engine('mysql://username:password@localhost/games')




 
# Определяем базу данных
Base = declarative_base()



class User(Base):
    __tablename__ = 'User'
    
    id = Column(BigInteger, primary_key=True)
    created_date = Column(DateTime)
    nickname = Column(String)
    payload=Column(String)
    project=Column(String)
    activ_deal_id=Column(BigInteger)
   

class Message(Base):
    __tablename__ = 'Message'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_date = Column(DateTime)
    user_id=Column(BigInteger)
    # message_id = Column(BigInteger)
    payload = Column(String)
    type_chat = Column(String)
    text = Column(String)



class Project(Base):
    __tablename__ = 'Project'
    id = Column(BigInteger, primary_key=True)
    created_date = Column(DateTime)
    user_id=Column(BigInteger)
    name=Column(String)
    phone=Column(String)
    email=Column(String)
    folder_url=Column(String)
    time_work=Column(String)
    status=Column(String)
    address=Column(String)
    description=Column(String)
    photos=Column(ARRAY(String))
    is_add_to_sheet=Column(BOOLEAN)


Base.metadata.create_all(engine)
# Base.metadata.update_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
# session


def add_new_user(userID:int, nickname:str):
    with Session() as session:
        newUser=User(
            created_date=datetime.now(),
            id=userID,
            nickname=nickname,
            # all_token=0,
            # all_token_price=0,
            # payload=''
        )
        session.add(newUser)
        session.commit()

def add_new_message(userID:int, 
                    text:str, 
                    type_chat:str,
                    payload:str):
    
    with Session() as session:
        newMessage=Message(
            created_date=datetime.now(),
            user_id=userID,
            text=text,
            type_chat=type_chat,
            payload=payload
        )
        session.add(newMessage)
        session.commit()

def add_new_project(name:str, phone:str, 
                    email:str, folderURL:str, 
                    timeWork:str, status:str, 
                    address:str, description:str, 
                    photos:list):
    with Session() as session:
        newProject=Project(
            created_date=datetime.now(),
            name=name,
            phone=phone,
            email=email,
            folder_url=folderURL,
            time_work=timeWork,
            status=status,
            address=address,
            description=description,
            photos=photos,
            is_add_to_sheet=False
        )
        session.add(newProject)
        session.commit()


def update_deal_for_user(userID:int, dealID:int):
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        user.activ_deal_id=dealID
        session.commit()

def update_project_for_user(userID:int, project:str):
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        user.project=project
        session.commit()

def update_payload(userID:int, payload:str):
    with Session() as session:
        session.query(User).filter(User.id==userID)\
            .update({User.payload:payload}) 
        session.commit()

def update_token_for_user(userID:int, token:float):
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        user.all_token+=token
        session.commit()

def update_token_price_for_user(userID:int, tokenPrice:float):
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        user.all_token_price+=tokenPrice
        session.commit()



def update_project(projectID:int,name:str=None, phone:str=None,
                email:str=None, folderURL:str=None,
                timeWork:str=None, status:str=None,
                address:str=None, description:str=None,
                photos:list=None, isAddtoSheet:bool=False):                   
    """Обновляет только те поля, которые переданы, если поля нет, то оно остается прежним"""
    with Session() as session:
        project=session.query(Project).filter(Project.id==projectID).one()
        if name is not None:
            project.name=name
        if phone is not None:
            project.phone=phone
        if email is not None:
            project.email=email
        if folderURL is not None:
            project.folder_url=folderURL
        if timeWork is not None:
            project.time_work=timeWork
        if status is not None:
            project.status=status
        if address is not None:
            project.address=address
        if description is not None:
            project.description=description
        if photos is not None:
            project.photos=photos
        
        if isAddtoSheet is not None:
            project.is_add_to_sheet=isAddtoSheet
        
        session.commit()

   


def get_last_project_for_user(userID:int)->Project:
    with Session() as session:
        project=session.query(Project).filter(Project.user_id==userID).order_by(Project.created_date.desc()).first()
        return project

def get_user(userID:int)->User:
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        return user
 
def get_payload(userID:int)->str:
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        return user.payload


def get_activ_deal(userID:int)->int:
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        return user.activ_deal_id

def get_project_for_user(userID:int)->str:
    with Session() as session:
        user=session.query(User).filter(User.id==userID).one()
        return user.project

def check_user(userID:int)->bool:
    """Проверка наличия пользователя в базе"""
    with Session() as session:
        users=session.query(User).filter(User.id==userID).all()
        if len(users) > 0:
            return True
        else:
            return False



if __name__ == '__main__':
   
    pass