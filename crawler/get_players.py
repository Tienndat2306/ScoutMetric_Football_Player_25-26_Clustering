from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

def get_player_ids_from_team(team_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    # Thêm User-Agent để tránh bị FotMob chặn
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Đảm bảo URL dẫn đến tab Squad
    if "/squad/" not in team_url:
        # Chuyển đổi linh hoạt từ các dạng link khác sang link squad
        team_url = team_url.replace("/overview/", "/squad/")
    
    print(f"Đang quét danh sách cầu thủ từ: {team_url}")
    
    player_data = [] # Lưu danh sách dictionary: {'id': ..., 'position': ...}
    
    try:
        driver.get(team_url)
        # Đợi bảng dữ liệu xuất hiện
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Tìm tất cả các dòng trong bảng (tr)
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            # Một dòng chuẩn trong Squad thường có ít nhất 2 cột: Tên và Vị trí
            if len(cells) >= 2:
                # 1. Lấy Position (thường ở cột thứ 2 - index 1)
                position = cells[1].get_text(strip=True)
                
                # BỎ QUA nếu là Huấn luyện viên
                if position.lower() == "coach":
                    continue
                
                # 2. Tìm ID cầu thủ trong cột đầu tiên (index 0)
                link_tag = cells[0].find('a', href=re.compile(r'/players/(\d+)/'))
                name_span = link_tag.find('span', class_=lambda x: x and 'PlayerName' in x) # Hoặc class tương ứng
                if name_span:
                    name = name_span.get_text(strip=True)
                else:
                    # Nếu không thấy thẻ span riêng, lấy phần text đầu tiên (thường là tên)
                    name = list(link_tag.stripped_strings)[0]
                if link_tag:
                    href = link_tag.get('href')
                    match = re.search(r'/players/(\d+)/', href)
                    if match:
                        player_id = match.group(1)
                        
                        player_data.append({
                            "player_id": player_id,
                            "Name": name,
                            "Position": position
                        })

    except Exception as e:
        print(f"Lỗi khi lấy danh sách cầu thủ: {e}")
    finally:
        driver.quit()

    # Loại bỏ trùng lặp ID 
    seen_ids = set()
    unique_players = []
    for p in player_data:
        if p['player_id'] not in seen_ids:
            unique_players.append(p)
            seen_ids.add(p['player_id'])

    return unique_players