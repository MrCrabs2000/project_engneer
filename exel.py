from openpyxl import load_workbook
from werkzeug.security import generate_password_hash

from db_session import create_session, global_init
from Classes import User
import os


def import_users():
    db_path = os.path.join('db', 'users.db')
    global_init(True, db_path)

    workbook = load_workbook('Students.xlsx')
    sheet = workbook.active

    session = create_session()

    row = 2

    try:
        while (sheet[f'A{row}'].value is not None and
               sheet[f'B{row}'].value is not None and
               sheet[f'C{row}'].value is not None and
               sheet[f'D{row}'].value is not None):

            name = sheet[f'A{row}'].value
            surname = sheet[f'B{row}'].value
            otchestvo = sheet[f'C{row}'].value
            user_class = sheet[f'D{row}'].value

            existing_user = session.query(User).filter(
                User.username == name,
                User.usersurname == surname,
                User.userclass == user_class
            ).first()

            if existing_user:
                print(f"Пользователь уже существует: {name} {surname} - {user_class}")
                row += 1
                continue

            user = User(
                username=name,
                usersurname=surname,
                phonenumber='',
                userpassword=generate_password_hash('123456'),
                userclass=user_class,
                role='student',
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


print(import_users())
