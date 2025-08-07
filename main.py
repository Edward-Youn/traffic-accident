"""
교통사고 자문 시스템 메인 실행기
"""
import os
import sys
from pathlib import Path
import argparse
from dotenv import load_dotenv

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

def setup_environment():
    """환경 설정"""
    load_dotenv()
    
    # 필요한 디렉토리 생성
    dirs_to_create = [
        "data/laws",
        "data/cases", 
        "data/processed",
        "data/chroma_db",
        "logs",
        "tests"
    ]
    
    for dir_path in dirs_to_create:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ 환경 설정 완료")

def run_crawler():
    """크롤링 실행"""
    from src.data_processing.web_crawler import AccidentCrawler
    
    print("🕷️ 교통사고 판례 크롤링을 시작합니다...")
    
    crawler = AccidentCrawler()
    
    # 사용자 입력
    try:
        max_pages = int(input("크롤링할 최대 페이지 수 (기본값: 5, 전체: 62): ") or "5")
    except ValueError:
        max_pages = 5
    
    accident_data = crawler.crawl_accident_data(max_pages=max_pages)
    print(f"✅ 크롤링 완료! 총 {len(accident_data)}건의 사고 판례를 수집했습니다.")

def build_vectordb():
    """벡터 데이터베이스 구축"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 GOOGLE_API_KEY를 설정해주세요.")
        return
    
    from src.rag_system.document_processor import DocumentProcessor
    
    print("🔧 벡터 데이터베이스를 구축합니다...")
    
    processor = DocumentProcessor(google_api_key)
    
    # 판례 데이터 로드
    cases_file = PROJECT_ROOT / "data" / "cases" / "accident_cases.json"
    if cases_file.exists():
        print("📚 판례 데이터 로드 중...")
        case_documents = processor.load_accident_cases(str(cases_file))
        
        if case_documents:
            print("⚙️ 벡터 임베딩 및 저장 중...")
            processor.process_and_store_documents(case_documents)
            print("✅ 벡터 데이터베이스 구축 완료!")
        else:
            print("❌ 처리할 판례 데이터가 없습니다.")
    else:
        print("❌ 판례 데이터 파일을 찾을 수 없습니다.")
        print("   먼저 'python main.py --crawl' 명령으로 데이터를 수집해주세요.")

def run_cli_chat():
    """CLI 채팅 실행"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY가 설정되지 않았습니다.")
        return
    
    from src.rag_system.advisor import TrafficAccidentAdvisor
    
    print("🤖 교통사고 자문 챗봇 (CLI 모드)")
    print("사고 상황을 설명해주시면 법률 자문을 도와드리겠습니다.")
    print("'quit' 또는 'exit'를 입력하면 종료됩니다.\n")
    
    advisor = TrafficAccidentAdvisor(google_api_key)
    
    while True:
        try:
            user_input = input("\n💬 사용자: ")
            if user_input.lower() in ['quit', 'exit', '종료']:
                break
            
            if not user_input.strip():
                continue
            
            # 상황 분석
            print("🔍 상황 분석 중...")
            analysis = advisor.analyze_situation(user_input)
            
            if analysis["needs_clarification"]:
                print(f"\n🤖 자문사: {analysis['clarification_questions']}")
            else:
                # 자문 제공
                print("💭 법률 자문 생성 중...")
                advice = advisor.get_advice(user_input)
                print(f"\n🤖 자문사: {advice['answer']}")
                
                # 참고 자료 표시
                if advice['source_documents']:
                    print("\n📚 참고 자료:")
                    for i, doc in enumerate(advice['source_documents'][:2], 1):
                        case_id = doc['metadata'].get('case_id', 'N/A')
                        content_preview = doc['content'][:100] + "..."
                        print(f"   {i}. {case_id}: {content_preview}")
        
        except KeyboardInterrupt:
            print("\n\n👋 채팅을 종료합니다.")
            break
        except Exception as e:
            print(f"\n❌ 오류가 발생했습니다: {e}")

def run_improved_web_app():
    """교통사고 AI 자문 챗봇 실행 (상호작용 버전)"""
    import subprocess
    
    print("🌐 교통사고 AI 자문 챗봇을 시작합니다...")
    print("💬 상호작용 질문-답변 기능으로 더 정확한 분석!")
    print("브라우저에서 http://localhost:8501 로 접속하세요.")
    
    # 상호작용 Streamlit 앱 실행
    app_path = PROJECT_ROOT / "src" / "ui" / "interactive_app.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

def run_web_app():
    """기존 Streamlit 웹앱 실행"""
    import subprocess
    
    print("🌐 웹 애플리케이션을 시작합니다...")
    print("브라우저에서 http://localhost:8501 로 접속하세요.")
    
    # Streamlit 앱 실행
    app_path = PROJECT_ROOT / "src" / "ui" / "streamlit_app.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

def check_system():
    """시스템 상태 확인"""
    print("🔍 시스템 상태 확인\n")
    
    # API 키 확인
    api_key = os.getenv("GOOGLE_API_KEY")
    api_status = "✅ 설정됨" if api_key else "❌ 미설정"
    print(f"Google API 키: {api_status}")
    
    # 데이터 파일 확인
    cases_file = PROJECT_ROOT / "data" / "cases" / "accident_cases.json"
    cases_status = "✅ 존재" if cases_file.exists() else "❌ 없음"
    cases_count = 0
    if cases_file.exists():
        try:
            import json
            with open(cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cases_count = len(data)
        except:
            pass
    print(f"판례 데이터: {cases_status} ({cases_count}건)")
    
    # 벡터DB 확인
    vectordb_path = PROJECT_ROOT / "data" / "chroma_db"
    vectordb_status = "✅ 구축됨" if vectordb_path.exists() and list(vectordb_path.glob("*")) else "❌ 미구축"
    print(f"벡터 DB: {vectordb_status}")
    
    # 권장 사항
    print("\n📋 권장 실행 순서:")
    print("1. python main.py --crawl     # 판례 데이터 수집")
    print("2. python main.py --build     # 벡터DB 구축") 
    print("3. python main.py --web       # 웹앱 실행")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="교통사고 자문 시스템")
    parser.add_argument("--setup", action="store_true", help="환경 설정")
    parser.add_argument("--crawl", action="store_true", help="판례 데이터 크롤링")
    parser.add_argument("--build", action="store_true", help="벡터 데이터베이스 구축")
    parser.add_argument("--chat", action="store_true", help="CLI 채팅 실행")
    parser.add_argument("--web", action="store_true", help="기존 웹 애플리케이션 실행")
    parser.add_argument("--mvp", action="store_true", help="교통사고 AI 자문 챗봇 실행 (추천)")
    parser.add_argument("--check", action="store_true", help="시스템 상태 확인")
    
    args = parser.parse_args()
    
    # 기본 환경 설정
    setup_environment()
    
    if args.setup:
        print("✅ 환경 설정이 완료되었습니다.")
    elif args.crawl:
        run_crawler()
    elif args.build:
        build_vectordb()
    elif args.chat:
        run_cli_chat()
    elif args.web:
        run_web_app()
    elif args.mvp:
        run_improved_web_app()
    elif args.check:
        check_system()
    else:
        # 기본 동작: 상태 확인 후 AI 자문 챗봇 실행
        check_system()
        print("\n" + "="*50)
        print("🤖 추천: 교통사고 AI 자문 챗봇 (이미지 업로드 + 빠른 진단)")
        response = input("AI 자문 챗봇을 실행하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            run_improved_web_app()

if __name__ == "__main__":
    main()
