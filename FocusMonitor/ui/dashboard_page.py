import cv2
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# camera_worker.py から CameraWorker クラスを読み込む
from camera_worker import CameraWorker

# matplotlibの日本語文字化け対策 (Windows標準フォントを指定)
plt.rcParams['font.family'] = 'MS Gothic' 

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        # スライド5の濃い青背景を再現
        self.setStyleSheet("background-color: #1a5276; color: white;")
        
        # 全体のメインレイアウト
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # --- ヘッダーエリア (ID表示・ボタン類) ---
        header_layout = QHBoxLayout()
        self.user_label = QLabel("ログインID: ---") # スライド5
        self.user_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.user_label)
        
        # キャリブレーションボタン (オレンジ色で目立たせる)
        self.recal_btn = QPushButton("顔再キャリブレーション")
        self.recal_btn.setStyleSheet("""
            QPushButton { background-color: #e67e22; color: white; padding: 8px 15px; 
                          border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.recal_btn.clicked.connect(self.start_calibration)
        header_layout.addWidget(self.recal_btn)
        
        header_layout.addStretch() # 中央に余白を作る
        
        # 期間切り替えボタン
        for t in ["現在", "日", "週", "月"]:
            btn = QPushButton(t)
            btn.setFixedWidth(60)
            btn.setStyleSheet("background-color: #34495e; color: white; padding: 5px;")
            header_layout.addWidget(btn)
        
        self.main_layout.addLayout(header_layout)

        # --- コンテンツエリア (カメラ映像とグラフを横に並べる) ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 1. 左側：カメラ映像表示用ラベル (スライド4のイメージ)
        self.camera_label = QLabel("「顔再キャリブレーション」を\n押すとカメラが起動します")
        self.camera_label.setFixedSize(450, 350) # サイズを固定
        self.camera_label.setStyleSheet("background-color: black; border: 2px solid #e67e22; color: white;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.camera_label)

        # 2. 右側：グラフエリア (上下に円グラフと棒グラフ)
        graphs_v_layout = QVBoxLayout()
        
        self.pie_canvas = self.create_chart("pie") # 円グラフ
        self.bar_canvas = self.create_chart("bar") # 棒グラフ
        
        graphs_v_layout.addWidget(self.pie_canvas)
        graphs_v_layout.addWidget(self.bar_canvas)
        
        content_layout.addLayout(graphs_v_layout)
        
        self.main_layout.addLayout(content_layout)

        # カメラスレッドの管理用
        self.worker = None

    def create_chart(self, chart_type):
        """Matplotlibを使用して日本語対応のグラフを作成する"""
        fig = Figure(figsize=(5, 3), facecolor='#1a5276')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a5276')
        ax.tick_params(colors='white') # 軸の文字色を白に

        if chart_type == "pie":
            # 集中度割合のダミーデータ
            ax.pie([70, 20, 10], labels=["集中", "注意散漫", "離席"], 
                   textprops={'color':"white"}, colors=['#9b59b6', '#2ecc71', '#f1c40f'])
            ax.set_title("集中度の内訳", color='white')
        else:
            # スコア推移のダミーデータ
            ax.bar(["1/1", "1/2", "1/3", "1/4", "1/5"], [69, 88, 88, 69, 69], color='#3498db')
            ax.set_title("集中度スコアの推移", color='white')
        
        fig.tight_layout()
        return FigureCanvas(fig)

    def start_calibration(self):
        """ボタンクリックでカメラ解析スレッドを開始する"""
        self.recal_btn.setEnabled(False)
        self.recal_btn.setText("計測中(10秒)...")
        
        # 前回のスレッドが残っていれば終了を待つ
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()

        self.worker = CameraWorker()
        # スレッドからの信号(画像)を update_camera_view に接続
        self.worker.image_data.connect(self.update_camera_view)
        # 終了信号を on_finished に接続
        self.worker.finished.connect(self.on_calibration_finished)
        self.worker.start()

    def update_camera_view(self, qt_img):
        """CameraWorkerから送られてきたQImageを画面に表示する"""
        # ラベルのサイズに合わせて画像をスケーリングして表示
        pixmap = QPixmap.fromImage(qt_img)
        self.camera_label.setPixmap(pixmap.scaled(
            self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_calibration_finished(self):
        """10秒間の計測が終わった後の処理"""
        self.recal_btn.setEnabled(True)
        self.recal_btn.setText("顔再キャリブレーション")
        self.camera_label.setText("計測が完了しました")
        # 実際にはここで基準値をDBに保存するなどの処理を入れる