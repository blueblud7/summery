from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import enum

class VideoCategory(enum.Enum):
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    TECHNOLOGY = "technology"
    GAMING = "gaming"
    MUSIC = "music"
    SPORTS = "sports"
    OTHER = "other"

class SummaryStyle(enum.Enum):
    SIMPLE = "simple"
    DETAILED = "detailed"

# 비디오-태그 연결 테이블
video_tags = Table(
    'video_tags',
    Base.metadata,
    Column('video_id', Integer, ForeignKey('videos.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    videos = relationship("Video", back_populates="channel")

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    videos = relationship("Video", back_populates="keyword")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    videos = relationship("Video", secondary=video_tags, back_populates="tags")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    published_at = Column(DateTime(timezone=True))
    duration = Column(String)  # ISO 8601 duration format
    category = Column(Enum(VideoCategory), default=VideoCategory.OTHER)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    
    # 요약 관련 필드
    summary = Column(Text)
    summary_style = Column(Enum(SummaryStyle), default=SummaryStyle.SIMPLE)
    summary_length = Column(Integer, default=200)  # 문자 수
    summary_language = Column(String, default="ko")  # ISO 639-1 언어 코드
    key_phrases = Column(Text)  # JSON 형식으로 저장된 핵심 구문
    is_summarized = Column(Boolean, default=False)
    
    # 중복 체크 관련 필드
    similarity_score = Column(Float, default=0.0)  # 다른 비디오와의 유사도 점수
    is_duplicate = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_checked_at = Column(DateTime(timezone=True))  # 마지막 업데이트 확인 시간

    channel = relationship("Channel", back_populates="videos")
    keyword = relationship("Keyword", back_populates="videos")
    tags = relationship("Tag", secondary=video_tags, back_populates="videos")

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(String)
    filters = Column(Text)  # JSON 형식으로 저장된 필터
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 