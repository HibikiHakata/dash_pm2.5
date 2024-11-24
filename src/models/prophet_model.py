# モジュールのインポート
import os
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from sklearn.impute import SimpleImputer

class PM25Predictor:
    def __init__(self):
        self.model = None
        self.numerical_features = ['SO2', 'NO', 'NO2', 'NOX', 'CO', 'OX', 'NMHC', 'CH4', 'THC', 'SPM', 'SP', 'WS', 'TEMP', 'HUM']
        self.categorical_features = ['WD']

    def load_data(self):
        # データの読み込み
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'processed', 'processed_environmental_data.csv')
        df = pd.read_csv(data_path, parse_dates=['DATETIME'])
        return df

    def preprocess_data(self, df):
        # Prophet用にデータフレームを準備
        df_prophet = df[['DATETIME', 'PM2_5'] + self.numerical_features + self.categorical_features].rename(columns={'DATETIME': 'ds', 'PM2_5': 'y'})

        # 欠損値の割合を計算
        missing_ratio = df_prophet[self.numerical_features].isnull().mean()

        # 欠損値が80%以上の特徴量を除外
        features_to_keep = missing_ratio[missing_ratio < 0.8].index.tolist()
        features_to_drop = [f for f in self.numerical_features if f not in features_to_keep]
        
        if features_to_drop:
            print(f"Dropping features with more than 80% missing values: {features_to_drop}")
            df_prophet = df_prophet.drop(columns=features_to_drop)
            self.numerical_features = [f for f in self.numerical_features if f not in features_to_drop]

        # 残りの数値特徴量の欠損値を補完
        for feature in self.numerical_features:
            if df_prophet[feature].isnull().sum() > 0:
                # 線形補間で欠損値を埋める
                df_prophet[feature] = df_prophet[feature].interpolate(method='linear').ffill().bfill()

        # カテゴリカル特徴量の欠損値を 'Unknown' で埋める
        for feature in self.categorical_features:
            df_prophet[feature] = df_prophet[feature].fillna('Unknown')

        # カテゴリカル特徴量のダミー変数化
        if self.categorical_features:
            df_prophet = pd.get_dummies(df_prophet, columns=self.categorical_features, drop_first=True)
            # ダミー変数化後のカテゴリカル特徴量の列名を更新
            self.categorical_features = [col for col in df_prophet.columns if col.startswith(tuple(self.categorical_features))]

        return df_prophet

    def train_model(self, df_prophet):
        # Prophetモデルの作成と学習
        self.model = Prophet()
        for feature in df_prophet.columns:
            if feature not in ['ds', 'y']:
                self.model.add_regressor(feature)
        
        try:
            self.model.fit(df_prophet)
        except ValueError as e:
            print(f"Error during model fitting: {e}")
            print("Checking for remaining NaN values:")
            for column in df_prophet.columns:
                nan_count = df_prophet[column].isnull().sum()
                if nan_count > 0:
                    print(f"Column '{column}' has {nan_count} NaN values.")
            raise

    def make_future_dataframe(self, df_prophet, periods=24, freq='h'):
        # 将来の予測用データフレームを作成
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        
        # 数値特徴量の最新値を使用して将来のデータフレームを埋める
        for feature in self.numerical_features:
            if feature in df_prophet.columns:
                future[feature] = df_prophet[feature].iloc[-1]

        # カテゴリカル特徴量の最新値を使用して将来のデータフレームを埋める
        for feature in self.categorical_features:
            if feature in df_prophet.columns:
                future[feature] = df_prophet[feature].iloc[-1]

        # カテゴリカル特徴量のダミー変数化
        if self.categorical_features:
            future = pd.get_dummies(future, columns=self.categorical_features, drop_first=True)

        # df_prophetにあるダミー変数のカラムを確認し、futureにない場合は0で埋める
        for col in df_prophet.columns:
            if col not in future.columns and col not in ['ds', 'y']:
                future[col] = 0

        return future

    def predict(self, future):
        # 予測の実行
        forecast = self.model.predict(future)
        return forecast

    def evaluate_model(self, df_prophet):
        # データの日数を計算
        data_days = (df_prophet['ds'].max() - df_prophet['ds'].min()).days

        # データ量に応じてパラメータを調整
        if data_days >= 730:
            initial = '730 days'
            period = '30 days'
        elif data_days >= 365:
            initial = '365 days'
            period = '15 days'
        elif data_days >= 180:
            initial = '180 days'
            period = '7 days'
        else:
            initial = f'{data_days // 2} days'
            period = '1 days'

        horizon = '24 hours'

        try:
            cv_results = cross_validation(self.model, initial=initial, period=period, horizon=horizon)
            performance = performance_metrics(cv_results)
            return performance
        except ValueError as e:
            print(f"Error during cross-validation: {e}")
            print("Skipping cross-validation due to insufficient data.")
            return None

    def save_prediction(self, forecast, periods=24):
        # 予測結果の保存先ディレクトリを設定
        predict_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'predict')
        os.makedirs(predict_dir, exist_ok=True)

        # 現在の日時を取得してファイル名に使用
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'prediction_{current_time}.csv'
        
        # 直近24時間の予測結果を抽出
        recent_forecast = forecast.tail(periods)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        
        # CSVファイルとして保存
        file_path = os.path.join(predict_dir, filename)
        recent_forecast.to_csv(file_path, index=False)
        print(f"Prediction saved to: {file_path}")


def main():
    predictor = PM25Predictor()
    df = predictor.load_data()
    df_prophet = predictor.preprocess_data(df)
    
    predictor.train_model(df_prophet)
    
    # 直近24時間の予測
    future = predictor.make_future_dataframe(df_prophet, periods=24, freq='h')
    forecast = predictor.predict(future)
    
    # 結果の表示
    print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(24))
    
    # 予測結果の保存
    predictor.save_prediction(forecast)
    
    # モデルの評価
    performance = predictor.evaluate_model(df_prophet)
    if performance is not None:
        print("\nModel Performance:")
        print(performance)
    else:
        print("\nUnable to perform cross-validation due to insufficient data.")

if __name__ == "__main__":
    main()