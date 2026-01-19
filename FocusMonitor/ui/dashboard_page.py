import cv2
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


from camera_worker import CameraWorker

plt.rcParams['font.family'] = 'MS Gothic' 

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setStyleSheet("background-color: #1a5276; color: white;") 
        self.main_layout = QVBoxLayout(self)

        # --- ヘッダーエリア ---
        header_layout = QHBoxLayout()
        self.user_label = QLabel("ログインID: ---")
        header_layout.addWidget(self.user_label)
        
        self.recal_btn = QPushButton("顔再キャリブレーション")
        
        self.recal_btn.clicked.connect(self.start_calibration)
        header_layout.addWidget(self.recal_btn)
        header_layout.addStretch()
        
        # 期間切り替えボタン
        for t in ["現在", "日", "週", "月"]:
            btn = QPushButton(t)
            btn.setFixedWidth(60)
            btn.setStyleSheet("background-color: #34495e; color: white; padding: 5px;")
            btn.clicked.connect(lambda checked=False, period=t: self.update_charts(period))
            header_layout.addWidget(btn)
        
        self.main_layout.addLayout(header_layout)

        # --- コンテンツエリア ---
        content_layout = QHBoxLayout()
        self.camera_label = QLabel("カメラ待機中")
        self.camera_label.setFixedSize(450, 350)
        self.camera_label.setStyleSheet("background-color: black; border: 2px solid #e67e22;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.camera_label)

        # グラフエリア
        graphs_v_layout = QVBoxLayout()
        self.fig_pie = Figure(figsize=(5, 3), facecolor='#1a5276')
        self.ax_pie = self.fig_pie.add_subplot(111)
        self.canvas_pie = FigureCanvas(self.fig_pie)
        
        self.fig_bar = Figure(figsize=(5, 3), facecolor='#1a5276')
        self.ax_bar = self.fig_bar.add_subplot(111)
        self.canvas_bar = FigureCanvas(self.fig_bar)
        
        graphs_v_layout.addWidget(self.canvas_pie)
        graphs_v_layout.addWidget(self.canvas_bar)
        content_layout.addLayout(graphs_v_layout)
        self.main_layout.addLayout(content_layout)

        self.worker = None
        self.update_charts("現在")

    # --- グラフ更新ロジック ---
    def update_charts(self, period):
        data = {
            "現在": {"pie": [70, 20, 10], "bar": [65, 70, 75, 80, 85], "labels": ["10分前", "8分前", "6分前", "4分前", "現在"]},
            "日":   {"pie": [60, 30, 10], "bar": [50, 60, 80, 70, 90], "labels": ["朝", "昼前", "昼後", "夕方", "夜"]},
            "週":   {"pie": [80, 10, 10], "bar": [85, 88, 82, 90, 87], "labels": ["月", "火", "水", "木", "金"]},
            "月":   {"pie": [75, 15, 10], "bar": [70, 75, 80, 78, 82], "labels": ["1週", "2週", "3週", "4週", "平均"]}
        }
        curr = data[period]
        
        self.ax_pie.clear()
        self.ax_pie.pie(curr["pie"], labels=["集中", "散漫", "離席"], textprops={'color':"white"}, colors=['#9b59b6', '#2ecc71', '#f1c40f'])
        self.ax_pie.set_title(f"集中度内訳 ({period})", color='white')
        self.canvas_pie.draw()

        self.ax_bar.clear()
        self.ax_bar.bar(curr["labels"], curr["bar"], color='#3498db')
        self.ax_bar.tick_params(colors='white')
        self.ax_bar.set_title(f"スコア推移 ({period})", color='white')
        self.ax_bar.set_ylim(0, 100)
        self.canvas_bar.draw()

    # --- カメラ連携ロジック 
    def start_calibration(self):
        self.recal_btn.setEnabled(False)
        self.recal_btn.setText("計測中...")
        self.worker = CameraWorker()
        self.worker.image_data.connect(self.update_camera_view)
        self.worker.finished.connect(self.on_calibration_finished)
        self.worker.start()

    def update_camera_view(self, qt_img):
        pixmap = QPixmap.fromImage(qt_img)
        self.camera_label.setPixmap(pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_calibration_finished(self):
        self.recal_btn.setEnabled(True)
        self.recal_btn.setText("顔再キャリブレーション")
        self.camera_label.setText("計測完了")