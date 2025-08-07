import google.generativeai as genai
import time
from pathlib import Path
from PIL import Image
from typing import Optional, Dict, Any
from loguru import logger
import base64
import io

from config.config import Config

class GeminiClient:
    def __init__(self):
        """Gemini 1.5 Flash 클라이언트 초기화"""
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")
        
        # API 키 설정
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        
        # 모델 초기화 
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        self.vision_model = genai.GenerativeModel(Config.GEMINI_VISION_MODEL)
        
        # 무료 버전 제한 관리
        self.last_request_time = 0
        self.min_interval = 60 / Config.GEMINI_RATE_LIMIT  # 분당 요청 제한
        
        logger.info(f"Gemini 클라이언트 초기화 완료: {Config.GEMINI_MODEL}")
    
    def _wait_for_rate_limit(self):
        """요청 제한 관리"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.info(f"API 제한으로 {wait_time:.2f}초 대기 중...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def analyze_accident_image(self, image_path: str) -> Optional[str]:
        """교통사고 현장 이미지 분석 (Gemini 1.5 Flash)"""
        try:
            self._wait_for_rate_limit()
            
            # 이미지 로드
            image = Image.open(image_path)
            
            # 이미지 크기 최적화 (무료 버전 토큰 절약)
            image = self._optimize_image(image)
            
            # 분석 프롬프트 (한국어)
            prompt = """
이 교통사고 현장 사진을 분석하여 다음 정보를 한국어로 추출해주세요:

1. **사고 유형**: (추돌, 측면충돌, 정면충돌, 접촉사고 등)
2. **차량 정보**: 
   - 차량 대수
   - 차종 (승용차, SUV, 트럭 등)
   - 손상 정도 (경미, 중간, 심함)
3. **도로 상황**:
   - 도로 종류 (일반도로, 교차로, 고속도로 등)
   - 신호등/표지판 여부
   - 날씨/시간대
4. **기타 중요 정보**:
   - 특이사항
   - 과실 판단에 중요한 요소

간결하고 명확하게 작성해주세요.
            """
            
            # Gemini 1.5 Flash로 분석
            response = self.vision_model.generate_content([prompt, image])
            
            if response.text:
                logger.info("이미지 분석 완료")
                return response.text
            else:
                logger.warning("이미지 분석 결과가 없습니다.")
                return None
                
        except Exception as e:
            logger.error(f"이미지 분석 실패: {e}")
            return None
    
    def _optimize_image(self, image: Image.Image, max_size=(1024, 1024)) -> Image.Image:
        """이미지 최적화 (무료 버전 토큰 절약)"""
        # 크기 조정
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # RGB 변환 (필요시)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """텍스트 생성 (일반적인 용도)"""
        try:
            self._wait_for_rate_limit()
            
            # 토큰 제한 확인
            if max_tokens > Config.GEMINI_OUTPUT_LIMIT:
                max_tokens = Config.GEMINI_OUTPUT_LIMIT
            
            # 생성 설정
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.1,  # 법률 분야이므로 정확성 중시
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text if response.text else None
            
        except Exception as e:
            logger.error(f"텍스트 생성 실패: {e}")
            return None
    
    def check_api_status(self) -> Dict[str, Any]:
        """API 상태 확인"""
        try:
            # 간단한 테스트 요청
            test_response = self.model.generate_content("안녕하세요")
            
            return {
                "status": "success",
                "model": Config.GEMINI_MODEL,
                "api_key_valid": True,
                "test_response": test_response.text if test_response.text else "No response"
            }
        except Exception as e:
            return {
                "status": "error",
                "model": Config.GEMINI_MODEL,
                "api_key_valid": False,
                "error": str(e)
            }

def test_gemini_connection():
    """Gemini API 연결 테스트"""
    print("🔧 Gemini API 연결 테스트 중...")
    
    try:
        client = GeminiClient()
        status = client.check_api_status()
        
        if status["status"] == "success":
            print("✅ Gemini API 연결 성공!")
            print(f"📋 모델: {status['model']}")
            print(f"💬 테스트 응답: {status['test_response']}")
        else:
            print("❌ Gemini API 연결 실패!")
            print(f"🚫 오류: {status['error']}")
            
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        print("💡 .env 파일에서 GOOGLE_API_KEY를 확인해주세요.")

if __name__ == "__main__":
    test_gemini_connection()