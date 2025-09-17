from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

SqlAlchemyBase = declarative_base()

class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    usersurname = Column(String(100), nullable=False)
    userpassword = Column(String(200), nullable=False)
    phonenumber = Column(String(20), nullable=True)
    userclass = Column(String(100), nullable=False)
    role = Column(String(10), nullable=False, default='user')
    userbalance = Column(String(5), nullable=False, default='0')
    avatar = Column(String(255), nullable=True)

class Item(SqlAlchemyBase):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    usersid = Column(Integer, ForeignKey('users.id'))
    count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)


def init_db(db_path='sqlite:///db/users.db'):
    os.makedirs('db', exist_ok=True)
    engine = create_engine(db_path)
    SqlAlchemyBase.metadata.create_all(engine)
    return engine


def create_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()