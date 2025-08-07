"""
기본 시스템 테스트
"""
import unittest
import os
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class TestSystemSetup(unittest.TestCase):
    """시스템 설정 테스트"""
    
    def test_environment_variables(self):
        """환경 변수 테스트"""
        from dotenv import load_dotenv
        load_dotenv(project_root / ".env")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        self.assertIsNotNone(api_key, "GOOGLE_API_KEY가 설정되지 않았습니다")
        self.assertTrue(len(api_key) > 20, "API 키가 너무 짧습니다")
    
    def test_directory_structure(self):
        """디렉토리 구조 테스트"""
        required_dirs = [
            "data/laws",
            "data/cases", 
            "data/processed",
            "src/data_processing",
            "src/rag_system",
            "src/ui",
            "config",
            "logs"
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            self.assertTrue(full_path.exists(), f"디렉토리가 없습니다: {dir_path}")
    
    def test_import_modules(self):
        """모듈 import 테스트"""
        try:
            from src.data_processing.web_crawler import AccidentCrawler
            from src.rag_system.advisor import TrafficAccidentAdvisor
            from src.rag_system.document_processor import DocumentProcessor
        except ImportError as e:
            self.fail(f"모듈 import 실패: {e}")

class TestCrawler(unittest.TestCase):
    """크롤러 테스트"""
    
    def test_crawler_init(self):
        """크롤러 초기화 테스트"""
        from src.data_processing.web_crawler import AccidentCrawler
        
        crawler = AccidentCrawler()
        self.assertIsNotNone(crawler)
        self.assertEqual(crawler.base_url, "https://accident.knia.or.kr/myaccident-content")

class TestUtils(unittest.TestCase):
    """유틸리티 함수 테스트"""
    
    def test_clean_text(self):
        """텍스트 정리 테스트"""
        from src.utils import clean_text
        
        test_text = "⊙ 테스트\n\n텍스트\r\n입니다."
        expected = "테스트 텍스트 입니다."
        result = clean_text(test_text)
        self.assertEqual(result, expected)
    
    def test_extract_fault_ratio(self):
        """과실비율 추출 테스트"""
        from src.utils import extract_fault_ratio
        
        test_string = "70 : 30"
        ratio_a, ratio_b = extract_fault_ratio(test_string)
        self.assertEqual(ratio_a, 70)
        self.assertEqual(ratio_b, 30)

if __name__ == "__main__":
    unittest.main()
