"""
한글 지원 PDF 생성기 (간소화 버전)
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import streamlit as st
from typing import Dict, Any
import os
import platform

class SimpleKoreanPDFGenerator:
    def __init__(self):
        """간소화된 PDF 생성기 초기화"""
        self.korean_font = self.setup_font()
        
    def setup_font(self):
        """한글 폰트 설정 (간소화)"""
        try:
            # Windows 시스템 폰트 우선 시도
            if platform.system() == "Windows":
                font_paths = [
                    r"C:\Windows\Fonts\malgun.ttf",  # 맑은 고딕
                    r"C:\Windows\Fonts\gulim.ttc",   # 굴림
                ]
                
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('Korean', font_path))
                            print(f"✅ 한글 폰트 로드 성공: {font_path}")
                            return 'Korean'
                        except Exception as e:
                            print(f"⚠️ 폰트 로드 실패: {e}")
                            continue
            
            # 기본 폰트 사용 (영문만 지원)
            print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
            return 'Helvetica'
            
        except Exception as e:
            print(f"❌ 폰트 설정 실패: {e}")
            return 'Helvetica'
    
    def clean_korean_text(self, text: str) -> str:
        """한글 텍스트 정리"""
        if not text:
            return ""
        
        try:
            # 이모지 제거
            import re
            # 이모지 패턴 제거
            emoji_pattern = re.compile("["
                                     u"\U0001F600-\U0001F64F"  # emoticons
                                     u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                     u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                     u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                     "]+", flags=re.UNICODE)
            text = emoji_pattern.sub('', text)
            
            # 특수 문자를 일반 문자로 변경
            replacements = {
                '⚖️': '[과실비율]',
                '🚗': '[사고상황]',
                '📋': '[조치사항]',
                '💡': '[주요포인트]',
                '📊': '[분석]',
                '🔍': '[법률분석]',
                '🛡️': '[대응전략]',
                '❓': '[고려사항]',
                '📚': '[참고판례]',
                '##': ''
            }
            
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            return text.strip()
            
        except Exception as e:
            print(f"⚠️ 텍스트 정리 실패: {e}")
            return str(text)
    
    def parse_analysis_sections(self, analysis_result: str) -> dict:
        """분석 결과를 섹션별로 파싱"""
        sections = {
            'legal_analysis': '',
            'fault_ratio': '',
            'response_strategy': '',
            'additional_considerations': '',
            'other': ''
        }
        
        try:
            # 섹션 구분자들
            section_markers = {
                'legal_analysis': ['법률적 분석', '법률분석', '[법률분석]', '🔍'],
                'fault_ratio': ['과실비율', '과실 비율', '[과실비율]', '⚖️'],
                'response_strategy': ['대응전략', '대응 전략', '[대응전략]', '🛡️'],
                'additional_considerations': ['추가 고려사항', '고려사항', '[고려사항]', '❓', '추가고려사항']
            }
            
            lines = analysis_result.split('\n')
            current_section = 'other'
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 섹션 헤더 확인
                section_found = False
                for section_key, markers in section_markers.items():
                    for marker in markers:
                        if marker in line:
                            current_section = section_key
                            section_found = True
                            break
                    if section_found:
                        break
                
                # 내용 추가
                if not section_found or not any(marker in line for markers in section_markers.values() for marker in markers):
                    if sections[current_section]:
                        sections[current_section] += '\n' + line
                    else:
                        sections[current_section] = line
            
            return sections
            
        except Exception as e:
            print(f"⚠️ 섹션 파싱 실패: {e}")
            return {'other': analysis_result}

    def generate_simple_pdf(self, user_input: str, analysis_result: str) -> io.BytesIO:
        """간소화된 PDF 생성"""
        buffer = io.BytesIO()
        
        try:
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            
            # 제목 (영문)
            story.append(Paragraph("Traffic Accident Analysis Report", getSampleStyleSheet()['Title']))
            story.append(Spacer(1, 20))
            
            # 기본 정보 (영문)
            story.append(Paragraph("Analysis Date: " + datetime.now().strftime('%Y-%m-%d %H:%M'), getSampleStyleSheet()['Normal']))
            story.append(Paragraph("Report Type: Detailed Analysis", getSampleStyleSheet()['Normal']))
            story.append(Spacer(1, 20))
            
            # 사용자 입력 (한글 처리)
            story.append(Paragraph("Accident Description", getSampleStyleSheet()['Heading2']))
            
            clean_input = self.clean_korean_text(user_input)
            if self.korean_font == 'Korean':
                # 한글 폰트 사용 가능
                korean_style = ParagraphStyle(
                    'Korean',
                    parent=getSampleStyleSheet()['Normal'],
                    fontName=self.korean_font,
                    fontSize=10
                )
                korean_heading_style = ParagraphStyle(
                    'KoreanHeading',
                    parent=getSampleStyleSheet()['Heading3'],
                    fontName=self.korean_font,
                    fontSize=12
                )
                story.append(Paragraph(clean_input, korean_style))
            else:
                # 영문으로 설명 추가
                story.append(Paragraph("[Korean text - please view original for details]", getSampleStyleSheet()['Normal']))
                story.append(Paragraph(f"Original: {clean_input[:200]}...", getSampleStyleSheet()['Normal']))
            
            story.append(Spacer(1, 20))
            
            # 분석 결과를 섹션별로 처리
            clean_analysis = self.clean_korean_text(analysis_result)
            sections = self.parse_analysis_sections(clean_analysis)
            
            if self.korean_font == 'Korean':
                # 1. 법률적 분석
                if sections['legal_analysis']:
                    story.append(Paragraph("Legal Analysis / 법률적 분석", getSampleStyleSheet()['Heading2']))
                    story.append(Paragraph(sections['legal_analysis'][:800], korean_style))
                    story.append(Spacer(1, 15))
                
                # 2. 과실비율 분석
                if sections['fault_ratio']:
                    story.append(Paragraph("Fault Ratio Analysis / 과실비율 분석", getSampleStyleSheet()['Heading2']))
                    story.append(Paragraph(sections['fault_ratio'][:800], korean_style))
                    story.append(Spacer(1, 15))
                
                # 3. 대응전략
                if sections['response_strategy']:
                    story.append(Paragraph("Response Strategy / 대응전략", getSampleStyleSheet()['Heading2']))
                    story.append(Paragraph(sections['response_strategy'][:800], korean_style))
                    story.append(Spacer(1, 15))
                
                # 4. 추가 고려사항
                if sections['additional_considerations']:
                    story.append(Paragraph("Additional Considerations / 추가 고려사항", getSampleStyleSheet()['Heading2']))
                    story.append(Paragraph(sections['additional_considerations'][:800], korean_style))
                    story.append(Spacer(1, 15))
                
                # 5. 기타 내용
                if sections['other']:
                    story.append(Paragraph("Additional Information / 기타 정보", getSampleStyleSheet()['Heading2']))
                    story.append(Paragraph(sections['other'][:800], korean_style))
                    story.append(Spacer(1, 15))
                
            else:
                story.append(Paragraph("Analysis Results", getSampleStyleSheet()['Heading2']))
                story.append(Paragraph("[Korean analysis results - please view original for details]", getSampleStyleSheet()['Normal']))
                story.append(Paragraph(f"Original length: {len(clean_analysis)} characters", getSampleStyleSheet()['Normal']))
            
            # 면책 조항 (영문)
            story.append(Spacer(1, 30))
            story.append(Paragraph("Disclaimer", getSampleStyleSheet()['Heading2']))
            disclaimer = "This AI analysis is for reference only. For accurate legal advice, please consult with a professional lawyer."
            story.append(Paragraph(disclaimer, getSampleStyleSheet()['Normal']))
            
            # PDF 생성
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            print(f"❌ PDF 생성 실패: {e}")
            # 에러 발생 시 기본 PDF 생성
            return self.generate_error_pdf(str(e))
    
    def generate_error_pdf(self, error_msg: str) -> io.BytesIO:
        """에러 발생시 기본 PDF 생성"""
        buffer = io.BytesIO()
        
        try:
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            story.append(Paragraph("PDF Generation Error", getSampleStyleSheet()['Title']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Error: {error_msg}", getSampleStyleSheet()['Normal']))
            story.append(Spacer(1, 20))
            story.append(Paragraph("Please try again or contact support.", getSampleStyleSheet()['Normal']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            print(f"❌ 에러 PDF 생성도 실패: {e}")
            # 최후의 수단: 빈 버퍼
            return io.BytesIO(b"PDF generation failed")

def create_simple_pdf_download_button(user_input: str, analysis_result: str, case_info: list = None):
    """간소화된 PDF 다운로드 버튼"""
    try:
        generator = SimpleKoreanPDFGenerator()
        pdf_buffer = generator.generate_simple_pdf(user_input, analysis_result)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"traffic_analysis_{timestamp}.pdf"
        
        st.download_button(
            label="📄 PDF 리포트 다운로드 (간소화 버전)",
            data=pdf_buffer.getvalue(),
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
        
        st.info("💡 한글이 깨져 보이는 경우, 시스템에 한글 폰트가 없을 수 있습니다. 영문 버전으로 제공됩니다.")
        
        return True
        
    except Exception as e:
        st.error(f"❌ PDF 생성 실패: {e}")
        return False

# 기존 함수와의 호환성을 위한 wrapper
def create_pdf_download_button(user_input: str, analysis_result: str, case_info: list = None):
    """기존 함수와 호환되는 wrapper"""
    return create_simple_pdf_download_button(user_input, analysis_result)

if __name__ == "__main__":
    # 테스트
    generator = SimpleKoreanPDFGenerator()
    test_input = "신호등 교차로에서 직진 중 좌회전 차량과 충돌했습니다."
    test_result = "과실비율: 좌회전차량 80-90%, 직진차량 10-20%"
    
    pdf = generator.generate_simple_pdf(test_input, test_result)
    print("✅ 간소화 PDF 생성 테스트 완료")