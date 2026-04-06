import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote, parse_qs
from app.config import Config


class FontCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": Config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        })
    
    def fetch_page(self, url: str) -> str:
        """Скачать HTML страницы"""
        try:
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"Не удалось загрузить страницу: {str(e)}")
    
    def extract_css_urls(self, html: str, base_url: str) -> list:
        """Извлечь ссылки на CSS файлы"""
        soup = BeautifulSoup(html, 'html.parser')
        css_urls = []
        
        for link in soup.find_all('link', rel=lambda x: x and 'stylesheet' in x):
            href = link.get('href')
            if href:
                css_urls.append(urljoin(base_url, href))
        
        for style in soup.find_all('style'):
            if style.string:
                imports = re.findall(r'@import\s+url\(["\']?([^"\')]+)["\']?\)', style.string)
                for imp in imports:
                    css_urls.append(urljoin(base_url, imp))
        
        return css_urls
    
    def fetch_css(self, url: str) -> str:
        """Скачать CSS файл"""
        try:
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except:
            return ""
    
    def extract_font_name_from_url(self, font_url: str) -> str:
        """Извлечь название шрифта из URL — улучшенная версия"""
        if not font_url:
            return "Неизвестный"
        
        filename = unquote(font_url.split('/')[-1].split('?')[0])
        
        # Убираем расширение
        name = re.sub(r'\.(woff2?|ttf|otf|eot)$', '', filename, flags=re.IGNORECASE)
        
        # Убираем cache-busting хеши: .cb123456, .abc123def и т.д.
        name = re.sub(r'[-_]?(var|vf|variable|regular|bold|light|medium|thin|black|demo).*$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\.[a-f0-9]{6,}$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'-[a-f0-9]{8,}$', '', name, flags=re.IGNORECASE)
		
        name = re.sub(r'\d+$', '', name)
		
        name = name.strip('-_').title()
		
        return name if name else "Неизвестный"

        
        # Собираем название: сохраняем CamelCase для имён типа MonaSans
        result = []
        for part in clean_parts:
            # Если часть уже в CamelCase (MonaSans) — оставляем как есть
            if re.match(r'^[A-Z][a-z]+[A-Z]', part):
                # Разбиваем CamelCase: MonaSans → Mona Sans
                sub_parts = re.findall(r'[A-Z][a-z]*', part)
                result.extend(sub_parts)
            else:
                # Обычное слово — капитулизируем
                result.append(part.capitalize())
        
        return ' '.join(result).strip() or "Неизвестный"
    
    def parse_google_fonts_css(self, css_content: str, base_url: str) -> list:
        """Парсит CSS от Google Fonts и извлекает ссылки на шрифты"""
        fonts = []
        font_face_pattern = r'@font-face\s*{([^}]+)}'
        font_faces = re.findall(font_face_pattern, css_content, re.DOTALL)
        
        for font_face in font_faces:
            family_match = re.search(r"font-family\s*:\s*['\"]?([^'\";]+)['\"]?", font_face, re.IGNORECASE)
            if not family_match:
                continue
            font_family = family_match.group(1).strip()
            
            src_match = re.search(r"url\(['\"]?([^)'\"]+\.(woff2?|ttf|otf))['\"]?\)", font_face, re.IGNORECASE)
            if not src_match:
                continue
            
            font_url = src_match.group(1).strip()
            if not font_url.startswith('http'):
                font_url = urljoin(base_url, font_url)
            
            fonts.append({"url": font_url, "name": font_family})
        
        return fonts
    
    def extract_fonts_from_font_family(self, css_content: str) -> list:
        """
        Извлекает названия шрифтов из font-family деклараций
        Работает с минифицированным CSS
        """
        fonts_found = []
        
        # Системные/платформенные шрифты которые НЕ нужно проверять
        system_fonts = {
            '-apple-system', 'blinkmacsystemfont', 'system-ui',
            'sans-serif', 'serif', 'monospace', 'cursive', 'fantasy',
            'ui-sans-serif', 'ui-serif', 'ui-monospace', 'ui-rounded',
            'inherit', 'initial', 'unset', 'revert', 'emoji', 'math',
            'arial', 'helvetica', 'times new roman', 'times', 'georgia',
            'verdana', 'tahoma', 'trebuchet ms', 'courier new', 'courier',
            'impact', 'comic sans ms', 'palatino', 'garamond', 'bookman',
            'avant garde', 'helvetica neue'
        }
		
		# Технические суффиксы для удаления
        tech_suffixes = ['-var', '-vf', '-variable', '-regular', '-bold', '-light', '-medium']
		
        # Ищем все вхождения font-family:
        for match in re.finditer(r'font-family\s*:\s*([^;}\n]+)', css_content, re.IGNORECASE):
            value = match.group(1).strip()
            
            # Разбиваем по запятой, корректно обрабатывая кавычки
            font_list = []
            current = ""
            in_quotes = False
            quote_char = None
            
            for char in value:
                if char in '"\'':
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                    current += char
                elif char == ',' and not in_quotes:
                    if current.strip():
                        font_list.append(current.strip().strip('"\''))
                    current = ""
                else:
                    current += char
            
            if current.strip():
                font_list.append(current.strip().strip('"\''))
            
            # Обрабатываем каждый шрифт
            for font_name in font_list:
                if not font_name or len(font_name) < 2:
                    continue
                
                # Пропускаем системные (регистронезависимо)
                if font_name.lower() in system_fonts:
                    continue
				
				# Убираем технические суффиксы (sohne-var → sohne)
                for suffix in tech_suffixes:
                    if font_name.lower().endswith(suffix):
                        font_name = font_name[:-len(suffix)]
                        font_name = re.sub(r'[-_]?(var|vf|regular|bold|light|medium).*$', '', font_name, flags=re.IGNORECASE)
                        font_name = re.sub(r'\d+$', '', font_name)  # Убираем цифры в конце
                        break
                
                # Пропускаем CSS-переменные
                if font_name.startswith('var('):
                    continue
					
				# Пропускаем слишком короткие после очистки
                if len(font_name) < 2:
                    continue
                
                # Добавляем если ещё не добавляли
                if font_name not in [f["name"] for f in fonts_found]:
                    fonts_found.append({
                        "name": font_name,
                        "source": "font_family_declaration",
                        "url": None
                    })
        
        return fonts_found
    
    def extract_font_urls(self, css_content: str, base_url: str) -> list:
        """Извлечь URL шрифтов из CSS"""
        font_urls = []
        
        # Проверка: это Google Fonts CSS?
        if 'fonts.googleapis.com' in base_url or 'fonts.gstatic.com' in base_url:
            google_fonts = self.parse_google_fonts_css(css_content, base_url)
            return google_fonts
        
        # 1. Обычный парсинг @font-face
        pattern = r'@font-face[^}]*src:[^}]*url\(["\']?([^"\')]+\.(woff2?|ttf|otf|eot))["\']?'
        matches = re.findall(pattern, css_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            font_url = match[0]
            if font_url.startswith('data:'):
                continue
            
            full_url = urljoin(base_url, font_url)
            font_name = "Неизвестный"
            
            # Ищем font-family в том же @font-face блоке
            font_face_pattern = r'@font-face\s*{([^}]+)}'
            font_faces = re.findall(font_face_pattern, css_content, re.IGNORECASE | re.DOTALL)
            
            for font_face in font_faces:
                if font_url in font_face or full_url in font_face:
                    family_match = re.search(r'font-family\s*:\s*["\']?([^"\';\}]+)["\']?', font_face, re.IGNORECASE)
                    if family_match:
                        font_name = family_match.group(1).strip().strip('"\'')
                        break
            
            if font_name == "Неизвестный":
                font_name = self.extract_font_name_from_url(full_url)
            
            font_urls.append({"url": full_url, "name": font_name})
        
        # 2. Извлекаем шрифты из font-family деклараций
        font_family_fonts = self.extract_fonts_from_font_family(css_content)
        for ff_font in font_family_fonts:
            # Добавляем только если нет дубликатов по имени
            if ff_font["name"] not in [f["name"] for f in font_urls]:
                font_urls.append(ff_font)
        
        return font_urls[:Config.MAX_FONTS_PER_SITE]
    
    def extract_google_fonts_from_link(self, href: str) -> list:
        """Извлекает названия шрифтов из ссылки Google Fonts"""
        fonts = []
        if 'fonts.googleapis.com' not in href:
            return fonts
        
        try:
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            families = params.get('family', [])
            for family_param in families:
                font_name = family_param.split(':')[0].split('+')[0].replace('+', ' ')
                if font_name:
                    fonts.append({"name": font_name, "source": "google_fonts_link"})
        except:
            pass
        return fonts
    
    def download_font(self, url: str) -> bytes:
        """Скачать файл шрифта"""
        try:
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Не удалось скачать шрифт: {str(e)}")
    
    def extract_system_fonts(self, html: str) -> list:
        """Извлечь системные шрифты из CSS"""
        soup = BeautifulSoup(html, 'html.parser')
        system_fonts = []
        system_font_names = ['-apple-system', 'blinkmacsystemfont', 'system-ui', 'sans-serif', 'serif', 'monospace', 'cursive', 'fantasy']
        
        for style in soup.find_all(['style', 'link']):
            if style.name == 'style' and style.string:
                matches = re.findall(r'font-family\s*:\s*["\']?([^"\';]+)["\']?', style.string, re.IGNORECASE)
                for match in matches:
                    for font in match.split(','):
                        font = font.strip().strip('"\'').lower()
                        if font in system_font_names:
                            if font not in system_fonts:
                                system_fonts.append(font)
        return system_fonts
    
    def scan_site(self, url: str) -> dict:
        """Основной метод сканирования"""
        result = {
            "url": url,
            "font_files": [],
            "system_fonts": [],
            "google_fonts_names": [],
            "errors": []
        }
        
        try:
            html = self.fetch_page(url)
            result["system_fonts"] = self.extract_system_fonts(html)
            css_urls = self.extract_css_urls(html, url)
            
            for css_url in css_urls:
                if 'fonts.googleapis.com' in css_url:
                    gf_names = self.extract_google_fonts_from_link(css_url)
                    result["google_fonts_names"].extend(gf_names)
                
                css_content = self.fetch_css(css_url)
                font_urls = self.extract_font_urls(css_content, css_url)
                
                for font_info in font_urls:
                    is_duplicate = False
                    for existing in result["font_files"]:
                        if existing["url"] == font_info["url"] or (font_info["url"] is None and existing["name"] == font_info["name"]):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        result["font_files"].append({
                            "url": font_info["url"],
                            "name": font_info["name"],
                            "source_css": css_url
                        })
            
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all(href=re.compile(r'\.(woff2?)$', re.I)):
                font_url = urljoin(url, link.get('href'))
                if font_url not in [f["url"] for f in result["font_files"] if f["url"]]:
                    font_name = self.extract_font_name_from_url(font_url)
                    result["font_files"].append({
                        "url": font_url,
                        "name": font_name,
                        "source_css": "html_link"
                    })
                    
        except Exception as e:
            result["errors"].append(str(e))
        
        return result