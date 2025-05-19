from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class YoutubeChannel(Base):
    __tablename__ = "youtube_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(255), unique=True, index=True)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class YoutubeKeyword(Base):
    __tablename__ = "youtube_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(255), unique=True, index=True)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    channel_id = Column(String(255), index=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SummaryHistory(Base):
    __tablename__ = "summary_history"
    
    id = Column(Integer, primary_key=True, index=True)
    summary_type = Column(String(50))  # 'text', 'youtube', 'document' 등
    original_text = Column(Text, nullable=True)
    summary_text = Column(Text, nullable=True)
    key_phrases = Column(Text, nullable=True)  # JSON 형식으로 저장
    metadata = Column(JSON, nullable=True)  # 원본 정보(URL, 파일명 등)
    quality_score = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "summary_type": self.summary_type,
            "original_text": self.original_text[:200] + "..." if self.original_text and len(self.original_text) > 200 else self.original_text,
            "summary_text": self.summary_text,
            "key_phrases": self.key_phrases,
            "metadata": self.metadata,
            "quality_score": self.quality_score,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 