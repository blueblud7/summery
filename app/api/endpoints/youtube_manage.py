from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.db.models import YoutubeChannel as DBYoutubeChannel
from app.db.models import YoutubeKeyword as DBYoutubeKeyword
from app.models.youtube import (
    YoutubeChannel, 
    YoutubeChannelCreate, 
    YoutubeChannelUpdate,
    YoutubeKeyword,
    YoutubeKeywordCreate,
    YoutubeKeywordUpdate
)
from app.services.youtube_service import YouTubeService
from app.db import crud

router = APIRouter()
logger = logging.getLogger(__name__)

# 채널 관련 엔드포인트
@router.post("/channels/", response_model=YoutubeChannel, status_code=status.HTTP_201_CREATED)
def create_channel(channel: YoutubeChannelCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"채널 생성 요청: {channel.channel_id}")
        
        # 유튜브 API를 통해 채널 정보 확인
        youtube_service = YouTubeService()
        
        # URL 또는 핸들인 경우 실제 채널 ID 추출
        channel_info = youtube_service.get_channel_info(channel.channel_id)
        if "error" in channel_info:
            logger.warning(f"채널 정보 가져오기 실패: {channel_info['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 채널 ID 또는 URL: {channel_info['error']}"
            )
        
        # 실제 채널 ID로 업데이트
        real_channel_id = channel_info['channel_id']
        
        # 로그 추가 - 디버깅을 위한 정보 출력
        logger.info(f"검색된 채널 정보: ID={real_channel_id}, 제목={channel_info.get('title', '제목 없음')}")
        
        # 이미 존재하는 채널인지 확인 (실제 채널 ID로)
        db_channel = crud.get_youtube_channel_by_id(db, channel_id=real_channel_id)
        if db_channel:
            logger.warning(f"중복된 채널 ID: {real_channel_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 채널입니다."
            )
            
        # URL 형태로 저장된 채널도 확인
        if channel.channel_id.startswith('http') or channel.channel_id.startswith('@'):
            url_channel = db.query(DBYoutubeChannel).filter(DBYoutubeChannel.channel_id == channel.channel_id).first()
            if url_channel:
                logger.warning(f"URL 형태로 이미 등록된 채널: {channel.channel_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 채널입니다."
                )
            
        # 새 채널 추가
        try:
            # 채널 객체 업데이트 - 항상 실제 채널 ID 사용
            channel_obj = YoutubeChannelCreate(
                channel_id=real_channel_id,  # 실제 채널 ID 저장
                title=channel_info.get('title', ''),
                description=channel_info.get('description', '')
            )
            return crud.create_youtube_channel(db=db, channel=channel_obj)
        except Exception as e:
            logger.error(f"채널 추가 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"채널 추가 중 오류가 발생했습니다: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류: {str(e)}"
        )

@router.get("/channels/", response_model=List[YoutubeChannel])
def read_channels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        logger.info(f"채널 목록 조회 요청: skip={skip}, limit={limit}")
        channels = crud.get_youtube_channels(db, skip=skip, limit=limit)
        return channels
    except Exception as e:
        logger.error(f"채널 목록 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채널 목록을 불러오는 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/channels/{channel_id}", response_model=YoutubeChannel)
