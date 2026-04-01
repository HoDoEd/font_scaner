import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # База данных
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fonts.db")
    
    # Настройки сканера
    MAX_FONTS_PER_SITE = int(os.getenv("MAX_FONTS_PER_SITE", "20"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
    USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Google Fonts
    GOOGLE_FONTS_API_URL = "https://www.googleapis.com/webfonts/v1/webfonts"
    GOOGLE_FONTS_API_KEY = os.getenv("GOOGLE_FONTS_API_KEY", "")  # Опционально
    
    # Пути
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_UPDATE_INTERVAL_DAYS = 30