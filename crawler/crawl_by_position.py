import pandas as pd
import os
import time
import glob
from get_stats import get_player_stats_per90

POSITION_SCHEMAS = {
    'goalkeeper': [
        'id', 'Name', 'Minutes played', 'Primary Position', 'Team', 'League',
        'Saves', 'Save percentage', 'Goals conceded', 'Goals prevented', 'Clean sheets',
        'Penalty saves', 'Penalty goals conceded', 'Penalty save %', 
        'Error led to goal', 'Acted as sweeper', 'High claim',
        'Successful passes', 'Successful passes %',
        'Accurate long balls', 'Accurate long balls %',
        'Chances created', 'Expected assists (xA)'
    ],
    'defender': [
        'id', 'Name', 'Minutes played', 'Primary Position', 'Team', 'League',
        'Goals', 'Expected goals (xG)', 'xG on target (xGOT)', 'Non-penalty xG', 'Shots', 'Shots on target', 'Headed shots',
        'Assists', 'Expected assists (xA)', 'Successful passes', 'Successful passes %', 'Accurate long balls', 'Accurate long balls %',
        'Chances created', 'Big chances created', 'Successful crosses', 'Successful crosses %',
        'Successful dribbles', 'Successful dribbles %', 'Duels won', 'Duels won %', 'Aerial duels won', 'Aerial duels won %',
        'Touches', 'Touches in opposition box', 'Dispossessed', 'Fouls won',
        'Defensive contributions', 'Tackles', 'Interceptions', 'Blocked shots', 'Fouls committed', 'Penalties conceded', 'Recoveries',
        'Possession won final 3rd', 'Dribbled past', 'Clearances', 'Clean sheets', 'Goals conceded while on pitch', 'xG against while on pitch',
        'Yellow cards', 'Red cards'
    ],
    'fullback': [
        'id', 'Name', 'Minutes played', 'Primary Position', 'Team', 'League',
        'Goals', 'Expected goals (xG)', 'xG on target (xGOT)', 'Non-penalty xG', 'Shots', 'Shots on target', 'Headed shots',
        'Assists', 'Expected assists (xA)', 'Successful passes', 'Successful passes %', 'Accurate long balls', 'Accurate long balls %',
        'Chances created', 'Big chances created', 'Successful crosses', 'Successful crosses %',
        'Successful dribbles', 'Successful dribbles %', 'Duels won', 'Duels won %', 'Aerial duels won', 'Aerial duels won %',
        'Touches', 'Touches in opposition box', 'Dispossessed', 'Fouls won',
        'Defensive contributions', 'Tackles', 'Interceptions', 'Blocked shots', 'Fouls committed', 'Penalties conceded', 'Recoveries',
        'Possession won final 3rd', 'Dribbled past', 'Clearances', 'Clean sheets', 'Goals conceded while on pitch', 'xG against while on pitch',
        'Yellow cards', 'Red cards'
    ],
    'midfielder': [
        'id', 'Name', 'Minutes played', 'Primary Position', 'Team', 'League',
        'Goals', 'Expected goals (xG)', 'xG on target (xGOT)', 'Penalty goals', 'Non-penalty xG', 'Shots', 'Shots on target', 'Headed shots',
        'Assists', 'Expected assists (xA)', 'Successful passes', 'Successful passes %', 'Accurate long balls', 'Accurate long balls %',
        'Chances created', 'Big chances created', 'Successful crosses', 'Successful crosses %',
        'Successful dribbles', 'Successful dribbles %', 'Duels won', 'Duels won %', 'Aerial duels won', 'Aerial duels won %',
        'Touches', 'Touches in opposition box', 'Dispossessed', 'Fouls won',
        'Defensive contributions', 'Tackles', 'Interceptions', 'Blocked shots', 'Fouls committed', 'Penalties conceded', 'Recoveries',
        'Possession won final 3rd', 'Dribbled past', 'Clearances', 'Clean sheets', 'Goals conceded while on pitch', 'xG against while on pitch',
        'Yellow cards', 'Red cards'
    ],
    'winger': [
        'id', 'Name', 'Minutes played', 'Primary Position', 'Team', 'League',
        'Goals', 'Expected goals (xG)', 'xG on target (xGOT)', 'Penalty goals', 'Non-penalty xG', 'Shots', 'Shots on target', 'Headed shots',
        'Assists', 'Expected assists (xA)', 'Successful passes', 'Successful passes %', 'Accurate long balls', 'Accurate long balls %',
        'Chances created', 'Big chances created', 'Successful crosses', 'Successful crosses %',
        'Successful dribbles', 'Successful dribbles %', 'Duels won', 'Duels won %', 'Aerial duels won', 'Aerial duels won %',
        'Touches', 'Touches in opposition box', 'Dispossessed', 'Fouls won',
        'Defensive contributions', 'Tackles', 'Interceptions', 'Blocked shots', 'Fouls committed', 'Penalties conceded', 'Recoveries',
        'Possession won final 3rd', 'Dribbled past', 'Clearances', 'Goals conceded while on pitch', 'xG against while on pitch',
        'Yellow cards', 'Red cards'
    ],
    'striker': [
        'id', 'Name', 'Minutes played', 'Primary Position', 'Team', 'League',
        'Goals', 'Expected goals (xG)', 'xG on target (xGOT)', 'Penalty goals', 'Non-penalty xG', 'Shots', 'Shots on target', 'Headed shots',
        'Assists', 'Expected assists (xA)', 'Successful passes', 'Successful passes %', 'Accurate long balls', 'Accurate long balls %',
        'Chances created', 'Big chances created', 'Successful crosses', 'Successful crosses %',
        'Successful dribbles', 'Successful dribbles %', 'Duels won', 'Duels won %', 'Aerial duels won', 'Aerial duels won %',
        'Touches', 'Touches in opposition box', 'Dispossessed', 'Fouls won',
        'Defensive contributions', 'Tackles', 'Interceptions', 'Blocked shots', 'Fouls committed', 'Penalties conceded', 'Recoveries',
        'Possession won final 3rd', 'Dribbled past', 'Clearances', 'Goals conceded while on pitch', 'xG against while on pitch',
        'Yellow cards', 'Red cards'
    ]
}

