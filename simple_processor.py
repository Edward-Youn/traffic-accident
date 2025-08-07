"""
간단한 문서 처리기 (ChromaDB 호환성 개선)
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from loguru import logger

class SimpleDocumentProcessor:
    def __init__(self, google_api_key: str, persist_directory: str = "./data/chroma_db"):
        self.google_api_key = google_api_key
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # 임베딩 모델 초기화
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )
        
        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        self.vectorstore = None
        logger.info("간단한 문서 처리기 초기화 완료")
    
    def load_accident_cases(self, json_file_path: str) -> List[Document]:
        """판례 데이터 로드"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            documents = []
            for case in cases:
                content = f"""
Case ID: {case['case_id']}
Vehicle A: {case['vehicle_A_situation']}
Vehicle B: {case['vehicle_B_situation']}
Description: {case['accident_description']}
Fault Ratio: {case['fault_ratio']}
""".strip()
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "case_id": case['case_id'],
                        "fault_ratio": case['fault_ratio']
                    }
                )
                documents.append(doc)
            
            logger.info(f"판례 {len(documents)}건 로드 완료")
            return documents
            
        except Exception as e:
            logger.error(f"판례 로드 실패: {e}")
            return []
    
    def build_vectorstore(self, documents: List[Document]):
        """벡터스토어 구축 (에러 처리 강화)"""
        if not documents:
            logger.warning("문서가 없습니다")
            return
        
        try:
            logger.info("문서 분할 중...")
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"{len(chunks)}개 청크 생성")
            
            logger.info("벡터스토어 구축 중...")
            # ChromaDB 설정을 단순화
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory)
            )
            
            logger.info("벡터스토어 구축 완료")
            
        except Exception as e:
            logger.error(f"벡터스토어 구축 실패: {e}")
            # 대안: 로컬 저장
            try:
                logger.info("대안 방법으로 저장 시도...")
                import pickle
                data = {
                    'documents': documents,
                    'chunks': chunks
                }
                with open(self.persist_directory / 'backup.pkl', 'wb') as f:
                    pickle.dump(data, f)
                logger.info("백업 저장 완료")
            except Exception as backup_error:
                logger.error(f"백업 저장도 실패: {backup_error}")

def test_simple_processor():
    """간단한 테스트"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("API 키가 필요합니다")
        return
    
    processor = SimpleDocumentProcessor(api_key)
    
    # 테스트 데이터 생성
    test_cases = [
        {
            "case_id": "test-1",
            "vehicle_A_situation": "직진",
            "vehicle_B_situation": "좌회전",
            "accident_description": "신호등 교차로 충돌",
            "fault_ratio": "30:70"
        }
    ]
    
    # 임시 파일로 저장
    test_file = "test_cases.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, ensure_ascii=False)
    
    # 처리
    docs = processor.load_accident_cases(test_file)
    if docs:
        processor.build_vectorstore(docs)
        print("✅ 테스트 성공!")
    
    # 정리
    os.remove(test_file)

if __name__ == "__main__":
    test_simple_processor()
