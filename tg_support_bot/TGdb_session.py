import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session



SqlAlchemyBase = orm.declarative_base()

__factory = None


def global_init(*db_file):
    if db_file[0]:
        global __factory

        if __factory:
            return

        if not db_file[1] or not db_file[1].strip():
            raise Exception("Необходимо указать файл базы данных.")

        conn_str = 'sqlite:///' + db_file[1].strip() + '?check_same_thread=False'
        print('Подключение к базе данных по адресу' + conn_str)

        engine = sa.create_engine(conn_str, echo=False)
        __factory = orm.sessionmaker(bind=engine)

        from TGClasses import User, Question

        SqlAlchemyBase.metadata.create_all(engine)
    else:
        if __factory:
            return
        url = 'mysql://h544655_nohybe:ca2endaurelt9@h544655_nohybe.mysql.masterhost.ru/h544655_nohybe'
        engine = sa.create_engine(url)
        __factory = orm.sessionmaker(bind=engine)

        from TGClasses import User, Question

        SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()