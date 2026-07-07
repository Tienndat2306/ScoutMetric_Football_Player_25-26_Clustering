from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def get_team_ids_from_leagues(league_urls):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_teams = [] # Danh sách lưu kết quả: {League, Team Name, Team ID}

    # Loại bỏ ID của các quốc gia
    excluded_ids = {'6720', '8204', '8570', '6723', '8491', '6708', '8361', '6595', '8498'} 

    for league_name, url in league_urls.items():
        print(f"Đang quét giải đấu: {league_name}...")
        driver.get(url)
        time.sleep(3) # Đợi bảng xếp hạng load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Tìm các link chứa "/teams/"
        # FotMob thường để link trong bảng xếp hạng
        team_links = soup.find_all('a', href=re.compile(r'/teams/\d+/'))

        league_team_ids = set() # Tránh lấy trùng 
        for link in team_links:
            href = link.get('href')
            match = re.search(r'/teams/(\d+)/overview/([\w-]+)', href)
            if match:
                team_id = match.group(1)
                if team_id in excluded_ids:
                    continue
                team_name = match.group(2).replace('-', ' ').title()
                if team_id not in league_team_ids:
                    league_team_ids.add(team_id)
                    all_teams.append({
                        "League": league_name,
                        "Team Name": team_name,
                        "Team ID": team_id,
                        "URL": f"https://www.fotmob.com{href}"
                    })
        print(f"-> Tìm thấy {len(league_team_ids)} đội tại {league_name}.")

    driver.quit()
    return all_teams