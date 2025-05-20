from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import SummaryHistory
from app.services.history_service import HistoryService
import json

router = APIRouter()

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