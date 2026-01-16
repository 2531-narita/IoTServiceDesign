from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt

class LoginPage(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: white;") # スライド1の白背景

        title = QLabel("ログイン画面")
        title.setStyleSheet("font-size: 24px; color: black; font-weight: bold;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ユーザーIDを入力")
        self.id_input.setFixedWidth(200)
        layout.addWidget(self.id_input, alignment=Qt.AlignCenter)

        self.login_btn = QPushButton("ログイン")
        self.login_btn.setFixedWidth(100)
        # 成功時の関数を呼び出す
        self.login_btn.clicked.connect(on_login_success)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)