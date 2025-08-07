"""
상호작용 기능이 추가된 교통사고 AI 자문 챗봇
"""
import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.rag_system.enhanced_advisor import EnhancedTrafficAdvisor
from src.multimodal.image_analyzer import AccidentImageAnalyzer
from src.data_processing.web_crawler import AccidentCrawler
# PDF 생성 - 간소화 버전 사용
try:
    from src.utils.simple_pdf import create_simple_pdf_download_button as create_pdf_download_button
except ImportError:
    # fallback: 원본 버전 시도
    try:
        from src.utils.pdf_generator import create_pdf_download_button
    except ImportError:
        # PDF 기능 비활성화
        def create_pdf_download_button(*args, **kwargs):
            st.warning("📄 PDF 다운로드 기능이 현재 사용할 수 없습니다.")
            return False

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
            st.session_state.advisor = EnhancedTrafficAdvisor(google_api_key)
            st.session_state.image_analyzer = AccidentImageAnalyzer(google_api_key)
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
    st.caption("💬 상호작용형 질문-답변으로 더 정확한 분석이 가능합니다")
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
            st.session_state.waiting_for_answer = False
            st.rerun()
        
        st.markdown("---")
        
        # 사용 가이드
        st.header("📋 사용법")
        st.markdown("""
        **1️⃣ 초기 상담**
        - 사진과 기본 상황 설명
        
        **2️⃣ 추가 질문**
        - "더 질문하기" 버튼으로 정확도 향상
        
        **3️⃣ 상세 분석**
        - 충분한 정보 수집 후 최종 분석
        
        **4️⃣ 결과 활용**
        - 보험사 대응 및 법률 자문 활용
        """)

def display_input_section():
    """통합 입력 섹션"""
    if not st.session_state.waiting_for_answer:
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

def display_follow_up_form():
    """추가 질문 답변 폼"""
    if st.session_state.waiting_for_answer:
        st.header("🔍 추가 정보 입력")
        st.info("더 정확한 분석을 위해 위 질문들에 답변해주세요")
        
        with st.form("follow_up_answers", clear_on_submit=True):
            st.write("📝 **위 질문들에 대한 답변을 아래에 입력해주세요:**")
            
            user_answer = st.text_area(
                "답변 내용:",
                height=150,
                placeholder="예: 1. 사고는 오후 3시경 맑은 날씨에 발생했습니다. 2. 신호등은 제가 직진할 때 초록불이었습니다. 3. 제 차량은 시속 40km, 상대방은 천천히 좌회전하고 있었습니다.",
                help="각 질문에 대해 순서대로 답변해주세요. 모르는 부분은 '모름'이라고 적어주세요."
            )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("📝 답변 제출", use_container_width=True):
                    if user_answer.strip():
                        process_follow_up_answer(user_answer)
                    else:
                        st.error("❌ 답변을 입력해주세요!")
            
            with col2:
                if st.form_submit_button("⏭️ 현재 정보로 분석", use_container_width=True, help="추가 정보 없이 현재 정보만으로 분석합니다"):
                    st.session_state.waiting_for_answer = False
                    finalize_analysis()

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

def process_follow_up_answer(answer: str):
    """추가 질문 답변 처리"""
    if not st.session_state.advisor:
        return
    
    with st.spinner("🔍 추가 정보를 바탕으로 재분석 중..."):
        try:
            # 사용자 답변 저장
            st.session_state.chat_history.append({
                "role": "user",
                "content": f"추가 정보: {answer}",
                "type": "follow_up_answer"
            })
            
            # 전체 대화를 바탕으로 재분석
            chat_context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in st.session_state.chat_history[-6:]
            ])
            
            result = st.session_state.advisor.quick_diagnosis(
                f"추가 정보를 반영한 재분석: {answer}",
                ""
            )
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["answer"],
                "type": "updated_analysis"
            })
            
            st.session_state.waiting_for_answer = False
            st.success("✅ 추가 정보를 바탕으로 재분석 완료!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 재분석 중 오류가 발생했습니다: {str(e)}")

def finalize_analysis():
    """현재 정보로 최종 분석"""
    if not st.session_state.advisor:
        return
    
    with st.spinner("📊 최종 분석 중..."):
        try:
            result = st.session_state.advisor.detailed_analysis("현재 정보를 바탕으로 최종 분석 요청")
            
            st.session_state.chat_history.append({
                "role": "user",
                "content": "현재 정보로 최종 분석 요청"
            })
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["answer"],
                "type": "final_analysis"
            })
            
            st.success("✅ 최종 분석 완료!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 최종 분석 중 오류가 발생했습니다: {str(e)}")

