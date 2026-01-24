import cv2
import random
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QStackedWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from database.db_manager import DBManager
from config import HISTORY_DISPLAY_COUNT

plt.rcParams['font.family'] = 'MS Gothic'

class DashboardPage(QWidget):
    def __init__(self, detector=None, main_window=None):
        super().__init__()
        self.setStyleSheet("background-color: #1a5276; color: white;") # スライド背景色
        self.main_layout = QVBoxLayout(self)
        self.detector = detector  # detectorインスタンスを保持
        self.main_window = main_window  # MainWindowインスタンスを保持
        self.frame_update_timer = None  # タイマー用
        self.db_manager = DBManager()  # DBManagerインスタンスを保持

        # --- 1. ヘッダー (ログインID / 再キャリブ / 各種切替ボタン) ---
        header_top = QHBoxLayout()
        self.user_label = QLabel("ログインID(例:間々田)")
        self.user_label.setStyleSheet("background-color: white; color: black; padding: 5px; border: 1px solid black;")
        
        self.recal_btn = QPushButton("顔再キャリブレーション")
        self.recal_btn.setStyleSheet("background-color: white; color: black; border: 1px solid black; padding: 5px;")
        self.recal_btn.clicked.connect(self.start_calibration)
        
        header_top.addWidget(self.user_label)
        header_top.addWidget(self.recal_btn)
        header_top.addStretch()

        self.history_btn = QPushButton("履歴")
        self.history_btn.setFixedSize(60, 30)
        self.history_btn.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
        self.history_btn.clicked.connect(lambda: self.update_view_mode("履歴"))
        header_top.addWidget(self.history_btn)
        self.main_layout.addLayout(header_top)

        header_bottom = QHBoxLayout()
        header_bottom.addStretch()
        for t in ["現在", "日", "週", "月"]:
            btn = QPushButton(t)
            btn.setFixedSize(50, 30)
            btn.setStyleSheet("background-color: white; color: black; border: 1px solid black;")
            btn.clicked.connect(lambda ch=False, p=t: self.update_view_mode(p))
            header_bottom.addWidget(btn)
        self.main_layout.addLayout(header_bottom)

        # --- 2. メインコンテンツ (左右分割レイアウト) ---
        # 左側は常にカメラ、右側がスタックで切り替わる
        content_main_layout = QHBoxLayout()

        # 【左側】共通カメラエリア
        left_cam_layout = QVBoxLayout()
        face_title = QLabel("顔 (カメラ映像)")
        face_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_cam_layout.addWidget(face_title)

        self.camera_label = QLabel("カメラ待機中")
        self.camera_label.setFixedSize(400, 400)
        self.camera_label.setStyleSheet("background-color: #ddd; border: 2px solid black; color: black;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        left_cam_layout.addWidget(self.camera_label)
        left_cam_layout.addStretch()
        content_main_layout.addLayout(left_cam_layout)

        # 【右側】切り替えコンテンツ (スタック)
        self.right_stack = QStackedWidget()
        
        # A. 現在 (リスト表示)
        self.page_now = QWidget()
        now_v = QVBoxLayout(self.page_now)
        now_v.addWidget(QLabel("スコア"))
        self.score_log = QTextEdit()
        self.score_log.setReadOnly(True)
        self.score_log.setFont(QFont("MS Gothic", 11))
        self.score_log.setStyleSheet("background-color: white; color: black;")
        now_v.addWidget(self.score_log)
        self.right_stack.addWidget(self.page_now) # Index 0

        # B. 統計 (円グラフ + 棒グラフ)
        self.page_stats = QWidget()
        stats_v = QVBoxLayout(self.page_stats)
        self.fig = Figure(figsize=(5, 8), facecolor='#1a5276')
        self.canvas = FigureCanvas(self.fig)
        stats_v.addWidget(self.canvas)
        self.right_stack.addWidget(self.page_stats) # Index 1

        # C. 履歴 (テーブル)
        self.page_history = QWidget()
        hist_v = QVBoxLayout(self.page_history)
        hist_v.addWidget(QLabel("過去の履歴"))
        self.history_table = QTableWidget(HISTORY_DISPLAY_COUNT, 2)
        self.history_table.setHorizontalHeaderLabels(["平均スコア", "状態"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setStyleSheet("background-color: white; color: black;")
        hist_v.addWidget(self.history_table)
        self.right_stack.addWidget(self.page_history) # Index 2

        content_main_layout.addWidget(self.right_stack)
        self.main_layout.addLayout(content_main_layout)

        self.worker = None
        self.update_view_mode("現在")
        
        # フレーム更新タイマーの初期化
        if self.detector:
            self.frame_update_timer = QTimer()
            self.frame_update_timer.timeout.connect(self.update_frame_from_detector)
            self.frame_update_timer.start(50)  # 50ms = 5fps で更新

    def update_view_mode(self, period):
        if period == "現在":
            self.right_stack.setCurrentIndex(0)
            self.refresh_current_view()
        elif period == "履歴":
            self.right_stack.setCurrentIndex(2)
            self.fill_history_table()
        else:
            self.right_stack.setCurrentIndex(1)
            self.draw_stats_graphs(period)
    
    def refresh_current_view(self):
        """現在訪啊を更新（main.pyからの直接呼び出し用）"""
        self.score_log.setPlainText(self.generate_dummy_list())

    def get_status(self, score, reaving_ratio):
        """スコアと離席率からステータスを判定"""
        # 離席率が90%を超えている場合は離席
        if reaving_ratio > 90:
            return "離席"
        # スコアに基づいて判定
        elif score >= 70:
            return "集中"
        elif 40 <= score < 70:
            return "注意散漫"
        else:  # score < 40
            return "非集中"

    def generate_dummy_list(self):
        """DBから最近のスコアを取得して表示"""
        recent_scores = self.db_manager.get_recent_scores(limit=10)
        lines = []
        for score_data in recent_scores:
            timestamp = score_data['timestamp']
            score = score_data['score']
            reaving_ratio = score_data.get('reaving_ratio', 0) or 0  # NullやNoneの場合は0
            status = self.get_status(score, reaving_ratio)
            lines.append(f"{timestamp}  {score:.1f}  {status}")
        
        # データがない場合はダミーメッセージ
        if not lines:
            return "スコアデータが利用できません"
        return "\n".join(lines)

    def draw_stats_graphs(self, period):
        """日・週・月用のグラフ描画（時間帯ごとの最大スコアを表示）"""
        self.fig.clear()
        recent_scores = self.db_manager.get_recent_scores(limit=1000)  # より多くのデータを取得
        
        if not recent_scores:
            ax = self.fig.add_subplot(111)
            ax.set_facecolor('#1a5276')
            ax.text(0.5, 0.5, 'データが利用できません', 
                   horizontalalignment='center', verticalalignment='center',
                   color='white', transform=ax.transAxes)
            self.canvas.draw()
            return
        
        # タイムスタンプをパース
        parsed_data = []
        for s in recent_scores:
            try:
                timestamp = datetime.strptime(s['timestamp'], '%Y-%m-%d %H:%M:%S')
                parsed_data.append({
                    'timestamp': timestamp,
                    'score': s['score'],
                    'reaving_ratio': s.get('reaving_ratio', 0) or 0
                })
            except:
                continue
        
        if not parsed_data:
            ax = self.fig.add_subplot(111)
            ax.set_facecolor('#1a5276')
            ax.text(0.5, 0.5, 'パース可能なデータがありません', 
                   horizontalalignment='center', verticalalignment='center',
                   color='white', transform=ax.transAxes)
            self.canvas.draw()
            return
        
        # スコアデータから統計情報を計算（全体用）
        scores = [s['score'] for s in recent_scores]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 集中度による分類（新しい条件）
        focused_count = sum(1 for s in recent_scores if s['reaving_ratio'] <= 90 and s['score'] >= 70)
        distracted_count = sum(1 for s in recent_scores if s['reaving_ratio'] <= 90 and 40 <= s['score'] < 70)
        unfocused_count = sum(1 for s in recent_scores if s['reaving_ratio'] <= 90 and s['score'] < 40)
        away_count = sum(1 for s in recent_scores if s['reaving_ratio'] > 90)
        
        # 上段：円グラフ
        ax1 = self.fig.add_subplot(211)
        ax1.set_facecolor('#1a5276')
        vals = [focused_count, distracted_count, unfocused_count, away_count]
        labels = ["集中", "注意散漫", "非集中", "離席"]
        ax1.pie(vals, labels=labels, autopct='%1.1f%%', colors=['#9b59b6', '#f1c40f', '#e74c3c', '#3498db'], textprops={'color':"white"})
        ax1.set_title(f"{period}の集中度内訳", color='white')

        # 下段：棒グラフ（時間帯ごとの最大スコア）
        ax2 = self.fig.add_subplot(212)
        ax2.set_facecolor('#1a5276')
        
        if period == "日":
            display_labels, bar_vals = self._get_daily_max_scores(parsed_data)
        elif period == "週":
            display_labels, bar_vals = self._get_weekly_max_scores(parsed_data)
        elif period == "月":
            display_labels, bar_vals = self._get_monthly_max_scores(parsed_data)
        else:
            display_labels = []
            bar_vals = []
        
        ax2.bar(display_labels, bar_vals, color='#2ecc71')
        ax2.set_ylim(0, 100)
        ax2.tick_params(colors='white')
        ax2.set_title(f"{period}の推移 (平均: {avg_score:.1f})", color='white')
        ax2.set_ylabel('スコア', color='white')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _get_daily_max_scores(self, parsed_data):
        """今日のデータを6つの時間帯に分割して、各時間帯の最大スコアを取得"""
        today = datetime.now().date()
        today_data = [d for d in parsed_data if d['timestamp'].date() == today]
        
        time_ranges = [
            ("0-4時", 0, 4),
            ("4-8時", 4, 8),
            ("8-12時", 8, 12),
            ("12-16時", 12, 16),
            ("16-20時", 16, 20),
            ("20-24時", 20, 24)
        ]
        
        labels = []
        values = []
        for label, start_hour, end_hour in time_ranges:
            range_data = [d['score'] for d in today_data if start_hour <= d['timestamp'].hour < end_hour]
            max_score = max(range_data) if range_data else 0
            labels.append(label)
            values.append(max_score)
        
        return labels, values
    
    def _get_weekly_max_scores(self, parsed_data):
        """今週のデータを1日ごとに7つに分割して、各日の最大スコアを取得"""
        today = datetime.now().date()
        # 今週の月曜日を取得
        sunday = today - timedelta(days=today.weekday())
        
        labels = []
        values = []
        for i in range(7):
            target_date = sunday + timedelta(days=i)
            day_data = [d['score'] for d in parsed_data if d['timestamp'].date() == target_date]
            max_score = max(day_data) if day_data else 0
            labels.append(target_date.strftime("%m/%d"))  # 月/日 形式
            values.append(max_score)
        
        return labels, values
    
    def _get_monthly_max_scores(self, parsed_data):
        """今月のデータを週ごとに分割して、各週の最大スコアを取得"""
        today = datetime.now().date()
        # 月初を取得
        first_day = today.replace(day=1)
        # 月初の週の月曜日を取得
        sunday = first_day - timedelta(days=first_day.weekday()+1)
        
        labels = []
        values = []
        week_num = 1
        
        current_sunday = sunday
        while True:
            week_end = current_sunday + timedelta(days=6)
            # その週のデータを取得（ただし当月のみ）
            week_data = [d['score'] for d in parsed_data 
                        if current_sunday <= d['timestamp'].date() < week_end 
                        and d['timestamp'].month == today.month]
            
            if not week_data and current_sunday.month == today.month+1:
                # 来月のデータが出始めたら終了
                break
            
            max_score = max(week_data) if week_data else 0
            labels.append(f"第{week_num}週")
            values.append(max_score)
            
            current_sunday = week_end + timedelta(days=1)
            week_num += 1
            
            if week_num > 6:  # 最大6週まで
                break
        
        return labels, values

    def fill_history_table(self):
        """履歴テーブルにDBデータを補充"""
        recent_scores = self.db_manager.get_recent_scores(limit=HISTORY_DISPLAY_COUNT)
        for i, score_data in enumerate(recent_scores):
            if i >= 60:  # テーブルは最大60行
                break
            timestamp = score_data['timestamp']
            score = score_data['score']
            reaving_ratio = score_data.get('reaving_ratio', 0) or 0  # NullやNoneの場合は0
            status = self.get_status(score, reaving_ratio)
            self.history_table.setItem(i, 0, QTableWidgetItem(f"{timestamp}  {score:.1f}"))
            self.history_table.setItem(i, 1, QTableWidgetItem(status))
        
        # 残りの行をクリア
        for i in range(len(recent_scores), HISTORY_DISPLAY_COUNT):
            self.history_table.setItem(i, 0, QTableWidgetItem(""))
            self.history_table.setItem(i, 1, QTableWidgetItem(""))

    def start_calibration(self):
        """キャリブレーション開始"""
        if self.main_window:
            self.main_window.start_calibration()

    def update_camera_display(self, qt_img):
        self.camera_label.setPixmap(QPixmap.fromImage(qt_img).scaled(400, 400, Qt.KeepAspectRatio))
    
    def update_frame_from_detector(self):
        """detectorから最新フレームを取得して表示"""
        if not self.detector:
            return
        
        frame = self.detector.get_latest_frame()
        if frame is not None:
            # OpenCV形式 (BGR) → RGB に変換
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # RGB → QImage に変換
            h, w, ch = rgb_frame.shape
            bytes_per_line = 3 * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # QLabel に表示
            pixmap = QPixmap.fromImage(qt_image)
            self.camera_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))