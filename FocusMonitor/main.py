import sys
import statistics
from datetime import datetime
from PySide6.QtWidgets import QApplication
import numpy as np

# 既存のモジュール
from ui.main_window import MainWindow
from core.detector import FaceDetector
from core.calculator import Calculator
from common.data_struct import SensingData, ScoreData, OneSecData, CalibrationData
from database.db_manager import DBManager


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # 各モジュールの初期化
        self.window = MainWindow()
        self.detector = FaceDetector()
        self.calculator = Calculator() # ロジック班担当
        self.db = DBManager()               # DB班担当

        # --- データバッファリング用変数 ---
        self.sec_buffer = []  # 1秒分のデータ (最大5個)
        self.min_buffer = []  # 1分分のデータ (最大60個)
        self.nose_5sec_buffer_x = []    # 鼻の座標xの5秒分のデータ（最大25個）
        self.nose_5sec_buffer_y = []    # 鼻の座標yの5秒分のデータ
        self.nose_data_buffer = 0.0 # 5秒に1回更新される鼻の座標の標準偏差

        # --- キャリブレーションによる閾値データ ---
        self.calibration = CalibrationData(
            # キャリブレーションで得る閾値の定義
            # 閾値は、集計処理に使用するやつ
            # - 視線が画面外にあると判定する角度
            # - 目を閉じていると判定する閉じ具合
            # 現状ふたつのみ
            eye_closedness_threshold = 0.0,  # 目の閉じ具合の閾値
            gaze_angle_threshold = 0.0,      # 画面外視線角度の閾値
        )

        # 検出開始
        self.detector.start()
        self.window.show()

        
        # タイマー設定 (200ms = 5fps)
        from PySide6.QtCore import QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.main_loop)
        self.timer.start(200) 

    def loop_stop(self):
        self.timer.stop

    def loop_start(self):
        self.timer.start(200)

    def main_loop(self):
        """
        200msごとに呼ばれるメインループ
        """
        # 1. 現在の生データを取得 (AI解析班)
        raw_data: SensingData = self.detector.get_current_data()
        
        # バッファに追加
        self.sec_buffer.append(raw_data)

        # 2. 1秒経過判定 (データが5個溜まったら処理)
        if len(self.sec_buffer) >= 5:
            self.process_one_second()
            self.sec_buffer.clear() # バッファをリセット

    def process_one_second(self):
        """
        1秒ごとの処理：データの集約とDB保存
        """
        # 5回分のデータを取り出し
        data_list = self.sec_buffer

        # print("debug data_list:", data_list)

        # --- 集計処理 ---
        # A. 目線が画面外にあったフレーム数
        looking_away_cnt = sum(1 for d in data_list if d.face_detected and d.gaze_angle_yaw > 25.0 and d.gaze_angle_pitch > 25.0)
        
        # B. 目を閉じているフレーム数 (eye_closedness < 0.5)
        sleeping_cnt = sum(1 for d in data_list if d.face_detected and d.eye_closedness < 0.5)
        
        # C. 顔認識できなかったフレーム数
        no_face_cnt = sum(1 for d in data_list if not d.face_detected)

        # D. 5秒間の鼻の座標の標準偏差 (顔が見えているフレームだけで計算)
        self.nose_5sec_buffer_x += [d.nose_x for d in data_list if d.face_detected]    # x座標バッファに追加
        self.nose_5sec_buffer_y += [d.nose_y for d in data_list if d.face_detected]    # y座標バッファに追加
        # print(len(self.nose_5sec_buffer_x),"debug nose_5sec_buffer_x:",self.nose_5sec_buffer_x)
        if((len(self.min_buffer)+1) % 5 == 0):                  # 5秒分のバッファがたまったとき
            if len(self.nose_5sec_buffer_x) >= 5:                 # データの数が5個以上のとき
                # 動きの激しさを計算 (ここでは顔の向きのブレを標準偏差とする例)
                self.nose_data_buffer = np.average([np.std(self.nose_5sec_buffer_x),np.std(self.nose_5sec_buffer_y)], weights = [2, 1])   # 座標の標準偏差の加重平均(x:2, y:1)を代入
                self.nose_5sec_buffer_x = []
                self.nose_5sec_buffer_y = []
            else:
                self.nose_data_buffer = 0.0     # バッファデータの数が足りない場合は0.0を代入

        # --- DB保存用データ構造 ---
        one_sec_summary = OneSecData(
            timestamp = datetime.now(),
            looking_away_count = looking_away_cnt,      # 目線が画面外にあったフレーム数 (0-5)
            sleeping_count = sleeping_cnt,              # 目を閉じていたフレーム数 (0-5)
            no_face_count = no_face_cnt,                # 顔認識できなかったフレーム数 (0-5)
            nose_coord_std_ave = self.nose_data_buffer, # 鼻の座標の標準偏差の平均 (顔の動きの激しさ)
        )

        # 3. DBへ保存 (DB班)
        self.db.save_detail_log(one_sec_summary)

        # 1分バッファに追加
        self.min_buffer.append(one_sec_summary)

        # 4. 1分経過判定 (データが60個溜まったら処理)
        if len(self.min_buffer) >= 60:
            self.process_one_minute()
            self.min_buffer.clear()

    def process_one_minute(self):
        """
        1分ごとの処理：スコア算出と画面更新
        """
        # 1分間の集計データをロジック班の計算機に渡す
        score_data:ScoreData = self.calculator.calculate_score(self.min_buffer)
        
        # DBへ保存
        # self.db.save_score_log(score_data)
        print("1分のスコア：", score_data.concentration_score)
        
        # 画面更新 (UI班)
        # UI側には update_score などのメソッドを作っておく
        if hasattr(self.window, 'update_display'):
            self.window.update_display(score_data)
        else:
            print(f"現在のスコア: {score_data.concentration_score}")

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = MainApp()
    app.run()