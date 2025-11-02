from openpyxl import load_workbook
from werkzeug.security import generate_password_hash
from transliterate import translit
from db_session import create_session, global_init
from Classes import User
import os
import pdf_maker
from random import shuffle



def generate_password_for_user(liters):
    shuffle(liters)
    return ''.join(liters)



def import_users():
    db_path = os.path.join('db', 'users.db')
    global_init(True, db_path)

    workbook = load_workbook('exel/users.xlsx')
    sheet = workbook.active

    session = create_session()

    row = 2

    students_data = []

    try:
        while (sheet[f'A{row}'].value is not None and
               sheet[f'B{row}'].value is not None and
               sheet[f'C{row}'].value is not None and
               sheet[f'D{row}'].value is not None):

            name1 = (sheet[f'A{row}'].value, 'ru', True)[0]
            surname1 = (sheet[f'B{row}'].value, 'ru', True)[0]
            otchestvo1 = (sheet[f'C{row}'].value, 'ru', True)[0]
            user_class1 = (sheet[f'D{row}'].value, 'ru', True)[0]

            name = translit(name1, 'ru', True)
            surname = translit(surname1, 'ru', True)
            otchestvo = translit(otchestvo1, 'ru', True)
            user_class = translit(user_class1, 'ru', True)

            existing_user = session.query(User).filter(
                User.username == name,
                User.usersurname == surname,
                User.userotchestvo == otchestvo,
            ).first()

            liters = ([el for el in name[:3]] + [el for el in surname[:3]]
                      + [el for el in otchestvo[:3]] + [user_class[-1], user_class[0]])

            index = 0
            while existing_user:
                while name[-1].isdigit():
                    name = name[:-1]
                    surname = surname[:-1]
                    otchestvo = otchestvo[:-1]

                name += str(index)
                surname += str(index)
                otchestvo += str(index)

                index += 1

                existing_user = session.query(User).filter(
                    User.username == name,
                    User.usersurname == surname,
                    User.userotchestvo == otchestvo,
                ).first()

            password = generate_password_for_user(liters)
            pupil = {
                'last_name': surname1,
                'first_name': name1,
                'patronymic': otchestvo1,
                'class': user_class1,
                'password': password
            }
            students_data.append(pupil)
            user = User(
                username=name,
                usersurname=surname,
                userpassword=generate_password_hash(password),
                userotchestvo=otchestvo,
                userclass=user_class,
                role='Student',
                userbalance='0'
            )
            print(user)
            session.add(user)

            print(f"Добавлен пользователь: {name} {surname} {otchestvo} - {user_class}")
            row += 1
        session.commit()
        pdf_maker.main(students_data)

    except Exception as e:
        session.rollback()
        print(f"Ошибка при импорте: {e}")

    finally:
        session.close()
