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
        # 이미 존재하는 채널인지 확인
        db_channel = crud.get_youtube_channel_by_id(db, channel_id=channel.channel_id)
        if db_channel:
            logger.warning(f"중복된 채널 ID: {channel.channel_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 채널입니다."
            )
        
        # 유튜브 API를 통해 채널 정보 확인 (옵션)
        youtube_service = YouTubeService()
        
        # 새 채널 추가
        try:
            return crud.create_youtube_channel(db=db, channel=channel)
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
        db_channel = crud.get_youtube_channel_by_id(db, channel_id=channel_id)
        if db_channel is None:
            logger.warning(f"존재하지 않는 채널 ID: {channel_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채널을 찾을 수 없습니다."
            )
        crud.delete_youtube_channel(db=db, channel_id=channel_id)
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
        # 채널 존재 여부 확인
        db_channel = crud.get_youtube_channel_by_id(db, channel_id=channel_id)
        if db_channel is None:
            logger.warning(f"존재하지 않는 채널 ID: {channel_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="채널을 찾을 수 없습니다."
            )
        
        # YouTube API 호출
        try:
            youtube_service = YouTubeService()
            videos = youtube_service.get_channel_videos(channel_id)
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
        logger.error(f"채널 비디오 검색 중 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류: {str(e)}"
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