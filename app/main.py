import logging
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from app.api.endpoints import summarizer, history, youtube_manage, auth
from app.core.config import settings
from app.db.database import init_db
from app.db.models import YoutubeChannel, YoutubeKeyword, Video, SummaryHistory
from app.utils.auth import get_current_active_user, get_premium_user
from app.models.models import User
import os

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# 애플리케이션 생성
app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="app/templates")

# API 라우터 등록
logger.info("Registering routers...")
app.include_router(summarizer.router, prefix="/api/v1", tags=["summarizer"])
app.include_router(history.router, prefix="/api/v1/history", tags=["history"])
app.include_router(youtube_manage.router, prefix="/api/v1/youtube", tags=["youtube"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.on_event("startup")
async def startup_db_client():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    try:
        logger.info("데이터베이스 초기화 중...")
        init_db()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 오류: {e}")

# 계정 관리 페이지
@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """
    Returns the account management page.
    """
    logger.info("Account page called")
    return templates.TemplateResponse(
        "account.html", 
        {
            "request": request, 
            "user": current_user,
            "is_premium": current_user.subscription_tier != "free"
        }
    )

# 구독 페이지
@app.get("/subscription", response_class=HTMLResponse)
async def subscription_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """
    Returns the subscription page.
    """
    logger.info("Subscription page called")
    return templates.TemplateResponse(
        "subscription.html", 
        {
            "request": request, 
            "user": current_user,
            "premium_price": settings.PREMIUM_MONTHLY_PRICE,
            "enterprise_price": settings.ENTERPRISE_MONTHLY_PRICE,
            "current_tier": current_user.subscription_tier
        }
    )

# 로그인 페이지
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    로그인 페이지를 반환합니다.
    """
    logger.info("Login page called")
    return templates.TemplateResponse("login.html", {"request": request})

# 회원가입 페이지
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    회원가입 페이지를 반환합니다.
    """
    logger.info("Register page called")
    return templates.TemplateResponse("register.html", {"request": request})

# 루트 페이지
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Returns the home page.
    """
    logger.info("Root endpoint called")
    return templates.TemplateResponse("index.html", {"request": request})

# 관리 페이지
@app.get("/manage", response_class=HTMLResponse)
async def youtube_manage_page(request: Request):
    """
    Returns the YouTube management page.
    """
    logger.info("YouTube manage page called")
    is_ajax = request.query_params.get("ajax", "false") == "true"
    return templates.TemplateResponse(
        "youtube_manage.html", 
        {"request": request, "is_ajax": is_ajax}
    )

# 히스토리 페이지
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """
    요약 히스토리 페이지를 반환합니다.
    """
    logger.info("History page called")
    is_ajax = request.query_params.get("ajax", "false") == "true"
    return templates.TemplateResponse(
        "history.html", 
        {"request": request, "is_ajax": is_ajax}
    )

# 채널 페이지
@app.get("/channels", response_class=HTMLResponse)
async def channels_page(request: Request):
    """
    Returns the channels page.
    """
    logger.debug("Channels page called")
    return templates.TemplateResponse("youtube_manage.html", {"request": request})

# 키워드 페이지
@app.get("/keywords", response_class=HTMLResponse)
async def keywords_page(request: Request):
    """
    Returns the keywords page.
    """
    logger.debug("Keywords page called")
    return templates.TemplateResponse("youtube_manage.html", {"request": request})

# 검색 페이지
@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """
    Returns the search page.
    """
    logger.debug("Search page called")
    return templates.TemplateResponse("youtube_manage.html", {"request": request})

# 리포트 페이지
@app.get("/report", response_class=HTMLResponse)
async def report_page(request: Request):
    """
    리포트 페이지를 반환합니다.
    """
    logger.info("Report page called")
    return templates.TemplateResponse("youtube_manage.html", {"request": request, "tab": "reports"})

# 메인 시작점
logger.info("Starting application...")
logger.debug(f"Settings: {settings.PROJECT_NAME}, {settings.VERSION}") 