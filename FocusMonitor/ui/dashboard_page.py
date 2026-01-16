from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# 日本語フォントの設定（Windows用）
plt.rcParams['font.family'] = 'MS Gothic' 

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1a5276; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ヘッダーエリア
        header = QHBoxLayout()
        self.user_label = QLabel("ログインID: ---")
        self.user_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(self.user_label)
        
        # 目立つオレンジ色のボタン
        self.recal_btn = QPushButton("顔再キャリブレーション")
        self.recal_btn.setStyleSheet("""
            QPushButton { background-color: #e67e22; color: white; padding: 8px 15px; 
                          border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #d35400; }
        """)
        header.addWidget(self.recal_btn)
        header.addStretch()
        
        for t in ["現在", "日", "週", "月"]:
            btn = QPushButton(t)
            btn.setFixedWidth(60)
            btn.setStyleSheet("background-color: #34495e; color: white; padding: 5px;")
            header.addWidget(btn)
        layout.addLayout(header)

        # グラフエリア
        graphs = QHBoxLayout()
        self.pie_canvas = self.create_chart("pie")
        self.bar_canvas = self.create_chart("bar")
        graphs.addWidget(self.pie_canvas)
        graphs.addWidget(self.bar_canvas)
        layout.addLayout(graphs)

    def create_chart(self, chart_type):
        fig = Figure(figsize=(5, 4), facecolor='#1a5276')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a5276')
        ax.tick_params(colors='white')

        if chart_type == "pie":
            # 集中度割合
            ax.pie([70, 20, 10], labels=["集中", "注意散漫", "離席"], 
                   textprops={'color':"white"}, colors=['#9b59b6', '#2ecc71', '#f1c40f'])
            ax.set_title("集中度の内訳", color='white', fontsize=12)
        else:
            # スコア履歴
            ax.bar(["1/1", "1/2", "1/3", "1/4", "1/5"], [69, 88, 88, 69, 69], color='#3498db')
            ax.set_title("集中度スコアの推移", color='white', fontsize=12)
        
        return FigureCanvas(fig)