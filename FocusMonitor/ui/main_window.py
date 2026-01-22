import sys
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from ui.login_page import LoginPage
from ui.dashboard_page import DashboardPage
from ui.calibration_page import CalibrationPage

class MainWindow(QMainWindow):
    def __init__(self, detector=None, main_app=None):
        super().__init__()
        self.setWindowTitle("集中度モニタリングサービス")
        self.detector = detector
        self.main_app = main_app  # MainAppインスタンスを保持
        self.resize(1100, 700)

        # 画面を重ねて切り替えるスタック構造をメインウィンドウに持たせる
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # ログイン画面とダッシュボード画面を初期化
        self.login_page = LoginPage(self.on_logged_in)
        self.dashboard_page = DashboardPage(detector=self.detector, main_window=self)
        self.calibration_page = CalibrationPage(detector=self.detector)

        # 画面をスタックに登録
        self.stack.addWidget(self.login_page)       # Index 0
        self.stack.addWidget(self.dashboard_page)   # Index 1
        self.stack.addWidget(self.calibration_page) # Index 2

    def on_logged_in(self):
        """ログイン成功時の処理"""
        user_id = self.login_page.id_input.text() or "間々田"
        # ダッシュボードにユーザー名を反映
        self.dashboard_page.user_label.setText(f"ログインID: {user_id}")
        # 画面をダッシュボードへ切り替え
        self.stack.setCurrentIndex(1)
    
    def start_calibration(self):
        """キャリブレーション開始"""
        # キャリブレーション画面に遷移
        self.stack.setCurrentIndex(2)
        # main.pyのキャリブレーション処理を実行
        if self.main_app:
            self.main_app.start_calibration_mode()
    
    def end_calibration(self):
        """キャリブレーション終了"""
        # ダッシュボードに戻る
        self.stack.setCurrentIndex(1)