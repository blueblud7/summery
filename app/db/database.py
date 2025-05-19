from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# 데이터베이스 파일 경로 설정
DB_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(DB_DIRECTORY, exist_ok=True)
DB_FILE = os.path.join(DB_DIRECTORY, "app.db")

# 로그 추가
logger.info(f"데이터베이스 파일 경로: {DB_FILE}")

# SQLite 데이터베이스 URL 생성
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

# 데이터베이스 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델 기본 클래스 생성
Base = declarative_base()

# 데이터베이스 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 데이터베이스 초기화 함수
def init_db():
    try:
        logger.info("데이터베이스 테이블 생성 시작")
        from app.db.models import YoutubeChannel, YoutubeKeyword, Video
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류: {e}")
        raise e 