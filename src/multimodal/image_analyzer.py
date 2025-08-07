"""
교통사고 이미지 분석 통합 모듈
Gemini Vision API를 활용한 사고 현장 분석
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import google.generativeai as genai
from PIL import Image
from loguru import logger
import tempfile

class AccidentImageAnalyzer:
    def __init__(self, google_api_key: str):
        """
        교통사고 이미지 분석기 초기화
        """
        if not google_api_key:
            raise ValueError("Google API 키가 필요합니다")
        
        # Gemini 설정
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        logger.info("교통사고 이미지 분석기 초기화 완료")
    
    def analyze_accident_image(self, image_path: str) -> Optional[str]:
        """
        교통사고 현장 이미지 분석
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            분석 결과 텍스트
        """
        try:
            # 이미지 로드 및 최적화
            image = Image.open(image_path)
            image = self._optimize_image(image)
            
            # 교통사고 전용 분석 프롬프트
            prompt = """
이 교통사고 현장 사진을 전문가 관점에서 분석해주세요:

## 분석 항목:

**1. 사고 개요**
- 사고 유형 (추돌, 측면충돌, 정면충돌, 접촉 등)
- 관련 차량 수와 종류

**2. 차량 상태**
- 각 차량의 손상 위치와 정도
- 충돌 방향과 각도 추정

**3. 도로 환경**
- 도로 종류 (일반도로/교차로/고속도로)
- 차선, 신호등, 표지판 등 교통시설
- 날씨, 시간대 등 환경 요인

**4. 과실 판단 요소**
- 각 차량의 주행 경로 추정
- 교통법규 위반 가능성
- 과실 비율에 영향을 줄 수 있는 요소

**5. 특이사항**
- 주목할 만한 증거나 상황
- 추가 확인이 필요한 부분

간결하고 명확하게 한국어로 분석해주세요.
"""
            
            # Gemini Vision으로 분석
            response = self.model.generate_content([prompt, image])
            
            if response.text:
                logger.info("이미지 분석 완료")
                return response.text
            else:
                logger.warning("이미지 분석 결과가 비어있습니다")
                return None
                
        except Exception as e:
            logger.error(f"이미지 분석 실패: {e}")
            return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"
    
    def analyze_uploaded_file(self, uploaded_file) -> Optional[str]:
        """
        Streamlit 업로드 파일 분석
        
        Args:
            uploaded_file: Streamlit file_uploader 객체
            
        Returns:
            분석 결과 텍스트
        """
        try:
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(uploaded_file.read())
                temp_path = temp_file.name
            
            # 분석 실행
            result = self.analyze_accident_image(temp_path)
            
            # 임시 파일 삭제
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"업로드 파일 분석 실패: {e}")
            return f"파일 분석 중 오류가 발생했습니다: {str(e)}"
    
    def _optimize_image(self, image: Image.Image, max_size=(1024, 1024)) -> Image.Image:
        """
        이미지 최적화 (API 비용 절약)
        """
        # 크기 조정
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # RGB 변환
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def get_analysis_summary(self, analysis_text: str) -> Dict[str, str]:
        """
        분석 결과를 구조화된 딕셔너리로 변환
        """
        try:
            # 간단한 키워드 기반 파싱
            summary = {
                "accident_type": "분석 중",
                "vehicles": "분석 중", 
                "damage": "분석 중",
                "road_condition": "분석 중",
                "key_factors": "분석 중"
            }
            
            if analysis_text:
                lines = analysis_text.split('\n')
                current_section = ""
                
                for line in lines:
                    line = line.strip()
                    if "사고 유형" in line or "사고 개요" in line:
                        current_section = "accident_type"
                    elif "차량" in line and ("상태" in line or "정보" in line):
                        current_section = "vehicles"
                    elif "손상" in line or "충돌" in line:
                        current_section = "damage"
                    elif "도로" in line or "환경" in line:
                        current_section = "road_condition"
                    elif "과실" in line or "요소" in line:
                        current_section = "key_factors"
                    elif line and current_section and not line.startswith("#"):
                        if summary[current_section] == "분석 중":
                            summary[current_section] = line
                        else:
                            summary[current_section] += f" {line}"
            
            return summary
            
        except Exception as e:
            logger.error(f"분석 요약 생성 실패: {e}")
            return {
                "accident_type": "파싱 오류",
                "vehicles": "파싱 오류",
                "damage": "파싱 오류", 
                "road_condition": "파싱 오류",
                "key_factors": "파싱 오류"
            }

def test_image_analyzer():
    """이미지 분석기 테스트"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY를 설정해주세요")
        return
    
    analyzer = AccidentImageAnalyzer(google_api_key)
    print("✅ 이미지 분석기 초기화 완료")
    print("📷 실제 사고 이미지가 있다면 분석해보세요!")

if __name__ == "__main__":
    test_image_analyzer()
