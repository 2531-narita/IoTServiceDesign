from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt

class LoginPage(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("集中度モニタリング")
        title.setStyleSheet("font-size: 32px; color: #1a5276; font-weight: bold;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ユーザーIDを入力してください")
        self.id_input.setFixedWidth(280)
        self.id_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; color: black;")
        layout.addWidget(self.id_input, alignment=Qt.AlignCenter)

        self.login_btn = QPushButton("ログイン")
        self.login_btn.setFixedWidth(280)
        self.login_btn.setStyleSheet("""
            QPushButton { background-color: #1a5276; color: white; padding: 12px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #2471a3; }
        """)
        self.login_btn.clicked.connect(on_login_success)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)