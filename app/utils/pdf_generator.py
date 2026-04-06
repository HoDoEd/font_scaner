#!/usr/bin/env python3
"""
Простой генератор PDF отчётов для Font Scanner
Версия без кириллицы для надёжности
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import io


def translate_license(russian_license: str) -> str:
    """Переводит лицензию на английский для отчёта"""
    translations = {
        "OFL": "Open Font License",
        "Apache": "Apache License 2.0",
        "MIT": "MIT License",
        "Free (FontSquirrel)": "Free for Commercial Use",
        "OFL (GitHub)": "Open Font License",
        "Неизвестная лицензия": "Unknown License",
        "Системный шрифт (легально)": "System Font",
        "Google Fonts (требуется проверка)": "Google Fonts - Verify",
    }
    
    # Убираем технические пометки
    clean = russian_license.replace(" ⚠️ эвристика", "").strip()
    clean = clean.replace(" ⚠️ по имени", "").strip()
    
    return translations.get(clean, clean)


def generate_pdf_report(scan_data: dict) -> bytes:
    """
    Генерирует простой PDF отчёт на английском
    
    Args:
        scan_data: dict с результатами сканирования
    
    Returns:
        bytes: PDF файл
    """
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Заголовок
    elements.append(Paragraph("Font Scanner Report", styles['Title']))
    elements.append(Spacer(1, 20))
    
    # Информация
    elements.append(Paragraph(
        f"<b>Website:</b> {scan_data.get('scan_url', 'N/A')}",
        styles['Normal']
    ))
    elements.append(Paragraph(
        f"<b>Scan Date:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        styles['Normal']
    ))
    elements.append(Paragraph(
        f"<b>Total Fonts Found:</b> {scan_data.get('total_fonts', 0)}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 20))
    
    # Таблица
    table_data = [['Font', 'Status', 'License']]
    
    for font in scan_data.get('fonts', []):
        # Название шрифта (без технических пометок)
        font_name = font.get('matched_font', font.get('name', 'Unknown'))
        if font_name and ' (по имени)' in font_name:
            font_name = font_name.replace(' (по имени)', '')
        
        # Статус на английском
        status = font.get('status', 'UNKNOWN')
        status_text = {
            'OK': 'Free License',
            'WARNING': 'Check Needed',
            'SYSTEM': 'System Font',
            'ERROR': 'Error'
        }.get(status, status)
        
        # Лицензия на английском
        license_info = translate_license(font.get('license_info', '-'))
        
        table_data.append([font_name, status_text, license_info])
    
    # Создаём таблицу
    table = Table(table_data, colWidths=[180, 120, 180])
    table.setStyle(TableStyle([
        # Заголовок
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Чередование цветов строк
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('BACKGROUND', (0, 2), (-1, -1), colors.white),
        
        # Сетка
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Отступы
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        
        # Размер шрифта для данных
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    # Дисклеймер
    disclaimer = Paragraph(
        "<i>Disclaimer: This report is not a legal consultation. "
        "License status is determined automatically and may contain errors. "
        "For final confirmation, contact the copyright holder.</i>",
        styles['Normal']
    )
    elements.append(disclaimer)
    
    # Генерируем PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes