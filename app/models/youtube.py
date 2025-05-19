from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class YoutubeChannelBase(BaseModel):
    channel_id: str
    title: Optional[str] = None
    description: Optional[str] = None

class YoutubeChannelCreate(YoutubeChannelBase):
    pass

class YoutubeChannelUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class YoutubeChannel(YoutubeChannelBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class YoutubeKeywordBase(BaseModel):
    keyword: str
    description: Optional[str] = None

class YoutubeKeywordCreate(YoutubeKeywordBase):
    pass

class YoutubeKeywordUpdate(BaseModel):
    description: Optional[str] = None

class YoutubeKeyword(YoutubeKeywordBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class VideoBase(BaseModel):
    video_id: str
    title: str
    description: Optional[str] = None
    channel_id: str
    published_at: Optional[datetime] = None

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True 