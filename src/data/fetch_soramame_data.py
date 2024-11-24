import os
import yaml
import requests
from datetime import datetime, timedelta

from tqdm import tqdm
import pandas as pd



def load_config():
    """YAMLファイルから設定を読み込む"""
    config_path = os.path.join(os.path.dirname(__file__), 'fetch_soramame_data.yml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def fetch_station_data(prefecture_code, station_code, start_ym, end_ym):
    """指定された測定局の指定期間のデータを取得する"""
    query = f'https://soramame.env.go.jp/soramame/api/data_search?Start_YM={start_ym}&End_YM={end_ym}&TDFKN_CD={prefecture_code}&SKT_CD={station_code}&REQUEST_DATA=SO2,NO,NO2,NOX,CO,OX,NMHC,CH4,THC,SPM,PM2_5,SP,WD,WS,TEMP,HUM'
    response = requests.get(query)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data for station {prefecture_code}: {response.status_code}")
        return None

def main():
    config = load_config()
    
    # 保存先ディレクトリの設定
    save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')
    os.makedirs(save_dir, exist_ok=True)

    all_data = []

    # tqdmを使用してプログレスバーを表示
    for skt_cd in tqdm(config['station_code'], desc="Fetching data"):
        data = fetch_station_data(
            prefecture_code = config['prefecture_code'], 
            station_code = skt_cd, 
            start_ym = config['start_ym'], 
            end_ym = config['end_ym']
        )
        if data:
            all_data.extend(data)

    # データをDataFrameに変換
    df = pd.DataFrame(all_data)

    # 現在の日時を取得してファイル名に使用
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    get_pf = config['prefecture_code']
    filename = f'{get_pf}_{current_time}.csv'
    
    # CSVファイルとして保存
    file_path = os.path.join(save_dir, filename)
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")

if __name__ == "__main__":
    main()