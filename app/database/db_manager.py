from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, FontEthalon, ScanResult
from app.config import Config

engine = create_engine(
    Config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in Config.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Генератор сессий БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_ethalon(db, font_family, font_variant, file_hash, source_url, license_type="OFL"):
    """Добавить эталон в базу"""
    ethalon = FontEthalon(
        font_family=font_family,
        font_variant=font_variant,
        file_hash=file_hash,
        source_url=source_url,
        license_type=license_type
    )
    db.add(ethalon)
    db.commit()
    return ethalon

def find_ethalon_by_hash(db, file_hash):
    """Найти эталон по хешу"""
    return db.query(FontEthalon).filter(FontEthalon.file_hash == file_hash).first()

def add_scan_result(db, scan_url, font_url, font_name, file_hash, status, matched_font=None, license_info=None):
    """Добавить результат сканирования"""
    result = ScanResult(
        scan_url=scan_url,
        font_url=font_url,
        font_name=font_name,
        file_hash=file_hash,
        status=status,
        matched_font=matched_font,
        license_info=license_info
    )
    db.add(result)
    db.commit()
    return result