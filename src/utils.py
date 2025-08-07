"""
유틸리티 함수들
"""
import re
import json
from typing import List, Dict, Any
from pathlib import Path

def clean_text(text: str) -> str:
    """텍스트 정리"""
    if not text:
        return ""
    
    # 줄바꿈 문자 제거 및 특수 문자 정리
    cleaned = text.strip()
    cleaned = cleaned.replace("\r\n", " ").replace("\n", " ")
    cleaned = cleaned.replace("⊙ ", "")
    
    # 연속된 공백 제거
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()

def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """JSON 파일 로드"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"JSON 파일 로드 실패: {e}")
        return []

def save_json_file(data: List[Dict[str, Any]], file_path: str) -> bool:
    """JSON 파일 저장"""
    try:
        # 디렉토리 생성
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"JSON 파일 저장 실패: {e}")
        return False

def extract_fault_ratio(fault_string: str) -> tuple:
    """과실비율 문자열에서 숫자 추출"""
    try:
        # "70 : 30" 형태에서 숫자 추출
        matches = re.findall(r'\d+', fault_string)
        if len(matches) >= 2:
            return int(matches[0]), int(matches[1])
        return None, None
    except:
        return None, None

def format_case_summary(case_data: Dict[str, Any]) -> str:
    """사고 사례 요약 포맷팅"""
    template = """
사고 유형: {case_id}

상황:
- 차량 A: {vehicle_A}
- 차량 B: {vehicle_B}

사고 설명:
{description}

과실 비율: {fault_ratio}
""".strip()
    
    return template.format(
        case_id=case_data.get('case_id', 'N/A'),
        vehicle_A=case_data.get('vehicle_A_situation', 'N/A'),
        vehicle_B=case_data.get('vehicle_B_situation', 'N/A'),
        description=case_data.get('accident_description', 'N/A'),
        fault_ratio=case_data.get('fault_ratio', 'N/A')
    )

def validate_api_key(api_key: str) -> bool:
    """API 키 유효성 검사"""
    if not api_key:
        return False
    
    # Google API 키 형태 확인 (기본적인 검증)
    if len(api_key) < 30 or not api_key.startswith('AIza'):
        return False
    
    return True

def create_error_response(error_message: str) -> Dict[str, Any]:
    """에러 응답 생성"""
    return {
        "status": "error",
        "error": error_message,
        "answer": f"죄송합니다. 오류가 발생했습니다: {error_message}",
        "source_documents": []
    }

def create_success_response(answer: str, sources: List[Dict] = None) -> Dict[str, Any]:
    """성공 응답 생성"""
    return {
        "status": "success", 
        "answer": answer,
        "source_documents": sources or []
    }
