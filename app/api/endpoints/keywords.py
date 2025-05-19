from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.youtube_service import YouTubeService
from app.models.models import Keyword, Video
from app.services.summarizer_service import SummarizerService

router = APIRouter()
youtube_service = YouTubeService()
summarizer_service = SummarizerService()

@router.post("/keywords/")
async def add_keyword(keyword: str, db: Session = Depends(get_db)):
    # Check if keyword already exists
    existing_keyword = db.query(Keyword).filter(Keyword.keyword == keyword).first()
    if existing_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists")

    # Create new keyword
    keyword_obj = Keyword(keyword=keyword)
    db.add(keyword_obj)
    db.commit()
    db.refresh(keyword_obj)

    # Search videos by keyword
    videos = youtube_service.search_videos_by_keyword(keyword)
    for video_data in videos:
        video = Video(
            video_id=video_data['video_id'],
            title=video_data['title'],
            description=video_data['description'],
            published_at=video_data['published_at'],
            keyword_id=keyword_obj.id
        )
        db.add(video)
    
    db.commit()
    return {"message": "Keyword added successfully", "keyword": keyword_obj}

@router.get("/keywords/")
async def get_keywords(db: Session = Depends(get_db)):
    keywords = db.query(Keyword).all()
    return keywords

@router.get("/keywords/{keyword}/videos")
async def get_keyword_videos(keyword: str, db: Session = Depends(get_db)):
    keyword_obj = db.query(Keyword).filter(Keyword.keyword == keyword).first()
    if not keyword_obj:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    videos = db.query(Video).filter(Video.keyword_id == keyword_obj.id).all()
    return videos 