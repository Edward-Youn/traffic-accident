"""
교통사고 AI 자문 챗봇 - Streamlit Community Cloud 배포용
"""
import streamlit as st
import os
import sys
from pathlib import Path

# 프로젝트 루트 설정
if __name__ == "__main__":
    # 현재 파일의 디렉토리를 기준으로 설정
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir))

# Streamlit Cloud에서는 secrets를 사용
if hasattr(st, 'secrets'):
    try:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    except:
        st.error("🔑 Google API Key가 설정되지 않았습니다. Streamlit Cloud에서 Secrets를 설정해주세요.")
        st.stop()

from src.rag_system.enhanced_advisor import EnhancedTrafficAdvisor
from src.multimodal.image_analyzer import AccidentImageAnalyzer
from src.data_processing.web_crawler import AccidentCrawler
# PDF 생성 - 간소화 버전 사용
try:
    from src.utils.simple_pdf import create_simple_pdf_download_button as create_pdf_download_button
except ImportError:
    try:
        from src.utils.pdf_generator import create_pdf_download_button
    except ImportError:
        def create_pdf_download_button(*args, **kwargs):
            st.warning("📄 PDF 다운로드 기능이 현재 사용할 수 없습니다.")
            return False

# 페이지 설정
st.set_page_config(
    page_title="교통사고 AI 자문 챗봇",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일
st.markdown("""
<style>
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
    .chat-questions {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
    if "advisor" not in st.session_state:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            try:
                st.session_state.advisor = EnhancedTrafficAdvisor(google_api_key)
                st.session_state.image_analyzer = AccidentImageAnalyzer(google_api_key)
            except Exception as e:
                st.error(f"❌ AI 시스템 초기화 실패: {e}")
                st.session_state.advisor = None
                st.session_state.image_analyzer = None
        else:
            st.session_state.advisor = None
            st.session_state.image_analyzer = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "waiting_for_answer" not in st.session_state:
        st.session_state.waiting_for_answer = False

def display_header():
    """헤더 표시"""
    st.title("🚗 교통사고 AI 자문 챗봇")
    st.markdown("**📷 사진과 📝 상황 설명을 함께 분석해서 정확한 법률 자문을 제공합니다**")
    st.caption("💬 실제 판례 데이터 기반 + 상호작용형 질문-답변으로 정확한 분석!")
    
    # 배포 정보
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        st.badge("🎯 실제 판례 활용", type="secondary")
    with col3:
        st.badge("🔍 상호작용 분석", type="secondary")
    
    st.markdown("---")

def display_sidebar():
    """사이드바"""
    with st.sidebar:
        st.header("🔧 시스템 상태")
        
        # API 상태
        api_status = "✅ 연결됨" if st.session_state.advisor else "❌ 오류"
        st.info(f"**AI 시스템**: {api_status}")
        
        # 판례 데이터 상태
        if st.session_state.advisor:
            case_count = len(st.session_state.advisor.case_data)
            st.success(f"**판례 데이터**: {case_count}건 활용 중")
        
        # 대화 초기화
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            if st.session_state.advisor:
                st.session_state.advisor.clear_conversation()
            st.session_state.chat_history = []
            st.session_state.waiting_for_answer = False
            st.rerun()
        
        st.markdown("---")
        
        # 사용 가이드
        st.header("📋 사용 가이드")
        st.markdown("""
        **1️⃣ 초기 상담**
        - 사진 + 상황 설명 입력
        
        **2️⃣ 판례 기반 분석**
        - 23건 실제 판례 참조
        
        **3️⃣ 추가 질문**
        - "더 질문하기"로 정확도 향상
        
        **4️⃣ 상세 분석**
        - 법률적 근거와 대응방법
        """)
        
        st.markdown("---")
        
        # 주의사항
        st.warning("""
        ⚠️ **중요**
        
        본 서비스는 참고용이며, 
        정확한 법률 상담은 
        전문 변호사와 하세요.
        """)

def display_input_section():
    """입력 섹션"""
    if not st.session_state.waiting_for_answer:
        st.header("📝 교통사고 상담 시작")
        
        with st.form("accident_consultation", clear_on_submit=False):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📷 사고 현장 사진 (선택)")
                uploaded_file = st.file_uploader(
                    "사진 업로드하면 더 정확한 분석",
                    type=['jpg', 'jpeg', 'png'],
                    help="선택사항입니다"
                )
                
                if uploaded_file:
                    st.image(uploaded_file, caption="업로드된 사진", use_column_width=True)
            
            with col2:
                st.subheader("📝 사고 상황 설명")
                
                examples = [
                    "신호등 교차로에서 직진 중 좌회전 차량과 충돌",
                    "주차장에서 후진 중 지나가던 차량과 접촉", 
                    "고속도로 차선 변경 중 옆 차량과 충돌",
                    "비보호 좌회전 시 직진 차량과 충돌"
                ]
                
                selected = st.selectbox("💡 예시 선택:", ["직접 입력"] + examples)
                default_text = "" if selected == "직접 입력" else selected
                
                user_description = st.text_area(
                    "상황을 자세히 설명해주세요:",
                    value=default_text,
                    height=120,
                    placeholder="예: 신호등 교차로에서..."
                )
            
            submitted = st.form_submit_button("🚀 AI 상담 시작", use_container_width=True)
            
            if submitted:
                if user_description.strip():
                    process_consultation(user_description, uploaded_file)
                else:
                    st.error("❌ 사고 상황을 입력해주세요!")

def process_consultation(description: str, uploaded_file):
    """상담 처리"""
    if not st.session_state.advisor:
        st.error("❌ AI 시스템이 초기화되지 않았습니다.")
        return
    
    with st.spinner("🤖 AI가 판례를 분석하고 있습니다..."):
        try:
            # 이미지 분석
            image_analysis = ""
            if uploaded_file and st.session_state.image_analyzer:
                image_analysis = st.session_state.image_analyzer.analyze_uploaded_file(uploaded_file)
            
            # 통합 분석
            result = st.session_state.advisor.analyze_with_context(description, image_analysis)
            
            # 결과 저장
            user_content = description
            if uploaded_file:
                user_content += f"\n[사진 첨부: {uploaded_file.name}]"
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_content,
                "has_image": uploaded_file is not None
            })
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["answer"],
                "type": result.get("type", "unknown")
            })
            
            st.success("✅ 분석 완료!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 분석 중 오류: {str(e)}")

def display_chat_history():
    """대화 기록 표시"""
    if not st.session_state.chat_history:
        # 웰컴 메시지
        st.info("🎯 **교통사고 AI 자문을 시작해보세요!**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**📚 실제 판례 활용**\n\n23건의 교통사고 판례를 바탕으로 정확한 과실비율 제시")
        with col2:
            st.markdown("**🔍 상호작용 분석**\n\n단계별 질문-답변으로 점진적 정확도 향상")
        with col3:
            st.markdown("**📊 종합 자문**\n\n과실비율 + 즉시조치 + 법률적 근거까지")
        
        return
    
    st.header("💬 상담 기록")
    
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(f'<div class="chat-user"><strong>👤 사용자:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant"><strong>🤖 AI 자문사:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
            
            # 버튼들
            if message.get("type") in ["quick_diagnosis", "enhanced_diagnosis", "updated_analysis"]:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"🔍 더 질문하기", key=f"q_{i}"):
                        st.info("🔄 추가 질문 기능을 준비 중입니다...")
                
                with col2:
                    if st.button(f"📊 상세 분석", key=f"d_{i}"):
                        with st.spinner("분석 중..."):
                            try:
                                result = st.session_state.advisor.detailed_analysis("상세 분석 요청")
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": result["answer"],
                                    "type": "detailed_analysis"
                                })
                                st.rerun()
                            except Exception as e:
                                st.error(f"오류: {e}")
            
            # PDF 다운로드 버튼 (상세 분석 후)
            if message.get("type") == "detailed_analysis":
                st.markdown("---")
                
                # 사용자 입력 찾기
                user_input = ""
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user" and "상세 분석" not in msg.get("content", ""):
                        user_input = msg["content"]
                        break
                
                # PDF 다운로드
                if user_input:
                    st.success("📝 **상세 분석 완료!** PDF 리포트를 다운로드하세요.")
                    
                    try:
                        # 참조 판례 정보 가져오기
                        case_info = None
                        if hasattr(st.session_state.advisor, 'case_data'):
                            case_info = st.session_state.advisor._search_similar_cases(user_input)[:3]
                        
                        # PDF 다운로드 버튼 생성
                        create_pdf_download_button(
                            user_input=user_input,
                            analysis_result=message["content"],
                            case_info=case_info
                        )
                        
                    except Exception as e:
                        st.warning(f"PDF 생성 기능이 일시적으로 사용할 수 없습니다: {e}")
                        st.info("💡 대신 분석 내용을 복사하여 사용하세요.")

def main():
    """메인 함수"""
    initialize_session_state()
    
    display_header()
    display_sidebar()
    display_input_section()
    display_chat_history()

if __name__ == "__main__":
    main()
