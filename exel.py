from openpyxl import load_workbook
from werkzeug.security import generate_password_hash
from transliterate import translit
from db_session import create_session, global_init
from Classes import User
import os


def import_users():
    db_path = os.path.join('db', 'users.db')
    global_init(True, db_path)

    workbook = load_workbook('exel/users.xlsx')
    sheet = workbook.active

    session = create_session()

    row = 2

    try:
        while (sheet[f'A{row}'].value is not None and
               sheet[f'B{row}'].value is not None and
               sheet[f'C{row}'].value is not None and
               sheet[f'D{row}'].value is not None):

            name = translit(sheet[f'A{row}'].value, 'ru', True)
            surname = translit(sheet[f'B{row}'].value, 'ru', True)
            otchestvo = translit(sheet[f'C{row}'].value, 'ru', True)
            user_class = translit(sheet[f'D{row}'].value, 'ru', True)

            existing_user = session.query(User).filter(
                User.username == name,
                User.usersurname == surname,
                User.userclass == user_class
            ).first()

            if existing_user:
                print(f"Пользователь уже существует: {name} {surname} - {user_class}")
                row += 1
                continue
            password = name[:3] + surname[:3] + otchestvo[:3] + user_class
            user = User(
                username=name,
                usersurname=surname,
                userpassword=generate_password_hash(password),
                userclass=user_class,
                role='Student',
                userbalance='0'
            )

            session.add(user)
            print(f"Добавлен пользователь: {name} {surname} {otchestvo} - {user_class}")

            row += 1

        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Ошибка при импорте: {e}")

    finally:
        session.close()