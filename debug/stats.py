from app.database.db_manager import get_db
from app.database.models import FontEthalon
from sqlalchemy import func

db = next(get_db())

# Общее количество
total = db.query(FontEthalon).count()

# Уникальных семейств
families = db.query(FontEthalon.font_family).distinct().count()

# Топ-10 семейств по количеству вариантов
top_fonts = db.query(
    FontEthalon.font_family, 
    func.count(FontEthalon.id).label('count')
).group_by(FontEthalon.font_family).order_by(func.count(FontEthalon.id).desc()).limit(10).all()

# Типы лицензий
licenses = db.query(
    FontEthalon.license_type, 
    func.count(FontEthalon.id).label('count')
).group_by(FontEthalon.license_type).all()

print(f"📊 Статистика базы шрифтов:")
print(f"   ═════════════════════════════")
print(f"   Всего эталонов: {total}")
print(f"   Уникальных семейств: {families}")
print(f"\n🏆 Топ-10 шрифтов по количеству вариантов:")
for font, count in top_fonts:
    print(f"   • {font}: {count} вариантов")

print(f"\n📜 Типы лицензий:")
for lic, count in licenses:
    print(f"   • {lic}: {count}")

db.close()