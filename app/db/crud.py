from sqlalchemy.orm import Session
from app.db.models import YoutubeChannel, YoutubeKeyword, Video
from app.models.youtube import YoutubeChannelCreate, YoutubeChannelUpdate, YoutubeKeywordCreate, YoutubeKeywordUpdate
from typing import List, Optional, Union, Dict, Any, Tuple
from datetime import datetime, timedelta
from app.models.models import User
from app.utils.auth import get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)

# 채널 CRUD 연산
def create_youtube_channel(db: Session, channel: YoutubeChannelCreate) -> YoutubeChannel:
    logger.info(f"채널 생성 시작: {channel.channel_id}")
    db_channel = YoutubeChannel(
        channel_id=channel.channel_id,
        title=channel.title or "",
        description=channel.description or ""
    )
    try:
        db.add(db_channel)
        db.commit()
        db.refresh(db_channel)
        logger.info(f"채널 생성 완료: {channel.channel_id}")
        return db_channel
    except Exception as e:
        db.rollback()
        logger.error(f"채널 생성 실패: {str(e)}")
        raise e

def get_youtube_channel_by_id(db: Session, channel_id: str) -> Optional[YoutubeChannel]:
    return db.query(YoutubeChannel).filter(YoutubeChannel.channel_id == channel_id).first()

def get_youtube_channels(db: Session, skip: int = 0, limit: int = 100) -> List[YoutubeChannel]:
    return db.query(YoutubeChannel).offset(skip).limit(limit).all()

def update_youtube_channel(db: Session, channel_id: str, channel: YoutubeChannelUpdate) -> Optional[YoutubeChannel]:
    db_channel = get_youtube_channel_by_id(db, channel_id)
    if db_channel:
        logger.info(f"채널 업데이트 시작: {channel_id}")
        update_data = channel.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_channel, key, value)
        try:
            db.commit()
            db.refresh(db_channel)
            logger.info(f"채널 업데이트 완료: {channel_id}")
            return db_channel
        except Exception as e:
            db.rollback()
            logger.error(f"채널 업데이트 실패: {str(e)}")
            raise e
    return None

def delete_youtube_channel(db: Session, channel_id: str) -> bool:
    """
    채널 ID로 유튜브 채널을 삭제합니다.
    DB에 저장된 ID가 URL 형태일 수도 있으므로 직접 쿼리합니다.
    """
    logger.info(f"채널 삭제 시작: {channel_id}")
    try:
        # 직접 DB에서 채널 쿼리
        db_channel = db.query(YoutubeChannel).filter(YoutubeChannel.channel_id == channel_id).first()
        if db_channel:
            db.delete(db_channel)
            db.commit()
            logger.info(f"채널 삭제 완료: {channel_id}")
            return True
        logger.warning(f"삭제할 채널을 찾을 수 없음: {channel_id}")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"채널 삭제 실패: {str(e)}")
        raise e

# 키워드 CRUD 연산
def create_youtube_keyword(db: Session, keyword: YoutubeKeywordCreate) -> YoutubeKeyword:
    logger.info(f"키워드 생성 시작: {keyword.keyword}")
    db_keyword = YoutubeKeyword(
        keyword=keyword.keyword,
        description=keyword.description or ""
    )
    try:
        db.add(db_keyword)
        db.commit()
        db.refresh(db_keyword)
        logger.info(f"키워드 생성 완료: {keyword.keyword}")
        return db_keyword
    except Exception as e:
        db.rollback()
        logger.error(f"키워드 생성 실패: {str(e)}")
        raise e

def get_youtube_keyword(db: Session, keyword_id: int) -> Optional[YoutubeKeyword]:
    return db.query(YoutubeKeyword).filter(YoutubeKeyword.id == keyword_id).first()

def get_youtube_keyword_by_value(db: Session, keyword_value: str) -> Optional[YoutubeKeyword]:
    return db.query(YoutubeKeyword).filter(YoutubeKeyword.keyword == keyword_value).first()

def get_youtube_keywords(db: Session, skip: int = 0, limit: int = 100) -> List[YoutubeKeyword]:
    return db.query(YoutubeKeyword).offset(skip).limit(limit).all()

def update_youtube_keyword(db: Session, keyword_id: int, keyword: YoutubeKeywordUpdate) -> Optional[YoutubeKeyword]:
    db_keyword = get_youtube_keyword(db, keyword_id)
    if db_keyword:
        logger.info(f"키워드 업데이트 시작: ID={keyword_id}")
        update_data = keyword.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_keyword, key, value)
        try:
            db.commit()
            db.refresh(db_keyword)
            logger.info(f"키워드 업데이트 완료: ID={keyword_id}")
            return db_keyword
        except Exception as e:
            db.rollback()
            logger.error(f"키워드 업데이트 실패: {str(e)}")
            raise e
    return None

def delete_youtube_keyword(db: Session, keyword_id: int) -> bool:
    db_keyword = get_youtube_keyword(db, keyword_id)
    if db_keyword:
        logger.info(f"키워드 삭제 시작: ID={keyword_id}")
        try:
            db.delete(db_keyword)
            db.commit()
            logger.info(f"키워드 삭제 완료: ID={keyword_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"키워드 삭제 실패: {str(e)}")
            raise e
    return False

# 비디오 관련 CRUD 함수 (필요시 구현)
def save_video(db: Session, video_data: Dict[str, Any]) -> Video:
    db_video = Video(
        video_id=video_data.get('video_id', ''),
        title=video_data.get('title', ''),
        description=video_data.get('description', ''),
        channel_id=video_data.get('channel_id', ''),
        published_at=video_data.get('published_at')
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    """ID로 사용자 조회"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """이메일로 사용자 조회"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_oauth(db: Session, oauth_provider: str, oauth_id: str) -> Optional[User]:
    """OAuth 제공자 및 ID로 사용자 조회"""
    return db.query(User).filter(
        User.oauth_provider == oauth_provider,
        User.oauth_id == oauth_id
    ).first()

def create_user(db: Session, username: str, email: str, password: str) -> User:
    """일반 사용자 생성"""
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        subscription_tier="free"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_social_user(
    db: Session, 
    username: str, 
    email: str, 
    oauth_provider: str, 
    oauth_id: str, 
    profile_image: Optional[str] = None
) -> User:
    """소셜 로그인 사용자 생성"""
    db_user = User(
        username=username,
        email=email,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        profile_image=profile_image,
        subscription_tier="free"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_subscription(
    db: Session, 
    user_id: int, 
    subscription_tier: str, 
    duration_days: int = 30
) -> Optional[User]:
    """사용자 구독 상태 업데이트"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    user.subscription_tier = subscription_tier
    user.subscription_start = datetime.utcnow()
    user.subscription_end = datetime.utcnow() + timedelta(days=duration_days)
    user.payment_status = "active"
    
    db.commit()
    db.refresh(user)
    return user

def is_subscription_active(user: User) -> bool:
    """사용자 구독이 활성 상태인지 확인"""
    if user.subscription_tier == "free":
        return True
    
    if not user.subscription_end:
        return False
    
    return user.subscription_end > datetime.utcnow() and user.payment_status == "active" 