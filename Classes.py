from sqlalchemy import Column, Integer, String
from db_session import SqlAlchemyBase
from flask_login import UserMixin



class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    usersurname = Column(String(100), nullable=False)
    userpassword = Column(String(200), nullable=False)
    userotchestvo = Column(String(100), nullable=True)
    userclass = Column(String(100), nullable=False)
    role = Column(String(10), nullable=False, default='user')
    userbalance = Column(String(5), nullable=False, default='0')

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
    name = Column(String(100), nullable=False)
    description = Column(String(300), nullable=False)
    photo = Column(String(1000), nullable=False)

