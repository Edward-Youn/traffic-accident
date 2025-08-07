"""
PDF 리포트 생성 모듈 - 한글 지원
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st
from typing import Dict, Any
import requests
import tempfile
import os

class TrafficAccidentPDFGenerator:
    def __init__(self):
        """PDF 생성기 초기화"""
        self.setup_korean_font()
        
    def setup_korean_font(self):
        """한글 폰트 설정 (개선된 버전)"""
        try:
            # 방법 1: 시스템에 설치된 한글 폰트 사용
            import platform
            system = platform.system()
            
            if system == "Windows":
                # Windows 시스템 폰트
                font_paths = [
                    r"C:\Windows\Fonts\malgun.ttf",  # 맑은 고딕
                    r"C:\Windows\Fonts\gulim.ttc",   # 굴림
                    r"C:\Windows\Fonts\batang.ttc",  # 바탕
                ]
            elif system == "Darwin":  # macOS
                font_paths = [
                    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                    "/Library/Fonts/NanumGothic.ttf",
                ]
            else:  # Linux
                font_paths = [
                    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                ]
            
            # 시스템 폰트 시도
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
                        self.korean_font = 'KoreanFont'
                        print(f"✅ 시스템 폰트 로드 성공: {font_path}")
                        return
                    except Exception as e:
                        print(f"⚠️ 폰트 로드 실패: {font_path} - {e}")
                        continue
            
            # 방법 2: 온라인에서 나눔 고딕 다운로드
            try:
                print("🔄 온라인 한글 폰트 다운로드 시도...")
                import urllib.request
                
                # 나눔 고딕 Regular 다운로드
                font_url = "https://github.com/naver/nanumfont/releases/download/VER2.6/NanumFont_TTF_ALL.zip"
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ttf') as tmp_file:
                    # 간단한 폰트 URL로 시도
                    simple_font_url = "https://fonts.gstatic.com/ea/nanumgothic/v5/NanumGothic-Regular.ttf"
                    
                    try:
                        urllib.request.urlretrieve(simple_font_url, tmp_file.name)
                        pdfmetrics.registerFont(TTFont('KoreanFont', tmp_file.name))
                        self.korean_font = 'KoreanFont'
                        print("✅ 온라인 한글 폰트 로드 성공")
                        return
                    except Exception as e:
                        print(f"⚠️ 온라인 폰트 다운로드 실패: {e}")
                    finally:
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass
                            
            except Exception as e:
                print(f"⚠️ 온라인 폰트 처리 실패: {e}")
            
            # 방법 3: DejaVu Sans 사용 (유니코드 지원)
            try:
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                pdfmetrics.registerFont(UnicodeCIDFont('Korean'))
                self.korean_font = 'Korean'
                print("✅ Unicode CID 폰트 사용")
                return
            except Exception as e:
                print(f"⚠️ Unicode CID 폰트 실패: {e}")
            
            # 방법 4: 기본 폰트 사용 (한글 깨짐)
            self.korean_font = 'Helvetica'
            print("⚠️ 한글 폰트 로드 실패, 기본 폰트 사용")
            
        except Exception as e:
            self.korean_font = 'Helvetica'
            print(f"❌ 폰트 설정 전체 실패: {e}")
    
    def create_styles(self):
        """PDF 스타일 정의"""
        styles = getSampleStyleSheet()
        
        # 한글 지원 스타일들
        styles.add(ParagraphStyle(
            name='KoreanTitle',
            parent=styles['Title'],
            fontName=self.korean_font,
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        styles.add(ParagraphStyle(
            name='KoreanHeading',
            parent=styles['Heading1'],
            fontName=self.korean_font,
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkred
        ))
        
        styles.add(ParagraphStyle(
            name='KoreanNormal',
            parent=styles['Normal'],
            fontName=self.korean_font,
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        styles.add(ParagraphStyle(
            name='KoreanBullet',
            parent=styles['Normal'],
            fontName=self.korean_font,
            fontSize=10,
            spaceAfter=6,
            leftIndent=20,
            bulletIndent=10
        ))
        
        return styles
    
    def parse_analysis_content(self, content: str) -> Dict[str, str]:
        """분석 내용을 섹션별로 파싱 (한글 안전 처리)"""
        sections = {}
        current_section = "기본정보"
        current_content = []
        
        # 한글 안전 처리
        try:
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            content = str(content)
        except Exception as e:
            print(f"⚠️ 텍스트 인코딩 문제: {e}")
            content = str(content)
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 섹션 헤더 감지 (##, 🚗, ⚖️ 등으로 시작)
            if line.startswith('##') or any(emoji in line for emoji in ['🚗', '⚖️', '📋', '💡', '📊', '🔍', '🛡️', '❓', '📚']):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # 섹션 이름 정리
                section_name = line
                for emoji in ['##', '🚗', '⚖️', '📋', '💡', '📊', '🔍', '🛡️', '❓', '📚']:
                    section_name = section_name.replace(emoji, '')
                current_section = section_name.strip()
                if not current_section:
                    current_section = f"섹션_{len(sections)+1}"
                current_content = []
            else:
                current_content.append(line)
        
        # 마지막 섹션 추가
        if current_content:
            sections[current_section] = '\n'.join(current_content)
            
        return sections
    
    def generate_pdf(self, user_input: str, analysis_result: str, case_info: list = None) -> io.BytesIO:
        """PDF 리포트 생성"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # 스타일 설정
        styles = self.create_styles()
        story = []
        
        # 제목
        title = Paragraph("교통사고 AI 분석 리포트", styles['KoreanTitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # 기본 정보
        info_data = [
            ['분석 일시', datetime.now().strftime('%Y년 %m월 %d일 %H:%M')],
            ['분석 유형', '상세 분석'],
            ['사용 데이터', '실제 판례 23건 기반']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # 사용자 입력 사항
        story.append(Paragraph("사고 상황 설명", styles['KoreanHeading']))
        story.append(Paragraph(user_input, styles['KoreanNormal']))
        story.append(Spacer(1, 15))
        
        # 분석 결과 파싱 및 추가
        sections = self.parse_analysis_content(analysis_result)
        
        for section_title, section_content in sections.items():
            if section_title and section_content:
                story.append(Paragraph(section_title, styles['KoreanHeading']))
                
                # 내용을 줄별로 나누어 처리
                content_lines = section_content.split('\n')
                for line in content_lines:
                    line = line.strip()
                    if line:
                        # 리스트 항목 처리 (-, *, 번호 등)
                        if line.startswith(('-', '*', '•')) or (len(line) > 2 and line[1] == '.'):
                            story.append(Paragraph(f"• {line.lstrip('- *•').lstrip('0123456789.')}", styles['KoreanBullet']))
                        else:
                            story.append(Paragraph(line, styles['KoreanNormal']))
                
                story.append(Spacer(1, 15))
        
        # 관련 판례 정보 (있는 경우)
        if case_info and len(case_info) > 0:
            story.append(Paragraph("참조 판례 상세 정보", styles['KoreanHeading']))
            
            for i, case in enumerate(case_info[:3], 1):  # 최대 3건만 표시
                case_data = [
                    ['판례 번호', case.get('case_id', 'N/A')],
                    ['과실 비율', case.get('fault_ratio', 'N/A')],
                    ['사고 유형', case.get('accident_description', 'N/A')[:100] + '...']
                ]
                
                case_table = Table(case_data, colWidths=[2*inch, 4*inch])
                case_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(case_table)
                story.append(Spacer(1, 10))
        
        # 면책 조항
        story.append(PageBreak())
        story.append(Paragraph("중요 고지사항", styles['KoreanHeading']))
        disclaimer = """
본 AI 분석 리포트는 일반적인 정보 제공 목적으로 작성되었으며, 구체적인 법률 자문을 대체할 수 없습니다.
실제 교통사고 처리 시에는 반드시 다음 사항을 준수하시기 바랍니다:

• 경찰서 신고 및 현장 조사 협조
• 보험사 신고 및 손해사정 절차 진행  
• 필요시 전문 변호사와 상담
• 의료진 진료 및 치료 우선

본 리포트의 과실 비율 및 법률적 해석은 참고용이며, 실제 결과와 다를 수 있습니다.
정확한 법률 판단을 위해서는 전문가와 상담하시기 바랍니다.
        """
        story.append(Paragraph(disclaimer, styles['KoreanNormal']))
        
        # 푸터 정보
        story.append(Spacer(1, 30))
        footer_text = f"교통사고 AI 자문 챗봇 | 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(footer_text, styles['KoreanNormal']))
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        return buffer

def create_pdf_download_button(user_input: str, analysis_result: str, case_info: list = None):
    """Streamlit PDF 다운로드 버튼 생성"""
    try:
        pdf_generator = TrafficAccidentPDFGenerator()
        pdf_buffer = pdf_generator.generate_pdf(user_input, analysis_result, case_info)
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"교통사고_분석리포트_{timestamp}.pdf"
        
        # 다운로드 버튼
        st.download_button(
            label="📄 상세 분석 PDF 다운로드",
            data=pdf_buffer.getvalue(),
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
        
        return True
        
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {e}")
        return False

if __name__ == "__main__":
    # 테스트
    generator = TrafficAccidentPDFGenerator()
    test_input = "신호등 교차로에서 직진 중 좌회전 차량과 충돌했습니다."
    test_result = "## 🚗 사고 상황 요약\n신호등 교차로 직진-좌회전 충돌\n\n## ⚖️ 예상 과실비율\n좌회전차량 80-90%, 직진차량 10-20%"
    
    pdf = generator.generate_pdf(test_input, test_result)
    print("✅ PDF 생성 테스트 완료")
