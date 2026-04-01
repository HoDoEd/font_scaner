#!/usr/bin/env python3
"""
Скрипт для обновления базы эталонов Google Fonts
Запускать раз в месяц: python scripts/update_font_db.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import hashlib
from app.database.db_manager import init_db, get_db, add_ethalon, FontEthalon
from app.config import Config
from sqlalchemy.orm import Session

def download_google_font(url: str) -> bytes:
    """Скачать файл шрифта"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except:
        return None

def update_font_database():
    """Обновить базу эталонов"""
    print("🔄 Начало обновления базы Google Fonts...")
    
    # Инициализация БД
    init_db()
    db = next(get_db())
    
    # Получаем список шрифтов из Google Fonts API
    api_url = Config.GOOGLE_FONTS_API_URL
    params = {"key": Config.GOOGLE_FONTS_API_KEY} if Config.GOOGLE_FONTS_API_KEY else {}
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        fonts_data = response.json()
    except Exception as e:
        print(f"❌ Ошибка получения списка шрифтов: {e}")
        print("💡 Попробуйте получить API ключ: https://developers.google.com/fonts/docs/developer_api")
        return
    
    fonts = fonts_data.get("items", [])
    print(f"📦 Найдено шрифтов: {len(fonts)}")
    
    updated_count = 0
    error_count = 0
    
    for font in fonts:
        font_family = font.get("family", "Unknown")
        variants = font.get("variants", [])
        font_files = font.get("files", {})
        
        for variant in variants:
            if variant in font_files:
                font_url = font_files[variant]
                
                # Скачиваем шрифт
                font_data = download_google_font(font_url)
                if not font_data:
                    error_count += 1
                    continue
                
                # Считаем хеш
                file_hash = hashlib.sha256(font_data).hexdigest()
                
                # Проверяем, есть ли уже в базе
                existing = db.query(FontEthalon).filter(
                    FontEthalon.file_hash == file_hash
                ).first()
                
                if not existing:
                    # Добавляем новый эталон
                    add_ethalon(
                        db=db,
                        font_family=font_family,
                        font_variant=variant,
                        file_hash=file_hash,
                        source_url=font_url,
                        license_type=font.get("license", "OFL")
                    )
                    updated_count += 1
                    print(f"✅ Добавлен: {font_family} ({variant})")
                
                # Очищаем память
                del font_data
    
    db.close()
    
    print(f"\n📊 Итоги:")
    print(f"   Добавлено эталонов: {updated_count}")
    print(f"   Ошибок: {error_count}")
    print(f"✅ Обновление завершено!")

if __name__ == "__main__":
    update_font_database()