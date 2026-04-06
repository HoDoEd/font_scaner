#!/usr/bin/env python3
"""Детальная отладка сканирования piccheck.ru"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.scanner.crawler import FontCrawler
from app.database.db_manager import get_db, init_db
from app.scanner.font_analyzer import FontAnalyzer

url = "https://piccheck.ru"
print(f"🔍 Глубокая отладка: {url}\n")

# 1. Запускаем crawler
print("=" * 70)
print("1️⃣  CRAWLER")
print("=" * 70)

crawler = FontCrawler()
crawl_result = crawler.scan_site(url)

print(f"✅ HTML загружен")
print(f"📦 Найдено файлов шрифтов: {len(crawl_result['font_files'])}")
print(f"🔗 Найдено Google Fonts ссылок: {len(crawl_result.get('google_fonts_names', []))}")
print(f"ℹ️  Системных шрифтов: {len(crawl_result['system_fonts'])}")

if crawl_result['font_files']:
    print("\n📝 Файлы шрифтов:")
    for font in crawl_result['font_files']:
        print(f"   • URL: {font['url']}")
        print(f"     Имя: {font.get('name', 'N/A')}")
        print(f"     Источник: {font.get('source_css', 'N/A')}")

if crawl_result.get('google_fonts_names'):
    print("\n📝 Google Fonts из ссылок:")
    for gf in crawl_result['google_fonts_names']:
        print(f"   • {gf.get('name', 'N/A')}")

if crawl_result['system_fonts']:
    print("\n📝 Системные шрифты:")
    for font in crawl_result['system_fonts']:
        print(f"   • {font}")

# 2. Запускаем analyzer
print("\n" + "=" * 70)
print("2️⃣  ANALYZER")
print("=" * 70)

init_db()
db = next(get_db())
analyzer = FontAnalyzer(db)

analysis_result = analyzer.scan_site(url)

print(f"\n📊 Итоговый результат:")
print(f"   Всего шрифтов: {analysis_result['total_fonts']}")
print(f"   Ошибок: {len(analysis_result['errors'])}")

if analysis_result['fonts']:
    print(f"\n📝 Проанализированные шрифты:")
    for i, font in enumerate(analysis_result['fonts'], 1):
        print(f"\n   [{i}] {font.get('matched_font', 'Неизвестный')}")
        print(f"       Статус: {font.get('status', 'N/A')}")
        print(f"       Лицензия: {font.get('license_info', 'N/A')}")
        print(f"       Метод: {font.get('match_method', 'N/A')}")
        print(f"       Источник: {font.get('source', 'N/A')}")
else:
    print("\n⚠️  Шрифты НЕ найдены в анализе!")

if analysis_result['errors']:
    print(f"\n❌ Ошибки:")
    for error in analysis_result['errors']:
        print(f"   • {error}")

db.close()

print("\n" + "=" * 70)
print("✅ Отладка завершена")
print("=" * 70)