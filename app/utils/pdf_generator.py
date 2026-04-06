#!/usr/bin/env python3
"""
Генератор PDF отчётов для сканирования шрифтов
С полной поддержкой кириллицы
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import io
import os


def generate_pdf_report(scan_data: dict) -> bytes:
    """
    Генерирует PDF отчёт по результатам сканирования
    С поддержкой кириллицы
    """
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=3*cm  # Больше места для дисклеймера
    )
    
    elements = []
    
    # ===========================================
    # РЕГИСТРАЦИЯ ШРИФТА С КИРИЛЛИЦЕЙ
    # ===========================================
    font_registered = False
    font_name = 'Helvetica'  # fallback
    
    # Пути к шрифтам с кириллицей
    font_paths = [
        (r"C:\Windows\Fonts\arial.ttf", 'Arial'),
        (r"C:\Windows\Fonts\arialbd.ttf", 'Arial-Bold'),
        (r"C:\Windows\Fonts\times.ttf", 'Times'),
        (r"C:\Windows\Fonts\timesbd.ttf", 'Times-Bold'),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 'DejaVuSans'),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 'DejaVuSans-Bold'),
        ("/System/Library/Fonts/Arial.ttf", 'Arial'),
        ("/System/Library/Fonts/Arial Bold.ttf", 'Arial-Bold'),
    ]
    
    # Регистрируем обычный и жирный шрифт
    for font_path, name in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(name, font_path))
                if 'Bold' in name or 'bd' in font_path.lower():
                    pass  # Жирный уже зарегистрирован
                else:
                    font_name = name
                    font_registered = True
            except Exception as e:
                print(f"⚠️  Не удалось загрузить шрифт {font_path}: {e}")
    
    # Проверяем что оба шрифта зарегистрированы
    bold_font = font_name + '-Bold' if font_registered else 'Helvetica-Bold'
    normal_font = font_name if font_registered else 'Helvetica'
    
    # ===========================================
    # ЗАГОЛОВОК
    # ===========================================
    title_style = ParagraphStyle(
        'CustomTitle',
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName=bold_font,
        leading=30
    )
    
    elements.append(Paragraph("🔍 Font Scanner Report", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # ===========================================
    # ИНФОРМАЦИЯ О СКАНИРОВАНИИ
    # ===========================================
    info_style = ParagraphStyle(
        'InfoStyle',
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=15,
        fontName=normal_font,
        leading=16
    )
    
    scan_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    elements.append(Paragraph(f"<b>Сайт:</b> {scan_data.get('scan_url', 'N/A')}", info_style))
    elements.append(Paragraph(f"<b>Дата сканирования:</b> {scan_date}", info_style))
    elements.append(Paragraph(f"<b>Всего шрифтов:</b> {scan_data.get('total_fonts', 0)}", info_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # ===========================================
    # ТАБЛИЦА РЕЗУЛЬТАТОВ
    # ===========================================
    table_data = [['Шрифт', 'Статус', 'Лицензия']]
    
    status_map = {
        'OK': ('✅', 'Свободная лицензия', colors.HexColor('#27ae60')),
        'WARNING': ('⚠️', 'Требуется проверка', colors.HexColor('#f39c12')),
        'SYSTEM': ('ℹ️', 'Системный шрифт', colors.HexColor('#3498db')),
        'ERROR': ('❌', 'Ошибка', colors.HexColor('#e74c3c'))
    }
    
    for font in scan_data.get('fonts', []):
        font_name_text = font.get('matched_font', font.get('name', 'Неизвестный'))
        status = font.get('status', 'UNKNOWN')
        
        icon, status_text, _ = status_map.get(status, ('❓', 'Неизвестно', colors.gray))
        license_info = font.get('license_info', '-')
        
        # Убираем технические пометки
        license_info = license_info.replace(" ⚠️ эвристика", "").replace(" (по имени)", "")
        
        table_data.append([
            font_name_text,
            f"{icon} {status_text}",
            license_info
        ])
    
    # Создаём таблицу
    table = Table(table_data, colWidths=[4*cm, 3.5*cm, 5*cm])
    table.setStyle(TableStyle([
        # Заголовок
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Чередование цветов
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('BACKGROUND', (0, 2), (-1, -1), colors.white),
        
        # Сетка
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        
        # Отступы
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        
        # Размер шрифта
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('FONTNAME', (0, 1), (-1, -1), normal_font),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.7*inch))
    
    # ===========================================
    # ВАЖНЫЙ ДИСКЛЕЙМЕР (подробный)
    # ===========================================
    disclaimer_title_style = ParagraphStyle(
        'DisclaimerTitle',
        fontSize=12,
        textColor=colors.HexColor('#e67e22'),
        spaceAfter=10,
        fontName=bold_font,
        leading=16
    )
    
    disclaimer_text_style = ParagraphStyle(
        'DisclaimerText',
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=10,
        fontName=normal_font,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    elements.append(Paragraph("⚠️  Важная информация:", disclaimer_title_style))
    
    disclaimer_text = """
    Данный сервис не является юридической консультацией. Узнать, куплена ли лицензия на шрифт 
    на указанном сайте или нет, мы не можем. Наш сервис распознаёт только <b>"что"</b> используется, 
    но не <b>"на каком основании"</b>.
    </br></br>
    Техническими средствами сканирования сайта мы не можем достоверно узнать, куплена ли лицензия. 
    Поэтому, пользователь, узнав что лицензия неизвестна, должен уже сам удостовериться, что либо 
    шрифт всё таки является бесплатным, либо, если под авторским правом — приобрести лицензию 
    или заменить шрифт.
    </br></br>
    Для окончательного подтверждения прав обратитесь к правообладателю шрифта.
    """
    
    elements.append(Paragraph(disclaimer_text, disclaimer_text_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # ===========================================
    # СТАТУСЫ И ОБОЗНАЧЕНИЯ
    # ===========================================
    legend_style = ParagraphStyle(
        'LegendStyle',
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        fontName=normal_font,
        leading=13
    )
    
    elements.append(Paragraph("<b>Обозначения статусов:</b>", legend_style))
    elements.append(Paragraph("✅ Свободная лицензия — шрифт найден в базе бесплатных шрифтов", legend_style))
    elements.append(Paragraph("⚠️ Требуется проверка — шрифт не найден в базе, возможна платная лицензия", legend_style))
    elements.append(Paragraph("ℹ️ Системный шрифт — шрифт встроен в операционную систему", legend_style))
    elements.append(Paragraph("❌ Ошибка — не удалось скачать или проанализировать шрифт", legend_style))
    
    # ===========================================
    # ГЕНЕРАЦИЯ PDF
    # ===========================================
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes