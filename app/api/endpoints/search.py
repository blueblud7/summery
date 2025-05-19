from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.models import Video, Channel, Tag, SearchHistory, User
from app.utils.auth import oauth2_scheme

router = APIRouter()

@router.get("/search")
async def search_videos(
    query: Optional[str] = None,
    category: Optional[str] = None,
    channel_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_duration: Optional[str] = None,
    max_duration: Optional[str] = None,
    tags: Optional[List[str]] = None,
    sort_by: str = "published_at",
    sort_order: str = "desc",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2_scheme)
):
    # 기본 쿼리
    video_query = db.query(Video)
    
    # 검색어 필터링
    if query:
        video_query = video_query.filter(
            or_(
                Video.title.ilike(f"%{query}%"),
                Video.description.ilike(f"%{query}%")
            )
        )
    
    # 카테고리 필터링
    if category:
        video_query = video_query.filter(Video.category == category)
    
    # 채널 필터링
    if channel_id:
        video_query = video_query.filter(Channel.channel_id == channel_id)
    
    # 날짜 범위 필터링
    if start_date:
        video_query = video_query.filter(Video.published_at >= start_date)
    if end_date:
        video_query = video_query.filter(Video.published_at <= end_date)
    
    # 태그 필터링
    if tags:
        video_query = video_query.join(Video.tags).filter(Tag.name.in_(tags))
    
    # 정렬
    if sort_by == "published_at":
        video_query = video_query.order_by(
            Video.published_at.desc() if sort_order == "desc" else Video.published_at.asc()
        )
    elif sort_by == "title":
        video_query = video_query.order_by(
            Video.title.desc() if sort_order == "desc" else Video.title.asc()
        )
    
    # 페이지네이션
    total = video_query.count()
    videos = video_query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 검색 히스토리 저장
    search_history = SearchHistory(
        user_id=current_user.id,
        query=query,
        filters={
            "category": category,
            "channel_id": channel_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "tags": tags
        }
    )
    db.add(search_history)
    db.commit()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": videos
    }

@router.get("/search/history")
async def get_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(oauth2_scheme)
):
    history = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(SearchHistory.created_at.desc()).limit(10).all()
    
    return history 