import logging
import sys
import os
from typing import Dict, Any, Optional, List
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
    
    # YouTube API 키 (선택적) - 쉼표로 구분된 문자열에서 리스트로 변환
    YOUTUBE_API_KEYS: str = ""
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    
    # 데이터베이스 설정
    DB_PATH: str = "./data/app.db"
    
    # 모델 설정
    DEFAULT_MODEL: str = "gpt-4o-mini"
    AVAILABLE_MODELS: List[str] = ["gpt-4o-mini"]
    
    # 기본 요약 설정
    DEFAULT_MAX_LENGTH: int = 200
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_STYLE: str = "simple"
    DEFAULT_FORMAT: str = "text"
    
    # 현재 사용 중인 YouTube API 키 인덱스
    _youtube_api_key_index: int = 0
    
    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 추가 필드를 허용
    
    @property
    def youtube_api_keys_list(self) -> List[str]:
        """YOUTUBE_API_KEYS 문자열을 리스트로 변환하여 반환"""
        if not self.YOUTUBE_API_KEYS:
            return []
        return [key.strip() for key in self.YOUTUBE_API_KEYS.split(",") if key.strip()]
    
    @property
    def YOUTUBE_API_KEY(self) -> str:
        """현재 사용할 YouTube API 키를 반환"""
        keys = self.youtube_api_keys_list
        if not keys:
            return ""
        return keys[self._youtube_api_key_index % len(keys)]
    
    def next_youtube_api_key(self) -> str:
        """다음 YouTube API 키로 전환하고 그 키를 반환"""
        keys = self.youtube_api_keys_list
        if not keys:
            return ""
        self._youtube_api_key_index = (self._youtube_api_key_index + 1) % len(keys)
        return self.YOUTUBE_API_KEY

logger.info("Creating settings instance...")
settings = Settings()
if not settings.OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not set. API calls will fail.")
logger.info("Settings loaded successfully") 