#!/usr/bin/env python3
"""Проверяем какие font-family используются на сайте"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

url = "https://piccheck.ru"
print(f"🔍 Анализирую: {url}\n")

# Скачиваем HTML
response = requests.get(url)
html = response.text

soup = BeautifulSoup(html, 'html.parser')

# Ищем все style теги
inline_styles = soup.find_all('style')
print(f"📄 Найдено <style> блоков: {len(inline_styles)}")

# Ищем ссылки на CSS
css_links = soup.find_all('link', rel='stylesheet')
print(f"📄 Найдено CSS файлов: {len(css_links)}\n")

# Собираем все font-family
all_fonts = set()

# Из inline CSS
for style in inline_styles:
    if style.string:
        matches = re.findall(r'font-family\s*:\s*([^;}\n]+)', style.string, re.IGNORECASE)
        for match in matches:
            fonts = [f.strip().strip('"\'') for f in match.split(',')]
            all_fonts.update(fonts)

# Из ссылок на CSS
for link in css_links:
    href = link.get('href')
    if href:
        full_url = urljoin(url, href)
        try:
            css_response = requests.get(full_url, timeout=10)
            matches = re.findall(r'font-family\s*:\s*([^;}\n]+)', css_response.text, re.IGNORECASE)
            for match in matches:
                fonts = [f.strip().strip('"\'') for f in match.split(',')]
                all_fonts.update(fonts)
        except:
            pass

# Из inline стилей элементов
for element in soup.find_all(style=True):
    style = element.get('style', '')
    matches = re.findall(r'font-family\s*:\s*([^;}\n]+)', style, re.IGNORECASE)
    for match in matches:
        fonts = [f.strip().strip('"\'') for f in match.split(',')]
        all_fonts.update(fonts)

print("🎨 Найденные шрифты:")
for font in sorted(all_fonts):
    # Проверяем системный ли это шрифт
    system_fonts = ['arial', 'helvetica', 'times', 'georgia', 'verdana', 'tahoma', 
                    'trebuchet', 'courier', 'impact', 'comic', 'sans-serif', 
                    'serif', 'monospace', 'cursive', 'fantasy']
    
    is_system = any(sf in font.lower() for sf in system_fonts)
    status = "🖥️ Системный" if is_system else "📦 Веб-шрифт"
    
    print(f"   • {font} {status}")

print(f"\nВсего: {len(all_fonts)} уникальных шрифтов")