"""
개선된 교통사고 자문 Streamlit 웹앱
- 이미지 업로드 지원
- 간단한 초기 진단 + 상세 분석 옵션
"""
import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.rag_system.improved_advisor import ImprovedTrafficAdvisor
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

# CSS 스타일 (더 모던하게)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    }
    
    .quick-diagnosis {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
    }
    
    .detailed-analysis {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
    }
    
    .image-analysis {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #2d3436;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .user-message {
        background-color: #f8f9fa;
        border-left-color: #28a745;
    }
    
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #667eea;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
    if "advisor" not in st.session_state:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            st.session_state.advisor = ImprovedTrafficAdvisor(google_api_key)
            st.session_state.image_analyzer = AccidentImageAnalyzer(google_api_key)
        else:
            st.session_state.advisor = None
            st.session_state.image_analyzer = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "current_image_analysis" not in st.session_state:
        st.session_state.current_image_analysis = ""

def display_header():
    """헤더 표시"""
    st.markdown("""
    <div class="main-header">
        <h1>🚗 교통사고 AI 자문 챗봇</h1>
        <p>📷 사진 + 📝 상황설명 → ⚡ 즉시 진단!</p>
        <p><small>간단한 초기 진단 후 원하시면 상세 분석도 가능합니다</small></p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """개선된 사이드바"""
    with st.sidebar:
        st.header("🔧 시스템 관리")
        
        # 빠른 상태 확인
        api_key_status = "✅" if os.getenv("GOOGLE_API_KEY") else "❌"
        st.write(f"**API 상태**: {api_key_status}")
        
        # 대화 초기화
        if st.button("🗑️ 새로 시작"):
            if st.session_state.advisor:
                st.session_state.advisor.clear_conversation()
            st.session_state.chat_history = []
            st.session_state.current_image_analysis = ""
            st.rerun()
        
        st.markdown("---")
        
        # 데이터 관리 (축소)
        with st.expander("📊 데이터 관리"):
            if st.button("📥 판례 수집 (5페이지)"):
                with st.spinner("수집 중..."):
                    try:
                        crawler = AccidentCrawler()
                        data = crawler.crawl_accident_data(max_pages=5, delay=0.5)
                        st.success(f"✅ {len(data)}건 수집 완료!")
                    except Exception as e:
                        st.error(f"❌ 수집 실패: {e}")
        
        st.markdown("---")
        
        # 사용 가이드
        st.header("📋 사용법")
        st.markdown("""
        **1단계**: 사고 사진 업로드 (선택)
        
        **2단계**: 간단한 상황 설명
        
        **3단계**: 즉시 진단 확인
        
        **4단계**: 필요시 "상세 분석" 요청
        """)

def display_image_upload():
    """이미지 업로드 섹션"""
    st.markdown("""
    <div class="image-analysis">
        <h3>📷 사고 현장 사진 분석 (선택사항)</h3>
        <p>사진이 있으면 더 정확한 분석이 가능합니다!</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "사고 현장 사진을 업로드하세요",
        type=['jpg', 'jpeg', 'png'],
        help="사진이 있으면 AI가 현장을 분석해서 더 정확한 조언을 드립니다"
    )
    
    if uploaded_file is not None:
        # 이미지 표시
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(uploaded_file, caption="업로드된 사진", use_column_width=True)
        
        with col2:
            if st.button("🔍 사진 분석하기", key="analyze_image"):
                if st.session_state.image_analyzer:
                    with st.spinner("🤖 AI가 사진을 분석하고 있습니다..."):
                        try:
                            analysis = st.session_state.image_analyzer.analyze_uploaded_file(uploaded_file)
                            if analysis:
                                st.session_state.current_image_analysis = analysis
                                st.success("✅ 사진 분석 완료!")
                                st.write("**분석 결과:**")
                                st.write(analysis[:300] + "..." if len(analysis) > 300 else analysis)
                            else:
                                st.error("❌ 사진 분석에 실패했습니다")
                        except Exception as e:
                            st.error(f"❌ 분석 오류: {e}")
                else:
                    st.error("❌ 이미지 분석기를 초기화할 수 없습니다")

