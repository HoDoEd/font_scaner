from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FontEthalon(Base):
    """База эталонов (белая база Google Fonts)"""
    __tablename__ = "font_ethalons"
    
    id = Column(Integer, primary_key=True, index=True)
    font_family = Column(String(255), nullable=False, index=True)
    font_variant = Column(String(100))
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    source_url = Column(Text)
    license_type = Column(String(100), default="OFL")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScanResult(Base):
    """Результаты сканирования"""
    __tablename__ = "scan_results"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_url = Column(String(500), nullable=False)
    font_url = Column(Text)
    font_name = Column(String(255))
    file_hash = Column(String(64), index=True)
    status = Column(String(50), nullable=False)  # OK, WARNING, SYSTEM, ERROR
    matched_font = Column(String(255))
    license_info = Column(String(500))
    scanned_at = Column(DateTime, default=datetime.utcnow)