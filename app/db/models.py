from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
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