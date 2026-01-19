"""画像解析（MediaPipe 等で顔・ランドマークなどを検出する想定）

ここではインターフェースの骨組みだけ用意しています。実装時には MediaPipe のモデルを読み込み、`analyze` を実装してください。
"""
# core/detector.py
import time
import cv2
import mediapipe as mp
import threading
from datetime import datetime

# 自作モジュールのインポート
from common.data_struct import SensingData
from config import CAMERA_ID, FRAME_WIDTH, FRAME_HEIGHT

class FaceDetector:
    def __init__(self):
        self.running = False
        self.latest_data = SensingData(timestamp=datetime.now())
        self.lock = threading.Lock() # データの読み書き衝突防止
        
        # MediaPipe設定
        self._init_mediapipe()
        
        # カメラ設定
        self.cap = cv2.VideoCapture(CAMERA_ID)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    def _init_mediapipe(self):
        """MediaPipe Tasks APIの初期化"""
        BaseOptions = mp.tasks.BaseOptions
        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path='./FocusMonitor/core/face_landmarker.task'),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=self._result_callback,
            num_faces=1,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
        )
        self.landmarker = FaceLandmarker.create_from_options(options)

    def _result_callback(self, result, output_image, timestamp_ms):
        """AI解析が終わったら自動的に呼ばれる関数"""
        if result.face_blendshapes and result.face_landmarks:
            # データの抽出（Blendshapesとlandmarksを利用）
            blendshapes = result.face_blendshapes[0]
            landmarkers = result.face_landmarks[0]
            
            # カテゴリ名からスコアを探すヘルパー関数
            def get_score(name):
                for b in blendshapes:
                    if b.category_name == name:
                        return b.score
                return 0.0

            # 両目の閉じ具合の平均 (0.0〜1.0)
            eye_closedness_ave = (get_score('eyeBlinkLeft') + get_score('eyeBlinkRight')) / 2.0

            # 視線角度(上下, 左右)
            gaze_yaw, gaze_pitch = self._calculate_gaze_angle()

            # 鼻の座標
            nose_coord_x, nose_coord_y = landmarkers[4].x, landmarkers[4].y

            # データを更新（排他制御） 
            with self.lock:
                self.latest_data = SensingData(
                    timestamp=datetime.now(),
                    face_detected=True,                     # 顔認識の有無
                    eye_closedness = eye_closedness_ave,    # 両目の閉じ具合の平均値 (0.0〜1.0)
                    gaze_angle_yaw = gaze_yaw,              # 視線の横方向角度 (度)
                    gaze_angle_pitch = gaze_pitch,          # 視線の縦方向角度 (度)
                    nose_x = nose_coord_x,                  # 鼻のX座標
                    nose_y = nose_coord_y,                  # 鼻のY座標
                )
        else:
            # 顔が見つからない場合
            with self.lock:
                self.latest_data = SensingData(
                    timestamp=datetime.now(),
                    face_detected=False
                )
    
    def _calculate_gaze_angle(self):
        """視線角度の計算（未実装）
        demo_looking_away.pyを参考に、上下の角度計算も追加したものを実装してください。
        返すのは yaw（左右）と pitch（上下）の2つの視線角度。
        """
        return 0,0

    def start(self):
        """解析ループを別スレッドで開始"""
        self.running = True
        self.thread = threading.Thread(target=self._process_loop)
        self.thread.daemon = True
        self.thread.start()

    def _process_loop(self):
        while self.running and self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.1)
                continue

            # 画像をAIに渡す
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            timestamp_ms = int(time.time() * 1000)
            self.landmarker.detect_async(mp_image, timestamp_ms)
            
            # 負荷調整（PCスペックに合わせて調整）
            time.sleep(0.03) 

    def get_current_data(self) -> SensingData:
        """外部（UIやロジック）から最新データを取得するためのメソッド"""
        with self.lock:
            return self.latest_data
            
    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()