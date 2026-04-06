from .crawler import FontCrawler
from .hash_calculator import calculate_font_hash
from app.database.db_manager import find_ethalon_by_hash, get_db
from app.database.models import FontEthalon
from app.config import Config
from urllib.parse import unquote
import re


class FontAnalyzer:
    def __init__(self, db_session):
        self.crawler = FontCrawler()
        self.db = db_session
    
    def _normalize_font_name(self, name: str) -> str:
        """Нормализует имя шрифта"""
        return re.sub(r'[\s\-_]', '', name).lower()
    
    def _fuzzy_match_font(self, font_url: str, font_name: str) -> dict | None:
        """Эвристическое сравнение по имени"""
        normalized_search = self._normalize_font_name(font_name)
        if not normalized_search or len(normalized_search) < 3:
            return None
        
        all_fonts = self.db.query(FontEthalon).distinct(FontEthalon.font_family).all()
        best_match = None
        best_score = 0
        
        for font in all_fonts:
            normalized_db = self._normalize_font_name(font.font_family)
            score = 0
            
            if normalized_db == normalized_search:
                score = 100
            elif normalized_search in normalized_db or normalized_db in normalized_search:
                score = 80
            elif normalized_search.replace(' ', '') == normalized_db.replace(' ', ''):
                score = 90
            elif len(normalized_search) >= 4 and len(normalized_db) >= 4:
                if normalized_search.startswith(normalized_db[:4]) or normalized_db.startswith(normalized_search[:4]):
                    score = 60
            
            if score > best_score:
                best_score = score
                best_match = font
        
        if best_match and best_score >= 50:
            return {"font_family": best_match.font_family, "license_type": best_match.license_type}
        return None
    
    def analyze_font(self, font_url: str, scan_url: str, font_name: str = "Неизвестный") -> dict:
        """Анализ одного шрифта"""
        result = {
            "url": font_url,
            "status": "UNKNOWN",
            "matched_font": None,
            "license_info": None,
            "hash": None,
            "error": None,
            "match_method": None
        }
        
        # Если есть URL — скачиваем и проверяем по хешу
        if font_url:
            try:
                font_data = self.crawler.download_font(font_url)
                hash_info = calculate_font_hash(font_data)
                result["hash"] = hash_info["sha256"]
                
                ethalon = find_ethalon_by_hash(self.db, hash_info["sha256"])
                if ethalon:
                    result["status"] = "OK"
                    result["matched_font"] = f"{ethalon.font_family} ({ethalon.font_variant})"
                    result["license_info"] = ethalon.license_type
                    result["match_method"] = "hash"
                    del font_data
                    return result
                del font_data
            except:
                pass  # Если не скачался — пробуем по имени
        
        # Fuzzy-поиск по имени (работает и с файлами, и без)
        fuzzy_match = self._fuzzy_match_font(font_url or "", font_name)
        
        if fuzzy_match:
            result["status"] = "OK"
            result["matched_font"] = f"{fuzzy_match['font_family']}"
            result["license_info"] = f"{fuzzy_match['license_type']}"
            result["match_method"] = "fuzzy"
        else:
            result["status"] = "WARNING"
            result["matched_font"] = font_name if font_name != "Неизвестный" else None
            result["license_info"] = "Неизвестная лицензия"
            result["match_method"] = None
        
        return result
    
    def analyze_system_font(self, font_name: str, scan_url: str) -> dict:
        """Анализ системного шрифта"""
        return {
            "url": "system",
            "status": "SYSTEM",
            "matched_font": font_name,
            "license_info": "Системный шрифт (легально)",
            "hash": None,
            "error": None
        }
    
    def scan_site(self, url: str) -> dict:
        """Полное сканирование сайта с дедупликацией"""
        crawl_result = self.crawler.scan_site(url)
        fonts_analysis = []
        
        # 1. Анализируем файлы шрифтов (с URL и без)
        for font_info in crawl_result["font_files"]:
            analysis = self.analyze_font(
                font_info["url"], 
                url,
                font_info.get("name", "Неизвестный")
            )
            analysis["source"] = font_info.get("source_css", "unknown")
            fonts_analysis.append(analysis)
        
        # 2. Google Fonts из ссылок
        for gf_info in crawl_result.get("google_fonts_names", []):
            font_name = gf_info.get("name", "")
            if not font_name:
                continue
            
            already_added = any(
                f.get("matched_font", "").lower() == font_name.lower()
                for f in fonts_analysis
            )
            
            if not already_added:
                fuzzy_match = self._fuzzy_match_font(
                    f"https://fonts.googleapis.com/css2?family={font_name}", 
                    font_name
                )
                
                if fuzzy_match:
                    fonts_analysis.append({
                        "url": f"https://fonts.google.com/specimen/{font_name.replace(' ', '+')}",
                        "status": "OK",
                        "matched_font": f"{fuzzy_match['font_family']}",
                        "license_info": f"{fuzzy_match['license_type']}",
                        "hash": None, "error": None, "match_method": "fuzzy",
                        "source": "google_fonts_link"
                    })
                else:
                    fonts_analysis.append({
                        "url": f"https://fonts.google.com/specimen/{font_name.replace(' ', '+')}",
                        "status": "WARNING",
                        "matched_font": font_name,
                        "license_info": "Unknown License",
                        "hash": None, "error": None, "match_method": None,
                        "source": "google_fonts_link"
                    })
        
        # 3. Системные шрифты
        for sys_font in crawl_result["system_fonts"]:
            analysis = self.analyze_system_font(sys_font, url)
            fonts_analysis.append(analysis)
			
        # 4. 🎯 ДЕДУПЛИКАЦИЯ: убираем повторяющиеся шрифты
        seen_fonts = set()
        unique_fonts = []
    
        for font in fonts_analysis:
            # Нормализуем имя для сравнения
            font_name = font.get('matched_font', '').lower().strip()
        
            # Пропускаем если уже видели это имя
            if font_name and font_name in seen_fonts:
                continue
        
            seen_fonts.add(font_name)
            unique_fonts.append(font)
		
        # 5. Возвращаем только уникальные шрифты
        return {
            "scan_url": url,
            "fonts": unique_fonts,
            "errors": crawl_result["errors"],
            "total_fonts": len(unique_fonts)
        }