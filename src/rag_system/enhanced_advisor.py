"""
판례 데이터를 활용하는 개선된 자문사
벡터DB 없이 키워드 기반으로 유사 판례 검색
"""
import os
import json
from typing import Dict, Any, List
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

class EnhancedTrafficAdvisor:
    def __init__(self, google_api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        판례 데이터를 활용하는 교통사고 자문사
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
        
        # 판례 데이터 로드
        self.case_data = self._load_case_data()
        
        # 프롬프트 설정
        self._setup_prompts()
        
        logger.info(f"판례 데이터 활용 자문사 초기화 완료 ({len(self.case_data)}건 판례)")
    
    def _load_case_data(self) -> List[Dict]:
        """판례 데이터 로드"""
        try:
            case_file = Path("./data/cases/accident_cases.json")
            if case_file.exists():
                with open(case_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("판례 데이터 파일이 없습니다")
                return []
        except Exception as e:
            logger.error(f"판례 데이터 로드 실패: {e}")
            return []
    
    def _search_similar_cases(self, user_input: str) -> List[Dict]:
        """키워드 기반 유사 판례 검색"""
        if not self.case_data:
            return []
        
        # 키워드 추출
        keywords = ["직진", "좌회전", "우회전", "신호등", "교차로", "녹색", "적색", "황색", 
                   "비보호", "화살표", "점멸", "후진", "차선변경", "주차장"]
        
        user_keywords = [kw for kw in keywords if kw in user_input]
        
        if not user_keywords:
            return []
        
        # 유사 사례 찾기
        similar_cases = []
        for case in self.case_data:
            score = 0
            case_text = f"{case['vehicle_A_situation']} {case['vehicle_B_situation']} {case['accident_description']}"
            
            for keyword in user_keywords:
                if keyword in case_text:
                    score += 1
            
            if score > 0:
                case['similarity_score'] = score
                similar_cases.append(case)
        
        # 점수순으로 정렬하고 상위 3개 반환
        similar_cases.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_cases[:3]
    
    def _setup_prompts(self):
        """프롬프트 설정"""
        
        # 판례 활용 진단 프롬프트
        self.enhanced_diagnosis_prompt = ChatPromptTemplate.from_template("""
당신은 교통사고 전문 법률 자문사입니다. 
사용자의 상황을 분석하여 즉시 활용 가능한 조언을 제공해주세요.

사용자 상황: {user_input}
이미지 분석 결과: {image_analysis}

**관련 판례 정보:**
{similar_cases}

위 판례들을 참고하여 다음 형식으로 답변해주세요:

## 🚗 사고 상황 요약
상황을 한 문장으로 명확하게 요약해주세요.

## ⚖️ 예상 과실비율
**유사 판례 기준:** {case_examples}
**예상 과실비율:** [판례를 바탕으로 한 예상 비율과 근거]

## 📋 즉시 조치사항
1. 가장 우선적으로 해야 할 일
2. 두 번째로 중요한 조치
3. 세 번째 조치사항

## 💡 주요 포인트
과실 비율에 영향을 주는 핵심 요소를 판례를 바탕으로 설명해주세요.

## 📚 참고 판례
{reference_cases}

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
        
        # 추가 질문 프롬프트
        self.follow_up_prompt = ChatPromptTemplate.from_template("""
당신은 교통사고 전문 조사원입니다.
사용자가 제공한 정보를 바탕으로 더 정확한 분석을 위해 추가로 필요한 정보를 파악하고 질문해주세요.

현재까지의 정보:
{user_input}

대화 기록:
{chat_history}

다음 형식으로 답변해주세요:

## 🔍 추가 정보 필요
더 정확한 분석을 위해 몇 가지 더 알려주세요:

**1. [첫 번째 질문]**
- 예: 사고 당시 정확한 시간과 날씨는 어떠했나요?

**2. [두 번째 질문]**
- 예: 사고 지점의 신호등 상황은 어떠했나요?

**3. [세 번째 질문]**
- 예: 양 차량의 주행 속도는 대략 얼마였나요?

이 정보들을 알려주시면 훨씬 더 정확한 과실비율 분석을 드릴 수 있습니다.
""")
    
    def quick_diagnosis(self, user_input: str, image_analysis: str = "") -> Dict[str, Any]:
        """판례를 활용한 빠른 진단"""
        try:
            # 유사 판례 검색
            similar_cases = self._search_similar_cases(user_input)
            
            # 판례 정보 포맷팅
            case_examples = ""
            reference_cases = ""
            similar_cases_text = "관련 판례가 없습니다."
            
            if similar_cases:
                case_examples = "\n".join([
                    f"- {case['case_id']}: {case['fault_ratio']}"
                    for case in similar_cases
                ])
                
                reference_cases = "\n".join([
                    f"**{case['case_id']}**: {case['accident_description'][:100]}... (과실비율: {case['fault_ratio']})"
                    for case in similar_cases
                ])
                
                similar_cases_text = "\n".join([
                    f"{case['case_id']}: {case['accident_description']} (과실비율: {case['fault_ratio']})"
                    for case in similar_cases
                ])
            
            chain = LLMChain(llm=self.llm, prompt=self.enhanced_diagnosis_prompt)
            
            result = chain.invoke({
                "user_input": user_input,
                "image_analysis": image_analysis or "이미지 분석 결과 없음",
                "similar_cases": similar_cases_text,
                "case_examples": case_examples or "관련 판례 없음",
                "reference_cases": reference_cases or "관련 판례 없음"
            })
            
            # 대화 기록에 추가
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(result["text"])
            
            return {
                "answer": result["text"],
                "type": "quick_diagnosis",  # UI 호환성을 위해 quick_diagnosis로 변경
                "status": "success",
                "similar_cases": similar_cases
            }
            
        except Exception as e:
            logger.error(f"판례 활용 진단 실패: {e}")
            return {
                "answer": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
                "type": "error",
                "status": "error",
                "error": str(e)
            }
    
    def detailed_analysis(self, user_input: str) -> Dict[str, Any]:
        """상세 분석"""
        try:
            chat_history = "\n".join([
                f"{'사용자' if isinstance(msg, HumanMessage) else '자문사'}: {msg.content}"
                for msg in self.memory.chat_memory.messages[-6:]
            ])
            
            chain = LLMChain(llm=self.llm, prompt=self.detailed_analysis_prompt)
            
            result = chain.invoke({
                "chat_history": chat_history,
                "user_input": user_input
            })
            
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
        """추가 질문 생성"""
        try:
            chain = LLMChain(llm=self.llm, prompt=self.follow_up_prompt)
            
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
    
    def analyze_with_context(self, user_input: str, image_analysis: str = "") -> Dict[str, Any]:
        """컨텍스트 기반 분석"""
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

def test_enhanced_advisor():
    """판례 활용 자문사 테스트"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        print("GOOGLE_API_KEY를 설정해주세요")
        return
    
    advisor = EnhancedTrafficAdvisor(google_api_key)
    
    print("🚗 판례 활용 교통사고 자문사 테스트")
    test_case = "신호등 교차로에서 직진 중 좌회전 차량과 충돌했습니다"
    
    result = advisor.quick_diagnosis(test_case)
    print("✅ 테스트 성공!" if result["status"] == "success" else "❌ 테스트 실패")
    if result["status"] == "success":
        print(f"📚 관련 판례: {len(result.get('similar_cases', []))}건")

if __name__ == "__main__":
    test_enhanced_advisor()
