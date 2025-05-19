from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.summarizer_service import SummarizerService
from app.services.youtube_service import YouTubeService
from app.services.document_service import DocumentService
from app.core.config import settings
import os
import tempfile
import shutil
import logging

router = APIRouter()
summarizer_service = SummarizerService()
youtube_service = YouTubeService(use_mock_data=False)
document_service = DocumentService()
logger = logging.getLogger(__name__)

class SummarizeRequest(BaseModel):
    text: str
    style: str = "simple"
    max_length: int = 200
    language: str = "ko"
    format: str = "text"
    model: Optional[str] = None

class YouTubeSummarizeRequest(BaseModel):
    url: str
    language: str = "ko"
    model: Optional[str] = None

class DocumentSummarizeResponse(BaseModel):
    file_name: str
    file_extension: str
    file_size: int
    text_length: int
    text_preview: str
    summary: str

class SummarizeResponse(BaseModel):
    summary: str
    metadata: Dict
    key_phrases: Optional[List[str]] = None
    quality_score: Optional[Dict] = None

class BatchSummarizeRequest(BaseModel):
    texts: Optional[List[SummarizeRequest]] = []
    youtube_urls: Optional[List[str]] = []
    style: str = "simple"
    max_length: int = 200
    language: str = "ko"
    format: str = "text"
    model: Optional[str] = None

class BatchSummarizeResponse(BaseModel):
    text_summaries: List[SummarizeResponse] = []
    youtube_summaries: List[Dict[str, Any]] = []
    document_summaries: List[DocumentSummarizeResponse] = []
    overall_summary: Optional[str] = None

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    try:
        # 모델 확인 및 유효성 검사
        model = request.model or settings.DEFAULT_MODEL
        if model not in settings.AVAILABLE_MODELS:
            logger.warning(f"요청된 모델 {model}이 유효하지 않습니다. 기본 모델로 대체합니다.")
            model = settings.DEFAULT_MODEL
            
        summarization_result = summarizer_service.summarize_text(
            text=request.text,
            style=request.style,
            max_length=request.max_length,
            language=request.language,
            format=request.format,
            model=model
        )
        
        if "error" in summarization_result:
            raise HTTPException(status_code=500, detail=summarization_result["error"])
        
        # 키 문구 추출 (옵션)
        key_phrases = summarizer_service.extract_key_phrases(request.text, model=model)
        summarization_result["key_phrases"] = key_phrases
        
        # 품질 평가 (옵션)
        quality_score = summarizer_service.evaluate_summary_quality(
            request.text, summarization_result["summary"], model=model
        )
        summarization_result["quality_score"] = quality_score
        
        return summarization_result
    except Exception as e:
        logger.error(f"Error in summarization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize/youtube", response_model=Dict[str, Any])
async def summarize_youtube(request: YouTubeSummarizeRequest):
    try:
        # 모델 확인 및 유효성 검사
        model = request.model or settings.DEFAULT_MODEL
        if model not in settings.AVAILABLE_MODELS:
            logger.warning(f"요청된 모델 {model}이 유효하지 않습니다. 기본 모델로 대체합니다.")
            model = settings.DEFAULT_MODEL
            
        video_result = youtube_service.summarize_video(
            video_url=request.url,
            language_code=request.language,
            model=model
        )
        
        if "error" in video_result:
            raise HTTPException(status_code=500, detail=video_result["error"])
            
        return video_result
    except Exception as e:
        logger.error(f"Error in YouTube summarization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize/document")
