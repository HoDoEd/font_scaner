#!/usr/bin/env python3
"""
Скачиваем шрифты с лицензией OFL из GitHub репозиториев
Исправленная версия: работает с ограничениями GitHub Code Search API
"""

import os
import sys
import hashlib
import time
import requests
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.db_manager import get_db, add_ethalon, FontEthalon

# GitHub API
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

# Известные репозитории со свободными шрифтами (curated list)
# Это надёжнее чем поиск по всему GitHub
KNOWN_FONT_REPOS = [
    "google/fonts",
    "fontsource/font-files",
    "catppuccin/fonts",
    "ryanoasis/nerd-fonts",
    "adobe-fonts/source-sans",
    "adobe-fonts/source-serif",
    "adobe-fonts/source-code-pro",
    "googlefonts/roboto",
    "googlefonts/opensans",
    "googlefonts/montserrat",
    "googlefonts/lato",
    "googlefonts/inter",
    "googlefonts/noto-fonts",
    "cyrealtype/Comfortaa",
    "cyrealtype/Cormorant",
    "alexeiva/alegreya",
    "impallari/Montserrat",
    "vernnobile/Lato",
    "weiweihuanghuang/Work-Sans",
    "mckayla/inter",
    "rsms/inter",
]

def get_github_token():
    """Безопасно получаем токен из .env"""
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        print("⚠️  GITHUB_TOKEN не найден в .env")
        print("   Без токена лимит: 60 запросов/час")
        print("   С токеном: 5000 запросов/час")
        print("   Получить: https://github.com/settings/tokens")
    return token

def get_repo_contents(repo: str, path: str, token: str = "") -> list:
    """Получаем содержимое папки в репозитории"""
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FontScanner/1.0"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(
            f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 404:
            return []
        
        if response.status_code == 403:
            print(f"   ⚠️  Лимит API для {repo}")
            return []
        
        response.raise_for_status()
        data = response.json()
        
        # Если это файл, а не список
        if isinstance(data, dict):
            return [data]
        
        return data
        
    except Exception as e:
        print(f"   ⚠️  Ошибка получения {repo}/{path}: {e}")
        return []

def find_font_files_in_repo(repo: str, token: str = "") -> list:
    """Рекурсивно ищем файлы шрифтов в репозитории"""
    
    font_extensions = ('.woff2', '.woff', '.ttf', '.otf')
    fonts_found = []
    
    # Начинаем с корня и популярных папок
    paths_to_check = ['', 'fonts', 'font', 'static', 'web', 'dist', 'build']
    
    for base_path in paths_to_check:
        contents = get_repo_contents(repo, base_path, token)
        
        for item in contents:
            if item.get('type') == 'file' and item.get('name', '').lower().endswith(font_extensions):
                # Нашли файл шрифта
                fonts_found.append({
                    'repo': repo,
                    'path': item.get('path', ''),
                    'url': item.get('download_url', ''),
                    'size': item.get('size', 0)
                })
            elif item.get('type') == 'dir':
                # Рекурсивно проверяем подпапки (но не слишком глубоко)
                sub_path = item.get('path', '')
                if sub_path.count('/') < 3:  # Не лезем глубже 3 уровней
                    sub_contents = get_repo_contents(repo, sub_path, token)
                    for sub_item in sub_contents:
                        if sub_item.get('type') == 'file' and sub_item.get('name', '').lower().endswith(font_extensions):
                            fonts_found.append({
                                'repo': repo,
                                'path': sub_item.get('path', ''),
                                'url': sub_item.get('download_url', ''),
                                'size': sub_item.get('size', 0)
                            })
        
        time.sleep(0.3)  # Не спамим API
    
    return fonts_found

def download_and_hash(url: str, token: str = "") -> tuple:
    """Скачиваем файл и считаем хеш"""
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            file_hash = hashlib.sha256(response.content).hexdigest()
            size = len(response.content)
            return file_hash, size
    except:
        pass
    
    return None, None

def extract_font_name(path: str) -> str:
    """Извлекаем название шрифта из пути"""
    filename = Path(path).stem
    # Убираем технические суффиксы
    name = filename.replace('.woff2', '').replace('.ttf', '').replace('.woff', '').replace('.otf', '')
    name = name.replace('-', ' ').replace('_', ' ')
    # Убираем лишние слова
    for word in ['VF', 'Variable', 'Regular', 'Bold', 'Italic', 'Light', 'Medium', 'Thin', 'Black', 'UI', 'Text', 'Display']:
        name = name.replace(word, '')
    return ' '.join(word for word in name.split() if word).strip().title()

def update_github_fonts():
    """Основная функция обновления"""
    
    print("=" * 70)
    print("🔄 Обновление базы шрифтов из GitHub (OFL)")
    print("=" * 70)
    
    # Получаем токен
    token = get_github_token()
    
    # Инициализация БД
    from app.database.db_manager import init_db
    init_db()
    db = next(get_db())
    
    print(f"📦 Проверка {len(KNOWN_FONT_REPOS)} известных репозиториев...\n")
    
    # Скачивание и добавление в базу
    added = 0
    skipped = 0
    errors = 0
    
    for i, repo in enumerate(KNOWN_FONT_REPOS, 1):
        print(f"[{i}/{len(KNOWN_FONT_REPOS)}] 📁 {repo}")
        
        # Ищем шрифты в репозитории
        fonts = find_font_files_in_repo(repo, token)
        
        if not fonts:
            print("   ⏭️  Шрифты не найдены или репозиторий недоступен")
            continue
        
        print(f"   Найдено файлов: {len(fonts)}")
        
        for font_info in fonts:
            # Пропускаем если URL нет
            if not font_info.get('url'):
                continue
            
            # Скачиваем
            file_hash, size = download_and_hash(font_info['url'], token)
            
            if not file_hash:
                continue
            
            # Проверяем дубликаты
            existing = db.query(FontEthalon).filter(
                FontEthalon.file_hash == file_hash
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Добавляем в базу
            font_name = extract_font_name(font_info['path'])
            
            try:
                add_ethalon(
                    db=db,
                    font_family=font_name if font_name else Path(font_info['path']).stem,
                    font_variant="regular",
                    file_hash=file_hash,
                    source_url=font_info['url'],
                    license_type="OFL (GitHub)"
                )
                added += 1
                
            except Exception as e:
                errors += 1
        
        # Пауза между репозиториями
        time.sleep(1)
    
    # Итоги
    db.close()
    
    print("\n" + "=" * 70)
    print("📊 Итоги:")
    print(f"   Добавлено: {added}")
    print(f"   Пропущено (дубликаты): {skipped}")
    print(f"   Ошибок: {errors}")
    print("=" * 70)

if __name__ == "__main__":
    update_github_fonts()