import logging
from app.core.config import settings
from typing import Optional, List, Dict
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SummarizerService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.use_mock = not self.api_key

    def summarize_text(
        self,
        text: str,
        style: str = "simple",
        max_length: int = 200,
        language: str = "ko",
        format: str = "text"
    ) -> Dict:
        try:
            # API 키가 없으면 모의 요약 반환
            if self.use_mock:
                logger.warning("OpenAI API 키가 없어 모의 요약을 반환합니다.")
                return {
                    "summary": f"이것은 스타일 '{style}'로 생성된 최대 {max_length}자의 '{language}' 언어 모의 요약입니다. 형식은 '{format}'입니다.",
                    "metadata": {
                        "style": style,
                        "language": language,
                        "format": format,
                        "max_length": max_length,
                        "timestamp": datetime.now().isoformat(),
                        "model": "mock-model"
                    }
                }
            
            system_prompt = self._get_system_prompt(style, language, format)
            
            try:
                import openai
                
                # OpenAI API v1.0 이상 호환
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Please summarize the following text, keeping it under {max_length} characters:\n\n{text}"}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                summary = response.choices[0].message.content.strip()
                
                return {
                    "summary": summary,
                    "metadata": {
                        "style": style,
                        "language": language,
                        "format": format,
                        "max_length": max_length,
                        "timestamp": datetime.now().isoformat(),
                        "model": "gpt-3.5-turbo"
                    }
                }
                
            except Exception as e:
                logger.error(f"OpenAI API 호출 중 오류: {str(e)}")
                return {
                    "summary": "API 호출 중 오류가 발생했습니다.",
                    "error": str(e),
                    "metadata": {
                        "style": style,
                        "language": language,
                        "format": format,
                        "max_length": max_length,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            return {
                "error": "요약을 생성하는 중 오류가 발생했습니다.",
                "details": str(e)
            }

    def extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        try:
            # API 키가 없으면 모의 키 문구 반환
            if self.use_mock:
                logger.warning("OpenAI API 키가 없어 모의 키 문구를 반환합니다.")
                return [f"모의 키 문구 {i+1}" for i in range(min(max_phrases, 5))]
            
            try:
                import openai
                
                # OpenAI API v1.0 이상 호환
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Extract key phrases from the text. Return as a JSON array of strings."},
                        {"role": "user", "content": f"Extract {max_phrases} key phrases from this text:\n\n{text}"}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                phrases_text = response.choices[0].message.content
                
                # JSON 파싱 시도
                try:
                    phrases = json.loads(phrases_text)
                    if isinstance(phrases, list):
                        return phrases[:max_phrases]
                except:
                    # JSON 파싱 실패 시 문자열 처리
                    phrases = [p.strip() for p in phrases_text.split('\n') if p.strip()]
                    return phrases[:max_phrases]
                
            except Exception as e:
                logger.error(f"키 문구 추출 중 오류: {str(e)}")
                return [f"추출 오류: {str(e)}"]
                
        except Exception as e:
            logger.error(f"Error in key phrase extraction: {str(e)}")
            return [f"추출 오류: {str(e)}"]

    def _get_system_prompt(self, style: str, language: str, format: str) -> str:
        style_prompts = {
            "simple": "Provide a concise summary focusing on the main points.",
            "detailed": "Provide a comprehensive summary including key details and supporting information.",
            "expert": "Provide a technical summary suitable for experts in the field.",
            "beginner": "Provide a simple explanation suitable for beginners.",
            "academic": "Provide a formal academic summary with citations.",
            "creative": "Provide a creative and engaging summary that captures the essence."
        }
        
        language_prompts = {
            "ko": "Summarize in Korean.",
            "en": "Summarize in English.",
            "ja": "Summarize in Japanese.",
            "zh": "Summarize in Chinese."
        }

        format_prompts = {
            "text": "Return the summary as plain text.",
            "bullet": "Return the summary as bullet points.",
            "structured": "Return the summary with sections: Main Points, Details, Conclusion.",
            "qa": "Return the summary as Q&A format."
        }
        
        style_prompt = style_prompts.get(style, style_prompts["simple"])
        language_prompt = language_prompts.get(language, language_prompts["ko"])
        format_prompt = format_prompts.get(format, format_prompts["text"])
        
        return f"You are a helpful assistant that summarizes text. {style_prompt} {language_prompt} {format_prompt}"

    def evaluate_summary_quality(self, original_text: str, summary: str) -> Dict:
        try:
            # API 키가 없으면 모의 평가 반환
            if self.use_mock:
                logger.warning("OpenAI API 키가 없어 모의 평가를 반환합니다.")
                return {
                    "accuracy": 0.8,
                    "completeness": 0.7,
                    "coherence": 0.9,
                    "overall_score": 0.8
                }
            
            try:
                import openai
                
                # OpenAI API v1.0 이상 호환
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Evaluate the quality of the summary. Return a JSON with scores for accuracy, completeness, and coherence."},
                        {"role": "user", "content": f"Original text:\n{original_text}\n\nSummary:\n{summary}"}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                result_text = response.choices[0].message.content
                
                try:
                    return json.loads(result_text)
                except:
                    return {"error": "평가 결과를 파싱할 수 없습니다.", "raw_result": result_text}
                
            except Exception as e:
                logger.error(f"평가 중 오류: {str(e)}")
                return {"error": f"평가 중 오류가 발생했습니다: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error in quality evaluation: {str(e)}")
            return {"error": f"평가 중 오류가 발생했습니다: {str(e)}"} 