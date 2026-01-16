from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt

class LoginPage(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        # スライド1の白背景を再現
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("ログイン画面")
        title.setStyleSheet("font-size: 32px; color: black; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ログインID(例:間々田)")
        self.id_input.setFixedWidth(250)
        self.id_input.setStyleSheet("color: black; padding: 5px;")
        layout.addWidget(self.id_input, alignment=Qt.AlignCenter)

        self.login_btn = QPushButton("ログイン")
        self.login_btn.setFixedWidth(120)
        self.login_btn.setStyleSheet("padding: 8px;")
        self.login_btn.clicked.connect(on_login_success)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)