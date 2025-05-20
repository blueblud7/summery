import sys
import os
import logging

# 프로젝트 루트 디렉토리를 PYTHONPATH에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import YoutubeChannel
from app.services.youtube_service import YouTubeService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_channel_ids():
    """
    URL 형태로 저장된 채널 ID를 실제 채널 ID로 변경합니다.
    """
    db = SessionLocal()
    youtube_service = YouTubeService()
    
    try:
        # URL이나 @ 형태로 저장된 채널 검색
        channels = db.query(YoutubeChannel).filter(
            (YoutubeChannel.channel_id.like('http%')) | 
            (YoutubeChannel.channel_id.like('@%'))
        ).all()
        
        logger.info(f"URL 형태의 채널 ID {len(channels)}개를 찾았습니다.")
        
        for channel in channels:
            old_channel_id = channel.channel_id
            logger.info(f"처리 중: {old_channel_id}")
            
            try:
                # 실제 채널 ID 가져오기
                channel_info = youtube_service.get_channel_info(old_channel_id)
                
                if "error" in channel_info:
                    logger.warning(f"채널 정보 가져오기 실패: {channel_info['error']}")
                    continue
                
                real_channel_id = channel_info['channel_id']
                
                # 이미 실제 ID로 존재하는지 확인
                existing = db.query(YoutubeChannel).filter(
                    YoutubeChannel.channel_id == real_channel_id
                ).first()
                
                if existing and existing.id != channel.id:
                    logger.warning(f"실제 ID {real_channel_id}가 이미 존재합니다. {old_channel_id} 채널을 삭제합니다.")
                    db.delete(channel)
                else:
                    # 채널 ID 업데이트
                    logger.info(f"채널 ID 변경: {old_channel_id} -> {real_channel_id}")
                    channel.channel_id = real_channel_id
                    channel.title = channel_info.get('title', channel.title)
                    channel.description = channel_info.get('description', channel.description)
                
                db.commit()
                
            except Exception as e:
                logger.error(f"채널 ID 변경 중 오류 ({old_channel_id}): {str(e)}")
                db.rollback()
        
        logger.info("작업 완료")
        
    except Exception as e:
        logger.error(f"전체 마이그레이션 중 오류: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("URL 형태의 채널 ID 수정 시작")
    fix_channel_ids()
    logger.info("URL 형태의 채널 ID 수정 완료") 