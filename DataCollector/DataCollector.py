'''
import requests
from bs4 import BeautifulSoup

url = "https://www.warcraftlogs.com/reports/HDhTjCg126XJbLxA"
#url = "https://www.naver.com/"

response = requests.get(url)

if response.status_code == 200:
    # HTML 소스 코드 파싱
    soup = BeautifulSoup(response.text, 'html.parser')

    # 'report-overview-boss-box' 클래스를 가진 div 요소 찾기
    boss_boxes = soup.find_all('div', class_='report-overview-boss-box')

    # 찾은 boss box의 내용을 출력
    for box in boss_boxes:
        link = box.find('a')  # box 내부의 첫 번째 <a> 태그 찾기
        if link:
            href = link.get('href')  # href 속성 값 추출
            print(f"링크: {href}")

else:
    print(f"페이지 요청 실패: {response.status_code}")
'''
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# webdriver-manager로 크롬 드라이버를 자동으로 다운로드하고 설정
chrome_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_options = Options()
chrome_options.binary_location = chrome_path
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = chrome_options)

# 원하는 웹 페이지 열기
driver.get("https://www.warcraftlogs.com/reports/HDhTjCg126XJbLxA")

# 페이지 타이틀 출력
print(driver.title)

# 브라우저 닫기
driver.quit()

