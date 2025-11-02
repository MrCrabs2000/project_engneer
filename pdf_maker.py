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
        leftMargin=15,
        rightMargin=15
    )

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
        page_width * 0.18,  # Имя
        page_width * 0.18,  # Фамилия
        page_width * 0.24,  # Отчество
        page_width * 0.15,  # Класс
        page_width * 0.25,  # Пароль
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
            colors.white]),

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
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
    table_data = [['Имя', 'Фамилия', 'Отчество', 'Класс', 'Пароль']]
    for student in students_data:
        table_data.append([
            student['last_name'],
            student['first_name'],
            student['patronymic'],
            student['class'],
            student['password']
        ])
    table = Table(table_data, repeatRows=1)
    table._argW = 'auto'
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
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


if __name__ == "__main__":
    main()