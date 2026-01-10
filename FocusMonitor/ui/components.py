"""UI コンポーネント（カメラ表示やグラフなど）の部品を定義する場所

ここではスケルトンのクラスだけ用意します。
"""
from PySide6.QtWidgets import QWidget


class VideoWidget(QWidget):
    """カメラフレームを描画するウィジェットの骨組み"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO: QPainter を使ってフレームを描画する実装を追加


class GraphWidget(QWidget):
    """スコアの時系列グラフを表示するウィジェットの骨組み"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO: matplotlib / pyqtgraph などで実装
