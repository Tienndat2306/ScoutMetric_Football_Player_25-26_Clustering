from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def get_player_stats_per90(player_id):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = f"https://www.fotmob.com/players/{player_id}/"

    VALID_LEAGUES = [
        "Premier League", 
        "LaLiga", 
        "Bundesliga", 
        "Serie A", 
        "Ligue 1",
        "Liga Portugal",
        "Eredivisie",
        "Super Lig",
        "Championship"
    ]
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # 1. Tự lấy tên giải đấu đang hiển thị (Phân vùng Season Performance)
        try:
            # Tìm vùng Season Performance trước để không bị lẫn với Match Stats
            # Chúng ta dựa vào class 'SeasonPerformance' để làm mốc
            performance_section = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "css-1b8ajmb-PlayerDetailedStatsCSS")))
            
            # Chỉ tìm thẻ select bên trong vùng này
            league_select = performance_section.find_element(By.CSS_SELECTOR, 'select[aria-label*="Selected:"]')
            
            aria_label = league_select.get_attribute("aria-label")
            current_league = aria_label.replace("Selected: ", "").strip()
            
            # print(f"DEBUG: Giải đấu tìm thấy trong Season Performance: '{current_league}'") 

            if current_league not in VALID_LEAGUES:
                print(f"Bỏ qua: {current_league} (Không thuộc Top 5)")
                return None
        except Exception as e:
            print(f"Không thể xác định giải đấu trong phần Season Performance cho ID {player_id}")
            return None
        
        # 2. Click chuyển sang chế độ Per 90
        per90_xpath = "//button[contains(., 'Per 90')]"
        per90_button = wait.until(EC.element_to_be_clickable((By.XPATH, per90_xpath)))
        driver.execute_script("arguments[0].click();", per90_button)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        player_stats = {"id": player_id}
        
        # 3. Lấy Tên cầu thủ
        name_tag = soup.find('h1')
        player_stats['Name'] = name_tag.text.strip() if name_tag else "N/A"

        # 4. Lấy Vị trí đầy đủ (Ví dụ: "Left-back" từ image_993294.png)
        pos_tag = soup.find('div', class_=lambda x: x and 'PositionsCSS' in x)
        player_stats['All Positions'] = pos_tag.text.strip() if pos_tag else "N/A"
        
        # 5. Xử lý Minutes Played từ Subtitle (Cho cầu thủ thường)
        player_stats['Minutes played'] = 0
        found_minutes = False
        subtitle_div = soup.find('div', class_=lambda x: x and 'SeasonPerformanceSubtitle' in x)
        if subtitle_div:
            spans = subtitle_div.find_all('span')
            for s in spans:
                text = s.text.strip().replace(',', '')
                if text.isdigit():
                    player_stats['Minutes played'] = int(text)
                    found_minutes = True
                    break

        # 6. Lấy tất cả chỉ số từ các ô (StatBox cho GK và StatItem cho cầu thủ thường)
        # Sử dụng CSS Selector để tìm cả hai loại class
        all_stats = soup.select('div[class*="StatBox"], div[class*="StatItemCSS"]')
        
        for item in all_stats:
            title_tag = item.find('span', class_=lambda x: x and 'StatTitle' in x)
            value_tag = item.find('div', class_=lambda x: x and 'StatValue' in x)
            
            if title_tag and value_tag:
                title = title_tag.text.strip()
                value = value_tag.text.strip()
                
                # Nếu chưa tìm thấy phút ở Subtitle, lấy ở đây (Thủ môn - image_308dfd.png)
                if not found_minutes and title.lower() == "minutes played":
                    raw_min = value.replace(',', '')
                    if raw_min.isdigit():
                        player_stats['Minutes played'] = int(raw_min)
                        found_minutes = True
                
                # Lưu các chỉ số khác vào dict
                if title != "Minutes played":
                    player_stats[title] = value

        return player_stats

    except Exception as e:
        print(f"Lỗi khi lấy chỉ số cầu thủ {player_id}: {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    # Ví dụ: Lấy chỉ số Per 90 cho Bruno Fernandes (ID 422685)
    test_player_id = "422685"
    print(f"Đang lấy chỉ số Per 90 cho ID: {test_player_id}...")
    stats = get_player_stats_per90(test_player_id)
    
    if stats:
        print("\n--- Chỉ số Per 90 của cầu thủ ---")
        for key, value in stats.items():
            print(f"{key}: {value}")
    else:
        print("Không thể lấy chỉ số cầu thủ.")