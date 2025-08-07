import requests
from bs4 import BeautifulSoup
import json
import time
import urllib3
import os
from loguru import logger
from pathlib import Path

class AccidentCrawler:
    def __init__(self, output_dir="./data/cases"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://accident.knia.or.kr/myaccident-content"
        
        # SSL 인증서 경고 무시
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 로깅 설정
        logger.add("./logs/crawler.log", rotation="10 MB")
    
    def crawl_accident_data(self, max_pages=62, delay=1):
        """교통사고 판례 데이터 크롤링"""
        accident_data = []
        total_cases = 0
        
        logger.info(f"크롤링 시작: 최대 {max_pages}페이지")
        
        for page_number in range(1, max_pages + 1):
            sub_page_number = 1
            page_cases = 0
            
            while True:
                try:
                    # URL 생성
                    params = {
                        'chartNo': f'차{page_number}-{sub_page_number}',
                        'chartType': '1'
                    }
                    
                    # 페이지 요청
                    response = requests.get(
                        self.base_url, 
                        params=params,
                        verify=False,
                        timeout=10
                    )
                    
                    logger.debug(f"요청 URL: {response.url}")
                    
                    # 페이지가 존재하지 않으면 종료
                    if "요청하신 페이지를 찾을 수 없습니다" in response.text:
                        logger.debug(f"페이지 {page_number} 완료 (총 {page_cases}건)")
                        break
                    
                    # 데이터 추출
                    case_data = self._extract_case_data(response.text, page_number, sub_page_number)
                    
                    if case_data:
                        accident_data.append(case_data)
                        page_cases += 1
                        total_cases += 1
                        logger.info(f"추출 완료: 차{page_number}-{sub_page_number}")
                    
                    sub_page_number += 1
                    time.sleep(delay)  # 서버 부하 방지
                    
                except requests.RequestException as e:
                    logger.error(f"요청 실패 차{page_number}-{sub_page_number}: {e}")
                    break
                except Exception as e:
                    logger.error(f"처리 오류 차{page_number}-{sub_page_number}: {e}")
                    sub_page_number += 1
                    continue
            
            logger.info(f"페이지 {page_number}/{max_pages} 완료 (현재까지 총 {total_cases}건)")
        
        # 데이터 저장
        output_file = self.output_dir / "accident_cases.json"
        self._save_data(accident_data, output_file)
        
        logger.info(f"크롤링 완료! 총 {total_cases}건 수집, {output_file}에 저장")
        return accident_data
    
    def _extract_case_data(self, html_content, page_num, sub_page_num):
        """HTML에서 사고 데이터 추출"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 각 요소 추출
            car_A = soup.select_one(".cont_l .con")
            car_B = soup.select_one(".cont_r .con")
            accident_description = soup.select_one("#smrizeexplna")
            fault_A = soup.select_one("td .red")
            fault_B = soup.select_one("td .orange")
            
            # 모든 요소가 있는지 확인
            if not all([car_A, car_B, accident_description, fault_A, fault_B]):
                logger.warning(f"차{page_num}-{sub_page_num}: 일부 데이터 누락")
                return None
            
            # 텍스트 정리
            description_text = self._clean_text(accident_description.text)
            
            return {
                "case_id": f"차{page_num}-{sub_page_num}",
                "vehicle_A_situation": car_A.text.strip(),
                "vehicle_B_situation": car_B.text.strip(),
                "accident_description": description_text,
                "fault_ratio": f"{fault_A.text.strip()} : {fault_B.text.strip()}",
                "page_number": page_num,
                "sub_page_number": sub_page_num,
                "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"데이터 추출 오류 차{page_num}-{sub_page_num}: {e}")
            return None
    
    def _clean_text(self, text):
        """텍스트 정리"""
        if not text:
            return ""
        
        # 줄바꿈 문자 제거 및 특수 문자 정리
        cleaned = text.strip()
        cleaned = cleaned.replace("\r\n", " ").replace("\n", " ")
        cleaned = cleaned.replace("⊙ ", "")
        
        # 연속된 공백 제거
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _save_data(self, data, output_file):
        """데이터를 JSON 파일로 저장"""
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"데이터 저장 완료: {output_file}")
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")
            raise

def main():
    """메인 실행 함수"""
    crawler = AccidentCrawler()
    
    # 크롤링 실행 (테스트용으로 5페이지만)
    print("🕷️ 교통사고 판례 크롤링을 시작합니다...")
    print("⚠️ 전체 데이터 수집에는 시간이 오래 걸릴 수 있습니다.")
    
    # 사용자 확인
    response = input("계속 진행하시겠습니까? (y/n): ")
    if response.lower() != 'y':
        print("크롤링을 중단합니다.")
        return
    
    # 페이지 수 설정
    try:
        max_pages = int(input("크롤링할 최대 페이지 수 (기본값: 5, 전체: 62): ") or "5")
    except ValueError:
        max_pages = 5
    
    accident_data = crawler.crawl_accident_data(max_pages=max_pages)
    print(f"✅ 크롤링 완료! 총 {len(accident_data)}건의 사고 판례를 수집했습니다.")

if __name__ == "__main__":
    main()