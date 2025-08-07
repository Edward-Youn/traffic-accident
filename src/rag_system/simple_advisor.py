"""
벡터DB 없이 작동하는 간소화된 어드바이저 (프롬프트 오류 수정)
"""
import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

class SimpleTrafficAdvisor:
    def __init__(self, google_api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        간소화된 교통사고 자문사 (벡터DB 불필요)
        """
        self.google_api_key = google_api_key
        
        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        
        # 메모리 초기화
        self.memory = ConversationBufferWindowMemory(
            k=3,
            memory_key="chat_history",
            return_messages=True
        )
        
        # 프롬프트 설정
        self._setup_prompts()
        
        logger.info("간소화된 교통사고 자문사 초기화 완료 (벡터DB 없음)")
    
    def _setup_prompts(self):
        """프롬프트 설정 (중괄호 문제 해결)"""
        
        # 빠른 진단 프롬프트 (중괄호 제거)
        self.quick_diagnosis_prompt = ChatPromptTemplate.from_template("""
당신은 교통사고 전문 법률 자문사입니다. 
사용자의 상황을 분석하여 즉시 활용 가능한 조언을 제공해주세요.

사용자 상황: {user_input}
이미지 분석 결과: {image_analysis}

다음 형식으로 답변해주세요:

## 🚗 사고 상황 요약
상황을 한 문장으로 명확하게 요약해주세요.

## ⚖️ 예상 과실비율
일반적인 과실비율과 간단한 근거를 제시해주세요.

## 📋 즉시 조치사항
1. 가장 우선적으로 해야 할 일
2. 두 번째로 중요한 조치
3. 세 번째 조치사항

## 💡 주요 포인트
과실 비율에 영향을 주는 핵심 요소 1-2개를 설명해주세요.

---
**더 자세한 분석을 원하시면 "상세 분석"이라고 말씀해주세요.**

⚠️ 정확한 법률 자문을 위해서는 전문 변호사와 상담하시기 바랍니다.
""")
        
        # 상세 분석 프롬프트
        self.detailed_analysis_prompt = ChatPromptTemplate.from_template("""
사용자가 상세 분석을 요청했습니다.

기존 대화: {chat_history}
사용자 요청: {user_input}

다음 사항들을 자세히 분석해주세요:

## 🔍 법률적 분석
- 적용 가능한 도로교통법 조항
- 과실 비율 결정 요인

## 📊 과실비율 상세 분석
- A차량 과실 요인
- B차량 과실 요인
- 조정 가능한 요소들

## 🛡️ 대응 전략
- 보험사 대응 방법
- 필요한 증거 자료
- 주의사항

## ❓ 추가 고려사항
정확한 판단을 위해 고려해야 할 사항들을 알려주세요.

필요하다면 추가 질문해주세요.
""")
    
    def quick_diagnosis(self, user_input: str, image_analysis: str = "") -> Dict[str, Any]:
        """빠른 진단"""
        try:
            chain = LLMChain(llm=self.llm, prompt=self.quick_diagnosis_prompt)
            
            result = chain.invoke({
                "user_input": user_input,
                "image_analysis": image_analysis or "이미지 분석 결과 없음"
            })
            
            # 대화 기록에 추가
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(result["text"])
            
            return {
                "answer": result["text"],
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
        """상세 분석"""
        try:
            # 대화 기록 가져오기
            chat_history = "\n".join([
                f"{'사용자' if isinstance(msg, HumanMessage) else '자문사'}: {msg.content}"
                for msg in self.memory.chat_memory.messages[-6:]
            ])
            
            chain = LLMChain(llm=self.llm, prompt=self.detailed_analysis_prompt)
            
            result = chain.invoke({
                "chat_history": chat_history,
                "user_input": user_input
            })
            
            # 대화 기록에 추가
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(result["text"])
            
            return {
                "answer": result["text"],
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
    
    def generate_follow_up_questions(self, user_input: str, chat_history: str = "") -> Dict[str, Any]:
        """부족한 정보를 위한 추가 질문 생성"""
        try:
            follow_up_prompt = ChatPromptTemplate.from_template("""
당신은 교통사고 전문 조사원입니다.
사용자가 제공한 정보를 바탕으로 더 정확한 분석을 위해 추가로 필요한 정보를 파악하고 질문해주세요.

현재까지의 정보:
{user_input}

대화 기록:
{chat_history}

다음 영역에서 가장 중요한 2-3개의 질문을 선택해서 물어보세요:

**필수 정보 체크리스트:**
- 사고 발생 시간과 날씨 (주간/야간, 맑음/비/눈)
- 정확한 사고 위치 (교차로 종류, 차선 수, 신호등 상황)
- 양 차량의 주행 상황 (속도, 방향, 우선권)
- 충돌 범위와 손상 정도
- 목격자나 블랙박스 존재 여부
- 사고 당시 음주 여부
- 차량 정비 상태 (타이어, 브레이크 등)

다음 형식으로 답변해주세요:

## 🔍 추가 정보 필요
더 정확한 분석을 위해 몽 가지 더 알려주세요:

**1. [첫 번째 질문]**
- 예: 사고 당시 정확한 시간과 날씨는 어떠했나요?

**2. [두 번째 질문]**
- 예: 사고 지점의 신호등 상황은 어떠했나요?

**3. [세 번째 질문]**
- 예: 양 차량의 주행 속도는 대략 얼마였나요?

이 정보들을 알려주시면 훨씬 더 정확한 과실비율 분석을 드릴 수 있습니다.
""")
            
            chain = LLMChain(llm=self.llm, prompt=follow_up_prompt)
            
            result = chain.invoke({
                "user_input": user_input,
                "chat_history": chat_history or "대화 기록 없음"
            })
            
            return {
                "questions": result["text"],
                "type": "follow_up_questions",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"추가 질문 생성 실패: {e}")
            return {
                "questions": "추가 질문을 생성하는 중 오류가 발생했습니다.",
                "type": "error",
                "status": "error"
            }
        """컨텍스트 기반 분석"""
        
        # 상세 분석 요청인지 확인
        detail_keywords = ["상세", "더 자세히", "상세 분석", "더 알고 싶", "자세한 설명"]
        is_detail_request = any(keyword in user_input for keyword in detail_keywords)
        
        if is_detail_request:
            return self.detailed_analysis(user_input)
        else:
            return self.quick_diagnosis(user_input, image_analysis)
    
    def analyze_with_context(self, user_input: str, image_analysis: str = "") -> Dict[str, Any]:
        """컨텍스트 기반 분석"""
        
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

def test_simple_advisor():
    """간소화된 자문사 테스트"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("GOOGLE_API_KEY를 설정해주세요")
        return
    
    advisor = SimpleTrafficAdvisor(google_api_key)
    
    print("🚗 간소화된 교통사고 자문사 테스트")
    test_case = "신호등 교차로에서 직진 중 좌회전 차량과 충돌했습니다"
    
    result = advisor.quick_diagnosis(test_case)
    print("✅ 테스트 성공!" if result["status"] == "success" else "❌ 테스트 실패")
    if result["status"] == "success":
        print("답변 일부:")
        print(result["answer"][:200] + "...")

if __name__ == "__main__":
    test_simple_advisor()