def crawl_and_save_by_position(target_league):
    base_dir = "data"
    stats_output_dir = os.path.join(base_dir, "player_stats")
    
    if not os.path.exists(stats_output_dir):
        os.makedirs(stats_output_dir)

    # 1. Cấu trúc lại map để khớp với tên đầy đủ trên FotMob
    position_map = {
        'Keeper': 'goalkeeper', 'keeper': 'goalkeeper',
        'Center-back': 'defender', 'Centre-back': 'defender',
        'center-back': 'defender', 'centre-back': 'defender',
        'Right-back': 'fullback', 'Left-back': 'fullback', 'right-back': 'fullback', 'left-back': 'fullback',
        'Right Wing Back': 'fullback', 'Left Wing Back': 'fullback', 'right wing back': 'fullback', 'left wing back': 'fullback',
        'Attacking Midfielder': 'midfielder', 'Defensive Midfielder': 'midfielder', 'Central Midfielder': 'midfielder',
        'attacking midfielder': 'midfielder', 'defensive midfielder': 'midfielder', 'central midfielder': 'midfielder',
        'Left Winger': 'winger', 'Right Winger': 'winger', 'left winger': 'winger', 'right winger': 'winger',
        'Left Midfielder': 'winger', 'Right Midfielder': 'winger', 'left midfielder': 'winger', 'right midfielder': 'winger',
        'Striker': 'striker', 'striker': 'striker'
    }

    # 2. Checkpoint thông minh: Quét tất cả ID đã cào một lần duy nhất
    crawled_ids = set()
    for existing_file in glob.glob(os.path.join(stats_output_dir, "*.csv")):
        try:
            temp_df = pd.read_csv(existing_file, usecols=['id'])
            crawled_ids.update(temp_df['id'].astype(str).tolist())
        except: continue

    search_path = os.path.join(base_dir, target_league, "*_player_ids.csv")
    player_id_files = glob.glob(search_path)
    
    if not player_id_files:
        print(f"[!] Không tìm thấy dữ liệu cho giải đấu: {target_league}")
        return

    print(f"--- BẮT ĐẦU CÀO GIẢI ĐẤU: {target_league.upper()} ---")

    for file_path in player_id_files:
        league_name = target_league.replace("_", " ").title()
        team_name = os.path.basename(file_path).replace("_player_ids.csv", "").replace("-", " ").title()
        
        df_ids = pd.read_csv(file_path)
        print(f"\n>> Đội bóng: {team_name}")

        for _, row in df_ids.iterrows():
            p_id = str(row['player_id'])
            p_name = str(row['Name'])
            
            if p_id in crawled_ids:
                print(f"   [Skip] ID {p_id} đã tồn tại.")
                continue

            print(f"   [Crawl] ID {p_id} - {p_name}...", end=" ", flush=True)
            stats = get_player_stats_per90(p_id)
            
            if stats:
                full_pos = stats.get('All Positions', 'N/A')
                
                if 'All Positions' in stats:
                    del stats['All Positions']
                
                group = position_map.get(full_pos)
                
                if not group:
                    print(f"Bỏ qua (Vị trí '{full_pos}' không nằm trong nhóm cần lấy)")
                    continue

                stats['Primary Position'] = full_pos
                stats['Team'] = team_name
                stats['League'] = league_name
                
                df_single = pd.DataFrame([stats])
                
                schema_cols = POSITION_SCHEMAS.get(group)
                
                if schema_cols:
                    # reindex sẽ:
                    # - Giữ lại các cột có trong schema_cols
                    # - Thêm cột thiếu và điền giá trị NaN (tự động)
                    # - Loại bỏ các cột thừa (ví dụ 'All Positions' cũ)
                    df_single = df_single.reindex(columns=schema_cols)
                    df_single = df_single.fillna(0.0)
                
                save_path = os.path.join(stats_output_dir, f"{group}_stats.csv")
                file_exists = os.path.isfile(save_path)
                
                df_single.to_csv(save_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
                
                crawled_ids.add(p_id) 
                print(f"Thành công -> {group}_stats.csv")
                time.sleep(1)
            else:
                print("Lỗi/Không có dữ liệu.")

    print(f"\n--- HOÀN THÀNH GIẢI ĐẤU ---")

if __name__ == "__main__":
    # Chạy từng giải một bằng cách thay đổi tham số ở đây
    # Ví dụ: "premier_league", "la_liga", "bundesliga", "serie_a", "ligue_1"
    
        current_league = "eredivisie"  # Thay đổi giải đấu ở đây
        crawl_and_save_by_position(current_league)