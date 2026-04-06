#!/usr/bin/env python3
"""Диагностика: почему шрифты не находятся"""

from app.database.db_manager import get_db
from app.database.models import FontEthalon

db = next(get_db())

# Тестируемые шрифты
test_fonts = [
    "pt-root",
    "TildaSans", 
    "Pythonicon",
    "Flux",
    "Unbounded"
]

print("🔍 Поиск шрифтов в базе:\n")

for font_name in test_fonts:
    print(f"📄 {font_name}:")
    
    # Ищем по подстроке
    matches = db.query(FontEthalon).filter(
        FontEthalon.font_family.ilike(f"%{font_name}%")
    ).limit(3).all()
    
    if matches:
        print(f"   ✅ Найдено {len(matches)} совпадений:")
        for m in matches:
            print(f"      • {m.font_family} ({m.font_variant}) - {m.license_type}")
    else:
        print(f"   ❌ Не найден в базе")
    
    print()

# Статистика
total = db.query(FontEthalon).count()
print(f"📊 Всего в базе: {total} эталонов")

db.close()