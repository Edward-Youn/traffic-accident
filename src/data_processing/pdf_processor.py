import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

import PyPDF2
import fitz  # PyMuPDF
import pdfplumber
from docx import Document

class LegalDocumentProcessor:
    def __init__(self, input_dir="./data/laws", output_dir="./data/processed"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # 디렉토리 생성
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 로깅 설정
        logger.add("./logs/pdf_processor.log", rotation="10 MB")
        
        # 법률 문서 패턴들
        self.legal_patterns = {
            'article': r'제(\d+)조\s*(?:\(([^)]+)\))?',  # 제1조(목적)
            'paragraph': r'[①②③④⑤⑥⑦⑧⑨⑩]',  # 항 번호
            'item': r'(\d+)\.',  # 호 번호
            'subitem': r'([가-힣])\.',  # 목 번호
        }
    
    def process_all_documents(self) -> List[Dict[str, Any]]:
        """모든 법률 문서 처리"""
        all_documents = []
        
        logger.info(f"법률 문서 처리 시작: {self.input_dir}")
        
        # 지원 파일 형식
        supported_extensions = {'.pdf', '.docx', '.txt'}
        
        for file_path in self.input_dir.rglob('*'):
            if file_path.suffix.lower() in supported_extensions:
                try:
                    logger.info(f"처리 중: {file_path.name}")
                    document = self._process_single_document(file_path)
                    if document:
                        all_documents.append(document)
                except Exception as e:
                    logger.error(f"문서 처리 실패 {file_path.name}: {e}")
        
        # 처리된 문서 저장
        output_file = self.output_dir / "processed_legal_documents.json"
        self._save_processed_documents(all_documents, output_file)
        
        logger.info(f"문서 처리 완료: 총 {len(all_documents)}개 문서")
        return all_documents
    
    def _process_single_document(self, file_path: Path) -> Dict[str, Any]:
        """단일 문서 처리"""
        # 파일 확장자별 텍스트 추출
        if file_path.suffix.lower() == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif file_path.suffix.lower() == '.docx':
            text = self._extract_docx_text(file_path)
        elif file_path.suffix.lower() == '.txt':
            text = self._extract_txt_text(file_path)
        else:
            return None
        
        if not text.strip():
            logger.warning(f"빈 문서: {file_path.name}")
            return None
        
        # 법률 문서 구조 분석
        parsed_content = self._parse_legal_structure(text)
        
        return {
            "filename": file_path.name,
            "file_path": str(file_path),
            "document_type": self._classify_document_type(file_path.name, text),
            "raw_text": text,
            "parsed_content": parsed_content,
            "metadata": {
                "file_size": file_path.stat().st_size,
                "processed_at": logger._get_time().isoformat() if hasattr(logger, '_get_time') else None,
                "article_count": len(parsed_content.get('articles', [])),
                "total_length": len(text)
            }
        }
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """PDF 텍스트 추출 (여러 방법 시도)"""
        text = ""
        
        # 방법 1: PyMuPDF (가장 강력함)
        try:
            doc = fitz.open(file_path)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
            doc.close()
            
            if text.strip():
                logger.info(f"PyMuPDF로 {file_path.name} 추출 성공")
                return self._clean_extracted_text(text)
        except Exception as e:
            logger.warning(f"PyMuPDF 추출 실패 {file_path.name}: {e}")
        
        # 방법 2: pdfplumber (테이블 처리 좋음)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                logger.info(f"pdfplumber로 {file_path.name} 추출 성공")
                return self._clean_extracted_text(text)
        except Exception as e:
            logger.warning(f"pdfplumber 추출 실패 {file_path.name}: {e}")
        
        # 방법 3: PyPDF2 (마지막 시도)
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if text.strip():
                logger.info(f"PyPDF2로 {file_path.name} 추출 성공")
                return self._clean_extracted_text(text)
        except Exception as e:
            logger.error(f"PyPDF2 추출 실패 {file_path.name}: {e}")
        
        logger.error(f"모든 PDF 추출 방법 실패: {file_path.name}")
        return ""
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """DOCX 텍스트 추출"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"DOCX 추출 실패 {file_path.name}: {e}")
        
        return self._clean_extracted_text(text)
    
    def _extract_txt_text(self, file_path: Path) -> str:
        """TXT 파일 읽기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except UnicodeDecodeError:
            # UTF-8이 안 되면 CP949 시도
            try:
                with open(file_path, 'r', encoding='cp949') as file:
                    text = file.read()
            except Exception as e:
                logger.error(f"TXT 읽기 실패 {file_path.name}: {e}")
                return ""
        except Exception as e:
            logger.error(f"TXT 읽기 실패 {file_path.name}: {e}")
            return ""
        
        return self._clean_extracted_text(text)
    
    def _clean_extracted_text(self, text: str) -> str:
        """추출된 텍스트 정리"""
        if not text:
            return ""
        
        # 연속된 공백 및 줄바꿈 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 연속된 빈 줄 제거
        text = re.sub(r' +', ' ', text)  # 연속된 공백 제거
        text = text.strip()
        
        return text
    
    def _parse_legal_structure(self, text: str) -> Dict[str, Any]:
        """법률 문서 구조 파싱"""
        parsed = {
            'articles': [],
            'structure_info': {
                'has_articles': False,
                'has_paragraphs': False,
                'has_items': False
            }
        }
        
        # 조문 추출
        articles = self._extract_articles(text)
        parsed['articles'] = articles
        
        if articles:
            parsed['structure_info']['has_articles'] = True
        
        # 항, 호 확인
        if re.search(self.legal_patterns['paragraph'], text):
            parsed['structure_info']['has_paragraphs'] = True
        
        if re.search(self.legal_patterns['item'], text):
            parsed['structure_info']['has_items'] = True
        
        return parsed
    
    def _extract_articles(self, text: str) -> List[Dict[str, Any]]:
        """조문 추출"""
        articles = []
        
        # 조문 패턴으로 찾기
        article_matches = list(re.finditer(self.legal_patterns['article'], text))
        
        for i, match in enumerate(article_matches):
            article_num = match.group(1)
            article_title = match.group(2) if match.group(2) else ""
            
            # 조문 내용 추출 (다음 조문까지)
            start_pos = match.start()
            if i + 1 < len(article_matches):
                end_pos = article_matches[i + 1].start()
                content = text[start_pos:end_pos].strip()
            else:
                content = text[start_pos:].strip()
            
            articles.append({
                'article_number': int(article_num),
                'title': article_title,
                'content': content,
                'paragraphs': self._extract_paragraphs(content)
            })
        
        return articles
    
    def _extract_paragraphs(self, article_content: str) -> List[str]:
        """조문 내 항 추출"""
        paragraphs = []
        
        # 항 번호로 분할
        paragraph_pattern = self.legal_patterns['paragraph']
        parts = re.split(f'({paragraph_pattern})', article_content)
        
        current_paragraph = ""
        for part in parts:
            if re.match(paragraph_pattern, part):
                if current_paragraph.strip():
                    paragraphs.append(current_paragraph.strip())
                current_paragraph = part
            else:
                current_paragraph += part
        
        if current_paragraph.strip():
            paragraphs.append(current_paragraph.strip())
        
        return paragraphs
    
    def _classify_document_type(self, filename: str, text: str) -> str:
        """문서 유형 분류"""
        filename_lower = filename.lower()
        text_sample = text[:1000].lower()
        
        if '도로교통법' in text_sample or 'road traffic' in filename_lower:
            return "도로교통법"
        elif '자동차손해배상' in text_sample:
            return "자동차손해배상보장법"
        elif '판례' in filename_lower or 'case' in filename_lower:
            return "판례"
        elif '시행령' in text_sample:
            return "시행령"
        elif '시행규칙' in text_sample:
            return "시행규칙"
        else:
            return "기타법령"
    
    def _save_processed_documents(self, documents: List[Dict[str, Any]], output_file: Path):
        """처리된 문서 저장"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            logger.info(f"처리된 문서 저장 완료: {output_file}")
        except Exception as e:
            logger.error(f"문서 저장 실패: {e}")
            raise

def main():
    """메인 실행 함수"""
    processor = LegalDocumentProcessor()
    
    print("📄 법률 문서 처리를 시작합니다...")
    print(f"📁 입력 디렉토리: {processor.input_dir}")
    print(f"📁 출력 디렉토리: {processor.output_dir}")
    
    # 입력 디렉토리 확인
    if not any(processor.input_dir.iterdir()):
        print("⚠️ 입력 디렉토리에 파일이 없습니다.")
        print(f"다음 경로에 PDF, DOCX, TXT 파일을 넣어주세요: {processor.input_dir}")
        return
    
    # 파일 목록 출력
    files = list(processor.input_dir.rglob('*'))
    supported_files = [f for f in files if f.suffix.lower() in {'.pdf', '.docx', '.txt'}]
    
    print(f"📋 처리 대상 파일 ({len(supported_files)}개):")
    for file in supported_files:
        print(f"  - {file.name}")
    
    # 처리 실행
    documents = processor.process_all_documents()
    print(f"✅ 처리 완료! 총 {len(documents)}개 문서가 처리되었습니다.")

if __name__ == "__main__":
    main()