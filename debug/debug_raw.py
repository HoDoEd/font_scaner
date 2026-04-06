#!/usr/bin/env python3
"""Максимально детальный дамп запроса к piccheck.ru"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://piccheck.ru"
print(f"🔍 RAW DEBUG: {url}\n")

# Настройки как в нашем crawler
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# 1. Скачиваем HTML
print("=" * 70)
print("1️⃣  ЗАПРОС К САЙТУ")
print("=" * 70)

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"✅ Статус: {response.status_code}")
    print(f"📦 Размер HTML: {len(response.text)} байт")
    print(f"🔗 Final URL: {response.url}")
    print(f"📄 Content-Type: {response.headers.get('content-type', 'N/A')}")
except Exception as e:
    print(f"❌ Ошибка запроса: {e}")
    exit(1)

html = response.text

# 2. Ищем ВСЕ link теги
print("\n" + "=" * 70)
print("2️⃣  ВСЕ <link> ТЕГИ")
print("=" * 70)

soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('link')
print(f"Найдено <link> тегов: {len(links)}\n")

for i, link in enumerate(links, 1):
    href = link.get('href', '')
    rel = link.get('rel', [])
    print(f"[{i}] rel={rel}")
    print(f"    href={href}")
    
    # Если это Google Fonts — покажем подробнее
    if 'fonts.googleapis' in href:
        print(f"    🎯 GOOGLE FONTS DETECTED!")
        # Парсим параметры
        if '?' in href:
            params = href.split('?')[1]
            print(f"    Параметры: {params}")

# 3. Ищем ВСЕ style теги
print("\n" + "=" * 70)
print("3️⃣  ВСЕ <style> ТЕГИ")
print("=" * 70)

styles = soup.find_all('style')
print(f"Найдено <style> блоков: {len(styles)}\n")

for i, style in enumerate(styles, 1):
    content = style.string or ""
    if content:
        # Ищем font-family
        fonts = re.findall(r'font-family\s*:\s*[^;};]+', content, re.IGNORECASE)
        if fonts:
            print(f"[{i}] Найдено font-family: {fonts[:5]}")  # Первые 5

# 4. Ищем @import в HTML
print("\n" + "=" * 70)
print("4️⃣  @import ПРАВИЛА")
print("=" * 70)

imports = re.findall(r'@import\s+url\(["\']?([^"\')]+)["\']?\)', html, re.IGNORECASE)
if imports:
    print(f"Найдено @import: {len(imports)}")
    for imp in imports:
        print(f"   • {imp}")
else:
    print("Не найдено")

# 5. Скачиваем и парсим CSS файлы (первые 3)
print("\n" + "=" * 70)
print("5️⃣  ПАРСИНГ CSS ФАЙЛОВ")
print("=" * 70)

css_urls = []
for link in soup.find_all('link', rel=lambda x: x and 'stylesheet' in x):
    href = link.get('href')
    if href:
        from urllib.parse import urljoin
        css_urls.append(urljoin(url, href))

print(f"Найдено CSS ссылок: {len(css_urls)}\n")

for i, css_url in enumerate(css_urls[:3], 1):  # Первые 3
    print(f"[{i}] {css_url}")
    
    try:
        css_response = requests.get(css_url, headers=headers, timeout=10)
        css_content = css_response.text
        
        # Ищем @font-face
        font_faces = re.findall(r'@font-face\s*{[^}]+}', css_content, re.DOTALL)
        if font_faces:
            print(f"    ✅ Найдено @font-face: {len(font_faces)}")
            for ff in font_faces[:2]:
                # Извлекаем font-family и src
                family = re.search(r"font-family\s*:\s*['\"]?([^'\";]+)['\"]?", ff)
                src = re.search(r"url\(['\"]?([^)'\"]+\.(woff2?|ttf))['\"]?\)", ff)
                if family:
                    print(f"       • Family: {family.group(1).strip()}")
                if src:
                    print(f"       • Src: {src.group(1).strip()[:60]}...")
        else:
            print(f"    ⚪ Нет @font-face")
            
        # Ищем font-family вообще
        all_fonts = re.findall(r'font-family\s*:\s*[^;};]+', css_content, re.IGNORECASE)
        if all_fonts:
            unique_fonts = list(set(f.strip() for f in all_fonts))[:5]
            print(f"    🎨 font-family: {unique_fonts}")
            
    except Exception as e:
        print(f"    ❌ Ошибка: {e}")
    
    print()

print("=" * 70)
print("✅ RAW DEBUG ЗАВЕРШЕН")
print("=" * 70)