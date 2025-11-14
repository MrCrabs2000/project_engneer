from sqlalchemy import Column, Integer, String
from db_session import SqlAlchemyBase
from flask_login import UserMixin



class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    userlogin = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    usersurname = Column(String(100), nullable=False)
    userotchestvo = Column(String(100), nullable=True)
    userpassword = Column(String(200), nullable=False)
    userbalance = Column(Integer, nullable=False, default='0')
    userclass = Column(String(100), nullable=False)
    role = Column(String(10), nullable=False, default='user')
    adedusers = Column(String(10), nullable=True, default='False')

class Item_shop(SqlAlchemyBase):
    __tablename__ = 'items_shop'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(300), nullable=False)
    count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    photo = Column(String(1000), nullable=False)


class Item_user(SqlAlchemyBase):
    __tablename__ = 'items_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, nullable=False)
    itemshopid = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    count = Column(Integer, default=0)
    date = Column(String(40), nullable=True)
    photo = Column(String(1000), nullable=False)