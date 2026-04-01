from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.database.db_manager import get_db, init_db
from app.scanner.font_analyzer import FontAnalyzer
from app.config import Config
import os

app = FastAPI(title="Font Scanner MVP")

# Добавляем CORS middleware (для локальной разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статику
static_dir = os.path.join(Config.BASE_DIR, "app", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Инициализация шаблонов
templates_dir = os.path.join(Config.BASE_DIR, "app", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Инициализация БД при старте
init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Font Scanner - Проверка шрифтов на сайте"
    })

@app.post("/scan")
async def scan_site(url: str = Form(...), db = Depends(get_db)):
    """Сканирование сайта"""
    try:
        analyzer = FontAnalyzer(db)
        result = analyzer.scan_site(url)
        return result
    except Exception as e:
        return {
            "scan_url": url,
            "fonts": [],
            "errors": [str(e)],
            "total_fonts": 0
        }

@app.get("/api/health")
async def health_check():
    """Проверка статуса сервиса"""
    return {"status": "ok", "service": "font_scanner"}