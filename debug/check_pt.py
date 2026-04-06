import requests
import hashlib
from app.database.db_manager import get_db
from app.database.models import FontEthalon

url = "https://static.gismeteo.st/assets/fonts/pt-root-ui.woff"
print(f"📥 Скачиваем: {url}")

response = requests.get(url, timeout=30)
font_data = response.content

file_hash = hashlib.sha256(font_data).hexdigest()
print(f"🔐 Хеш: {file_hash}")

db = next(get_db())

# Ищем по хешу
ethalon = db.query(FontEthalon).filter(FontEthalon.file_hash == file_hash).first()
if ethalon:
    print(f"✅ НАЙДЕН: {ethalon.font_family} ({ethalon.font_variant})")
else:
    print("❌ Не найден по хешу")
    
    # Ищем по имени
    matches = db.query(FontEthalon).filter(
        FontEthalon.font_family.ilike("%pt%root%")
    ).all()
    
    if matches:
        print(f"\n📚 Похожи в базе ({len(matches)}):")
        for m in matches[:5]:
            print(f"   • {m.font_family} ({m.font_variant})")
    else:
        print("\n❌ PT Fonts вообще нет в базе!")

db.close()