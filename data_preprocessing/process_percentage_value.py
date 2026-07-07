import pandas as pd
import os
import glob

def process_percentage_columns(folder_path):
    # Danh sách các cột bạn muốn chuyển đổi
    target_cols = [
        "Successful passes %", "Accurate long balls %", "Successful crosses %",
        "Successful dribbles %", "Duels won %", "Save percentage", 
        "Penalty save %", "Aerial duels won %"
    ]
    
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    
    for file_path in csv_files:
        df = pd.read_csv(file_path)
        modified = False
        
        for col in target_cols:
            if col in df.columns:
                
                df[col] = df[col].astype(str).str.replace('%', '', regex=False)
                
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                
                df[col] = df[col].apply(lambda x: x / 100 if x > 1 else x)
                
                df[col] = df[col].round(2).fillna(0.00)
                
                modified = True
        
        if modified:
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            print(f"✅ Đã chuẩn hóa các cột % trong file: {os.path.basename(file_path)}")

# Sử dụng sau khi bạn đã làm sạch giải đấu (positions_stats_clean)
if __name__ == "__main__":
    path_data = "data/player_stats"
    process_percentage_columns(path_data)