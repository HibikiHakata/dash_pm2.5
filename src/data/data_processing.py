import os
import glob

import numpy as np
import pandas as pd

def process_data():
    # rawディレクトリのパスを設定
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')
    
    # CSVファイルのリストを取得
    csv_files = glob.glob(os.path.join(raw_dir, '*.csv'))
    
    # データフレームのリストを初期化
    dfs = []
    
    # 各CSVファイルを読み込み、リストに追加
    for file in csv_files:
        df = pd.read_csv(file, parse_dates=['SKT_DATE'])
        dfs.append(df)
    
    # すべてのデータフレームを縦に結合
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # SKT_TIMEを文字列に変換し、必要に応じてゼロパディングを行う
    combined_df['SKT_TIME'] = combined_df['SKT_TIME'].astype(str).str.zfill(2)
    
    # SKT_TIMEを適切な時刻形式に変換（HH:MM）
    combined_df['SKT_TIME'] = combined_df['SKT_TIME'].apply(lambda x: f"{x[:2]}:00")

    # 24:00を00:00に変換し、日付を1日進める
    mask = combined_df['SKT_TIME'] == '24:00'
    combined_df.loc[mask, 'SKT_TIME'] = '00:00'
    combined_df.loc[mask, 'SKT_DATE'] += pd.Timedelta(days=1)

    # SKT_DATEとSKT_TIMEを組み合わせて新しい日時列を作成
    combined_df['DATETIME'] = pd.to_datetime(combined_df['SKT_DATE'].dt.strftime('%Y-%m-%d') + ' ' + combined_df['SKT_TIME'])

    # 重複する日時のデータを削除（最新のデータを保持）
    combined_df = combined_df.sort_values('DATETIME').drop_duplicates(subset='DATETIME', keep='last')
    
    # 日時でソート
    combined_df = combined_df.sort_values('DATETIME')
    
    # DATETIME列を行の先頭に移動(系列識別子)し、SKT_CDをdrop、targetカラムのPM2_5を一番右端へ
    combined_df = combined_df.reindex(
        columns=[
            'DATETIME', 'SKT_DATE', 'SKT_TIME', 'SO2',
            'NO', 'NO2', 'NOX', 'CO', 'OX', 'NMHC', 
            'CH4', 'THC', 'SPM', 'SP', 'WD', 'WS', 'TEMP',
            'HUM', 'PM2_5'
        ]
    )    
    return combined_df

def main():
    processed_data = process_data()
    
    # 処理済みデータの保存先ディレクトリを設定
    processed_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # 処理済みデータをCSVファイルとして保存
    output_file = os.path.join(processed_dir, 'processed_environmental_data.csv')
    processed_data.to_csv(output_file, index=False)
    
    print(f"Processed data saved to: {output_file}")
    print(f"Shape of processed data: {processed_data.shape}")

if __name__ == "__main__":
    main()