import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.db.database import SQLALCHEMY_DATABASE_URL
from app.models.models import Base, User, Channel, Keyword, Tag, Video, SearchHistory, SummaryHistory

# 데이터베이스 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

def create_tables():
    print("데이터베이스 테이블 생성 시작...")
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 테이블 생성 완료!")

if __name__ == "__main__":
    create_tables() 