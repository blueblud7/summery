from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.models import Channel, Video
from app.services.youtube_service import YouTubeService
from app.services.summarizer_service import SummarizerService
from app.services.duplicate_checker import DuplicateChecker

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.youtube_service = YouTubeService()
        self.summarizer_service = SummarizerService()
        self.duplicate_checker = DuplicateChecker()
        
    def start(self):
        # 24시간마다 실행
        self.scheduler.add_job(
            self.check_new_videos,
            IntervalTrigger(hours=24),
            id='check_new_videos',
            replace_existing=True
        )
        self.scheduler.start()
    
    def check_new_videos(self):
        db = SessionLocal()
        try:
            # 모든 채널에 대해 새로운 비디오 확인
            channels = db.query(Channel).all()
            for channel in channels:
                self._check_channel_videos(channel, db)
        finally:
            db.close()
    
    def _check_channel_videos(self, channel: Channel, db: Session):
        # 마지막 확인 시간 이후의 비디오만 가져오기
        last_check = channel.videos[0].last_checked_at if channel.videos else datetime.min
        
        # YouTube API로 새 비디오 가져오기
        new_videos = self.youtube_service.get_channel_videos(
            channel.channel_id,
            max_results=50
        )
        
        for video_data in new_videos:
            # 이미 존재하는 비디오인지 확인
            existing_video = db.query(Video).filter(
                Video.video_id == video_data['video_id']
            ).first()
            
            if not existing_video:
                # 새 비디오 추가
                video = Video(
                    video_id=video_data['video_id'],
                    title=video_data['title'],
                    description=video_data['description'],
                    published_at=video_data['published_at'],
                    duration=video_data.get('duration'),
                    channel_id=channel.id,
                    last_checked_at=datetime.utcnow()
                )
                db.add(video)
                
                # 중복 체크
                if self.duplicate_checker.is_duplicate(video, db):
                    video.is_duplicate = True
                
                # 요약 생성
                if not video.is_duplicate:
                    video.summary = self.summarizer_service.summarize_text(
                        video.description,
                        max_length=video.summary_length
                    )
                    video.is_summarized = True
                
                db.commit() 