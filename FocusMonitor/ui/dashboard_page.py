import cv2
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QStackedWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from camera_worker import CameraWorker

plt.rcParams['font.family'] = 'MS Gothic'

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1a5276; color: white;") # スライド背景色
        self.main_layout = QVBoxLayout(self)

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
        self.history_table = QTableWidget(10, 2)
        self.history_table.setHorizontalHeaderLabels(["平均スコア", "状態"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setStyleSheet("background-color: white; color: black;")
        hist_v.addWidget(self.history_table)
        self.right_stack.addWidget(self.page_history) # Index 2

        content_main_layout.addWidget(self.right_stack)
        self.main_layout.addLayout(content_main_layout)

        self.worker = None
        self.update_view_mode("現在")

    def update_view_mode(self, period):
        if period == "現在":
            self.right_stack.setCurrentIndex(0)
            self.score_log.setPlainText(self.generate_dummy_list())
        elif period == "履歴":
            self.right_stack.setCurrentIndex(2)
            self.fill_history_table()
        else:
            self.right_stack.setCurrentIndex(1)
            self.draw_stats_graphs(period)

    def generate_dummy_list(self):
        """スライド4風のリスト用ダミーデータ生成"""
        lines = []
        for i in range(10):
            score = random.randint(40, 95)
            status = "集中" if score > 75 else "注意散漫"
            lines.append(f"10:22:{i:02d}  {score}  {status}")
        return "\n".join(lines)

    def draw_stats_graphs(self, period):
        """日・週・月用のバラバラなグラフ描画"""
        self.fig.clear()
        
        # 上段：円グラフ
        ax1 = self.fig.add_subplot(211)
        ax1.set_facecolor('#1a5276')
        vals = [random.randint(50, 80), random.randint(10, 30), random.randint(5, 15)]
        ax1.pie(vals, labels=["集中", "注意散漫", "離席"], autopct='%1.1f%%', colors=['#9b59b6', '#f1c40f', '#3498db'], textprops={'color':"white"})
        ax1.set_title(f"{period}の集中度内訳", color='white')

        # 下段：棒グラフ
        ax2 = self.fig.add_subplot(212)
        ax2.set_facecolor('#1a5276')
        if period == "日": labels = ["朝", "昼前", "昼後", "昼後2", "夕"]; count = 5
        elif period == "週": labels = ["月", "火", "水", "木", "金"]; count = 5
        else: labels = ["1週", "2週", "3週", "4週"]; count = 4
        
        bar_vals = [random.randint(60, 95) for _ in range(count)]
        ax2.bar(labels, bar_vals, color='#2ecc71')
        ax2.set_ylim(0, 100)
        ax2.tick_params(colors='white')
        ax2.set_title(f"{period}の推移", color='white')
        
        self.fig.tight_layout()
        self.canvas.draw()

    def fill_history_table(self):
        """履歴テーブルにランダムデータを補充"""
        for i in range(10):
            score = random.randint(60, 90)
            status = "集中" if score > 70 else "注意散漫"
            self.history_table.setItem(i, 0, QTableWidgetItem(f"1/{i+1}  {score}"))
            self.history_table.setItem(i, 1, QTableWidgetItem(status))

    def start_calibration(self):
        if self.worker and self.worker.isRunning(): return
        self.worker = CameraWorker()
        self.worker.image_data.connect(self.update_camera_display)
        self.worker.start()

    def update_camera_display(self, qt_img):

        self.camera_label.setPixmap(QPixmap.fromImage(qt_img).scaled(400, 400, Qt.KeepAspectRatio))