"""
설정 관리 모듈
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent

# 환경 변수 로드
load_dotenv(PROJECT_ROOT / ".env")

class Config:
    """설정 클래스"""
    
    # API 설정
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # 경로 설정
    DATA_DIR = PROJECT_ROOT / "data"
    LAWS_DIR = DATA_DIR / "laws"
    CASES_DIR = DATA_DIR / "cases"
    PROCESSED_DIR = DATA_DIR / "processed"
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(DATA_DIR / "chroma_db"))
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # 크롤링 설정
    CRAWLER_BASE_URL = "https://accident.knia.or.kr/myaccident-content"
    CRAWLER_DELAY = float(os.getenv("CRAWLER_DELAY", "1"))
    MAX_CRAWL_PAGES = int(os.getenv("MAX_CRAWL_PAGES", "62"))
    
    # LLM 설정
    MODEL_NAME = "gemini-1.5-flash"
    TEMPERATURE = 0.3
    MAX_TOKENS = 1000
    
    # 문서 처리 설정
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    SIMILARITY_SEARCH_K = 5
    
    # Streamlit 설정
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "localhost")
    
    # 로깅 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "app.log"))
    
    @classmethod
    def validate(cls):
        """설정 검증"""
        errors = []
        
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY가 설정되지 않았습니다.")
        
        # 필요한 디렉토리 생성
        for dir_path in [cls.DATA_DIR, cls.LAWS_DIR, cls.CASES_DIR, 
                        cls.PROCESSED_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return errors
    
    @classmethod
    def get_cases_file_path(cls):
        """판례 파일 경로 반환"""
        return cls.CASES_DIR / "accident_cases.json"
    
    @classmethod
    def get_chroma_db_path(cls):
        """ChromaDB 경로 반환"""
        return Path(cls.CHROMA_DB_PATH)

# 전역 설정 객체
config = Config()
