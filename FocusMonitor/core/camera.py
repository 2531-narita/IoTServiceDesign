"""カメラ映像取得モジュール

OpenCV を使ってフレームを読み出す最低限のラッパーを用意しています。
"""
import time

try:
    import cv2
except Exception:
    cv2 = None


class Camera:
    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self.cap = None

    def open(self):
        if cv2 is None:
            raise RuntimeError("OpenCV がインストールされていません。pip install opencv-python を実行してください。")
        self.cap = cv2.VideoCapture(self.device_index)

    def read(self):
        if self.cap is None:
            raise RuntimeError("カメラが開いていません。open() を呼んでください。")
        ret, frame = self.cap.read()
        timestamp = time.time()
        return (ret, frame, timestamp)

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
