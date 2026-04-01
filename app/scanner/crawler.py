import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
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
        
        # <link rel="stylesheet" href="...">
        for link in soup.find_all('link', rel=lambda x: x and 'stylesheet' in x):
            href = link.get('href')
            if href:
                css_urls.append(urljoin(base_url, href))
        
        # <style>@import url("...")</style>
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
        """Извлечь название шрифта из URL"""
        # Получаем имя файла из URL
        filename = unquote(font_url.split('/')[-1].split('?')[0])
        
        # Убираем расширение
        name = re.sub(r'\.(woff2?|ttf|otf|eot)$', '', filename, flags=re.IGNORECASE)
        
        # Заменяем дефисы и подчёркивания на пробелы
        name = re.sub(r'[-_]', ' ', name)
        
        # Убираем технические суффиксы
        name = re.sub(r'\s*(VF|Variable|Regular|Bold|Italic|Light|Medium|Thin|Black|White)\s*$', '', name, flags=re.IGNORECASE)
        
        # Capitalize каждое слово
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name.strip() if name else "Неизвестный"
    
    def extract_font_urls(self, css_content: str, base_url: str) -> list:
        """Извлечь URL шрифтов из CSS"""
        font_urls = []
        
        # @font-face { src: url(...) }
        pattern = r'@font-face[^}]*src:[^}]*url\(["\']?([^"\')]+\.(woff2?|ttf|otf|eot))["\']?'
        matches = re.findall(pattern, css_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            font_url = match[0]
            # Пропускаем Base64
            if font_url.startswith('data:'):
                continue
            
            full_url = urljoin(base_url, font_url)
            
            # Пытаемся извлечь название шрифта из CSS
            font_name = "Неизвестный"
            
            # Ищем font-family вблизи этого @font-face
            font_face_pattern = r'@font-face\s*{([^}]+)}'
            font_faces = re.findall(font_face_pattern, css_content, re.IGNORECASE | re.DOTALL)
            
            for font_face in font_faces:
                if font_url in font_face or full_url in font_face:
                    family_match = re.search(r'font-family\s*:\s*["\']?([^"\';\}]+)["\']?', font_face, re.IGNORECASE)
                    if family_match:
                        font_name = family_match.group(1).strip().strip('"\'')
                        break
            
            # Если не нашли в CSS, пробуем извлечь из URL
            if font_name == "Неизвестный":
                font_name = self.extract_font_name_from_url(full_url)
            
            font_urls.append({
                "url": full_url,
                "name": font_name
            })
        
        return font_urls[:Config.MAX_FONTS_PER_SITE]
    
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
        system_font_names = ['arial', 'times new roman', 'georgia', 'verdana', 'trebuchet', 'courier new', 'helvetica', 'tahoma']
        
        # Ищем font-family в стилях
        for style in soup.find_all(['style', 'link']):
            if style.name == 'style' and style.string:
                matches = re.findall(r'font-family\s*:\s*["\']?([^"\';]+)["\']?', style.string, re.IGNORECASE)
                for match in matches:
                    for font in match.split(','):
                        font = font.strip().strip('"\'').lower()
                        if any(sf in font for sf in system_font_names):
                            if font not in system_fonts:
                                system_fonts.append(font)
        
        return system_fonts
    
    def scan_site(self, url: str) -> dict:
        """Основной метод сканирования"""
        result = {
            "url": url,
            "font_files": [],
            "system_fonts": [],
            "errors": []
        }
        
        try:
            # Скачиваем главную страницу
            html = self.fetch_page(url)
            
            # Извлекаем системные шрифты
            result["system_fonts"] = self.extract_system_fonts(html)
            
            # Извлекаем CSS
            css_urls = self.extract_css_urls(html, url)
            
            # Из каждого CSS извлекаем шрифты
            for css_url in css_urls:
                css_content = self.fetch_css(css_url)
                font_urls = self.extract_font_urls(css_content, css_url)
                for font_info in font_urls:
                    if font_info["url"] not in [f["url"] for f in result["font_files"]]:
                        result["font_files"].append({
                            "url": font_info["url"],
                            "name": font_info["name"],
                            "source_css": css_url
                        })
            
            # Также ищем прямые ссылки на шрифты в HTML
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all(href=re.compile(r'\.(woff2?)$', re.I)):
                font_url = urljoin(url, link.get('href'))
                if font_url not in [f["url"] for f in result["font_files"]]:
                    font_name = self.extract_font_name_from_url(font_url)
                    result["font_files"].append({
                        "url": font_url,
                        "name": font_name,
                        "source_css": "html_link"
                    })
                    
        except Exception as e:
            result["errors"].append(str(e))
        
        return result