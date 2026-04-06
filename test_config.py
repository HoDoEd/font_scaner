from app.config import Config

Config.print_config()

print(f"\n✅ Production режим: {Config.is_production()}")
print(f"✅ Development режим: {Config.is_development()}")
print(f"✅ Тип БД: {Config.get_database_type()}")