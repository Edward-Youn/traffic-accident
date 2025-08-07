"""
교통사고 자문 챗봇 시스템
LangChain을 활용한 RAG 기반 질의응답
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

from .document_processor import DocumentProcessor

class TrafficAccidentAdvisor:
    def __init__(self, google_api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        교통사고 자문 챗봇 초기화
        
        Args:
            google_api_key: Google API 키
            model_name: 사용할 모델명
        """
        self.google_api_key = google_api_key
        
        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        
        # 문서 처리기 초기화
        self.doc_processor = DocumentProcessor(google_api_key)
        self.vectorstore = self.doc_processor.load_vectorstore()
        
        # 메모리 초기화
        self.memory = ConversationBufferWindowMemory(
            k=5,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # 프롬프트 템플릿 설정
        self._setup_prompts()
        
        # 대화 체인 초기화
        self._setup_chains()
        
        logger.info("교통사고 자문 챗봇 초기화 완료")
    
    def _setup_prompts(self):
        """프롬프트 템플릿 설정"""
        
        # 메인 자문 프롬프트
        self.advisor_prompt = ChatPromptTemplate.from_template("""
당신은 교통사고 전문 법률 자문사입니다. 
사용자의 교통사고 상황을 분석하고, 관련 법률과 판례를 바탕으로 전문적인 조언을 제공합니다.

관련 자료:
{context}

대화 기록:
{chat_history}

사용자 질문: {question}

다음 지침에 따라 답변해주세요:

1. **상황 분석**: 사용자가 제공한 사고 상황을 명확히 파악
2. **관련 법률**: 적용 가능한 도로교통법 및 관련 규정 설명
3. **유사 판례**: 제공된 자료에서 유사한 사고 사례와 과실 비율 참조
4. **예상 과실비율**: 상황에 따른 예상 과실 비율 제시
5. **조치 사항**: 취해야 할 구체적인 행동 방안 제시
6. **주의사항**: 추가로 고려해야 할 사항들

**중요**: 
- 정확한 법률 조언을 위해서는 전문 변호사와 상담이 필요함을 항상 명시
- 제공된 정보만으로는 한계가 있음을 인정
- 구체적이고 실용적인 조언 제공

답변:
""")
        
        # 상황 파악용 프롬프트
        self.clarification_prompt = ChatPromptTemplate.from_template("""
사용자가 교통사고 상황에 대해 질문했습니다. 
정확한 법률 자문을 위해 추가 정보가 필요한지 판단하고, 필요하다면 구체적인 질문을 제시해주세요.

사용자 입력: {user_input}

현재까지의 대화:
{chat_history}

다음 정보들이 충분히 제공되었는지 확인하고, 부족한 부분에 대해 질문해주세요:

필수 정보:
- 사고 발생 장소 및 도로 상황
- 사고 당시 양 차량의 행동 (직진, 좌회전, 우회전, 정차 등)
- 교통신호 상황
- 사고 경위 및 충돌 부위
- 부상 여부 및 정도
- 보험 처리 상황

만약 충분한 정보가 제공되었다면 "정보 충분"이라고 답하고,
부족하다면 구체적으로 어떤 정보가 더 필요한지 친근하게 질문해주세요.
""")
    
    def _setup_chains(self):
        """대화 체인 설정"""
        if self.vectorstore:
            # RAG 체인 설정
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
                memory=self.memory,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": self.advisor_prompt}
            )
        else:
            logger.warning("벡터스토어가 없어서 일반 LLM 체인만 사용합니다")
            self.qa_chain = None
        
        # 상황 파악 체인
        self.clarification_chain = LLMChain(
            llm=self.llm,
            prompt=self.clarification_prompt
        )
    
    def analyze_situation(self, user_input: str) -> Dict[str, Any]:
        """사용자 입력 상황 분석"""
        try:
            chat_history = self.memory.chat_memory.messages
            chat_history_str = "\n".join([
                f"{'사용자' if isinstance(msg, HumanMessage) else '자문사'}: {msg.content}"
                for msg in chat_history[-10:]  # 최근 10개 메시지만
            ])
            
            result = self.clarification_chain.run(
                user_input=user_input,
                chat_history=chat_history_str
            )
            
            return {
                "needs_clarification": "정보 충분" not in result,
                "clarification_questions": result,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"상황 분석 실패: {e}")
            return {
                "needs_clarification": False,
                "clarification_questions": "",
                "status": "error",
                "error": str(e)
            }
    
    def get_advice(self, question: str) -> Dict[str, Any]:
        """교통사고 자문 제공"""
        try:
            if self.qa_chain:
                # RAG 기반 답변
                result = self.qa_chain({
                    "question": question
                })
                
                return {
                    "answer": result["answer"],
                    "source_documents": [
                        {
                            "content": doc.page_content[:300] + "...",
                            "metadata": doc.metadata
                        }
                        for doc in result.get("source_documents", [])
                    ],
                    "status": "success"
                }
            else:
                # 일반 LLM 답변 (벡터DB 없을 때)
                general_prompt = f"""
당신은 교통사고 전문 자문사입니다.
다음 질문에 대해 일반적인 교통법규와 상식선에서 조언해주세요.

질문: {question}

**주의**: 정확한 법률 자문을 위해서는 전문 변호사와 상담이 필요합니다.
"""
                response = self.llm.invoke([HumanMessage(content=general_prompt)])
                
                return {
                    "answer": response.content,
                    "source_documents": [],
                    "status": "success"
                }
                
        except Exception as e:
            logger.error(f"자문 제공 실패: {e}")
            return {
                "answer": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
                "source_documents": [],
                "status": "error",
                "error": str(e)
            }
    
    def get_conversation_summary(self) -> str:
        """대화 요약 제공"""
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return "아직 대화 기록이 없습니다."
            
            conversation_text = "\n".join([
                f"{'사용자' if isinstance(msg, HumanMessage) else '자문사'}: {msg.content}"
                for msg in messages
            ])
            
            summary_prompt = f"""
다음은 교통사고 법률 자문 대화입니다. 핵심 내용을 요약해주세요:

{conversation_text}

요약 형식:
- 사고 상황: 
- 주요 쟁점:
- 제공된 조언:
- 추가 고려사항:
"""
            
            response = self.llm.invoke([HumanMessage(content=summary_prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"대화 요약 실패: {e}")
            return "대화 요약 중 오류가 발생했습니다."
    
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
    
    # 자문사 초기화
    advisor = TrafficAccidentAdvisor(google_api_key)
    
    print("🚗 교통사고 자문 챗봇입니다.")
    print("사고 상황을 설명해주시면 법률 자문을 도와드리겠습니다.")
    print("'quit'를 입력하면 종료됩니다.\n")
    
    while True:
        user_input = input("\n사용자: ")
        if user_input.lower() in ['quit', 'exit', '종료']:
            break
        
        # 상황 분석
        analysis = advisor.analyze_situation(user_input)
        
        if analysis["needs_clarification"]:
            print(f"\n자문사: {analysis['clarification_questions']}")
        else:
            # 자문 제공
            advice = advisor.get_advice(user_input)
            print(f"\n자문사: {advice['answer']}")
            
            if advice['source_documents']:
                print("\n📚 참고 자료:")
                for i, doc in enumerate(advice['source_documents'][:2], 1):
                    print(f"{i}. {doc['metadata'].get('case_id', 'N/A')}: {doc['content'][:100]}...")

if __name__ == "__main__":
    main()
