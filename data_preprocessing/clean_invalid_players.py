import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import glob

# 1. Hàm kiểm tra giải đấu thực tế (Giữ nguyên logic xác thực)
def verify_league(player_id, driver):
    url = f"https://www.fotmob.com/players/{player_id}/"
    VALID_LEAGUES = ["Premier League", "LaLiga", "Bundesliga", "Serie A", "Ligue 1"]
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        # Nhắm vào phân vùng Season Performance để lấy giải thực
        performance_section = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "css-1b8ajmb-PlayerDetailedStatsCSS")))
        league_select = performance_section.find_element(By.CSS_SELECTOR, 'select[aria-label*="Selected:"]')
        
        aria_label = league_select.get_attribute("aria-label")
        current_league = aria_label.replace("Selected: ", "").strip()
        
        return (current_league in VALID_LEAGUES), current_league
    except:
        return False, "Error/Not Found"

# 2. Hàm xử lý quét toàn bộ thư mục và lưu sang thư mục mới
def clean_invalid_players():
    # Cấu hình đường dẫn
    input_folder = "data/player_stats"
    output_folder = "data/player_stats_clean"
    
    # Tạo thư mục mới nếu chưa tồn tại
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"--- Đã tạo thư mục mới: {output_folder} ---")

    # Khởi tạo Selenium dùng chung
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Lấy danh sách tất cả file .csv trong thư mục gốc
        csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

        for file_path in csv_files:
            file_name = os.path.basename(file_path)
            print(f"\n🚀 Đang làm sạch file: {file_name}")
            
            df = pd.read_csv(file_path)
            if df.empty: continue

            keep_indices = []
            for index, row in df.iterrows():
                p_id = row['id']
                p_name = row['Name']
                
                is_valid, real_league = verify_league(p_id, driver)
                
                if is_valid:
                    print(f"  [✓] Giữ lại: {p_name} ({real_league})")
                    keep_indices.append(index)
                else:
                    print(f"  [✗] Loại bỏ: {p_name} (Thực tế: {real_league})")
            
            # Tạo DataFrame mới từ danh sách chỉ số đã lọc
            df_cleaned = df.iloc[keep_indices].copy()
            
            # Lưu vào thư mục mới với cùng tên file
            save_path = os.path.join(output_folder, file_name)
            df_cleaned.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"✅ Đã lưu file sạch vào: {save_path}")

    finally:
        driver.quit()
        print("\n--- HOÀN TẤT QUÁ TRÌNH LÀM SẠCH DỮ LIỆU ---")

if __name__ == "__main__":
    clean_invalid_players()