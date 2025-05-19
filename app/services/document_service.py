import os
import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDF 파일에서 텍스트를 추출합니다.
        """
        try:
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """
        DOCX 파일에서 텍스트를 추출합니다.
        """
        try:
            import docx
            
            doc = docx.Document(docx_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """
        TXT 파일에서 텍스트를 추출합니다.
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        파일 확장자에 따라 적절한 텍스트 추출 함수를 호출합니다.
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            logger.error(f"Unsupported file type: {file_extension}")
            return ""
    
    def summarize_document(self, file_path: str, language_code: str = 'ko') -> Dict[str, Any]:
        """
        문서 파일을 요약합니다.
        """
        from app.services.summarizer_service import SummarizerService
        
        # 텍스트 추출
        text = self.extract_text_from_file(file_path)
        if not text:
            return {"error": "Failed to extract text from document"}
        
        # 파일 정보
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1]
        file_size = os.path.getsize(file_path)
        
        # 요약하기
        summarizer = SummarizerService()
        summary_result = summarizer.summarize_text(
            text=text,
            style="detailed",
            max_length=300,
            language=language_code,
            format="text"
        )
        
        return {
            "file_name": file_name,
            "file_extension": file_extension,
            "file_size": file_size,
            "text_length": len(text),
            "text_preview": text[:500] + "..." if len(text) > 500 else text,
            "summary": summary_result["summary"] if "summary" in summary_result else "요약 실패"
        } 