# Summer AI

텍스트, 유튜브 동영상, 문서 등을 요약해주는 서비스입니다.

## 주요 기능

- 텍스트 요약: 긴 텍스트를 간결하게 요약
- 유튜브 동영상 요약: 유튜브 동영상 내용 요약
- 문서 요약: PDF 등 문서 내용 요약
- 배치 처리: 여러 항목을 한 번에 요약

## 기술 스택

- Backend: FastAPI, Python
- AI: OpenAI API
- 외부 API: YouTube Data API
- 데이터베이스: SQLite

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/blueblud7/summery.git
cd summery
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env.local` 파일을 생성하고 다음 내용을 추가:
```
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key
SECRET_KEY=your_secret_key
```

4. 서버 실행
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 사용법

### 텍스트 요약
```
POST /api/v1/summarize
{
    "text": "요약할 텍스트",
    "style": "simple", 
    "max_length": 200,
    "language": "ko",
    "format": "text"
}
```

### 유튜브 동영상 요약
```
POST /api/v1/youtube/summarize
{
    "url": "https://www.youtube.com/watch?v=video_id"
}
```

### 배치 요약
```
POST /api/v1/summarize/batch
{
    "items": [
        {"type": "text", "content": "요약할 텍스트"},
        {"type": "youtube", "content": "https://www.youtube.com/watch?v=video_id"},
        {"type": "document", "content": "문서 내용"}
    ]
} 
