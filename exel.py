from openpyxl import load_workbook
from werkzeug.security import generate_password_hash
from transliterate import translit
from db_session import create_session, global_init
from Classes import User
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def font():
    try:
        font_paths = [
            'arial.ttf',
            'C:/Windows/Fonts/arial.ttf',
            '/usr/share/fonts/truetype/msttcorefonts/arial.ttf',
            '/Library/Fonts/Arial.ttf',]
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                bold_path = font_path.replace('.ttf', 'bd.ttf')
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont('Arial-Bold', bold_path))
                return 'Arial'
    except:
        pass
    return 'Helvetica'



def import_users():
    db_path = os.path.join('db', 'users.db')
    global_init(True, db_path)

    workbook = load_workbook('exel/users.xlsx')
    sheet = workbook.active

    session = create_session()

    row = 2

    try:
        students_data = []
        while (sheet[f'A{row}'].value is not None and
               sheet[f'B{row}'].value is not None and
               sheet[f'C{row}'].value is not None and
               sheet[f'D{row}'].value is not None):

            name1 = sheet[f'A{row}'].value, 'ru', True
            surname1 = sheet[f'B{row}'].value, 'ru', True
            otchestvo1 = sheet[f'C{row}'].value, 'ru', True
            user_class1 = sheet[f'D{row}'].value, 'ru', True

            name = translit(name1, 'ru')
            surname = translit(surname1, 'ru')
            otchestvo = translit(otchestvo1, 'ru')
            user_class = translit(user_class1, 'ru')

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
            pdf_filename = "students.pdf"
            font_name = font()
            doc = SimpleDocTemplate(
                pdf_filename,
                pagesize=A4,
                topMargin=15,
                bottomMargin=15,
                leftMargin=15,
                rightMargin=15
            )
            print(1)
            table_data = []
            headers = ['Фамилия', 'Имя', 'Отчество', 'Класс', 'Пароль']
            table_data.append(headers)
            for student in students_data:
                table_data.append([
                    student['last_name'],
                    student['first_name'],
                    student['patronymic'],
                    student['class'],
                    student['password']
                ])
            table = Table(table_data, repeatRows=1)
            page_width = A4[0] - 30
            col_widths = [
                page_width * 0.18,
                page_width * 0.18,
                page_width * 0.24,
                page_width * 0.15,
                page_width * 0.25,
            ]

            table._argW = col_widths
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
                    colors.HexColor('#f8f9fa'),
                    colors.white
                ]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ])
            table.setStyle(style)
            doc.build([table])

            print(f"Добавлен пользователь: {name} {surname} {otchestvo} - {user_class}")
            row += 1
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Ошибка при импорте: {e}")

    finally:
        session.close()