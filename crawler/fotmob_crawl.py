import pandas as pd
import os
import time
from get_teams import get_team_ids_from_leagues
from get_players import get_player_ids_from_team
from get_stats import get_player_stats_per90

if __name__ == "__main__":
    base_output_dir = "data"
    # 1. Định nghĩa các giải đấu
    leagues = {
        "Premier League": "https://www.fotmob.com/leagues/47/table/premier-league",
        "La Liga": "https://www.fotmob.com/leagues/87/table/la-liga",
        "Bundesliga": "https://www.fotmob.com/leagues/54/table/bundesliga",
        "Serie A": "https://www.fotmob.com/leagues/55/table/serie-a",
        "Ligue 1": "https://www.fotmob.com/leagues/53/table/ligue-1",
        "Eredivisie": "https://www.fotmob.com/en-GB/leagues/57/table/eredivisie",
        "Liga Portugal": "https://www.fotmob.com/en-GB/leagues/61/table/liga-portugal",
        "Super Lig": "https://www.fotmob.com/en-GB/leagues/71/table/super-lig",
        "Premier": "https://www.fotmob.com/en-GB/leagues/64/table/premiership",
        "Championship": "https://www.fotmob.com/en-GB/leagues/48/table/championship"
    }

    # 2. Lấy ID các đội bóng
    teams = get_team_ids_from_leagues(leagues)
    if teams:
        df_teams = pd.DataFrame(teams)
        print("\n--- DANH SÁCH ĐỘI BÓNG ---")
        print(df_teams[['League', 'Team Name', 'Team ID']].to_string(index=False))
        df_teams.to_csv(os.path.join(base_output_dir, "all_leagues_teams.csv"), index=False, encoding='utf-8-sig')

        # 3. Duyệt danh sách đội bóng để lấy ID cầu thủ cho từng đội
        for index, row in df_teams.iterrows():
            league_name = row['League'] # Lấy tên giải đấu (vd: Premier League)
            team_name = row['Team Name']
            team_url = row['URL'].replace('/overview/', '/squad/')

            # --- BƯỚC CHỈNH SỬA CHÍNH: Tạo thư mục cho giải đấu ---
            # Chuyển "Premier League" thành "premier_league" để đặt tên thư mục
            league_dir_name = league_name.lower().replace(" ", "_")
            league_path = os.path.join(base_output_dir, league_dir_name)
            
            # Nếu thư mục giải đấu chưa có thì tạo mới
            if not os.path.exists(league_path):
                os.makedirs(league_path)
                print(f"\n--- Đã tạo thư mục cho giải: {league_name} ---")

            # --- Đặt đường dẫn file cầu thủ vào thư mục giải đấu tương ứng ---
            safe_team_name = team_name.lower().replace(" ", "-")
            filename = f"{safe_team_name}_player_ids.csv"
            player_file_path = os.path.join(league_path, filename)

            print(f"Đang lấy cầu thủ đội: {team_name} ({league_name})...")
            
            player_data_list = get_player_ids_from_team(team_url)
            
            if player_data_list:
                df_players = pd.DataFrame(player_data_list)
                df_players.to_csv(player_file_path, index=False, encoding='utf-8-sig')
                print(f"   => Đã lưu vào {league_dir_name}/{filename}")
            
            time.sleep(1)

        print("\n--- HOÀN THÀNH ---")

        # 4. Thử nghiệm lấy chỉ số 1 cầu thủ (Bruno Fernandes - ID 422685)
        # test_player_id = "422685"
        # print(f"\nĐang lấy chỉ số Per 90 cho ID: {test_player_id}...")
        # stats = get_player_stats_per90(test_player_id)
        
        # if stats:
        #     all_stats_file = os.path.join(output_dir, "players_stats.csv")
        #     df_new_player = pd.DataFrame([stats])
            
        #     # Kiểm tra xem file có tồn tại và đã có ID này chưa
        #     is_duplicate = False
        #     if os.path.exists(all_stats_file):
        #         df_existing = pd.read_csv(all_stats_file)
        #         # Kiểm tra xem ID (ví dụ 422685) đã nằm trong cột 'id' chưa
        #         if str(stats['id']) in df_existing['id'].astype(str).values:
        #             is_duplicate = True

        #     if not is_duplicate:
        #         file_exists = os.path.isfile(all_stats_file)
        #         df_new_player.to_csv(
        #             all_stats_file, 
        #             mode='a', 
        #             index=False, 
        #             header=not file_exists, 
        #             encoding='utf-8-sig'
        #         )
        #         print(f"Đã lưu mới cầu thủ: {stats['Name']}")
        #     else:
        #         print(f"Cầu thủ {stats['Name']} đã tồn tại trong file, bỏ qua ghi trùng.")
    else:
        print("Không thể lấy dữ liệu đội bóng.")