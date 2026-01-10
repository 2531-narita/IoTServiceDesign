import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QLabel, QPushButton, QMessageBox)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- ウィンドウの基本設定 ---
        self.setWindowTitle("G-4B 集中度モニター - PySide6")
        self.resize(500, 350)   

        # メインのウィジェット（土台）を作成
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # レイアウト（縦並び）を作成
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignCenter) # 中央寄せ

        # --- パーツの配置 ---
        
        # 1. タイトルラベル
        self.label_title = QLabel("システム正常動作中")
        # CSSのようなスタイルシートでデザイン設定が可能
        self.label_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_title)

        # 2. サブテキスト
        self.label_info = QLabel("PySide6 の読み込みに成功しました。\nボタンを押して動作を確認してください。")
        self.label_info.setStyleSheet("font-size: 14px; margin: 10px;")
        self.label_info.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_info)

        # 3. アクションボタン
        self.btn_action = QPushButton("クリックしてテスト")
        self.btn_action.setFixedSize(200, 50)
        self.btn_action.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
        """)
        # ボタンクリック時の動作を登録（シグナル・スロット）
        self.btn_action.clicked.connect(self.button_callback)
        self.layout.addWidget(self.btn_action)

        # カウント用変数
        self.count = 0

    def button_callback(self):
        """ボタンが押されたときの処理"""
        self.count += 1
        self.label_info.setText(f"ボタンが {self.count} 回クリックされました！\n描画更新も正常です。")
        print(f"Click Log: {self.count}")
        
        # 5回押したらポップアップを出してみるテスト
        if self.count == 5:
            QMessageBox.information(self, "通知", "5回クリックされました。\nポップアップ機能も正常です。")

def main():
    # アプリケーションの作成
    app = QApplication(sys.argv)

    # ウィンドウの作成と表示
    window = MainWindow()
    window.show()

    # アプリケーションの実行ループ
    sys.exit(app.exec())

if __name__ == "__main__":
    main()