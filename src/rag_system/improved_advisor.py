"""
개선된 교통사고 자문 챗봇 시스템
- 간단한 초기 진단 + 이미지 분석 기능
- 필요시 상세 분석으로 진행
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

from .document_processor import DocumentProcessor

class ImprovedTrafficAdvisor:
    def __init__(self, google_api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        개선된 교통사고 자문 챗봇 초기화
        """
        self.google_api_key = google_api_key
        
        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        
        # 문서 처리기 초기화 (선택적)
        try:
            self.doc_processor = DocumentProcessor(google_api_key)
            self.vectorstore = self.doc_processor.load_vectorstore()
        except:
            self.doc_processor = None
            self.vectorstore = None
            logger.warning("벡터스토어 로드 실패 - 일반 모드로 동작")
        
        # 메모리 초기화
        self.memory = ConversationBufferWindowMemory(
            k=3,  # 최근 3개 대화만 기억
            memory_key="chat_history",
            return_messages=True
        )
        
        # 프롬프트 설정
        self._setup_prompts()
        
        logger.info("개선된 교통사고 자문 챗봇 초기화 완료")
    
    def _setup_prompts(self):
        """간단한 진단용 프롬프트 설정"""
        
        # 초기 진단 프롬프트 (질문 최소화)
        self.quick_diagnosis_prompt = ChatPromptTemplate.from_template("""
당신은 교통사고 전문 자문사입니다. 
사용자가 제공한 정보를 바탕으로 **간단하고 즉시 활용 가능한 조언**을 제공해주세요.

사용자 상황: {user_input}
이미지 분석 결과: {image_analysis}

다음 형식으로 **간결하게** 답변해주세요:

## 🚗 사고 상황 요약
[사고 상황을 한 문장으로 요약]

## ⚖️ 예상 과실비율
[일반적인 과실비율과 간단한 근거]

## 📋 즉시 조치사항
1. [가장 우선적으로 해야 할 일]
2. [두 번째로 중요한 조치]
3. [세 번째 조치사항]

## 💡 주요 포인트
[과실 비율에 영향을 주는 핵심 요소 1-2개]

---
**더 자세한 분석을 원하시면 "상세 분석 요청"이라고 말씀해주세요.**

⚠️ 정확한 법률 자문을 위해서는 전문 변호사와 상담하시기 바랍니다.
""")
        
        # 상세 분석 프롬프트
        self.detailed_analysis_prompt = ChatPromptTemplate.from_template("""
사용자가 상세 분석을 요청했습니다. 
교통사고 전문가로서 더 깊이 있는 분석을 제공해주세요.

기존 대화: {chat_history}
사용자 요청: {user_input}

다음 사항들을 자세히 분석해주세요:

## 🔍 법률적 분석
- 적용 가능한 도로교통법 조항
- 유사 판례 (있다면)
- 과실 비율 결정 요인

## 📊 과실비율 상세 분석
- A차량 과실 요인
- B차량 과실 요인
- 조정 가능한 요소들

## 🛡️ 대응 전략
- 보험사 대응 방법
- 필요한 증거 자료
- 주의사항

## ❓ 추가 확인사항
[정확한 판단을 위해 필요한 추가 정보 2-3가지만]

필요하다면 추가 질문해주세요.
""")
    
    def quick_diagnosis(self, user_input: str, image_analysis: str = "") -> Dict[str, Any]:
        """빠른 초기 진단"""
        try:
            # 간단한 진단 체인
            chain = LLMChain(llm=self.llm, prompt=self.quick_diagnosis_prompt)
            
            result = chain.run(
                user_input=user_input,
                image_analysis=image_analysis or "이미지 분석 결과 없음"
            )
            
            # 대화 기록에 추가
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(result)
            
            return {
                "answer": result,
                "type": "quick_diagnosis",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"빠른 진단 실패: {e}")
            return {
                "answer": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
                "type": "error",
                "status": "error",
                "error": str(e)
            }
    
    def detailed_analysis(self, user_input: str) -> Dict[str, Any]:
        """상세 분석 제공"""
        try:
            # 대화 기록 가져오기
            chat_history = "\n".join([
                f"{'사용자' if isinstance(msg, HumanMessage) else '자문사'}: {msg.content}"
                for msg in self.memory.chat_memory.messages[-6:]  # 최근 6개
            ])
            
            # 상세 분석 체인
            chain = LLMChain(llm=self.llm, prompt=self.detailed_analysis_prompt)
            
            result = chain.run(
                chat_history=chat_history,
                user_input=user_input
            )
            
            # 대화 기록에 추가
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(result)
            
            return {
                "answer": result,
                "type": "detailed_analysis", 
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"상세 분석 실패: {e}")
            return {
                "answer": "상세 분석 중 오류가 발생했습니다. 다시 시도해주세요.",
                "type": "error",
                "status": "error",
                "error": str(e)
            }
    
    def analyze_with_context(self, user_input: str, image_analysis: str = "") -> Dict[str, Any]:
        """컨텍스트 기반 분석 (이미지 + 텍스트)"""
        
        # 상세 분석 요청인지 확인
        detail_keywords = ["상세", "더 자세히", "상세 분석", "더 알고 싶", "자세한 설명"]
        is_detail_request = any(keyword in user_input for keyword in detail_keywords)
        
        if is_detail_request:
            return self.detailed_analysis(user_input)
        else:
            return self.quick_diagnosis(user_input, image_analysis)
    
    def clear_conversation(self):
        """대화 기록 초기화"""
        self.memory.clear()
        logger.info("대화 기록이 초기화되었습니다")

def main():
    """테스트용 메인 함수"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("GOOGLE_API_KEY를 설정해주세요")
        return
    
    # 개선된 자문사 초기화
    advisor = ImprovedTrafficAdvisor(google_api_key)
    
    print("🚗 개선된 교통사고 자문 챗봇 (MVP)")
    print("간단한 상황 설명만으로도 즉시 조언을 받을 수 있습니다!")
    print("'quit'를 입력하면 종료됩니다.\n")
    
    while True:
        user_input = input("\n💬 사고 상황을 간단히 설명해주세요: ")
        if user_input.lower() in ['quit', 'exit', '종료']:
            break
        
        if not user_input.strip():
            continue
        
        # 분석 실행
        print("\n🔍 분석 중...")
        result = advisor.analyze_with_context(user_input)
        print(f"\n🤖 자문사:\n{result['answer']}")

if __name__ == "__main__":
    main()