def display_chat_history():
    """대화 기록 표시"""
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
            
            # 각 AI 응답 후 상호작용 버튼들
            col1, col2 = st.columns(2)
            
            with col1:
                # 더 질문하기 버튼 (진단 관련 응답에 모두 표시)
                if message.get("type") in ["quick_diagnosis", "enhanced_diagnosis", "updated_analysis"]:
                    if st.button(f"🔍 더 질문하기 (상담 {i//2+1})", key=f"questions_{i}"):
                        generate_follow_up_questions(i)
            
            with col2:
                # 상세 분석 버튼 (진단 관련 응답에 모두 표시)
                if message.get("type") in ["quick_diagnosis", "enhanced_diagnosis", "updated_analysis"]:
                    if st.button(f"📊 상세 분석 (상담 {i//2+1})", key=f"detail_{i}"):
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
            
            # PDF 다운로드 버튼 (상세 분석 후에만 표시)
            if message.get("type") == "detailed_analysis":
                st.markdown("---")
                
                # 사용자 입력 찾기 (최초 사용자 입력)
                user_input = ""
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user" and "상세 분석" not in msg["content"]:
                        user_input = msg["content"]
                        break
                
                # 참조 판례 정보 가져오기
                case_info = None
                if hasattr(st.session_state.advisor, 'case_data'):
                    case_info = st.session_state.advisor._search_similar_cases(user_input)[:3]
                
                # PDF 다운로드 버튼
                with st.container():
                    st.info("📝 **상세 분석 완료!** 아래 버튼으로 PDF 리포트를 다운로드하세요.")
                    
                    try:
                        create_pdf_download_button(
                            user_input=user_input,
                            analysis_result=message["content"],
                            case_info=case_info
                        )
                    except Exception as e:
                        st.error(f"😭 PDF 생성 기능이 일시적으로 사용할 수 없습니다: {e}")
                        st.info("📝 대신 분석 내용을 복사해서 사용하세요.")

def generate_follow_up_questions(message_index):
    """추가 질문 생성"""
    if not st.session_state.advisor:
        return
    
    with st.spinner("🤔 추가 질문을 생성하고 있습니다..."):
        try:
            # 현재까지의 대화 내용
            chat_history = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in st.session_state.chat_history[:message_index+1]
            ])
            
            # 최초 사용자 입력 찾기
            user_input = ""
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    user_input = msg["content"]
                    break
            
            # 추가 질문 생성
            questions_result = st.session_state.advisor.generate_follow_up_questions(user_input, chat_history)
            
            if questions_result["status"] == "success":
                # 질문을 대화 기록에 추가
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": questions_result["questions"],
                    "type": "follow_up_questions"
                })
                
                # 답변 대기 상태로 변경
                st.session_state.waiting_for_answer = True
                st.rerun()
            else:
                st.error("❌ 질문 생성에 실패했습니다.")
                
        except Exception as e:
            st.error(f"❌ 질문 생성 중 오류가 발생했습니다: {str(e)}")

def display_welcome():
    """웰컴 메시지"""
    if not st.session_state.chat_history:
        st.info("🎯 **교통사고 AI 자문을 시작해보세요!**")
        st.write("**새로운 상호작용 기능으로 더 정확한 분석이 가능합니다:**")
        
        # 기능 소개
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📷 이미지 AI 분석**
            
            사고 현장 사진을 업로드하면 AI가 자동으로 상황을 분석합니다
            """)
        
        with col2:
            st.markdown("""
            **🔍 추가 질문하기**
            
            AI가 부족한 정보를 파악해서 추가 질문을 합니다
            """)
        
        with col3:
            st.markdown("""
            **📊 점진적 정확도 향상**
            
            질문-답변을 통해 분석 정확도가 점점 높아집니다
            """)
        
        st.markdown("---")
        st.success("💡 **팁**: 처음에는 간단히 설명하고, '더 질문하기' 버튼으로 정확도를 높여보세요!")

def display_warning():
    """주의사항"""
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
    
    # 추가 질문 대기 상태에 따른 조건부 표시
    if st.session_state.waiting_for_answer:
        st.markdown("---")
        st.success("🔍 **아래 질문들에 답변해주세요 ↓**")
        display_follow_up_form()
    else:
        display_input_section()
    
    display_chat_history()

if __name__ == "__main__":
    main()
