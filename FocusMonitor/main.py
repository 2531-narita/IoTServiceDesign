import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from ui.login_page import LoginPage
from ui.dashboard_page import DashboardPage

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FocusMonitorApp()
    window.show() # これで画面が表示されます
    sys.exit(app.exec())