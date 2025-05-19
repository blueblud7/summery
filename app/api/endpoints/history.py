from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import SummaryHistory
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
    요약 히스토리 목록을 반환합니다.
    """
    query = db.query(SummaryHistory)
    
    # 타입으로 필터링
    if summary_type:
        query = query.filter(SummaryHistory.summary_type == summary_type)
    
    # 최신순으로 정렬
    query = query.order_by(SummaryHistory.created_at.desc())
    
    # 페이지네이션 적용
    total_count = query.count()
    history_items = query.offset(offset).limit(limit).all()
    
    return {
        "total": total_count,
        "items": [item.to_dict() for item in history_items]
    }

@router.get("/{history_id}")
async def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    """
    특정 히스토리 항목의 상세 정보를 반환합니다.
    """
    history_item = db.query(SummaryHistory).filter(SummaryHistory.id == history_id).first()
    if not history_item:
        raise HTTPException(status_code=404, detail="히스토리 항목을 찾을 수 없습니다.")
    
    return history_item.to_dict()

@router.delete("/{history_id}")
async def delete_history_item(history_id: int, db: Session = Depends(get_db)):
    """
    특정 히스토리 항목을 삭제합니다.
    """
    history_item = db.query(SummaryHistory).filter(SummaryHistory.id == history_id).first()
    if not history_item:
        raise HTTPException(status_code=404, detail="히스토리 항목을 찾을 수 없습니다.")
    
    db.delete(history_item)
    db.commit()
    
    return {"message": "히스토리 항목이 삭제되었습니다."}

@router.delete("/clear")
async def clear_history(
    summary_type: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    모든 또는 특정 타입의 히스토리를 삭제합니다.
    """
    query = db.query(SummaryHistory)
    
    if summary_type:
        query = query.filter(SummaryHistory.summary_type == summary_type)
    
    count = query.count()
    query.delete()
    db.commit()
    
    return {"message": f"{count}개의 히스토리 항목이 삭제되었습니다."} 