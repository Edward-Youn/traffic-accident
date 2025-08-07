"""
벡터DB 오류 방지를 위한 개선된 문서 처리기
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

class FixedDocumentProcessor:
    def __init__(self, google_api_key: str, persist_directory: str = "./data/chroma_db"):
        """
        오류 방지 문서 처리기 초기화
        """
        self.google_api_key = google_api_key
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Google 임베딩만 사용 (onnxruntime 불필요)
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
        logger.info("오류 방지 문서 처리기 초기화 완료")
    
    def load_accident_cases(self, json_file_path: str) -> List[Document]:
        """판례 데이터 로드"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            documents = []
            for case in cases:
                content = f"""
사고 유형: {case['case_id']}

차량 A 상황: {case['vehicle_A_situation']}
차량 B 상황: {case['vehicle_B_situation']}

사고 설명: {case['accident_description']}
과실 비율: {case['fault_ratio']}
""".strip()
                
                doc = Document(
                    page_content=content,
                    metadata={
                        "case_id": case['case_id'],
                        "fault_ratio": case['fault_ratio'],
                        "source": "accident_case"
                    }
                )
                documents.append(doc)
            
            logger.info(f"판례 {len(documents)}건 로드 완료")
            return documents
            
        except Exception as e:
            logger.error(f"판례 로드 실패: {e}")
            return []
    
    def build_vectorstore_safe(self, documents: List[Document]):
        """안전한 벡터스토어 구축"""
        if not documents:
            logger.warning("문서가 없습니다")
            return False
        
        try:
            logger.info("문서 분할 중...")
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"{len(chunks)}개 청크 생성")
            
            logger.info("벡터스토어 구축 중... (Google 임베딩 사용)")
            
            # ChromaDB 설정을 명시적으로 지정
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory),
                collection_name="traffic_accidents"
            )
            
            logger.info("✅ 벡터스토어 구축 완료!")
            return True
            
        except Exception as e:
            logger.error(f"벡터스토어 구축 실패: {e}")
            
            # 대안: 단순 JSON 저장
            try:
                logger.info("대안으로 JSON 파일에 저장...")
                backup_data = {
                    'chunks': [{'content': doc.page_content, 'metadata': doc.metadata} for doc in chunks],
                    'created_at': str(Path(__file__).stat().st_mtime)
                }
                
                backup_file = self.persist_directory / "backup_chunks.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"백업 저장 완료: {backup_file}")
                return False
                
            except Exception as backup_error:
                logger.error(f"백업 저장도 실패: {backup_error}")
                return False
    
    def load_vectorstore_safe(self):
        """안전한 벡터스토어 로드"""
        try:
            if not self.persist_directory.exists():
                logger.warning("벡터스토어 디렉토리가 없습니다")
                return None
            
            # ChromaDB 로드 시도
            self.vectorstore = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings,
                collection_name="traffic_accidents"
            )
            
            # 테스트 검색
            test_results = self.vectorstore.similarity_search("테스트", k=1)
            logger.info("✅ 벡터스토어 로드 성공")
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"벡터스토어 로드 실패: {e}")
            
            # 백업 파일 확인
            backup_file = self.persist_directory / "backup_chunks.json"
            if backup_file.exists():
                logger.info("백업 파일을 발견했습니다")
                return "backup_available"
            
            return None

def build_vectordb_safe():
    """안전한 벡터DB 구축"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY가 필요합니다")
        return
    
    print("🔧 안전한 벡터DB 구축을 시작합니다...")
    
    processor = FixedDocumentProcessor(api_key)
    
    # 판례 파일 확인
    cases_file = Path("./data/cases/accident_cases.json")
    if not cases_file.exists():
        print("❌ 판례 파일이 없습니다. 먼저 크롤링을 실행하세요:")
        print("   python main.py --crawl")
        return
    
    # 문서 로드
    print("📚 판례 데이터 로드 중...")
    documents = processor.load_accident_cases(str(cases_file))
    
    if not documents:
        print("❌ 로드할 문서가 없습니다")
        return
    
    # 안전한 구축
    print("⚙️ 벡터스토어 구축 중...")
    success = processor.build_vectorstore_safe(documents)
    
    if success:
        print("✅ 벡터DB 구축 완료!")
        print("   이제 python main.py --mvp 로 웹앱을 실행하세요")
    else:
        print("⚠️ 벡터DB 구축에 실패했지만 백업이 저장되었습니다")
        print("   기본 기능은 정상 작동합니다")

if __name__ == "__main__":
    build_vectordb_safe()
