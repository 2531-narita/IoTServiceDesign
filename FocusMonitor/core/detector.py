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
            base_options=BaseOptions(model_asset_path='face_landmarker.task'),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=self._result_callback,
            num_faces=1,
            output_face_blendshapes=True
        )
        self.landmarker = FaceLandmarker.create_from_options(options)

    def _result_callback(self, result, output_image, timestamp_ms):
        """AI解析が終わったら自動的に呼ばれる関数"""
        if result.face_blendshapes:
            # データの抽出（Blendshapesを利用）
            blendshapes = result.face_blendshapes[0]
            
            # カテゴリ名からスコアを探すヘルパー関数
            def get_score(name):
                for b in blendshapes:
                    if b.category_name == name:
                        return b.score
                return 0.0

            eye_left = get_score('eyeBlinkLeft') # 0=開, 1=閉
            eye_right = get_score('eyeBlinkRight')
            
            # 顔の向きはTransformation Matrix等から計算が必要だが
            # ここでは簡易的に「鼻の座標」のズレなどを代用するか、
            # 本格的な回転行列計算を実装する（今回は枠組みなので省略）

            #この間に、解析結果（numpy配列の中身）から、画像の顔が
            # ・目が空いているかを瞼の開き具合（0に行くほど開いて、１に行くほど閉じている）から、一定の数値で閉じていると判定
            # ・目線が画面の外にあるか
            # ・鼻の座標
            
            # データを更新（排他制御） ここで定義しているものを最終的にmainにわたるため、ここを変える必要がある
            with self.lock:
                self.latest_data = SensingData(
                    timestamp=datetime.now(),
                    face_detected=True,
                    eye_openness_left=1.0 - eye_left,   # 1.0が開いている状態に変換
                    eye_openness_right=1.0 - eye_right,
                    face_angle_yaw=0.0, # TODO: ロジック実装
                    face_angle_pitch=0.0
                )
        else:
            # 顔が見つからない場合
            with self.lock:
                self.latest_data = SensingData(
                    timestamp=datetime.now(),
                    face_detected=False
                )

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