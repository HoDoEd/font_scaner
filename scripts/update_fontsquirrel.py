#!/usr/bin/env python3
"""
Парсим FontSquirrel.com - бесплатные шрифты для коммерческого использования
"""

import os
import sys
import hashlib
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.db_manager import get_db, add_ethalon, FontEthalon

def get_font_list() -> list:
    """Получаем список страниц со шрифтами"""
    
    base_url = "https://www.fontsquirrel.com/fonts/list/popular"
    
    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        fonts = []
        
        # Ищем ссылки на страницы шрифтов
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/fonts/' in href and href not in fonts:
                full_url = f"https://www.fontsquirrel.com{href}"
                fonts.append(full_url)
        
        return fonts[:50]  # Первые 50 для теста
        
    except Exception as e:
        print(f"❌ Ошибка получения списка: {e}")
        return []

def get_font_details(url: str) -> dict | None:
    """Получаем информацию о шрифте"""
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Название
        name_elem = soup.find('h1', class_='pagetitle')
        name = name_elem.text.strip() if name_elem else "Unknown"
        
        # Лицензия
        license_elem = soup.find('div', string=lambda text: text and 'license' in text.lower())
        license_text = license_elem.text.strip() if license_elem else "Free for commercial use"
        
        # Ссылка на скачивание
        download_link = soup.find('a', class_='download-button')
        if not download_link:
            download_link = soup.find('a', href=lambda href: href and 'download' in href.lower())
        
        download_url = None
        if download_link:
            download_url = download_link.get('href', '')
            if not download_url.startswith('http'):
                download_url = f"https://www.fontsquirrel.com{download_url}"
        
        return {
            "name": name,
            "license": license_text,
            "download_url": download_url,
            "source_url": url
        }
        
    except Exception as e:
        print(f"   ⚠️  Ошибка: {e}")
        return None

def download_font(url: str) -> bytes | None:
    """Скачиваем файл шрифта"""
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.content
    except:
        return None

def update_fontsquirrel():
    """Основная функция"""
    
    print("=" * 70)
    print("🔄 Обновление базы шрифтов из FontSquirrel")
    print("=" * 70)
    
    # Инициализация БД
    from app.database.db_manager import init_db
    init_db()
    db = next(get_db())
    
    # Получаем список
    font_urls = get_font_list()
    
    if not font_urls:
        print("❌ Шрифты не найдены")
        return
    
    print(f"📦 Найдено {len(font_urls)} шрифтов для проверки\n")
    
    added = 0
    skipped = 0
    errors = 0
    
    for i, url in enumerate(font_urls, 1):
        print(f"[{i}/{len(font_urls)}] {url}")
        
        # Получаем информацию
        details = get_font_details(url)
        
        if not details or not details['download_url']:
            print("   ⏭️  Пропущено (нет ссылки на скачивание)")
            skipped += 1
            continue
        
        print(f"   Шрифт: {details['name']}")
        
        # Скачиваем
        font_data = download_font(details['download_url'])
        
        if not font_data:
            print("   ❌ Не удалось скачать")
            errors += 1
            continue
        
        # Считаем хеш
        file_hash = hashlib.sha256(font_data).hexdigest()
        
        # Проверяем дубликаты
        existing = db.query(FontEthalon).filter(
            FontEthalon.file_hash == file_hash
        ).first()
        
        if existing:
            print(f"   ⏭️  Уже в базе: {existing.font_family}")
            skipped += 1
            continue
        
        # Добавляем
        try:
            add_ethalon(
                db=db,
                font_family=details['name'],
                font_variant="regular",
                file_hash=file_hash,
                source_url=details['source_url'],
                license_type="Free (FontSquirrel)"
            )
            print(f"   ✅ Добавлен")
            added += 1
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            errors += 1
        
        # Пауза
        time.sleep(2)
    
    db.close()
    
    print("\n" + "=" * 70)
    print("📊 Итоги:")
    print(f"   Добавлено: {added}")
    print(f"   Пропущено: {skipped}")
    print(f"   Ошибок: {errors}")
    print("=" * 70)

if __name__ == "__main__":
    update_fontsquirrel()