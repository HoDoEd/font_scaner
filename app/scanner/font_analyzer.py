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
        """Нормализует имя шрифта: убирает пробелы, дефисы, приводит к нижнему регистру"""
        return re.sub(r'[\s\-_]', '', name).lower()
    
    def _fuzzy_match_font(self, font_url: str, font_name: str) -> dict | None:
        """
        Эвристическое сравнение: ищет шрифт по имени файла/URL
        Возвращает {'font_family', 'license_type'} или None
        """
        # Извлекаем "чистое" имя из URL
        filename = unquote(font_url.split('/')[-1].split('?')[0])
        
        # Убираем хеши и технические суффиксы
        clean_name = re.sub(r'\.(woff2?|ttf|otf|eot)$', '', filename, flags=re.IGNORECASE)
        clean_name = re.sub(r'-[a-f0-9]{8,}', '', clean_name)  # убираем хеши
        clean_name = re.sub(r'-?(VF|Variable|wdth|wght|opsz|ital)[-_]?[a-zA-Z0-9.]*', '', clean_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'[-_]', ' ', clean_name).strip()
        
        # Нормализуем имя для поиска (убираем пробелы)
        normalized_search = self._normalize_font_name(clean_name)
        
        if not normalized_search or len(normalized_search) < 3:
            return None
        
        # Получаем все шрифты из базы и ищем совпадения
        # (в идеале нужно оптимизировать, но для MVP сойдёт)
        all_fonts = self.db.query(FontEthalon).distinct(FontEthalon.font_family).all()
        
        best_match = None
        best_score = 0
        
        for font in all_fonts:
            # Нормализуем название из базы
            normalized_db = self._normalize_font_name(font.font_family)
            
            # Проверяем различные варианты совпадения
            score = 0
            
            # 1. Точное совпадение нормализованных имён
            if normalized_db == normalized_search:
                score = 100
            # 2. Одно содержит другое
            elif normalized_search in normalized_db or normalized_db in normalized_search:
                score = 80
            # 3. Похожее написание (например, MonaSans и Mona Sans)
            elif normalized_search.replace(' ', '') == normalized_db.replace(' ', ''):
                score = 90
            # 4. Частичное совпадение (минимум 4 символа)
            elif len(normalized_search) >= 4 and len(normalized_db) >= 4:
                # Проверяем, начинается ли одно с другого
                if normalized_search.startswith(normalized_db[:4]) or normalized_db.startswith(normalized_search[:4]):
                    score = 60
            
            # Если нашли хорошее совпадение
            if score > best_score:
                best_score = score
                best_match = font
        
        # Возвращаем, если нашли с уверенностью > 50%
        if best_match and best_score >= 50:
            return {
                "font_family": best_match.font_family,
                "license_type": best_match.license_type
            }
        
        return None
    
    def analyze_font(self, font_url: str, scan_url: str, font_name: str = "Неизвестный") -> dict:
        """Анализ одного шрифта с эвристическим сравнением"""
        result = {
            "url": font_url,
            "status": "UNKNOWN",
            "matched_font": None,
            "license_info": None,
            "hash": None,
            "error": None,
            "match_method": None  # "hash" или "fuzzy"
        }
        
        try:
            # Скачиваем шрифт
            font_data = self.crawler.download_font(font_url)
            
            # Считаем хеш
            hash_info = calculate_font_hash(font_data)
            result["hash"] = hash_info["sha256"]
            
            # 1. Пробуем точное совпадение по хешу
            ethalon = find_ethalon_by_hash(self.db, hash_info["sha256"])
            
            if ethalon:
                result["status"] = "OK"
                result["matched_font"] = f"{ethalon.font_family} ({ethalon.font_variant})"
                result["license_info"] = ethalon.license_type
                result["match_method"] = "hash"
            else:
                # 2. Fuzzy-поиск по названию файла
                fuzzy_match = self._fuzzy_match_font(font_url, font_name)
                
                if fuzzy_match:
                    result["status"] = "OK"  # Считаем безопасным, но с пометкой
                    result["matched_font"] = f"{fuzzy_match['font_family']} (по имени)"
                    result["license_info"] = f"{fuzzy_match['license_type']} ⚠️ эвристика"
                    result["match_method"] = "fuzzy"
                else:
                    result["status"] = "WARNING"
                    result["matched_font"] = None
                    result["license_info"] = "Неизвестная лицензия"
                    result["match_method"] = None
            
            # Если имя не найдено в базе, используем переданное (для отображения)
            if not result["matched_font"] and font_name and font_name != "Неизвестный":
                result["matched_font"] = font_name
            
            # Очищаем память
            del font_data
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
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
        """Полное сканирование сайта"""
        # Получаем данные от краулера
        crawl_result = self.crawler.scan_site(url)
        
        # Анализируем каждый шрифт
        fonts_analysis = []
        
        for font_info in crawl_result["font_files"]:
            analysis = self.analyze_font(
                font_info["url"], 
                url,
                font_info.get("name", "Неизвестный")
            )
            analysis["source"] = font_info.get("source_css", "unknown")
            fonts_analysis.append(analysis)
        
        # Анализируем системные шрифты
        for sys_font in crawl_result["system_fonts"]:
            analysis = self.analyze_system_font(sys_font, url)
            fonts_analysis.append(analysis)
        
        return {
            "scan_url": url,
            "fonts": fonts_analysis,
            "errors": crawl_result["errors"],
            "total_fonts": len(fonts_analysis)
        }