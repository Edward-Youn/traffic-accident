"""
교통사고 자문 Streamlit 웹앱
"""
import streamlit as st
import os
import sys
from pathlib import Path
import json
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.rag_system.advisor import TrafficAccidentAdvisor
from src.data_processing.web_crawler import AccidentCrawler

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="교통사고 법률 자문 챗봇",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e7db8 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2e7db8;
    }
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #4CAF50;
    }
    
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #2e7db8;
    }
    
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
    if "advisor" not in st.session_state:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            st.session_state.advisor = TrafficAccidentAdvisor(google_api_key)
        else:
            st.session_state.advisor = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "waiting_for_clarification" not in st.session_state:
        st.session_state.waiting_for_clarification = False

def display_header():
    """헤더 표시"""
    st.markdown("""
    <div class="main-header">
        <h1>🚗 교통사고 법률 자문 챗봇</h1>
        <p>AI 기반 교통사고 상황 분석 및 법률 자문 서비스</p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """사이드바 표시"""
    with st.sidebar:
        st.header("📋 서비스 안내")
        
        st.markdown("""
        <div class="sidebar-info">
        <h4>🎯 서비스 기능</h4>
        <ul>
            <li>교통사고 상황 분석</li>
            <li>관련 법률 및 판례 검색</li>
            <li>예상 과실비율 제시</li>
            <li>구체적 조치방안 안내</li>
        </ul>
        
        <h4>📝 입력 정보</h4>
        <ul>
            <li>사고 발생 장소 및 도로상황</li>
            <li>양 차량의 주행 상황</li>
            <li>교통신호 상태</li>
            <li>충돌 부위 및 경위</li>
            <li>부상 여부</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 데이터 관리 섹션
        st.header("🛠️ 데이터 관리")
        
        # 크롤링 기능
        if st.button("📥 판례 데이터 수집", help="교통사고 판례를 크롤링합니다"):
            run_crawler()
        
        # 벡터DB 구축
        if st.button("🔧 벡터DB 구축", help="수집된 데이터로 벡터DB를 구축합니다"):
            build_vectordb()
        
        # 대화 초기화
        if st.button("🗑️ 대화 초기화"):
            if st.session_state.advisor:
                st.session_state.advisor.clear_conversation()
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        
        # 시스템 상태
        st.header("📊 시스템 상태")
        
        # API 키 상태
        api_key_status = "✅ 연결됨" if os.getenv("GOOGLE_API_KEY") else "❌ 미설정"
        st.write(f"**Google API**: {api_key_status}")
        
        # 벡터DB 상태
        vectordb_path = project_root / "data" / "chroma_db"
        vectordb_status = "✅ 구축됨" if vectordb_path.exists() else "❌ 미구축"
        st.write(f"**벡터 DB**: {vectordb_status}")
        
        # 판례 데이터 상태
        cases_file = project_root / "data" / "cases" / "accident_cases.json"
        cases_status = "✅ 존재" if cases_file.exists() else "❌ 없음"
        st.write(f"**판례 데이터**: {cases_status}")

def display_warning():
    """주의사항 표시"""
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ 중요 고지사항</h4>
        <p>
        본 서비스는 일반적인 정보 제공 목적으로만 사용되며, 
        구체적인 법률 자문을 대체할 수 없습니다. 
        정확한 법률 상담을 위해서는 전문 변호사와 상담하시기 바랍니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_chat_interface():
    """채팅 인터페이스 표시"""
    st.header("💬 교통사고 상담")
    
    # 채팅 기록 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 사용자:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 자문사:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                # 참고 자료가 있다면 표시
                if message.get("sources"):
                    with st.expander("📚 참고 자료"):
                        for i, source in enumerate(message["sources"], 1):
                            st.write(f"**{i}. {source['metadata'].get('case_id', 'N/A')}**")
                            st.write(source["content"][:200] + "...")
    
    # 사용자 입력
    user_input = st.chat_input("교통사고 상황을 설명해주세요...")
    
    if user_input:
        process_user_input(user_input)

def process_user_input(user_input: str):
    """사용자 입력 처리"""
    if not st.session_state.advisor:
        st.error("❌ 시스템 초기화에 실패했습니다. Google API 키를 확인해주세요.")
        return
    
    # 사용자 메시지 추가
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    
    with st.spinner("분석 중..."):
        try:
            # 상황 분석
            analysis = st.session_state.advisor.analyze_situation(user_input)
            
            if analysis["needs_clarification"]:
                # 추가 정보 필요
                response = analysis["clarification_questions"]
                st.session_state.waiting_for_clarification = True
            else:
                # 자문 제공
                advice = st.session_state.advisor.get_advice(user_input)
                response = advice["answer"]
                
                # 어시스턴트 메시지 추가
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "sources": advice.get("source_documents", [])
                })
                
                st.session_state.waiting_for_clarification = False
                st.rerun()
                return
            
            # 어시스턴트 메시지 추가
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            
        except Exception as e:
            st.error(f"❌ 오류가 발생했습니다: {str(e)}")
    
    st.rerun()

def run_crawler():
    """크롤링 실행"""
    with st.spinner("판례 데이터를 수집하고 있습니다..."):
        try:
            crawler = AccidentCrawler()
            
            # 테스트용으로 5페이지만 크롤링
            accident_data = crawler.crawl_accident_data(max_pages=5, delay=0.5)
            
            if accident_data:
                st.success(f"✅ 판례 {len(accident_data)}건 수집 완료!")
            else:
                st.warning("⚠️ 수집된 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"❌ 크롤링 실패: {str(e)}")

def build_vectordb():
    """벡터DB 구축"""
    with st.spinner("벡터 데이터베이스를 구축하고 있습니다..."):
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                st.error("❌ Google API 키가 설정되지 않았습니다.")
                return
            
            from src.rag_system.document_processor import DocumentProcessor
            
            processor = DocumentProcessor(google_api_key)
            
            # 판례 데이터 로드
            cases_file = project_root / "data" / "cases" / "accident_cases.json"
            if cases_file.exists():
                case_documents = processor.load_accident_cases(str(cases_file))
                
                if case_documents:
                    processor.process_and_store_documents(case_documents)
                    st.success("✅ 벡터 데이터베이스 구축 완료!")
                    
                    # 자문사 재초기화
                    st.session_state.advisor = TrafficAccidentAdvisor(google_api_key)
                else:
                    st.warning("⚠️ 처리할 판례 데이터가 없습니다.")
            else:
                st.error("❌ 판례 데이터 파일을 찾을 수 없습니다. 먼저 데이터를 수집해주세요.")
                
        except Exception as e:
            st.error(f"❌ 벡터DB 구축 실패: {str(e)}")

def display_examples():
    """예시 질문 표시"""
    st.header("💡 예시 질문")
    
    examples = [
        "신호등이 있는 교차로에서 직진하는 차와 좌회전하는 차가 충돌했어요",
        "주차장에서 후진하다가 지나가던 차와 부딪혔습니다",
        "고속도로에서 차선 변경 중 사고가 났어요",
        "비보호 좌회전 시 직진차와 충돌했습니다"
    ]
    
    col1, col2 = st.columns(2)
    
    for i, example in enumerate(examples):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(f"📝 {example[:20]}...", key=f"example_{i}"):
                process_user_input(example)

def main():
    """메인 함수"""
    initialize_session_state()
    
    # 레이아웃
    display_header()
    display_sidebar()
    display_warning()
    
    # 메인 컨텐츠
    if not st.session_state.chat_history:
        display_examples()
    
    display_chat_interface()

if __name__ == "__main__":
    main()
