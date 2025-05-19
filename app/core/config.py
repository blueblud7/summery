import logging
import sys
import os
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

logger.info("Loading settings...")

# .env.local 파일 로드
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local')
load_dotenv(dotenv_path)
logger.debug(f"Loaded environment variables from {dotenv_path}")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Text Summarizer"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI API 키 (필수)
    OPENAI_API_KEY: str = ""
    
    # YouTube API 키 (선택적)
    YOUTUBE_API_KEY: str = ""
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 환경 변수에서 추가 필드 로드 허용
    model_config = {
        "env_file": ".env.local",
        "env_prefix": "",
        "case_sensitive": False,
        "extra": "allow"
    }

logger.info("Creating settings instance...")
settings = Settings()
if not settings.OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not set. API calls will fail.")
logger.info("Settings loaded successfully") 