def display_quick_input():
    """빠른 입력 섹션"""
    st.markdown("""
    <div class="quick-diagnosis">
        <h3>⚡ 빠른 상황 입력</h3>
        <p>간단히 설명만 해도 즉시 조언을 받을 수 있어요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 예시 버튼들
    st.write("**💡 예시 상황 (클릭하면 자동 입력):**")
    
    col1, col2 = st.columns(2)
    
    examples = [
        "신호등 교차로에서 직진 중 좌회전 차량과 충돌했어요",
        "주차장에서 후진하다가 지나가던 차와 부딪혔습니다",
        "고속도로에서 차선 변경 중 옆 차량과 접촉사고가 났어요",
        "비보호 좌회전 시 직진 차량과 충돌했습니다"
    ]
    
    for i, example in enumerate(examples):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(f"📝 {example[:15]}...", key=f"example_{i}"):
                st.session_state.user_input = example
                process_user_input(example)

def display_chat_interface():
    """채팅 인터페이스"""
    st.header("💬 AI 자문 대화")
    
    # 채팅 기록 표시
    if st.session_state.chat_history:
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
                    <strong>🤖 AI 자문사:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                # 상세 분석 버튼 (빠른 진단인 경우)
                if message.get("type") == "quick_diagnosis":
                    if st.button("📊 더 자세한 분석 받기", key=f"detail_{len(st.session_state.chat_history)}"):
                        process_user_input("상세 분석 요청")
    
    # 사용자 입력을 텍스트 입력으로 변경 (chat_input 대신)
    with st.form("user_input_form", clear_on_submit=True):
        user_input = st.text_area(
            "사고 상황을 간단히 설명해주세요...",
            height=100,
            placeholder="예: 신호등 교차로에서 직진 중 좌회전 차량과 충돌했어요"
        )
        submitted = st.form_submit_button("💬 상담 요청")
        
        if submitted and user_input:
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
    
    with st.spinner("🤖 AI가 분석하고 있습니다..."):
        try:
            # 이미지 분석 결과와 함께 처리
            result = st.session_state.advisor.analyze_with_context(
                user_input, 
                st.session_state.current_image_analysis
            )
            
            # AI 응답 추가
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["answer"],
                "type": result.get("type", "unknown")
            })
            
            # 이미지 분석 결과 초기화 (한 번만 사용)
            if st.session_state.current_image_analysis:
                st.session_state.current_image_analysis = ""
            
        except Exception as e:
            st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
    
    st.rerun()

def display_warning():
    """주의사항 표시"""
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ 중요 고지사항</h4>
        <p>
        본 AI 자문은 일반적인 정보 제공 목적이며, 구체적인 법률 자문을 대체할 수 없습니다. 
        정확한 법률 상담을 위해서는 <strong>전문 변호사와 상담</strong>하시기 바랍니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_welcome_screen():
    """웰컴 스크린 (대화가 없을 때)"""
    if not st.session_state.chat_history:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h2>🎯 어떻게 도와드릴까요?</h2>
            <p>사고 상황을 간단히 설명하시면 즉시 조언을 드립니다!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 기능 소개
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 📷 이미지 분석
            사고 현장 사진을 업로드하면
            AI가 자동으로 분석합니다
            """)
        
        with col2:
            st.markdown("""
            ### ⚡ 즉시 진단
            간단한 설명만으로도
            바로 과실비율과 조치사항 제공
            """)
        
        with col3:
            st.markdown("""
            ### 📊 상세 분석
            필요시 더 자세한 법률 분석과
            대응 전략까지 제공
            """)

def main():
    """메인 함수"""
    initialize_session_state()
    
    # 레이아웃
    display_header()
    display_sidebar()
    display_warning()
    
    # 메인 컨텐츠
    tab1, tab2 = st.tabs(["🚗 AI 자문", "📷 이미지 분석"])
    
    with tab1:
        display_welcome_screen()
        display_quick_input()
        display_chat_interface()
    
    with tab2:
        display_image_upload()
        
        # 현재 이미지 분석 결과 표시
        if st.session_state.current_image_analysis:
            st.markdown("""
            <div class="detailed-analysis">
                <h3>🔍 현재 이미지 분석 결과</h3>
                <p>아래 결과가 텍스트 상담에 자동으로 활용됩니다</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📋 전체 분석 결과 보기"):
                st.write(st.session_state.current_image_analysis)

if __name__ == "__main__":
    main()
