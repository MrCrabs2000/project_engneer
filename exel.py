from openpyxl import load_workbook
from werkzeug.security import generate_password_hash
from transliterate import translit
from db_session import create_session, global_init
from Classes import User
import os
import pdf_maker
from random import shuffle


liters = ['a', 'b', 'c', 'd', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
          'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T',
          'U', 'V', 'W', 'X', 'Y', 'Z']

num = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']



def generate_password_for_user():
    shuffle(liters)
    shuffle(num)
    return ''.join(liters[:3]) + ''.join(num[0]) + ''.join(liters[3:6]) + ''.join(num[1])



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
               sheet[f'D{row}'].value is not None and
               sheet[f'E{row}'].value is not None):

            name1 = (sheet[f'A{row}'].value, 'ru', True)[0]
            surname1 = (sheet[f'B{row}'].value, 'ru', True)[0]
            otchestvo1 = (sheet[f'C{row}'].value, 'ru', True)[0]
            user_class1 = (sheet[f'D{row}'].value, 'ru', True)[0]
            role = sheet[f'E{row}'].value[0]

            name = translit(name1, 'ru', True)
            surname = translit(surname1, 'ru', True)
            otchestvo = translit(otchestvo1, 'ru', True)
            user_class = translit(user_class1, 'ru', True)

            name2 = name[:3] + surname[:3] + otchestvo[:3] + user_class

            existing_user = session.query(User).filter(User.username == name2).first()

            index = 0

            while existing_user:
                while name2[-1].isdigit():
                    name2 = name2[:-1]
                name2 += str(index)
                index += 1

                existing_user = session.query(User).filter(User.username == name2).first()

            password = generate_password_for_user()
            pupil = {
                'last_name': surname1,
                'first_name': name1,
                'patronymic': otchestvo1,
                'class': user_class1,
                'username': name2,
                'password': password
            }
            students_data.append(pupil)
            user = User(
                username=name1,
                userlogin=name2,
                usersurname=surname1,
                userpassword=generate_password_hash(password),
                userotchestvo=otchestvo1,
                userclass=user_class1,
                role=role,
                userbalance='0'
            )
            session.add(user)

            row += 1
        session.commit()
        pdf_maker.main(students_data)

    except Exception:
        session.rollback()

    finally:
        session.close()