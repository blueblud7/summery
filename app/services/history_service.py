from sqlalchemy.orm import Session
from app.db.models import SummaryHistory
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class HistoryService:
    def __init__(self, db: Session = None):
        self.db = db
    
    def _generate_content_hash(self, content: str) -> str:
        """컨텐츠의 해시값을 생성하여 중복 확인에 사용합니다."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def find_duplicate_text_summary(self, text: str) -> Optional[SummaryHistory]:
        """동일한 텍스트에 대한 기존 요약이 있는지 확인합니다."""
        if not self.db:
            return None
            
        try:
            content_hash = self._generate_content_hash(text)
            # 원본 텍스트의 처음 100자를 기준으로 검색
            text_prefix = text[:100] if len(text) > 100 else text
            
            # 동일한 텍스트의 요약 검색
            existing_summary = self.db.query(SummaryHistory).filter(
                SummaryHistory.summary_type == "text",
                SummaryHistory.original_text.like(f"{text_prefix}%")
            ).order_by(SummaryHistory.created_at.desc()).first()
            
            if existing_summary:
                logger.info(f"기존 텍스트 요약을 찾았습니다. ID: {existing_summary.id}")
            return existing_summary
        except Exception as e:
            logger.error(f"텍스트 요약 중복 확인 중 오류 발생: {str(e)}")
            return None
    
    def find_duplicate_youtube_summary(self, video_url: str) -> Optional[SummaryHistory]:
        """동일한 유튜브 URL에 대한 기존 요약이 있는지 확인합니다."""
        if not self.db:
            return None
            
        try:
            # 유튜브 ID 추출 (URL에서 v= 파라미터 값)
            video_id = None
            if "v=" in video_url:
                video_id = video_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in video_url:
                video_id = video_url.split("youtu.be/")[1].split("?")[0]
            
            if not video_id:
                return None
            
            # 동일한 유튜브 영상의 요약 검색
            existing_summary = self.db.query(SummaryHistory).filter(
                SummaryHistory.summary_type == "youtube",
                SummaryHistory.source_info.contains(video_id)
            ).order_by(SummaryHistory.created_at.desc()).first()
            
            if existing_summary:
                logger.info(f"기존 유튜브 요약을 찾았습니다. ID: {existing_summary.id}")
            return existing_summary
        except Exception as e:
            logger.error(f"유튜브 요약 중복 확인 중 오류 발생: {str(e)}")
            return None
    
    def find_duplicate_document_summary(self, file_name: str, file_content: str) -> Optional[SummaryHistory]:
        """동일한 문서에 대한 기존 요약이 있는지 확인합니다."""
        if not self.db:
            return None
            
        try:
            content_hash = self._generate_content_hash(file_content)
            
            # 동일한 파일명과 비슷한 내용의 문서 요약 검색
            existing_summary = self.db.query(SummaryHistory).filter(
                SummaryHistory.summary_type == "document",
                SummaryHistory.source_info.contains(file_name)
            ).order_by(SummaryHistory.created_at.desc()).first()
            
            if existing_summary:
                logger.info(f"기존 문서 요약을 찾았습니다. ID: {existing_summary.id}")
            return existing_summary
        except Exception as e:
            logger.error(f"문서 요약 중복 확인 중 오류 발생: {str(e)}")
            return None
    
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
            # 중복 확인
            duplicate = self.find_duplicate_text_summary(original_text)
            if duplicate:
                logger.info(f"중복된 텍스트 요약이 발견되어 기존 요약을 반환합니다. ID: {duplicate.id}")
                return duplicate
                
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
            # 중복 확인
            duplicate = self.find_duplicate_youtube_summary(video_url)
            if duplicate:
                logger.info(f"중복된 유튜브 요약이 발견되어 기존 요약을 반환합니다. ID: {duplicate.id}")
                return duplicate
                
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
                source_info=metadata,
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
            # 중복 확인
            duplicate = self.find_duplicate_document_summary(file_name, original_text)
            if duplicate:
                logger.info(f"중복된 문서 요약이 발견되어 기존 요약을 반환합니다. ID: {duplicate.id}")
                return duplicate
                
            metadata = {
                "file_name": file_name,
                "file_type": file_type
            }
            
            history_item = SummaryHistory(
                summary_type="document",
                original_text=original_text,
                summary_text=summary_text,
                key_phrases=json.dumps(key_phrases) if key_phrases else None,
                source_info=metadata,
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
            
    def search_history(self, query: str, summary_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """히스토리에서 검색합니다."""
        try:
            db_query = self.db.query(SummaryHistory)
            
            if summary_type:
                db_query = db_query.filter(SummaryHistory.summary_type == summary_type)
                
            # 검색어로 필터링
            if query:
                search_term = f"%{query}%"
                db_query = db_query.filter(
                    (SummaryHistory.original_text.like(search_term)) | 
                    (SummaryHistory.summary_text.like(search_term))
                )
                
            items = db_query.order_by(SummaryHistory.created_at.desc()).limit(limit).all()
            return [item.to_dict() for item in items]
        except Exception as e:
            logger.error(f"히스토리 검색 중 오류 발생: {str(e)}")
            return [] 