def read_channel(channel_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"채널 조회 요청: {channel_id}")
        db_channel = crud.get_youtube_channel_by_id(db, channel_id=channel_id)
        if db_channel is None:
            logger.warning(f"존재하지 않는 채널 ID: {channel_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채널을 찾을 수 없습니다."
            )
        return db_channel
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채널 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채널 정보를 불러오는 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/channels/{channel_id}", response_model=YoutubeChannel)
def update_channel(channel_id: str, channel: YoutubeChannelUpdate, db: Session = Depends(get_db)):
    try:
        logger.info(f"채널 업데이트 요청: {channel_id}")
        db_channel = crud.get_youtube_channel_by_id(db, channel_id=channel_id)
        if db_channel is None:
            logger.warning(f"존재하지 않는 채널 ID: {channel_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채널을 찾을 수 없습니다."
            )
        return crud.update_youtube_channel(db=db, channel_id=channel_id, channel=channel)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채널 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채널 정보를 업데이트하는 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel(channel_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"채널 삭제 요청: {channel_id}")
        
        # URL 디코딩이 필요한 경우
        try:
            from urllib.parse import unquote
            decoded_channel_id = unquote(channel_id)
            if decoded_channel_id != channel_id:
                logger.info(f"URL 디코딩된 채널 ID: {decoded_channel_id}")
                channel_id = decoded_channel_id
        except Exception as e:
            logger.warning(f"URL 디코딩 중 오류: {str(e)}")
        
        # 삭제 시도
        result = crud.delete_youtube_channel(db=db, channel_id=channel_id)
        
        if not result:
            # DB에 있는 모든 채널을 불러와서 ID가 포함된 채널이 있는지 확인
            all_channels = crud.get_youtube_channels(db)
            for db_channel in all_channels:
                if channel_id in db_channel.channel_id:
                    logger.info(f"부분 일치하는 채널 삭제: {db_channel.channel_id}")
                    crud.delete_youtube_channel(db=db, channel_id=db_channel.channel_id)
                    return Response(status_code=status.HTTP_204_NO_CONTENT)
            
            # 채널을 찾지 못한 경우
            logger.warning(f"삭제할 채널을 찾을 수 없음: {channel_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채널을 찾을 수 없습니다."
            )
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채널 삭제 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채널을 삭제하는 중 오류가 발생했습니다: {str(e)}"
        )

# 키워드 관련 엔드포인트
@router.post("/keywords/", response_model=YoutubeKeyword, status_code=status.HTTP_201_CREATED)
def create_keyword(keyword: YoutubeKeywordCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"키워드 생성 요청: {keyword.keyword}")
        # 이미 존재하는 키워드인지 확인
        db_keyword = crud.get_youtube_keyword_by_value(db, keyword_value=keyword.keyword)
        if db_keyword:
            logger.warning(f"중복된 키워드: {keyword.keyword}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 키워드입니다."
            )
        # 새 키워드 추가
        try:
            return crud.create_youtube_keyword(db=db, keyword=keyword)
        except Exception as e:
            logger.error(f"키워드 추가 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"키워드 추가 중 오류가 발생했습니다: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류: {str(e)}"
        )

