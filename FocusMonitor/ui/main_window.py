import sys
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from ui.login_page import LoginPage
from ui.dashboard_page import DashboardPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("集中度モニタリングサービス")
        self.resize(1100, 700)

        # 画面を重ねて切り替えるスタック構造をメインウィンドウに持たせる
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # ログイン画面とダッシュボード画面を初期化
        self.login_page = LoginPage(self.on_logged_in)
        self.dashboard_page = DashboardPage()

        # 画面をスタックに登録
        self.stack.addWidget(self.login_page)    # Index 0
        self.stack.addWidget(self.dashboard_page) # Index 1

    def on_logged_in(self):
        """ログイン成功時の処理"""
        user_id = self.login_page.id_input.text() or "間々田"
        # ダッシュボードにユーザー名を反映
        self.dashboard_page.user_label.setText(f"ログインID: {user_id}")
        # 画面をダッシュボードへ切り替え
        self.stack.setCurrentIndex(1)