async def summarize_document(
    file: UploadFile = File(...),
    style: str = Form("simple"),
    max_length: int = Form(200),
    language: str = Form("ko"),
    format: str = Form("text"),
    model: Optional[str] = Form(None)
):
    try:
        # 모델 확인 및 유효성 검사
        use_model = model or settings.DEFAULT_MODEL
        if use_model not in settings.AVAILABLE_MODELS:
            logger.warning(f"요청된 모델 {use_model}이 유효하지 않습니다. 기본 모델로 대체합니다.")
            use_model = settings.DEFAULT_MODEL
            
        # 임시 파일 생성
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            shutil.copyfileobj(file.file, temp)
            temp_path = temp.name
            
        # 파일 처리
        try:
            # 문서 서비스를 사용하여 파일 처리
            file_extension = suffix.lower()
            text = document_service.extract_text_from_file(temp_path)
            
            if not text:
                raise HTTPException(status_code=400, detail=f"파일에서 텍스트를 추출할 수 없습니다: {file.filename}")
            
            # 요약 수행
            summary_result = summarizer_service.summarize_text(
                text=text,
                style=style,
                max_length=max_length,
                language=language,
                format=format,
                model=use_model
            )
            
            # 응답 준비
            file_size = os.path.getsize(temp_path)
            text_preview = text[:200] + "..." if len(text) > 200 else text
            
            result = {
                "file_name": file.filename,
                "file_extension": file_extension,
                "file_size": file_size,
                "text_length": len(text),
                "text_preview": text_preview,
                "summary": summary_result["summary"]
            }
            
            return result
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error in document summarization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-summarize", response_model=BatchSummarizeResponse)
async def batch_summarize(request: BatchSummarizeRequest, background_tasks: BackgroundTasks):
    """
    여러 텍스트, 유튜브 링크, 문서 파일을 일괄 요약하는 API
    """
    try:
        # 모델 확인 및 유효성 검사
        model = request.model or settings.DEFAULT_MODEL
        if model not in settings.AVAILABLE_MODELS:
            logger.warning(f"요청된 모델 {model}이 유효하지 않습니다. 기본 모델로 대체합니다.")
            model = settings.DEFAULT_MODEL
            
        response = BatchSummarizeResponse(
            text_summaries=[],
            youtube_summaries=[],
            document_summaries=[]
        )
        
        # 텍스트 요약 처리
        for text_req in request.texts:
            try:
                # 개별 텍스트 항목의 모델 설정 확인
                text_model = text_req.model or model
                if text_model not in settings.AVAILABLE_MODELS:
                    logger.warning(f"요청된 모델 {text_model}이 유효하지 않습니다. 기본 모델로 대체합니다.")
                    text_model = model
                    
                result = summarizer_service.summarize_text(
                    text=text_req.text,
                    style=text_req.style or request.style,
                    max_length=text_req.max_length or request.max_length,
                    language=text_req.language or request.language,
                    format=text_req.format or request.format,
                    model=text_model
                )
                
                # 키 문구 추출 (옵션)
                key_phrases = summarizer_service.extract_key_phrases(text_req.text, model=text_model)
                result["key_phrases"] = key_phrases
                
                response.text_summaries.append(result)
            except Exception as e:
                logger.error(f"텍스트 요약 중 오류: {str(e)}")
                response.text_summaries.append({"error": str(e), "text": text_req.text[:100] + "..."})
        
        # 유튜브 링크 요약 처리
        for url in request.youtube_urls:
            try:
                video_result = youtube_service.summarize_video(
                    video_url=url,
                    language_code=request.language,
                    model=model
                )
                response.youtube_summaries.append(video_result)
            except Exception as e:
                logger.error(f"유튜브 요약 중 오류: {str(e)}")
                response.youtube_summaries.append({"error": str(e), "url": url})
        
        # 전체 요약 생성 (옵션)
        if len(response.text_summaries) + len(response.youtube_summaries) + len(response.document_summaries) > 1:
            # 각 요약을 결합하여 최종 요약 생성 (백그라운드로 처리)
            summaries = []
            for summary in response.text_summaries:
                if "summary" in summary:
                    summaries.append(summary["summary"])
            
            for summary in response.youtube_summaries:
                if "summary" in summary:
                    summaries.append(summary["summary"])
                    
            for summary in response.document_summaries:
                summaries.append(summary.summary)
            
            if summaries:
                combined_text = "\n\n".join(summaries)
                background_tasks.add_task(
                    _generate_overall_summary, 
                    combined_text, 
                    response, 
                    request.style,
                    request.max_length,
                    request.language,
                    model
                )
        
        return response
    except Exception as e:
        logger.error(f"배치 요약 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 백그라운드에서 전체 요약 생성
async def _generate_overall_summary(
    combined_text: str, 
    response: BatchSummarizeResponse,
    style: str,
    max_length: int,
    language: str,
    model: str
):
    try:
        overall_result = summarizer_service.summarize_text(
            text=combined_text,
            style=style,
            max_length=max_length * 2,  # 전체 요약은 더 길게
            language=language,
            format="text",
            model=model
        )
        
        response.overall_summary = overall_result["summary"]
    except Exception as e:
        logger.error(f"전체 요약 생성 중 오류: {str(e)}")
        response.overall_summary = f"전체 요약 생성 실패: {str(e)}" 