import sys
import statistics
from datetime import datetime
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer
import numpy as np
import time

# 既存のモジュール
from ui.main_window import MainWindow
from core.detector import FaceDetector
from core.calculator import Calculator
from core.calibration import Calibration
from common.data_struct import SensingData, ScoreData, OneSecData, CalibrationData
from database.db_manager import DBManager

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # 各モジュールの初期化
        self.detector = FaceDetector()
        self.window = MainWindow(detector=self.detector, main_app=self) # UIに自分(MainApp)を渡す
        self.calculator = Calculator()
        self.db = DBManager()
        self.calibration = Calibration()

        # --- 状態管理フラグ ---
        self.is_calibration_mode = False  # 今キャリブレーション中かどうか

        # --- データバッファリング用変数 ---
        self.sec_buffer = []  # 1秒分のデータ (最大5個)
        self.min_buffer = []  # 1分分のデータ (最大60個)
        self.nose_5sec_buffer_x = []    # 鼻の座標xの5秒分のデータ
        self.nose_5sec_buffer_y = []    # 鼻の座標yの5秒分のデータ
        self.nose_data_buffer = 0.0     # 5秒に1回更新される鼻の座標の標準偏差

        # --- キャリブレーションによる閾値データ (初期値) ---
        self.calibration_data = CalibrationData(
            eye_closedness_threshold = 0.75,     # 目の閉じ具合の閾値
            gaze_angle_yaw_threshold = 20.0,     # 画面外視線横角度の閾値
            gaze_angle_pitch_threshold = 20.0,   # 画面外視線縦角度の閾値
        )

        # --- スコアデータ初期値 ---
        self.self.score_data = ScoreData(
            timestamp = datetime.now(),
            concentration_score = 0,
            reaving_ratio = 0,
        )

        # 検出開始
        self.detector.start()
        self.window.show()

        
        # タイマー設定 (200ms = 5fps)
        self.timer = QTimer()
        self.timer.timeout.connect(self.main_loop)

    def main_loop(self):
        """
        200msごとに呼ばれるメインループ
        ここで「通常モード」と「キャリブレーションモード」を切り替える
        """
        # 1. 現在の生データを取得 (AI解析班)
        raw_data: SensingData = self.detector.get_current_data()
        
        # モードによる分岐
        if self.is_calibration_mode:
            # === A. キャリブレーション中の処理 ===
            self.process_calibration(raw_data)
        else:
            # === B. 通常時の処理 (ログ保存・スコア計算) ===
            self.process_normal_recording(raw_data)

    # --- モードごとの処理 ---

    def start_calibration_mode(self):
        """UIボタンから呼ばれる: キャリブレーションを開始する"""
        print("MainApp: キャリブレーションモードを開始します")
        
        # 1. キャリブレーションモジュールの準備
        self.calibration.start() # calibration側のバッファクリア
        
        # 2. フラグを立てる (これで main_loop の動作が変わる)
        self.is_calibration_mode = True
        
        self.timer.start(200)
        

    def process_calibration(self, raw_data: SensingData):
        """キャリブレーション中のループ処理"""
        # データを1つ渡す。完了したら True が返ってくる想定
        is_finished = self.calibration.add_data(raw_data)

        if is_finished:
            print("MainApp: データ収集完了。計算します。")
            
            # 結果を取得して適用
            new_thresholds = self.calibration.calculate()
            if new_thresholds:
                self.calibration_data = new_thresholds
                print(f"新しい閾値: {self.calibration_data}")
            
            # モード終了
            self.is_calibration_mode = False
            
            # UIに戻るよう通知
            if hasattr(self.window, 'end_calibration'):
                self.window.end_calibration()

    def process_normal_recording(self, raw_data: SensingData):
        """通常時のログ保存処理 (元の main_loop の中身)"""
        
        # バッファに追加
        self.sec_buffer.append(raw_data)

        # 1秒経過判定 (データが5個溜まったら処理)
        if len(self.sec_buffer) >= 5:
            self.process_one_second()
            self.sec_buffer.clear() # バッファをリセット

    def process_one_second(self):
        """
        1秒ごとの処理：データの集約とDB保存
        """
        # 5回分のデータを取り出し
        data_list = self.sec_buffer

        # A. 目線が画面外にあったフレーム数
        looking_away_cnt = sum(1 for d in data_list if d.face_detected 
                               and (d.gaze_angle_yaw > self.calibration_data.gaze_angle_yaw_threshold 
                               or d.gaze_angle_yaw < -self.calibration_data.gaze_angle_yaw_threshold
                               or d.gaze_angle_pitch > self.calibration_data.gaze_angle_pitch_threshold
                               or d.gaze_angle_pitch < -self.calibration_data.gaze_angle_pitch_threshold))
        
        # B. 目を閉じているフレーム数
        sleeping_cnt = sum(1 for d in data_list if d.face_detected and d.eye_closedness > self.calibration_data.eye_closedness_threshold)
        
        # C. 顔認識できなかったフレーム数
        no_face_cnt = sum(1 for d in data_list if not d.face_detected)

        # D. 5秒間の鼻の座標の標準偏差(顔が見えているフレームだけで計算)
        self.nose_5sec_buffer_x += [d.nose_x for d in data_list if d.face_detected]    # x座標バッファに追加
        self.nose_5sec_buffer_y += [d.nose_y for d in data_list if d.face_detected]    # y座標バッファに追加
        
        if((len(self.min_buffer)+1) % 5 == 0):      # 5秒分のバッファがたまったとき
            if len(self.nose_5sec_buffer_x) >= 5:   # データの数が5個以上のとき
                # 動きの激しさを計算 (ここでは顔の向きのブレを標準偏差とする例)
                self.nose_5sec_buffer_x.clear()
                self.nose_5sec_buffer_y.clear()
            else:
                self.nose_data_buffer = 0.0

        # DB保存用データ構造
        one_sec_summary = OneSecData(
            timestamp = datetime.now(),
            looking_away_count = looking_away_cnt,      # 目線が画面外にあったフレーム数 (0-5)
            sleeping_count = sleeping_cnt,              # 目を閉じていたフレーム数 (0-5)
            no_face_count = no_face_cnt,                # 顔認識できなかったフレーム数 (0-5)
            nose_coord_std_ave = self.nose_data_buffer, # 鼻の座標の標準偏差の平均 (顔の動きの激しさ)
        )

        self.db.save_detail_log(one_sec_summary)
        self.min_buffer.append(one_sec_summary)

        # 1分経過判定
        if len(self.min_buffer) >= 60:
            self.process_one_minute()
            self.min_buffer.clear()

    def process_one_minute(self):
        """1分ごとの処理：スコア算出と画面更新"""
        self.score_data:ScoreData = self.calculator.calculate_score(self.min_buffer)
        print("1分のスコア：", self.score_data.concentration_score)
        
        if hasattr(self.window, 'update_display'):
            self.window.update_display(self.score_data)
        else:
            print(f"現在のスコア: {self.score_data.concentration_score}")

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = MainApp()
    app.run()