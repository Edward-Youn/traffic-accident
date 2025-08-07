"""
문서 처리 및 임베딩 모듈
법률 문서, 판례 등을 처리하여 벡터DB에 저장
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, JSONLoader
from langchain.schema import Document
from loguru import logger

class DocumentProcessor:
    def __init__(self, 
                 google_api_key: str,
                 persist_directory: str = "./data/chroma_db",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        문서 처리기 초기화
        
        Args:
            google_api_key: Google API 키
            persist_directory: 벡터DB 저장 경로
            chunk_size: 텍스트 청크 크기
            chunk_overlap: 청크 겹침 크기
        """
        self.google_api_key = google_api_key
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # 임베딩 모델 초기화
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=google_api_key
        )
        
        # 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 벡터 스토어 초기화
        self.vectorstore = None
        
        logger.info("문서 처리기 초기화 완료")
    
    def load_accident_cases(self, json_file_path: str) -> List[Document]:
        """교통사고 판례 JSON 파일을 Document 객체로 변환"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            documents = []
            for case in cases:
                # 사고 상황을 하나의 문서로 구성
                content = f"""
사고 유형: {case['case_id']}

차량 A 상황:
{case['vehicle_A_situation']}

차량 B 상황:
{case['vehicle_B_situation']}

사고 설명:
{case['accident_description']}

과실 비율: {case['fault_ratio']}
                """.strip()
                
                metadata = {
                    "source": "accident_case",
                    "case_id": case['case_id'],
                    "fault_ratio": case['fault_ratio'],
                    "type": "판례"
                }
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            logger.info(f"교통사고 판례 {len(documents)}건 로드 완료")
            return documents
            
        except Exception as e:
            logger.error(f"판례 로드 실패: {e}")
            return []
    
    def load_pdf_documents(self, pdf_directory: str) -> List[Document]:
        """PDF 문서들을 로드"""
        documents = []
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            logger.warning(f"PDF 디렉토리가 존재하지 않습니다: {pdf_directory}")
            return documents
        
        for pdf_file in pdf_dir.glob("*.pdf"):
            try:
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()
                
                # 메타데이터 추가
                for doc in docs:
                    doc.metadata.update({
                        "source": "legal_document",
                        "file_name": pdf_file.name,
                        "type": "법률문서"
                    })
                
                documents.extend(docs)
                logger.info(f"PDF 로드 완료: {pdf_file.name} ({len(docs)}페이지)")
                
            except Exception as e:
                logger.error(f"PDF 로드 실패 {pdf_file.name}: {e}")
                continue
        
        logger.info(f"총 {len(documents)}개 PDF 문서 로드 완료")
        return documents
    
    def process_and_store_documents(self, documents: List[Document]) -> None:
        """문서를 처리하고 벡터DB에 저장"""
        if not documents:
            logger.warning("처리할 문서가 없습니다")
            return
        
        try:
            # 문서 분할
            logger.info("문서 분할 시작...")
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"총 {len(chunks)}개 청크 생성")
            
            # 벡터 스토어에 저장
            logger.info("벡터 임베딩 및 저장 시작...")
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(self.persist_directory)
            )
            
            # 영구 저장
            self.vectorstore.persist()
            logger.info(f"벡터DB 저장 완료: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"문서 처리 및 저장 실패: {e}")
            raise
    
    def load_vectorstore(self) -> Chroma:
        """기존 벡터DB 로드"""
        try:
            self.vectorstore = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings
            )
            logger.info("기존 벡터DB 로드 완료")
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"벡터DB 로드 실패: {e}")
            return None
    
    def search_similar_cases(self, query: str, k: int = 5) -> List[Dict]:
        """유사한 사고 사례 검색"""
        if not self.vectorstore:
            self.load_vectorstore()
        
        if not self.vectorstore:
            logger.error("벡터DB가 로드되지 않았습니다")
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": score
                })
            
            logger.info(f"유사 사례 {len(formatted_results)}건 검색 완료")
            return formatted_results
            
        except Exception as e:
            logger.error(f"유사 사례 검색 실패: {e}")
            return []

def main():
    """테스트용 메인 함수"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("GOOGLE_API_KEY를 설정해주세요")
        return
    
    processor = DocumentProcessor(google_api_key)
    
    # 교통사고 판례 로드
    cases_file = "./data/cases/accident_cases.json"
    if os.path.exists(cases_file):
        print("교통사고 판례 로드 중...")
        case_documents = processor.load_accident_cases(cases_file)
        
        if case_documents:
            print("벡터DB에 저장 중...")
            processor.process_and_store_documents(case_documents)
            print("✅ 처리 완료!")
        else:
            print("❌ 판례 데이터가 없습니다")
    else:
        print(f"❌ 판례 파일을 찾을 수 없습니다: {cases_file}")

if __name__ == "__main__":
    main()
