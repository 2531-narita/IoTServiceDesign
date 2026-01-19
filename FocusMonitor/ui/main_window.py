"""PySide6 を使ったメインウィンドウの最小実装

実装はシンプルなプレースホルダを提供します。適宜拡張してください。
"""
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from main import MainApp

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusMonitor")
        self._init_ui()

    def _init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("FocusMonitor — メイン画面"))
        layout.addWidget(QLabel("ここにカメラ映像やスコアを表示します。"))

        btn_start = QPushButton("Start")
        btn_stop = QPushButton("Stop")
        btn_start.clicked.connect(MainApp.loop_start())
        btn_start.clicked.connect(MainApp.loop_stop())
        layout.addWidget(btn_start)
        layout.addWidget(btn_stop)

        central.setLayout(layout)
        self.setCentralWidget(central)
