import os
from pathlib import Path


class Config:
    """
    Конфигурация приложения
    
    Поддерживает переменные окружения для production
    """
    
    # Базовая директория проекта
    BASE_DIR = Path(__file__).parent.parent
    
    # ===========================================
    # БАЗА ДАННЫХ
    # ===========================================
    # Для production использовать PostgreSQL
    # Пример: postgresql://user:pass@host:5432/dbname
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR}/fonts.db"
    )
    
    # ===========================================
    # ТАЙМАУТЫ И ЛИМИТЫ
    # ===========================================
    # Таймаут запросов к сайтам (секунды)
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Максимум шрифтов на сайт
    MAX_FONTS_PER_SITE = int(os.getenv("MAX_FONTS_PER_SITE", "50"))
    
    # Таймаут скачивания шрифта
    FONT_DOWNLOAD_TIMEOUT = int(os.getenv("FONT_DOWNLOAD_TIMEOUT", "60"))
    
    # ===========================================
    # СЕТЕВЫЕ НАСТРОЙКИ
    # ===========================================
    # User Agent для запросов
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # ===========================================
    # РЕЖИМ РАБОТЫ
    # ===========================================
    # Отладочный режим (True для разработки, False для production)
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Хост и порт для uvicorn
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # ===========================================
    # БЕЗОПАСНОСТЬ
    # ===========================================
    # GitHub токен для API (опционально, увеличивает лимиты)
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    
    # Google Fonts API ключ (опционально)
    GOOGLE_FONTS_API_KEY = os.getenv("GOOGLE_FONTS_API_KEY", "")
    
    # ===========================================
    # КЭШИРОВАНИЕ
    # ===========================================
    # Включить кэширование результатов
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "False").lower() == "true"
    
    # Время жизни кэша (секунды)
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    
    # ===========================================
    # ЛОГИРОВАНИЕ
    # ===========================================
    # Уровень логирования
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # ===========================================
    # ПУТИ К ФАЙЛАМ
    # ===========================================
    # Директория для шаблонов
    TEMPLATES_DIR = BASE_DIR / "app" / "templates"
    
    # Директория для статики
    STATIC_DIR = BASE_DIR / "app" / "static"
    
    # Директория для скриптов
    SCRIPTS_DIR = BASE_DIR / "scripts"
    
    # ===========================================
    # Методы для проверки конфигурации
    # ===========================================
    
    @classmethod
    def is_production(cls) -> bool:
        """Проверяет, запущено ли приложение в production"""
        return not cls.DEBUG
    
    @classmethod
    def is_development(cls) -> bool:
        """Проверяет, запущено ли приложение в development"""
        return cls.DEBUG
    
    @classmethod
    def get_database_type(cls) -> str:
        """Возвращает тип базы данных (sqlite, postgresql, mysql)"""
        if cls.DATABASE_URL.startswith("sqlite"):
            return "sqlite"
        elif cls.DATABASE_URL.startswith("postgresql"):
            return "postgresql"
        elif cls.DATABASE_URL.startswith("mysql"):
            return "mysql"
        else:
            return "unknown"
    
    @classmethod
    def print_config(cls):
        """Выводит текущую конфигурацию (для отладки)"""
        print("=" * 60)
        print("📋 FONT SCANNER CONFIGURATION")
        print("=" * 60)
        print(f" BASE_DIR: {cls.BASE_DIR}")
        print(f"🗄️  DATABASE_URL: {cls.DATABASE_URL}")
        print(f"🗄️  DATABASE_TYPE: {cls.get_database_type()}")
        print(f"⏱️  REQUEST_TIMEOUT: {cls.REQUEST_TIMEOUT}s")
        print(f"📦 MAX_FONTS_PER_SITE: {cls.MAX_FONTS_PER_SITE}")
        print(f"🔧 DEBUG: {cls.DEBUG}")
        print(f"🌐 HOST: {cls.HOST}")
        print(f"🔌 PORT: {cls.PORT}")
        print(f"🔐 GITHUB_TOKEN: {'✗' if cls.GITHUB_TOKEN else '✗ (не установлен)'}")
        print(f"💾 ENABLE_CACHE: {cls.ENABLE_CACHE}")
        print(f"📝 LOG_LEVEL: {cls.LOG_LEVEL}")
        print("=" * 60)


# ===========================================
# Инициализация конфигурации
# ===========================================

# Для отладки: раскомментируй чтобы видеть конфиг при старте
# Config.print_config()