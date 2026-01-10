"""画像解析（MediaPipe 等で顔・ランドマークなどを検出する想定）

ここではインターフェースの骨組みだけ用意しています。実装時には MediaPipe のモデルを読み込み、`analyze` を実装してください。
"""
from typing import Optional
from common.data_struct import DetectionResult


class Detector:
    def __init__(self, conf_threshold: float = 0.5):
        self.conf_threshold = conf_threshold
        # TODO: MediaPipe のセットアップ

    def analyze(self, frame) -> DetectionResult:
        """フレームを解析して DetectionResult を返すダミー実装"""
        # TODO: ここで実際の検出処理を行う
        return DetectionResult(face_bbox=None, gaze=None, landmarks_present=False)
