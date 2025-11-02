from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


def setup_fonts():
    try:
        font_paths = [
            'arial.ttf',
            'C:/Windows/Fonts/arial.ttf',  # Windows
            '/usr/share/fonts/truetype/msttcorefonts/arial.ttf',  # Linux
            '/Library/Fonts/Arial.ttf',  # macOS
        ]

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


def create_full_page_table_pdf(filename, students_data):

    font_name = setup_fonts()

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        topMargin=15,
        bottomMargin=15,
        leftMargin=10,
        rightMargin=10
    )

    table_data = []

    headers = ['Имя', 'Фамилия', 'Отчество', 'Класс', 'Имя при входе', 'Пароль']
    table_data.append(headers)

    for student in students_data:
        table_data.append([
            student['first_name'],
            student['last_name'],
            student['patronymic'],
            student['class'],
            student['username'],
            student['password']
        ])

    table = Table(table_data, repeatRows=1)

    page_width = A4[0] - 20
    col_widths = [
        page_width * 0.12,  # Имя
        page_width * 0.12,  # Фамилия
        page_width * 0.18,  # Отчество
        page_width * 0.10,  # Класс
        page_width * 0.20,  # Имя при входе
        page_width * 0.18,  # Пароль
    ]

    table._argW = col_widths

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 6),

        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),

        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
            colors.HexColor('#f8f9fa'),
            colors.white
        ]),

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ])

    table.setStyle(style)
    doc.build([table])


def create_simple_pdf(filename, students_data):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        topMargin=10,
        bottomMargin=10,
        leftMargin=10,
        rightMargin=10
    )

    table_data = [['Имя', 'Фамилия', 'Отчество', 'Класс', 'Имя при входе', 'Пароль']]

    for student in students_data:
        table_data.append([
            student['first_name'],
            student['last_name'],
            student['patronymic'],
            student['class'],
            student['username'],
            student['password']
        ])
    table = Table(table_data, repeatRows=1)


    available_width = A4[0] - 20
    col_widths = [
        available_width * 0.12,
        available_width * 0.12,
        available_width * 0.18,
        available_width * 0.10,
        available_width * 0.20,
        available_width * 0.18,
    ]
    table._argW = col_widths

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ])
    table.setStyle(style)
    doc.build([table])


def main(students_data):
    pdf_filename = "users.pdf"
    try:
        create_full_page_table_pdf(pdf_filename, students_data)
    except Exception:
        try:
            create_simple_pdf(pdf_filename, students_data)
        except Exception:
            return