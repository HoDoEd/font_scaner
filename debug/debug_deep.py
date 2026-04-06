#!/usr/bin/env python3
"""Глубокая диагностика github.com"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.scanner.crawler import FontCrawler
import requests
from bs4 import BeautifulSoup
import re

url = "https://github.com"
print(f"🔍 ГЛУБОКАЯ ДИАГНОСТИКА: {url}\n")

# 1. Скачиваем HTML
print("=" * 70)
print("1️⃣  СКАЧИВАЕМ HTML")
print("=" * 70)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
response = requests.get(url, headers=headers, timeout=30)
html = response.text
print(f"✅ HTML загружен: {len(html)} байт")

# 2. Ищем ВСЕ CSS ссылки
print("\n" + "=" * 70)
print("2️⃣  ВСЕ CSS ССЫЛКИ")
print("=" * 70)

soup = BeautifulSoup(html, 'html.parser')
css_links = soup.find_all('link', rel=lambda x: x and 'stylesheet' in x)
print(f"Найдено CSS ссылок: {len(css_links)}\n")

for i, link in enumerate(css_links, 1):
    href = link.get('href', '')
    print(f"[{i}] {href}")

# 3. Парсим КАЖДЫЙ CSS на font-family
print("\n" + "=" * 70)
print("3️⃣  ПАРСИМ CSS НА font-family")
print("=" * 70)

all_fonts = set()

for i, link in enumerate(css_links[:5], 1):  # Первые 5 CSS
    href = link.get('href', '')
    if not href:
        continue
    
    full_url = f"https://github.com{href}" if href.startswith('/') else href
    
    try:
        css_response = requests.get(full_url, headers=headers, timeout=10)
        css_content = css_response.text
        
        # Ищем font-family
        pattern = r'font-family\s*:\s*([^;}\n]+)'
        matches = re.findall(pattern, css_content, re.IGNORECASE)
        
        if matches:
            print(f"\n📄 CSS [{i}]: {href[:80]}...")
            print(f"   Найдено font-family деклараций: {len(matches)}")
            
            for match in matches[:10]:  # Первые 10
                fonts = [f.strip().strip('"\'') for f in match.split(',')]
                for font in fonts:
                    if font and len(font) > 2:
                        # Игнорируем системные
                        if font.lower() in ['-apple-system', 'blinkmacsystemfont', 'system-ui', 'sans-serif', 'serif', 'monospace']:
                            continue
                        all_fonts.add(font)
                        print(f"   • {font}")
        
    except Exception as e:
        print(f"\n❌ Ошибка загрузки CSS {i}: {e}")

print("\n" + "=" * 70)
print("4️⃣  ИТОГОВЫЙ СПИСОК ШРИФТОВ")
print("=" * 70)
print(f"Всего уникальных шрифтов: {len(all_fonts)}")
for font in sorted(all_fonts):
    print(f"   • {font}")

# 5. Запускаем наш crawler
print("\n" + "=" * 70)
print("5️⃣  НАШ CRAWLER")
print("=" * 70)

crawler = FontCrawler()
result = crawler.scan_site(url)

print(f"Найдено файлов шрифтов: {len(result['font_files'])}")
print(f"Системных шрифтов: {len(result['system_fonts'])}")

if result['font_files']:
    print("\n📝 Файлы шрифтов:")
    for i, font in enumerate(result['font_files'], 1):
        print(f"   [{i}] {font['name']}")
        print(f"       URL: {font['url']}")
        print(f"       Источник: {font.get('source_css', 'N/A')}")

print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 70)