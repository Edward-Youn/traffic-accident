"""
패키지 설치 및 import 테스트 스크립트
"""
import subprocess
import sys

def install_missing_packages():
    """누락된 패키지 설치"""
    packages = [
        "reportlab>=4.0.0"
    ]
    
    for package in packages:
        try:
            print(f"📦 {package} 설치 중...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 설치 완료")
        except Exception as e:
            print(f"❌ {package} 설치 실패: {e}")

def test_imports():
    """import 테스트"""
    print("\n🧪 Import 테스트:")
    
    try:
        from reportlab.lib.pagesizes import A4
        print("✅ reportlab 임포트 성공")
    except ImportError as e:
        print(f"❌ reportlab 임포트 실패: {e}")
        return False
    
    try:
        import sys
        import os
        from pathlib import Path
        
        # 프로젝트 루트를 sys.path에 추가
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from src.utils.pdf_generator import create_pdf_download_button
        print("✅ PDF 생성기 임포트 성공")
        return True
    except ImportError as e:
        print(f"❌ PDF 생성기 임포트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🔧 패키지 설치 및 테스트")
    print("=" * 40)
    
    install_missing_packages()
    
    if test_imports():
        print("\n🎉 모든 패키지가 정상적으로 설치되었습니다!")
        print("이제 Streamlit 앱을 다시 실행해보세요.")
    else:
        print("\n⚠️ 일부 패키지에 문제가 있습니다.")
