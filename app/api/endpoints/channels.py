from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.youtube_service import YouTubeService
from app.models.models import Channel, Video
from app.services.summarizer_service import SummarizerService

router = APIRouter()
youtube_service = YouTubeService()
summarizer_service = SummarizerService()

@router.post("/channels/")
async def add_channel(channel_id: str, db: Session = Depends(get_db)):
    # Check if channel already exists
    existing_channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    if existing_channel:
        raise HTTPException(status_code=400, detail="Channel already exists")

    # Get channel info from YouTube
    channel_info = youtube_service.get_channel_info(channel_id)
    if not channel_info:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Create new channel
    channel = Channel(
        channel_id=channel_info['channel_id'],
        title=channel_info['title'],
        description=channel_info['description']
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)

    # Get recent videos
    videos = youtube_service.get_channel_videos(channel_id)
    for video_data in videos:
        video = Video(
            video_id=video_data['video_id'],
            title=video_data['title'],
            description=video_data['description'],
            published_at=video_data['published_at'],
            channel_id=channel.id
        )
        db.add(video)
    
    db.commit()
    return {"message": "Channel added successfully", "channel": channel}

@router.get("/channels/")
async def get_channels(db: Session = Depends(get_db)):
    channels = db.query(Channel).all()
    return channels

@router.get("/channels/{channel_id}/videos")
async def get_channel_videos(channel_id: str, db: Session = Depends(get_db)):
    channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    videos = db.query(Video).filter(Video.channel_id == channel.id).all()
    return videos 