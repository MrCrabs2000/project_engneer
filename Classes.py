from sqlalchemy import Column, Integer, String, ForeignKey
from db_session import SqlAlchemyBase
from flask_login import UserMixin



class User(SqlAlchemyBase, UserMixin):
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

class Item(SqlAlchemyBase, UserMixin):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    usersid = Column(Integer, ForeignKey('users.id'))
    count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

