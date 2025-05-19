from sqlalchemy.orm import Session
from app.db.models import SummaryHistory
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HistoryService:
    def __init__(self, db: Session = None):
        self.db = db
    
    def save_text_summary(
        self,
        original_text: str,
        summary_text: str,
        key_phrases: list = None,
        model_used: str = None,
        quality_score: int = None
    ) -> SummaryHistory:
        """텍스트 요약 결과를 히스토리에 저장합니다."""
        try:
            history_item = SummaryHistory(
                summary_type="text",
                original_text=original_text,
                summary_text=summary_text,
                key_phrases=json.dumps(key_phrases) if key_phrases else None,
                model_used=model_used,
                quality_score=quality_score,
            )
            
            self.db.add(history_item)
            self.db.commit()
            self.db.refresh(history_item)
            
            logger.info(f"텍스트 요약 히스토리가 저장되었습니다. ID: {history_item.id}")
            return history_item
        except Exception as e:
            logger.error(f"텍스트 요약 히스토리 저장 중 오류 발생: {str(e)}")
            self.db.rollback()
            return None
    
    def save_youtube_summary(
        self,
        video_url: str,
        video_title: str,
        channel_name: str,
        original_transcript: str,
        summary_text: str,
        key_phrases: list = None,
        model_used: str = None,
        quality_score: int = None
    ) -> SummaryHistory:
        """유튜브 동영상 요약 결과를 히스토리에 저장합니다."""
        try:
            metadata = {
                "video_url": video_url,
                "video_title": video_title,
                "channel_name": channel_name
            }
            
            history_item = SummaryHistory(
                summary_type="youtube",
                original_text=original_transcript,
                summary_text=summary_text,
                key_phrases=json.dumps(key_phrases) if key_phrases else None,
                metadata=metadata,
                model_used=model_used,
                quality_score=quality_score,
            )
            
            self.db.add(history_item)
            self.db.commit()
            self.db.refresh(history_item)
            
            logger.info(f"유튜브 요약 히스토리가 저장되었습니다. ID: {history_item.id}")
            return history_item
        except Exception as e:
            logger.error(f"유튜브 요약 히스토리 저장 중 오류 발생: {str(e)}")
            self.db.rollback()
            return None
    
    def save_document_summary(
        self,
        file_name: str,
        file_type: str,
        original_text: str,
        summary_text: str,
        key_phrases: list = None,
        model_used: str = None,
        quality_score: int = None
    ) -> SummaryHistory:
        """문서 요약 결과를 히스토리에 저장합니다."""
        try:
            metadata = {
                "file_name": file_name,
                "file_type": file_type
            }
            
            history_item = SummaryHistory(
                summary_type="document",
                original_text=original_text,
                summary_text=summary_text,
                key_phrases=json.dumps(key_phrases) if key_phrases else None,
                metadata=metadata,
                model_used=model_used,
                quality_score=quality_score,
            )
            
            self.db.add(history_item)
            self.db.commit()
            self.db.refresh(history_item)
            
            logger.info(f"문서 요약 히스토리가 저장되었습니다. ID: {history_item.id}")
            return history_item
        except Exception as e:
            logger.error(f"문서 요약 히스토리 저장 중 오류 발생: {str(e)}")
            self.db.rollback()
            return None
    
    def get_recent_history(self, limit: int = 5, summary_type: Optional[str] = None):
        """최근 요약 히스토리를 가져옵니다."""
        try:
            query = self.db.query(SummaryHistory)
            
            if summary_type:
                query = query.filter(SummaryHistory.summary_type == summary_type)
            
            items = query.order_by(SummaryHistory.created_at.desc()).limit(limit).all()
            return [item.to_dict() for item in items]
        except Exception as e:
            logger.error(f"히스토리 조회 중 오류 발생: {str(e)}")
            return [] 