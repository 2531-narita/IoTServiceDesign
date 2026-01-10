# main.py (骨組み)
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer

# 本来は別ファイルのクラスをimportするが、ここではイメージのためダミー定義
class MockDetector:
    """AI解析班が作るクラスのダミー"""
    def get_sensing_data(self):
        # 本当はここでMediaPipeが動く
        return {"face": True, "eye": 0.8}

class MockCalculator:
    """ロジック班が作るクラスのダミー"""
    def calculate_score(self, sensing_data):
        # 本当はここで減点ロジックが動く
        return 95  # 適当なスコア

class MainWindow(QMainWindow):
    """UI班が作る画面のダミー"""
    def __init__(self):
        super().__init__()
        self.label = QLabel("待機中...")
        self.setCentralWidget(self.label)

    def update_display(self, score):
        self.label.setText(f"現在の集中度: {score}")

# --- メイン処理 ---
def main():
    app = QApplication(sys.argv)
    
    # 1. 各機能のインスタンス化
    window = MainWindow()
    detector = MockDetector()
    calculator = MockCalculator()
    
    window.show()

    # 2. 定期実行のループ (例えば1秒に5回 = 200msごと)
    def main_loop():
        # A. データ取得 (AI班の仕事)
        data = detector.get_sensing_data()
        
        # B. スコア計算 (ロジック班の仕事)
        score = calculator.calculate_score(data)
        
        # C. 画面更新 (UI班の仕事)
        window.update_display(score)
        
        # D. DB保存 (DB班の仕事 / 今回は省略)
        # db.save(score)

    # タイマーでループを回す
    timer = QTimer()
    timer.timeout.connect(main_loop)
    timer.start(200) # 200ミリ秒ごとに実行

    sys.exit(app.exec())

if __name__ == "__main__":
    main()