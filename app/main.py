from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.database.db_manager import get_db, init_db
from app.scanner.font_analyzer import FontAnalyzer
from app.utils.pdf_generator import generate_pdf_report
from app.config import Config
import os
from datetime import datetime
import io

app = FastAPI(title="Font Scanner MVP")

# CORS middleware
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
        result["scan_url"] = url
        result["scan_date"] = datetime.now().isoformat()
        return result
    except Exception as e:
        return {
            "scan_url": url,
            "fonts": [],
            "errors": [str(e)],
            "total_fonts": 0,
            "scan_date": datetime.now().isoformat()
        }

@app.get("/export/pdf")
async def export_pdf(
    url: str = Query(..., description="URL сайта для сканирования"),
    db = Depends(get_db)
):
    """
    Экспорт результатов сканирования в PDF
    """
    try:
        analyzer = FontAnalyzer(db)
        result = analyzer.scan_site(url)
        result["scan_url"] = url
        result["scan_date"] = datetime.now().isoformat()
        
        # Генерируем PDF
        pdf_bytes = generate_pdf_report(result)
        
        # Возвращаем как файл
        filename = f"font_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/health")
async def health_check():
    """Проверка статуса сервиса"""
    return {"status": "ok", "service": "font_scanner"}