import sys
import statistics
from datetime import datetime
from PySide6.QtWidgets import QApplication

# 既存のモジュール
from ui.main_window import MainWindow
from core.detector import FaceDetector
from common.data_struct import SensingData, ScoreData

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from ui.login_page import LoginPage
from ui.dashboard_page import DashboardPage

# --- まだ実装されていないクラスのダミー定義 (後で別ファイルへ移動) ---
class ScoreCalculator:
    def calculate(self, one_minute_data: list) -> ScoreData:
        """
        1分間のデータリストを受け取り、減点方式でスコアを計算する
        one_minute_data: 1秒ごとの集計辞書のリスト
        """
        # TODO: ここに要件定義書の「減点ロジック」を実装する
        # 仮の実装：ランダムではなく、データに基づいた計算の枠組み
        current_score = 100
        
        # 例: よそ見秒数の合計
        total_looking_away = sum(d['looking_away_count'] for d in one_minute_data)
        # 5秒(25フレーム)以上よそ見してたら減点...などのロジック記述
        if total_looking_away > 25: 
            current_score -= 10

        return ScoreData(
            timestamp=datetime.now(),
            concentration_score=max(0, current_score), # 0未満にはしない
            message="集中できています" if current_score > 80 else "休憩しましょう"
        )

class DBManager:
    def save_detail_log(self, data: dict):
        """1秒ごとの詳細データを保存"""
        # print(f"[DB Save] Detail: {data}") # デバッグ用
        pass

    def save_score_log(self, data: ScoreData):
        """1分ごとのスコアを保存"""
        print(f"[DB Save] Score: {data.concentration_score}")
        pass


class FocusMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("集中度モニタリングサービス")
        self.resize(1100, 700)

        # 画面を重ねて切り替えるスタック構造
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 画面を作成して登録
        self.login_page = LoginPage(self.on_logged_in)
        self.dashboard_page = DashboardPage()

        self.stack.addWidget(self.login_page)    # Index 0
        self.stack.addWidget(self.dashboard_page) # Index 1

    def on_logged_in(self):
        # ログイン情報を反映して切り替え
        user_id = self.login_page.id_input.text() or "間々田"
        self.dashboard_page.user_label.setText(f"ログインID: {user_id}")
        self.stack.setCurrentIndex(1)


# -----------------------------------------------------------

class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # 各モジュールの初期化
        # self.window = MainWindow()
        self.window = FocusMonitorApp()
        self.detector = FaceDetector()
        self.calculator = ScoreCalculator() # ロジック班担当
        self.db = DBManager()               # DB班担当

        # --- データバッファリング用変数 ---
        self.sec_buffer = []  # 1秒分のデータ (最大5個)
        self.min_buffer = []  # 1分分のデータ (最大60個)

        # 検出開始
        self.detector.start()
        self.window.show()

        
        # タイマー設定 (200ms = 5fps)
        from PySide6.QtCore import QTimer
        self.timer = QTimer()
        self.timer.timeout.connect(self.main_loop)
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

        # --- 集計処理 ---
        # A. 目線が画面外にあったフレーム数 (ここでは仮に gaze_distance > 0.5 を閾値とする)
        # looking_away_count = sum(1 for d in data_list if d.face_detected and d.gaze_distance > 0.5)
        
        # B. 目を閉じているフレーム数 (eye_openness < 0.5)
        # 左右どちらかが開いていればOKとするか、両目か等は要件次第。ここでは平均で判定
        sleeping_count = sum(1 for d in data_list if d.face_detected and (d.eye_openness_left + d.eye_openness_right)/2 < 0.5)
        
        # C. 顔認識できなかったフレーム数
        no_face_count = sum(1 for d in data_list if not d.face_detected)

        # D. 鼻の座標の標準偏差 (顔が見えているフレームだけで計算)
        # 簡易的に、detector側で nose_x, nose_y を SensingData に含める必要があるが、
        # ここでは face_angle_yaw などの揺らぎで代用、あるいは0とする
        # ※本来は SensingData に nose_x, nose_y を追加すべき

        # valid_faces = [d for d in data_list if d.face_detected]
        # if len(valid_faces) >= 2:
        #     # 動きの激しさを計算 (ここでは顔の向きのブレを標準偏差とする例)
        #     stdev_val = statistics.stdev([d.face_angle_yaw for d in valid_faces])
        # else:
        #     stdev_val = 0.0

        # --- DB保存用データ構造 ---
        one_sec_summary = {
            "timestamp": datetime.now(),
            # "looking_away_count": looking_away_count, # 最大5
            "sleeping_count": sleeping_count,         # 最大5
            "no_face_count": no_face_count,           # 最大5
            # "movement_stdev": stdev_val
        }

        # 3. DBへ保存 (DB班)
        # self.db.save_detail_log(one_sec_summary)
        print("1秒のデータ：",one_sec_summary)

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
        score_data = self.calculator.calculate(self.min_buffer)
        
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