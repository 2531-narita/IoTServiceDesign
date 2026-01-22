import cv2
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont

class CalibrationPage(QWidget):
    def __init__(self, detector=None):
        super().__init__()
        self.setStyleSheet("background-color: #1a5276; color: white;")
        self.main_layout = QVBoxLayout(self)
        self.detector = detector  # detectorインスタンスを保持
        self.frame_update_timer = None  # フレーム更新タイマー
        
        # --- ヘッダー ---
        header_layout = QHBoxLayout()
        title = QLabel("顔キャリブレーション")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setFont(QFont("MS Gothic", 16))
        
        header_layout.addWidget(title)
        self.main_layout.addLayout(header_layout)
        
        # --- メインコンテンツ（カメラ映像と指示文を中央配置） ---
        content_layout = QVBoxLayout()
        content_layout.addStretch()
        
        # 指示文
        instruction = QLabel("モニターの縁を見回してください")
        instruction.setFont(QFont("MS Gothic", 18))
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: white; padding: 20px;")
        content_layout.addWidget(instruction)
        
        # カメラエリア
        camera_area = QHBoxLayout()
        camera_area.addStretch()
        
        self.camera_label = QLabel("カメラ待機中")
        self.camera_label.setFixedSize(500, 500)
        self.camera_label.setStyleSheet("background-color: #ddd; border: 2px solid black;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        camera_area.addWidget(self.camera_label)
        
        camera_area.addStretch()
        content_layout.addLayout(camera_area)
        
        # 補足テキスト
        supplement = QLabel("カメラ内に顔全体が写るよう、適切な距離を保ってください")
        supplement.setFont(QFont("MS Gothic", 12))
        supplement.setAlignment(Qt.AlignCenter)
        supplement.setStyleSheet("color: #ccc; padding: 10px;")
        content_layout.addWidget(supplement)
        
        content_layout.addStretch()
        self.main_layout.addLayout(content_layout)
        
        # フレーム更新タイマーの初期化
        if self.detector:
            self.frame_update_timer = QTimer()
            self.frame_update_timer.timeout.connect(self.update_frame_from_detector)
            self.frame_update_timer.start(50)  # 50ms = 5fps で更新
    
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
            self.camera_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio))
    
    def cleanup(self):
        """画面を離れる時のクリーンアップ"""
        if self.frame_update_timer:
            self.frame_update_timer.stop()
