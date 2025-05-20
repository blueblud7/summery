from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.models import User
from app.db.crud import is_subscription_active
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    """구독 서비스 및 사용량 제한 관리"""
    
    # 구독 등급별 제한
    TIER_LIMITS = {
        "free": {
            "daily_summaries": 5,
            "monthly_summaries": 50,
            "max_tokens": 1000,
            "max_document_size": 1,  # MB
            "max_video_length": 10,  # 분
            "advanced_features": False
        },
        "premium": {
            "daily_summaries": 20,
            "monthly_summaries": 500,
            "max_tokens": 4000,
            "max_document_size": 10,  # MB
            "max_video_length": 60,  # 분
            "advanced_features": True
        },
        "enterprise": {
            "daily_summaries": 100,
            "monthly_summaries": 5000,
            "max_tokens": 16000,
            "max_document_size": 50,  # MB
            "max_video_length": 240,  # 분
            "advanced_features": True
        }
    }
    
    @classmethod
    def check_subscription_active(cls, user: User) -> bool:
        """사용자 구독이 활성 상태인지 확인"""
        return is_subscription_active(user)
    
    @classmethod
    def get_user_limits(cls, user: User) -> Dict[str, Any]:
        """사용자 구독 등급에 따른 제한 사항 가져오기"""
        tier = user.subscription_tier
        if tier not in cls.TIER_LIMITS:
            tier = "free"
        return cls.TIER_LIMITS[tier]
    
    @classmethod
    def check_summary_limit(cls, user: User, db: Session) -> None:
        """사용자가 요약 기능을 사용할 수 있는지 한도 확인"""
        # 현재 날짜의 00:00:00 시간
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        if user.subscription_tier == "free":
            # 오늘 사용한 요약 수 확인
            daily_count = db.query(SummaryHistory).filter(
                SummaryHistory.user_id == user.id,
                SummaryHistory.created_at >= today
            ).count()
            
            if daily_count >= cls.TIER_LIMITS["free"]["daily_summaries"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="일일 요약 한도를 초과했습니다. 프리미엄으로 업그레이드하세요."
                )
                
            # 이번 달 사용한 요약 수 확인
            first_day_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_count = db.query(SummaryHistory).filter(
                SummaryHistory.user_id == user.id,
                SummaryHistory.created_at >= first_day_of_month
            ).count()
            
            if monthly_count >= cls.TIER_LIMITS["free"]["monthly_summaries"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="월간 요약 한도를 초과했습니다. 프리미엄으로 업그레이드하세요."
                )
    
    @classmethod
    def check_document_size(cls, user: User, file_size_mb: float) -> None:
        """문서 크기 제한 확인"""
        limits = cls.get_user_limits(user)
        if file_size_mb > limits["max_document_size"]:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"문서 크기가 너무 큽니다. 최대 {limits['max_document_size']}MB까지 허용됩니다."
            )
    
    @classmethod
    def check_video_length(cls, user: User, video_length_minutes: float) -> None:
        """비디오 길이 제한 확인"""
        limits = cls.get_user_limits(user)
        if video_length_minutes > limits["max_video_length"]:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"비디오 길이가 너무 깁니다. 최대 {limits['max_video_length']}분까지 허용됩니다."
            )
    
    @classmethod
    def check_advanced_feature_access(cls, user: User) -> None:
        """고급 기능 접근 권한 확인"""
        limits = cls.get_user_limits(user)
        if not limits["advanced_features"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 기능은 프리미엄 구독자만 사용할 수 있습니다."
            ) 