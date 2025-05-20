from googleapiclient.discovery import build
from datetime import datetime, timedelta
from app.core.config import settings
from typing import List, Dict, Any, Optional
import random
import logging
import os
import re
from googleapiclient.errors import HttpError
import time

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self, use_mock_data: bool = False):
        # API 키 체크
        self.api_key = settings.YOUTUBE_API_KEY
        self.use_mock_data = use_mock_data or not self.api_key
        self.youtube = None
        
        # API 키가 설정되어 있고 모의 데이터를 사용하지 않는 경우에만 클라이언트 생성
        if not self.use_mock_data and self.api_key:
            try:
                self.youtube = self._create_youtube_client()
                logger.info("YouTube API 클라이언트가 성공적으로 생성되었습니다.")
            except Exception as e:
                logger.error(f"YouTube API 클라이언트 생성 오류: {e}")
                self.use_mock_data = True
                self.youtube = None
        else:
            if not self.api_key:
                logger.warning("YouTube API 키가 설정되지 않았습니다. 모의 데이터를 사용합니다.")
            self.use_mock_data = True

    def _create_youtube_client(self):
        """YouTube API 클라이언트를 생성합니다."""
        return build('youtube', 'v3', developerKey=self.api_key)

    def _switch_api_key(self):
        """할당량 초과 시 다른 API 키로 전환합니다."""
        old_key = self.api_key
        new_key = settings.next_youtube_api_key()
        if new_key != old_key:
            self.api_key = new_key
            logger.info(f"YouTube API 키가 변경되었습니다: {old_key[:5]}... -> {new_key[:5]}...")
            self.youtube = self._create_youtube_client()
            return True
        return False

    def _make_request(self, request_func, mock_data_func=None):
        """API 요청을 수행하고 할당량 초과 시 키를 전환합니다."""
        if self.use_mock_data and mock_data_func:
            logger.info("모의 데이터를 사용합니다.")
            return mock_data_func()
            
        retry_count = 0
        max_retries = min(10, len(settings.youtube_api_keys_list))
        
        while retry_count < max_retries:
            try:
                return request_func()
            except HttpError as e:
                # 할당량 초과 오류 (403 Forbidden + "quota" 문자열 포함)
                if e.resp.status == 403 and "quota" in str(e).lower():
                    logger.warning(f"YouTube API 할당량 초과: {e}")
                    if self._switch_api_key():
                        retry_count += 1
                        continue
                    else:
                        logger.error("사용 가능한 YouTube API 키가 더 이상 없습니다.")
                        break
                else:
                    logger.error(f"YouTube API 오류: {e}")
                    break
            except Exception as e:
                logger.error(f"API 요청 오류: {e}")
                break
        
        # 모든 재시도 실패 후
        if mock_data_func:
            logger.info("오류 발생으로 모의 데이터로 대체합니다.")
            return mock_data_func()
        else:
            raise Exception("YouTube API 요청 실패")

    # 채널 정보에 대한 모의 데이터
    def _mock_channel_info(self, channel_id: str) -> Dict[str, Any]:
        return {
            'channel_id': channel_id,
            'title': f'모의 채널 {channel_id}',
            'description': '이것은 API 키가 없을 때 사용되는 모의 채널 정보입니다.'
        }

    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        # 채널 ID 또는 URL에서 실제 ID 추출
        if channel_id.startswith('http'):
            extracted_id = self.extract_channel_id(channel_id)
            if extracted_id:
                channel_id = extracted_id
            else:
                logger.error(f"유효하지 않은 채널 URL: {channel_id}")
                return {"error": "Invalid channel URL"}
        
        # '@' 형식의 핸들 처리
        if channel_id.startswith('@'):
            def request_by_handle():
                # 핸들로 채널 검색 - 더 정확한 검색을 위해 정확한 채널명 검색
                handle = channel_id  # 예: @yunjadong
                
                # 정확한 채널명 검색을 위한 쿼리 구성
                request = self.youtube.search().list(
                    part="snippet",
                    q=handle,
                    type="channel",
                    maxResults=1
                )
                response = request.execute()
                
                if not response.get('items'):
                    logger.error(f"채널 핸들에 해당하는 채널을 찾을 수 없음: {channel_id}")
                    return {"error": "Channel not found"}
                
                channel_item = response['items'][0]
                real_channel_id = channel_item['id']['channelId']
                
                # 실제 채널 ID로 추가 정보 요청
                channel_request = self.youtube.channels().list(
                    part="snippet",
                    id=real_channel_id
                )
                channel_response = channel_request.execute()
                
                if not channel_response['items']:
                    return {"error": "Channel details not found"}
                    
                channel = channel_response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description']
                }
            
            return self._make_request(request_by_handle, lambda: self._mock_channel_info(channel_id))
        # 이전 사용자 정의 URL 형식 처리
        elif channel_id.startswith('c/') or channel_id.startswith('user/'):
            def request_by_custom_url():
                # 사용자 정의 URL로 채널 검색
                username = channel_id.split('/', 1)[1]
                request = self.youtube.search().list(
                    part="snippet",
                    q=username,
                    type="channel",
                    maxResults=1
                )
                response = request.execute()
                
                if not response.get('items'):
                    logger.error(f"사용자 정의 URL에 해당하는 채널을 찾을 수 없음: {channel_id}")
                    return {"error": "Channel not found"}
                
                channel_item = response['items'][0]
                real_channel_id = channel_item['id']['channelId']
                
                # 실제 채널 ID로 추가 정보 요청
                channel_request = self.youtube.channels().list(
                    part="snippet",
                    id=real_channel_id
                )
                channel_response = channel_request.execute()
                
                if not channel_response['items']:
                    return {"error": "Channel details not found"}
                    
                channel = channel_response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description']
                }
            
            return self._make_request(request_by_custom_url, lambda: self._mock_channel_info(channel_id))
        else:
            # 기존 채널 ID 처리 방식
            def request():
                request = self.youtube.channels().list(
                    part="snippet",
                    id=channel_id
                )
                response = request.execute()
                
                if not response['items']:
                    return {"error": "Channel not found"}
                    
                channel = response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description']
                }
            
            return self._make_request(request, lambda: self._mock_channel_info(channel_id))

    # 키워드 검색에 대한 모의 데이터
    def _mock_videos_by_keyword(self, keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
        videos = []
        for i in range(min(max_results, 10)):
            videos.append({
                'video_id': f'mock_video_{i}',
                'title': f'모의 비디오 {i}: {keyword} 관련',
                'description': f'{keyword}에 관한 모의 비디오 설명입니다.',
                'published_at': datetime.now() - timedelta(days=i),
                'channel_id': 'mock_channel_id',
                'channel_title': '모의 채널'
            })
        return videos

    def search_videos_by_keyword(self, keyword: str, max_results: int = 50) -> List[Dict[str, Any]]:
        def request():
            request = self.youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                maxResults=max_results,
                order="date"
            )
            response = request.execute()
            
            videos = []
            for item in response['items']:
                video = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': datetime.strptime(
                        item['snippet']['publishedAt'],
                        '%Y-%m-%dT%H:%M:%SZ'
                    ),
                    'channel_id': item['snippet']['channelId'],
                    'channel_title': item['snippet']['channelTitle']
                }
                videos.append(video)
                
            return videos
        
        return self._make_request(request, lambda: self._mock_videos_by_keyword(keyword, max_results))

    # 채널 비디오에 대한 모의 데이터
    def _mock_channel_videos(self, channel_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        videos = []
        for i in range(min(max_results, 10)):
            videos.append({
                'video_id': f'mock_video_{i}',
                'title': f'모의 채널 비디오 {i}',
                'description': f'채널 {channel_id}의 모의 비디오 설명입니다.',
                'published_at': datetime.now() - timedelta(days=i),
                'channel_id': channel_id,
                'channel_title': f'모의 채널 {channel_id}'
            })
        return videos

    def get_channel_videos(self, channel_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        def request():
            try:
                # First, get the uploads playlist ID
                logger.info(f"채널 정보 요청: 채널 ID={channel_id}")
                request = self.youtube.channels().list(
                    part="contentDetails,snippet",
                    id=channel_id
                )
                response = request.execute()
                
                if not response.get('items'):
                    logger.warning(f"채널 {channel_id}에 대한 정보를 찾을 수 없음")
                    
                    # 채널 ID가 핸들 또는 사용자 정의 URL인 경우 검색 시도
                    if channel_id.startswith('@') or channel_id.startswith('c/') or channel_id.startswith('user/'):
                        logger.info(f"핸들 또는 커스텀 URL을 사용해 채널 검색 시도: {channel_id}")
                        return self.search_by_handle_or_custom_url(channel_id)
                    
                    return []
                
                channel = response['items'][0]
                channel_title = channel['snippet']['title']
                logger.info(f"채널 제목: {channel_title}")
                
                # Get the uploads playlist ID
                uploads_playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']
                logger.info(f"업로드 플레이리스트 ID: {uploads_playlist_id}")
                
                # Now get the videos from the uploads playlist
                logger.info(f"채널 업로드 비디오 요청: 플레이리스트 ID={uploads_playlist_id}")
                request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=max_results
                )
                response = request.execute()
                
                videos = []
                video_ids = []
                for item in response.get('items', []):
                    video_ids.append(item['snippet']['resourceId']['videoId'])
                    
                logger.info(f"총 {len(response.get('items', []))}개의 비디오 항목을 가져왔습니다.")
                
                # 비디오 상세 정보(조회수, 좋아요 수 등) 가져오기
                if video_ids:
                    batch_size = 50  # YouTube API 최대 제한
                    video_details = {}
                    
                    for i in range(0, len(video_ids), batch_size):
                        batch = video_ids[i:i + batch_size]
                        details_request = self.youtube.videos().list(
                            part="snippet,statistics,contentDetails",
                            id=",".join(batch)
                        )
                        details_response = details_request.execute()
                        
                        for video in details_response.get('items', []):
                            video_details[video['id']] = video
                    
                    # 비디오 정보 구성
                    for item in response.get('items', []):
                        video_id = item['snippet']['resourceId']['videoId']
                        video_data = {
                            'video_id': video_id,
                            'title': item['snippet']['title'],
                            'description': item['snippet'].get('description', ''),
                            'thumbnail': item['snippet']['thumbnails'].get('high', {}).get('url', 
                                          item['snippet']['thumbnails'].get('medium', {}).get('url', 
                                          item['snippet']['thumbnails'].get('default', {}).get('url', ''))),
                            'published_at': item['snippet'].get('publishedAt', ''),
                            'channel_title': channel_title
                        }
                        
                        # 상세 정보가 있으면 추가
                        if video_id in video_details:
                            details = video_details[video_id]
                            stats = details.get('statistics', {})
                            video_data.update({
                                'view_count': int(stats.get('viewCount', 0)),
                                'like_count': int(stats.get('likeCount', 0)),
                                'comment_count': int(stats.get('commentCount', 0)),
                                'duration': details.get('contentDetails', {}).get('duration', '')
                            })
                        
                        videos.append(video_data)
                
                return videos
                
            except Exception as e:
                logger.error(f"채널 비디오 가져오기 오류: {str(e)}")
                return []
        
        try:
            retries = 3
            while retries > 0:
                try:
                    return request()
                except HttpError as e:
                    logger.warning(f"YouTube API HTTP 오류: {str(e)}")
                    if e.resp.status in [429, 500, 503]:
                        retries -= 1
                        time.sleep(1)  # 재시도 전 잠시 대기
                    else:
                        raise
            return []
        except Exception as e:
            logger.error(f"채널 비디오 요청 중 오류 발생: {str(e)}")
            return []

    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """
        유튜브 동영상의 기본 정보를 가져옵니다.
        """
        try:
            if not self.youtube:
                # 모의 데이터 반환
                return {
                    "title": f"모의 비디오 {video_id}",
                    "description": "이것은 모의 비디오 설명입니다.",
                    "channel": "모의 채널",
                    "published_at": datetime.now().isoformat(),
                    "duration": "PT5M30S",
                    "view_count": "1000",
                    "like_count": "100"
                }
                
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )
            response = request.execute()
            
            if not response["items"]:
                return {"error": "Video not found"}
            
            video_data = response["items"][0]
            return {
                "title": video_data["snippet"]["title"],
                "description": video_data["snippet"]["description"],
                "channel": video_data["snippet"]["channelTitle"],
                "published_at": video_data["snippet"]["publishedAt"],
                "duration": video_data["contentDetails"]["duration"],
                "view_count": video_data["statistics"].get("viewCount", 0),
                "like_count": video_data["statistics"].get("likeCount", 0)
            }
        except Exception as e:
            logger.error(f"Error fetching video info: {str(e)}")
            return {"error": str(e)}
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        유튜브 URL에서 비디오 ID를 추출합니다.
        """
        youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(youtube_regex, url)
        if match:
            return match.group(1)
        return None
    
    def extract_channel_id(self, url: str) -> Optional[str]:
        """
        유튜브 URL에서 채널 ID 또는 핸들을 추출합니다.
        지원 형식:
        - youtube.com/channel/UC... (채널 ID)
        - youtube.com/@handle (핸들)
        - youtube.com/c/custom (사용자 정의 URL)
        - youtube.com/user/username (이전 형식)
        """
        # 채널 ID 형식 (UC로 시작하는 ID)
        channel_id_regex = r'youtube\.com\/channel\/([a-zA-Z0-9_-]+)'
        match = re.search(channel_id_regex, url)
        if match:
            return match.group(1)
        
        # @ 핸들 형식
        handle_regex = r'youtube\.com\/@([a-zA-Z0-9_-]+)'
        match = re.search(handle_regex, url)
        if match:
            # 핸들을 반환하고, 나중에 채널 ID로 변환
            return '@' + match.group(1)
        
        # 사용자 정의 URL (c/)
        custom_regex = r'youtube\.com\/c\/([a-zA-Z0-9_-]+)'
        match = re.search(custom_regex, url)
        if match:
            return 'c/' + match.group(1)
        
        # 이전 사용자 URL (user/)
        user_regex = r'youtube\.com\/user\/([a-zA-Z0-9_-]+)'
        match = re.search(user_regex, url)
        if match:
            return 'user/' + match.group(1)
        
        # 입력이 이미 채널 ID이거나 핸들인 경우
        if url.startswith('@') or url.startswith('UC') or url.startswith('c/') or url.startswith('user/'):
            return url
            
        return None
    
    def get_transcript(self, video_id: str, language_code: str = 'ko') -> List[Dict[str, Any]]:
        """
        유튜브 동영상의 자막을 가져옵니다.
        언어 우선순위: 지정 언어 -> 자동 생성된 지정 언어 -> 영어 -> 어떤 언어든 가능한 것 -> 대체 방법(pytube) 시도
        """
        # 모의 데이터 반환
        if self.use_mock_data:
            mock_transcript = []
            # 10개의 모의 자막 생성
            for i in range(10):
                mock_transcript.append({
                    "text": f"이것은 모의 자막 {i+1}번째 문장입니다.",
                    "start": i * 2.0,
                    "duration": 2.0
                })
            return mock_transcript
            
        try:
            # 먼저 pytube를 통해 직접 자막 시도
            try:
                logger.info(f"먼저 pytube를 통해 직접 자막을 가져오려고 시도합니다: {video_id}")
                transcript = self._get_transcript_directly_from_pytube(video_id, language_code)
                if transcript:
                    logger.info(f"pytube로 직접 자막을 성공적으로 가져왔습니다.")
                    return transcript
            except Exception as pytube_e:
                logger.warning(f"pytube로 직접 자막 가져오기 실패: {str(pytube_e)}")
            
            # pytube 실패 시 youtube_transcript_api 사용
            from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, NoTranscriptAvailable
            
            try:
                # 1. 먼저 지정된 언어로 시도
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language_code])
                logger.info(f"지정된 언어({language_code})로 자막을 찾았습니다.")
                return transcript
            except (NoTranscriptFound, NoTranscriptAvailable) as e:
                logger.warning(f"지정된 언어({language_code})로 자막을 찾을 수 없습니다: {str(e)}")
                
                try:
                    # 2. 자동 생성된 지정 언어 자막 시도 (asr: Auto Speech Recognition)
                    auto_language_code = f"{language_code}-generated"
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[auto_language_code])
                    logger.info(f"자동 생성된 자막({auto_language_code})을 찾았습니다.")
                    return transcript
                except Exception as e:
                    logger.warning(f"자동 생성된 자막(generated)도 찾을 수 없습니다: {str(e)}")
                    
                    try:
                        # 2-1. 새로운 방법: asr 태그로 자동 생성된 자막 시도
                        asr_auto_lang = f"asr-{language_code}"
                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[asr_auto_lang])
                        logger.info(f"ASR 자동 생성된 자막({asr_auto_lang})을 찾았습니다.")
                        return transcript
                    except Exception as e:
                        logger.warning(f"ASR 자동 생성된 자막도 찾을 수 없습니다: {str(e)}")
                        
                        # 3. 영어 자막 시도 (일반 영어와 자동 생성 영어)
                        for lang in ["en", "en-generated", "asr-en"]:
                            try:
                                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                                logger.info(f"{lang} 자막을 찾았습니다.")
                                return transcript
                            except Exception as inner_e:
                                logger.warning(f"{lang} 자막을 찾을 수 없습니다: {str(inner_e)}")
                        
                        # 영어 자막도 없는 경우
                        logger.warning("영어 자막도 찾을 수 없습니다.")
                        
                        try:
                            # 4. 사용 가능한 모든 자막 나열 및 첫 번째 시도
                            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                            available_transcripts = list(transcript_list)
                            
                            if available_transcripts:
                                logger.info(f"사용 가능한 자막 목록: {[t.language_code for t in available_transcripts]}")
                                first_transcript = available_transcripts[0]
                                transcript = first_transcript.fetch()
                                logger.info(f"사용 가능한 자막을 찾았습니다: {first_transcript.language_code}")
                                return transcript
                            else:
                                logger.warning("사용 가능한 자막이 없습니다.")
                                
                        except Exception as e:
                            logger.warning(f"사용 가능한 자막을 찾을 수 없습니다: {str(e)}")
                        
                        # 5. 대체 방법: pytube 시도
                        logger.info("대체 방법으로 pytube를 사용하여 자막을 가져오려고 시도합니다.")
                        return self._get_transcript_via_pytube(video_id)
                            
            except TranscriptsDisabled as e:
                logger.warning(f"이 비디오에는 자막이 비활성화되어 있습니다: {str(e)}")
                # pytube로 대체 시도
                return self._get_transcript_via_pytube(video_id)
                            
        except ImportError:
            logger.error("youtube_transcript_api 모듈을 설치해주세요: pip install youtube-transcript-api")
            # pytube로 대체 시도
            return self._get_transcript_via_pytube(video_id)
            
        except Exception as e:
            logger.error(f"자막 가져오기 오류: {str(e)}")
            return []
    
    def _get_transcript_directly_from_pytube(self, video_id: str, language_code: str = 'ko') -> List[Dict[str, Any]]:
        """
        pytube를 사용하여 직접 자막을 가져오는 방법
        """
        try:
            from pytube import YouTube, innertube
            
            logger.info(f"먼저 pytube를 통해 직접 자막을 가져오려고 시도합니다: {video_id}")
            
            # InnerTube 클라이언트 생성 (최신 버전 호환성)
            try:
                # 최신 버전 pytube는 use_json 매개변수가 없음
                client = innertube.InnerTube(client="WEB")
            except Exception as e:
                logger.error(f"InnerTube 클라이언트 생성 오류: {str(e)}")
                # 다른 방법으로 자막 가져오기 시도
                return []
            
            # 비디오 정보 및 자막 트랙 가져오기
            try:
                result = client.get_transcript(video_id)
            except Exception as e:
                logger.error(f"자막 트랙 가져오기 오류: {str(e)}")
                return []
                
            if not result:
                logger.warning(f"비디오 {video_id}에 대한 자막 트랙을 찾을 수 없습니다.")
                return []

            # 자막 데이터 처리
            try:
                transcript_data = []
                for item in result.get('events', []):
                    if 'segs' not in item:
                        continue
                        
                    start_time = float(item.get('tStartMs', 0)) / 1000
                    duration = float(item.get('dDurationMs', 0)) / 1000
                    
                    text_segments = []
                    for seg in item.get('segs', []):
                        if 'utf8' in seg:
                            text_segments.append(seg['utf8'])
                    
                    text = ' '.join(text_segments).strip()
                    if text:
                        transcript_data.append({
                            'start': start_time,
                            'duration': duration,
                            'text': text
                        })
                
                return transcript_data
            except Exception as e:
                logger.error(f"자막 데이터 처리 중 오류: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"pytube 직접 자막 가져오기 오류: {str(e)}")
            return []
    
    def _get_transcript_via_pytube(self, video_id: str) -> List[Dict[str, Any]]:
        """
        pytube를 사용하여 자막을 가져오는 대체 방법
        """
        try:
            from pytube import YouTube
            
            # YouTube 객체 생성
            url = f"https://www.youtube.com/watch?v={video_id}"
            yt = YouTube(url)
            
            # 자막 가져오기 시도
            caption_tracks = yt.captions
            if caption_tracks:
                # 첫 번째로 사용 가능한 자막 선택
                caption = next(iter(caption_tracks.values()))
                xml_captions = caption.xml_captions
                
                # XML 자막을 파싱하여 텍스트 추출
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(xml_captions)
                    transcript = []
                    for i, element in enumerate(root.findall('./text')):
                        start = float(element.get('start', i * 5.0))
                        duration = float(element.get('dur', 5.0))
                        text = element.text or ""
                        transcript.append({
                            "text": text.strip(),
                            "start": start,
                            "duration": duration
                        })
                    logger.info("pytube를 사용하여 자막을 가져왔습니다.")
                    return transcript
                except Exception as e:
                    logger.error(f"pytube XML 자막 파싱 오류: {str(e)}")
                    
                    # 단순 텍스트로 반환하는 대체 방법
                    caption_text = caption.generate_srt_captions()
                    if caption_text:
                        lines = caption_text.split('\n\n')
                        transcript = []
                        for i, line in enumerate(lines):
                            if line.strip():
                                try:
                                    parts = line.split('\n')
                                    if len(parts) >= 3:
                                        # SRT 형식: 인덱스, 시간, 텍스트
                                        time_parts = parts[1].split(' --> ')
                                        start_time = self._srt_time_to_seconds(time_parts[0])
                                        text = ' '.join(parts[2:])
                                        transcript.append({
                                            "text": text.strip(),
                                            "start": start_time,
                                            "duration": 5.0  # 추정값
                                        })
                                except Exception as parse_err:
                                    logger.warning(f"SRT 라인 파싱 오류: {str(parse_err)}")
                        
                        if transcript:
                            logger.info("pytube를 사용하여 SRT 자막을 가져왔습니다.")
                            return transcript
            
            # 자막이 없는 경우 비디오 제목과 설명으로 대체
            logger.warning("자막을 찾을 수 없어 비디오 제목과 설명으로 대체합니다.")
            title = yt.title or ""
            description = yt.description or ""
            if title or description:
                transcript = [
                    {"text": title, "start": 0.0, "duration": 5.0}
                ]
                
                # 설명을 여러 조각으로 나누기
                if description:
                    paragraphs = description.split('\n\n')
                    for i, para in enumerate(paragraphs):
                        if para.strip():
                            transcript.append({
                                "text": para.strip(),
                                "start": (i + 1) * 5.0,
                                "duration": 5.0
                            })
                
                return transcript
                
        except ImportError:
            logger.error("pytube 모듈을 설치해주세요: pip install pytube")
        except Exception as e:
            logger.error(f"pytube를 사용한 자막 가져오기 오류: {str(e)}")
        
        return []
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """
        SRT 시간 형식(HH:MM:SS,MS)을 초 단위 float로 변환
        """
        try:
            hours, minutes, seconds = time_str.replace(',', '.').split(':')
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            return total_seconds
        except Exception as e:
            logger.warning(f"SRT 시간 변환 오류: {str(e)}")
            return 0.0
    
    def transcript_to_text(self, transcript: List[Dict[str, Any]]) -> str:
        """
        자막 데이터를 텍스트로 변환합니다.
        """
        if not transcript:
            return "자막을 가져올 수 없습니다."
            
        text = ""
        for item in transcript:
            text += item["text"] + " "
        return text.strip()
    
    def get_video_transcript_text(self, video_id: str, language_code: str = 'ko') -> str:
        """
        비디오 ID에 해당하는 자막을 텍스트로 변환합니다.
        """
        try:
            transcript = self.get_transcript(video_id, language_code)
            if not transcript:
                return ""
                
            return self.transcript_to_text(transcript)
        except Exception as e:
            logger.error(f"자막 텍스트 변환 중 오류: {str(e)}")
            return ""
    
    def summarize_video(self, video_url: str, language_code: str = 'ko', model: str = None) -> Dict[str, Any]:
        """
        유튜브 동영상 URL을 받아 정보와 자막 텍스트를 요약하여 반환합니다.
        """
        try:
            from app.services.summarizer_service import SummarizerService
            
            logger.info(f"유튜브 영상 요약 시작: {video_url}")
            
            video_id = self.extract_video_id(video_url)
            if not video_id:
                logger.error(f"유효하지 않은 YouTube URL: {video_url}")
                return {"error": "유효하지 않은 YouTube URL입니다."}
            
            # 비디오 정보 가져오기
            video_info = self.get_video_info(video_id)
            if "error" in video_info:
                logger.error(f"비디오 정보 가져오기 실패: {video_info['error']}")
                return video_info
            
            logger.info(f"비디오 정보 가져오기 성공: {video_info.get('title', '제목 없음')}")
            
            # 자막 가져오기
            transcript_text = self.get_video_transcript_text(video_id, language_code)
            if not transcript_text:
                logger.warning(f"자막을 가져올 수 없습니다. 비디오 설명으로 대체합니다: {video_id}")
                # 자막 대신 비디오 설명 사용
                transcript_text = "자막을 가져올 수 없습니다."
                if 'description' in video_info and video_info['description']:
                    transcript_text += "\n\n비디오 설명:\n" + video_info['description']
            
            # 요약 서비스 호출
            summarizer = SummarizerService(model=model)
            
            # 자막이 너무 짧으면 요약 정보 제공
            if len(transcript_text) < 50:
                logger.warning(f"자막이 너무 짧아 요약을 생성하지 않습니다: {len(transcript_text)}자")
                summary_result = {"summary": transcript_text}
                keywords = ["자막 없음"]
                evaluation = {"accuracy": 0, "completeness": 0, "coherence": 0}
            else:
                # 텍스트 요약
                summary_result = summarizer.summarize_text(
                    text=transcript_text,
                    style="detailed",  # mode 대신 style 매개변수 사용
                    max_length=300,
                    language=language_code
                )
                
                # 키워드 추출
                keywords = summarizer.extract_key_phrases(transcript_text)
                
                # 요약 품질 평가
                evaluation = summarizer.evaluate_summary_quality(transcript_text, summary_result["summary"])
            
            # 결과 반환
            return {
                "video_id": video_id,
                "title": video_info.get("title", ""),
                "channel": video_info.get("channel", ""),
                "publish_date": video_info.get("published_at", ""),
                "views": video_info.get("view_count", 0),
                "likes": video_info.get("like_count", 0),
                "transcript": transcript_text,
                "summary": summary_result["summary"],
                "keywords": keywords,
                "evaluation": evaluation
            }
            
        except Exception as e:
            logger.error(f"유튜브 영상 요약 중 오류: {str(e)}")
            return {"error": f"요약 중 오류가 발생했습니다: {str(e)}"}

    def search_by_handle_or_custom_url(self, channel_identifier: str) -> List[Dict[str, Any]]:
        """
        핸들 또는 커스텀 URL을 사용하여 채널의 비디오를 검색합니다.
        :param channel_identifier: '@핸들' 또는 'c/커스텀URL' 또는 'user/사용자명' 형식의 식별자
        :return: 비디오 목록
        """
        try:
            logger.info(f"핸들 또는 커스텀 URL로 채널 검색: {channel_identifier}")
            
            # 먼저 채널 정보를 가져옵니다
            channel_info = self.get_channel_info(channel_identifier)
            if "error" in channel_info:
                logger.warning(f"채널 정보를 가져올 수 없음: {channel_info['error']}")
                return []
                
            # 실제 채널 ID를 사용하여 비디오를 가져옵니다
            real_channel_id = channel_info['channel_id']
            logger.info(f"변환된 실제 채널 ID: {real_channel_id}")
            
            # 실제 채널 ID로 비디오 검색
            return self.get_channel_videos(real_channel_id)
        except Exception as e:
            logger.error(f"핸들 또는 커스텀 URL로 채널 검색 중 오류: {str(e)}")
            return [] 