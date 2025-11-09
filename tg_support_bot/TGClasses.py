from sqlalchemy import Column, Integer, String, Text, Boolean
from TGdb_session import SqlAlchemyBase


class Question(SqlAlchemyBase):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    answered = Column(Boolean, default=False)
    admin_reply = Column(Text)


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_username = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False)
