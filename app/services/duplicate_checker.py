from sqlalchemy.orm import Session
from app.models.models import Video
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DuplicateChecker:
    def __init__(self, similarity_threshold=0.8):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def is_duplicate(self, video: Video, db: Session) -> bool:
        # 최근 100개의 비디오와 비교
        recent_videos = db.query(Video).filter(
            Video.id != video.id,
            Video.is_duplicate == False
        ).order_by(Video.created_at.desc()).limit(100).all()
        
        if not recent_videos:
            return False
        
        # 텍스트 데이터 준비
        texts = [video.description] + [v.description for v in recent_videos]
        
        # TF-IDF 벡터화
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            # 가장 높은 유사도 찾기
            max_similarity = np.max(similarities)
            video.similarity_score = float(max_similarity)
            
            return max_similarity > self.similarity_threshold
            
        except Exception as e:
            print(f"Error in duplicate checking: {str(e)}")
            return False 