from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import SummaryHistory
from app.services.history_service import HistoryService
import json
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/")
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns a list of summary history items with optional filtering by type and date.
    """
    query = db.query(SummaryHistory)
    
    # 타입으로 필터링 (channel, keyword, all)
    if type and type != "all":
        source_field = "source_metadata"
        
        if type == "channel":
            # JSON 필드에서 channel_id가 있는 항목 필터링
            query = query.filter(SummaryHistory.source_type == "youtube")
            query = query.filter(SummaryHistory.source_metadata.op('->>')('source_type') == 'channel')
        elif type == "keyword":
            # JSON 필드에서 keyword가 있는 항목 필터링
            query = query.filter(SummaryHistory.source_type == "youtube")
            query = query.filter(SummaryHistory.source_metadata.op('->>')('source_type') == 'keyword')
    
    # 날짜로 필터링
    if date:
        try:
            # 문자열을 날짜로 변환
            filter_date = datetime.strptime(date, "%Y-%m-%d")
            
            # 해당 날짜의 시작과 끝
            start_date = filter_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = filter_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # 날짜 범위로 필터링
            query = query.filter(SummaryHistory.created_at >= start_date, 
                                SummaryHistory.created_at <= end_date)
        except ValueError:
            # 날짜 형식이 잘못된 경우
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # 최신순으로 정렬
    query = query.order_by(SummaryHistory.created_at.desc())
    
    # 페이지네이션 적용
    total_count = query.count()
    history_items = query.offset(offset).limit(limit).all()
    
    # 결과 반환
    return [item.to_dict() for item in history_items]

@router.get("/list")
async def get_history_list(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    summary_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns a list of summary history items.
    """
    query = db.query(SummaryHistory)
    
    # Filter by type
    if summary_type:
        query = query.filter(SummaryHistory.summary_type == summary_type)
    
    # Sort by newest first
    query = query.order_by(SummaryHistory.created_at.desc())
    
    # Apply pagination
    total_count = query.count()
    history_items = query.offset(offset).limit(limit).all()
    
    return {
        "total": total_count,
        "items": [item.to_dict() for item in history_items]
    }

@router.get("/search")
async def search_history(
    query: str = "",
    summary_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Searches through history items by content.
    """
    history_service = HistoryService(db)
    results = history_service.search_history(query, summary_type, limit)
    
    return {
        "total": len(results),
        "items": results
    }

@router.post("/check-duplicate")
async def check_duplicate_summary(
    text: Optional[str] = None,
    youtube_url: Optional[str] = None,
    file_name: Optional[str] = None,
    file_content: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Checks if a similar summary already exists in the history.
    """
    history_service = HistoryService(db)
    duplicate = None
    
    if text:
        duplicate = history_service.find_duplicate_text_summary(text)
    elif youtube_url:
        duplicate = history_service.find_duplicate_youtube_summary(youtube_url)
    elif file_name and file_content:
        duplicate = history_service.find_duplicate_document_summary(file_name, file_content)
    
    if duplicate:
        return {
            "duplicate_found": True,
            "item": duplicate.to_dict()
        }
    else:
        return {
            "duplicate_found": False,
            "item": None
        }

@router.get("/{history_id}")
async def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    """
    Returns detailed information for a specific history item.
    """
    history_item = db.query(SummaryHistory).filter(SummaryHistory.id == history_id).first()
    if not history_item:
        raise HTTPException(status_code=404, detail="History item not found.")
    
    return history_item.to_dict()

@router.delete("/{history_id}")
async def delete_history_item(history_id: int, db: Session = Depends(get_db)):
    """
    Deletes a specific history item.
    """
    history_item = db.query(SummaryHistory).filter(SummaryHistory.id == history_id).first()
    if not history_item:
        raise HTTPException(status_code=404, detail="History item not found.")
    
    db.delete(history_item)
    db.commit()
    
    return {"message": "History item has been deleted."}

@router.delete("/clear")
async def clear_history(
    summary_type: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Clears all history or history of a specific type.
    """
    query = db.query(SummaryHistory)
    
    if summary_type:
        query = query.filter(SummaryHistory.summary_type == summary_type)
    
    count = query.count()
    query.delete()
    db.commit()
    
    return {"message": f"{count} history items have been deleted."} 