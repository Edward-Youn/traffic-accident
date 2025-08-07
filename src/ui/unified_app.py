"""
통합된 교통사고 AI 자문 챗봇 (HTML 태그 문제 완전 해결)
"""
import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.rag_system.simple_advisor import SimpleTrafficAdvisor
from src.multimodal.image_analyzer import AccidentImageAnalyzer
from src.data_processing.web_crawler import AccidentCrawler

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="교통사고 AI 자문 챗봇",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 간소화된 스타일
st.markdown("""
<style>
    .stAlert > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    .chat-user {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .chat-assistant {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
    if "advisor" not in st.session_state:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            st.session_state.advisor = SimpleTrafficAdvisor(google_api_key)
            st.session_state.image_analyzer = AccidentImageAnalyzer(google_api_key)
        else:
            st.session_state.advisor = None
            st.session_state.image_analyzer = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "waiting_for_answer" not in st.session_state:
        st.session_state.waiting_for_answer = False
    
    if "last_questions" not in st.session_state:
        st.session_state.last_questions = ""

def display_header():
    """헤더 표시 (HTML 없이)"""
    st.title("🚗 교통사고 AI 자문 챗봇")
    st.markdown("**📷 사진과 📝 상황 설명을 함께 분석해서 정확한 법률 자문을 제공합니다**")
    st.caption("사진은 선택사항이며, 간단한 설명만으로도 즉시 상담 가능합니다")
    st.markdown("---")

def display_sidebar():
    """사이드바"""
    with st.sidebar:
        st.header("🔧 시스템 관리")
        
        # API 상태
        api_status = "✅ 연결됨" if os.getenv("GOOGLE_API_KEY") else "❌ 미설정"
        st.info(f"**API 상태**: {api_status}")
        
        # 새로 시작
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            if st.session_state.advisor:
                st.session_state.advisor.clear_conversation()
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        
        # 간단한 데이터 관리
        with st.expander("📊 판례 데이터"):
            if st.button("📥 판례 수집 (5페이지)"):
                with st.spinner("수집 중..."):
                    try:
                        crawler = AccidentCrawler()
                        data = crawler.crawl_accident_data(max_pages=5)
                        st.success(f"✅ {len(data)}건 수집!")
                    except Exception as e:
                        st.error(f"❌ 오류: {e}")
        
        st.markdown("---")
        
        # 사용 가이드
        st.header("📋 사용법")
        st.markdown("""
        **1️⃣ 사진 업로드** (선택사항)
        
        **2️⃣ 상황 설명** 
        
        **3️⃣ 분석 요청**
        
        **4️⃣ 결과 확인**
        """)

def display_input_section():
    """통합 입력 섹션 (HTML 태그 없이)"""
    st.header("📝 교통사고 상담 시작")
    st.info("사진과 상황 설명을 입력하고 '상담 시작' 버튼을 눌러주세요")
    
    with st.form("accident_consultation", clear_on_submit=False):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📷 사고 현장 사진 (선택사항)")
            uploaded_file = st.file_uploader(
                "사진을 업로드하면 더 정확한 분석이 가능합니다",
                type=['jpg', 'jpeg', 'png'],
                help="선택사항입니다. 사진 없이도 상담 가능합니다."
            )
            
            if uploaded_file:
                st.success("📷 교통사고 현장 사진")
                st.image(uploaded_file, caption="업로드된 사진", use_column_width=True)
        
        with col2:
            st.subheader("📝 사고 상황 설명")
            
            # 예시 선택
            examples = [
                "신호등 교차로에서 직진 중 좌회전 차량과 충돌",
                "주차장에서 후진 중 지나가던 차량과 접촉",
                "고속도로 차선 변경 중 옆 차량과 충돌",
                "비보호 좌회전 시 직진 차량과 충돌"
            ]
            
            selected_example = st.selectbox(
                "💡 빠른 선택 (또는 직접 입력):",
                ["직접 입력"] + examples
            )
            
            # 텍스트 입력
            default_text = "" if selected_example == "직접 입력" else selected_example
            
            user_description = st.text_area(
                "사고 상황을 자세히 설명해주세요:",
                value=default_text,
                height=150,
                placeholder="예: 신호등이 있는 교차로에서 직진하던 중 좌회전하던 차량과 충돌했습니다."
            )
        
        # 제출 버튼
        st.markdown("---")
        submitted = st.form_submit_button(
            "🚀 AI 상담 시작",
            use_container_width=True
        )
        
        if submitted:
            if user_description.strip():
                process_consultation(user_description, uploaded_file)
            else:
                st.error("❌ 사고 상황을 입력해주세요!")

def process_consultation(description: str, uploaded_file):
    """통합 상담 처리"""
    if not st.session_state.advisor:
        st.error("❌ AI 시스템을 초기화할 수 없습니다. API 키를 확인해주세요.")
        return
    
    with st.spinner("🤖 AI가 분석하고 있습니다..."):
        try:
            # 1. 이미지 분석 (있는 경우)
            image_analysis = ""
            if uploaded_file and st.session_state.image_analyzer:
                st.info("📷 사진을 분석하고 있습니다...")
                image_analysis = st.session_state.image_analyzer.analyze_uploaded_file(uploaded_file)
                if image_analysis:
                    st.success("✅ 사진 분석 완료!")
            
            # 2. 통합 분석
            st.info("💭 종합 분석 중...")
            result = st.session_state.advisor.analyze_with_context(description, image_analysis)
            
            # 3. 결과 저장
            user_content = description
            if uploaded_file:
                user_content += f"\n[사진 첨부: {uploaded_file.name}]"
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_content,
                "has_image": uploaded_file is not None,
                "image_analysis": image_analysis if uploaded_file else ""
            })
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": result["answer"],
                "type": result.get("type", "unknown")
            })
            
            st.success("✅ 분석 완료!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")

def display_chat_history():
    """대화 기록 표시 (HTML 최소화)"""
    if not st.session_state.chat_history:
        return
    
    st.header("💬 상담 기록")
    
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            with st.container():
                st.markdown(f'<div class="chat-user"><strong>👤 사용자:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
            
            # 이미지 분석 결과 표시
            if message.get("has_image") and message.get("image_analysis"):
                with st.expander(f"📷 업로드된 사진 분석 결과 {i+1}"):
                    st.write(message["image_analysis"])
        
        else:
            with st.container():
                st.markdown(f'<div class="chat-assistant"><strong>🤖 AI 자문사:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
            
            # 상세 분석 버튼
            if message.get("type") == "quick_diagnosis":
                if st.button(f"📊 더 자세한 분석 받기 (상담 {i+1})", key=f"detail_{i}"):
                    with st.spinner("🔍 상세 분석 중..."):
                        detailed_result = st.session_state.advisor.detailed_analysis("상세 분석 요청")
                        
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": "상세 분석 요청"
                        })
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": detailed_result["answer"],
                            "type": "detailed_analysis"
                        })
                        st.rerun()

def display_welcome():
    """웰컴 메시지 (HTML 없이)"""
    if not st.session_state.chat_history:
        st.info("🎯 **교통사고 AI 자문을 시작해보세요!**")
        st.write("사진과 상황 설명을 입력하시면 즉시 전문적인 법률 자문을 받을 수 있습니다.")
        
        # 장점 소개
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📷 이미지 AI 분석**
            
            사고 현장 사진을 업로드하면 AI가 자동으로 상황을 분석합니다
            """)
        
        with col2:
            st.markdown("""
            **⚡ 즉시 진단**
            
            간단한 설명만으로도 바로 과실비율과 조치사항 제공
            """)
        
        with col3:
            st.markdown("""
            **📊 상세 분석**
            
            필요시 더 자세한 법률 분석과 구체적인 대응 전략까지 제공
            """)

def display_warning():
    """주의사항 (HTML 없이)"""
    st.warning("""
    ⚠️ **중요 고지사항**
    
    본 AI 자문은 일반적인 정보 제공 목적이며, 구체적인 법률 자문을 대체할 수 없습니다. 
    정확한 법률 상담을 위해서는 **전문 변호사와 상담**하시기 바랍니다.
    """)

def main():
    """메인 함수"""
    initialize_session_state()
    
    # 레이아웃
    display_header()
    display_sidebar()
    display_warning()
    
    # 메인 컨텐츠
    display_welcome()
    display_input_section()
    display_chat_history()

if __name__ == "__main__":
    main()