@router.get("/keywords/", response_model=List[YoutubeKeyword])
def read_keywords(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        logger.info(f"키워드 목록 조회 요청: skip={skip}, limit={limit}")
        keywords = crud.get_youtube_keywords(db, skip=skip, limit=limit)
        return keywords
    except Exception as e:
        logger.error(f"키워드 목록 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"키워드 목록을 불러오는 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/keywords/{keyword_id}", response_model=YoutubeKeyword)
def read_keyword(keyword_id: int, db: Session = Depends(get_db)):
    try:
        logger.info(f"키워드 조회 요청: ID={keyword_id}")
        db_keyword = crud.get_youtube_keyword(db, keyword_id=keyword_id)
        if db_keyword is None:
            logger.warning(f"존재하지 않는 키워드 ID: {keyword_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="키워드를 찾을 수 없습니다."
            )
        return db_keyword
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"키워드 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"키워드 정보를 불러오는 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/keywords/{keyword_id}", response_model=YoutubeKeyword)
def update_keyword(keyword_id: int, keyword: YoutubeKeywordUpdate, db: Session = Depends(get_db)):
    try:
        logger.info(f"키워드 업데이트 요청: ID={keyword_id}")
        db_keyword = crud.get_youtube_keyword(db, keyword_id=keyword_id)
        if db_keyword is None:
            logger.warning(f"존재하지 않는 키워드 ID: {keyword_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="키워드를 찾을 수 없습니다."
            )
        return crud.update_youtube_keyword(db=db, keyword_id=keyword_id, keyword=keyword)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"키워드 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"키워드 정보를 업데이트하는 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/keywords/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    try:
        logger.info(f"키워드 삭제 요청: ID={keyword_id}")
        db_keyword = crud.get_youtube_keyword(db, keyword_id=keyword_id)
        if db_keyword is None:
            logger.warning(f"존재하지 않는 키워드 ID: {keyword_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="키워드를 찾을 수 없습니다."
            )
        crud.delete_youtube_keyword(db=db, keyword_id=keyword_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"키워드 삭제 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"키워드를 삭제하는 중 오류가 발생했습니다: {str(e)}"
        )

# 검색 관련 엔드포인트
@router.get("/search/by-channel/{channel_id}", response_model=List[dict])
def search_videos_by_channel(channel_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"채널 비디오 검색 요청: channel_id={channel_id}")
        
        # YouTube API 서비스 생성
        youtube_service = YouTubeService()
        
        # URL 형태의 채널 ID인 경우 실제 채널 ID 추출 시도
        if channel_id.startswith('http') or channel_id.startswith('@') or channel_id.startswith('c/') or channel_id.startswith('user/'):
            logger.info(f"URL 또는 핸들 형식의 채널 ID 처리: {channel_id}")
            
            # 채널 정보 조회를 통해 실제 채널 ID 얻기
            channel_info = youtube_service.get_channel_info(channel_id)
            if "error" in channel_info:
                logger.warning(f"채널 정보 가져오기 실패: {channel_info['error']}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"채널을 찾을 수 없습니다: {channel_info['error']}"
                )
            
            real_channel_id = channel_info['channel_id']
            logger.info(f"URL에서 추출한 실제 채널 ID: {real_channel_id}")
            channel_id = real_channel_id
        
        # 실제 채널 ID로 DB에서 채널 확인
        db_channel = crud.get_youtube_channel_by_id(db, channel_id=channel_id)
        if db_channel is None:
            # DB에 채널이 없는 경우, 직접 YouTube API로 검색
            logger.info(f"DB에 등록되지 않은 채널이지만 직접 YouTube API로 검색 시도: {channel_id}")
            
            # YouTube API 호출하여 비디오 가져오기
            videos = youtube_service.get_channel_videos(channel_id)
            if not videos:
                logger.warning(f"채널 비디오를 찾을 수 없음: {channel_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="채널을 찾을 수 없거나 비디오가 없습니다."
                )
            
            logger.info(f"직접 API 검색으로 {len(videos)}개 비디오 발견")
            return videos
        
        # DB에 등록된 채널인 경우
        logger.info(f"DB에 등록된 채널: {db_channel.channel_id}")
        
        # YouTube API 호출
        logger.info(f"YouTube API 채널 비디오 검색 시작: 채널 ID={db_channel.channel_id}")
        videos = youtube_service.get_channel_videos(db_channel.channel_id)
        logger.info(f"YouTube API 채널 비디오 검색 결과: {len(videos)}개 비디오 발견")
        
        return videos
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채널 비디오 검색 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"채널 비디오를 검색하는 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/search/by-keyword/{keyword}", response_model=List[dict])
def search_videos_by_keyword(keyword: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"키워드 비디오 검색 요청: keyword={keyword}")
        # 키워드 존재 여부 확인
        db_keyword = crud.get_youtube_keyword_by_value(db, keyword_value=keyword)
        if db_keyword is None:
            logger.warning(f"존재하지 않는 키워드: {keyword}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="키워드를 찾을 수 없습니다."
            )
        
        # YouTube API 호출
        try:
            youtube_service = YouTubeService()
            videos = youtube_service.search_videos_by_keyword(keyword)
            return videos
        except Exception as e:
            logger.error(f"YouTube API 호출 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"영상 검색 중 오류가 발생했습니다: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"키워드 비디오 검색 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류: {str(e)}"
        ) 