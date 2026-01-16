from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        # スライド3, 5の濃い青背景を再現
        self.setStyleSheet("background-color: #1a5276; color: white;")
        layout = QVBoxLayout(self)

        # ヘッダーエリア
        top = QHBoxLayout()
        self.user_label = QLabel("ログインID: ---")
        top.addWidget(self.user_label)
        
        recal_btn = QPushButton("顔再キャリブレーション")
        top.addWidget(recal_btn)
        top.addStretch()
        
        for t in ["現在", "日", "週", "月"]:
            top.addWidget(QPushButton(t))
        layout.addLayout(top)

        # グラフエリア
        graphs = QHBoxLayout()
        graphs.addWidget(self.create_chart("pie")) # 左：円グラフ
        graphs.addWidget(self.create_chart("bar")) # 右：棒グラフ
        layout.addLayout(graphs)

    def create_chart(self, chart_type):
        # グラフの背景もアプリの背景色に合わせる
        fig = Figure(facecolor='#1a5276')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#1a5276')
        
        if chart_type == "pie":
            # 集中・注意散漫・離席の割合
            ax.pie([70, 20, 10], labels=["Focus", "Distract", "Away"], 
                   colors=['#9b59b6', '#2ecc71', '#e67e22'])
        else:
            # 履歴の棒グラフ
            ax.bar(["1/1", "1/2", "1/3", "1/4", "1/5"], [69, 88, 88, 69, 69], color='#3498db')
        
        canvas = FigureCanvas(fig)
        return canvas