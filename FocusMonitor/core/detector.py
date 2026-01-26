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
        self.latest_frame = None  # 最新フレーム（表示用）
        self.latest_landmarks = None  # 最新ランドマーク（表示用）
        self.lock = threading.Lock() # データの読み書き衝突防止
        
        # 視線角度変換の仮パラメータ
        self.EYE_MAX_YAW_DEG = 30.0
        self.EYE_MAX_PITCH_DEG = 20.0

        # 直近のblendshapes保持（視線角度計算用）
        self._last_blendshapes = None

        # MediaPipe設定
        self._init_mediapipe()
        
        # カメラ設定
        self.cap = cv2.VideoCapture(CAMERA_ID)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    def _init_mediapipe(self):
        """MediaPipe Tasks APIの初期化 (IMAGE モード)"""
        BaseOptions = mp.tasks.BaseOptions
        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path='./FocusMonitor/core/face_landmarker.task'),
            running_mode=VisionRunningMode.IMAGE,
            num_faces=1,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
        )
        self.landmarker = FaceLandmarker.create_from_options(options)

    def _analyze_result(self, result):
        """AI解析結果を処理 (IMAGE モード用)"""
        if result.face_blendshapes and result.face_landmarks:
            # データの抽出（Blendshapesとlandmarksを利用）
            blendshapes = result.face_blendshapes[0]
            landmarkers = result.face_landmarks[0]

            self._last_blendshapes = blendshapes
            
            # ランドマーク情報を保存（表示用）
            with self.lock:
                self.latest_landmarks = landmarkers
            
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
                self.latest_landmarks = None
    
    def _calculate_gaze_angle(self):
        """視線角度の計算（yaw=左右, pitch=上下）
        Blendshapes（eyeLook*）を使って角度に変換して返す。
        """
        blendshapes = getattr(self, "_last_blendshapes", None)
        if blendshapes is None:
            return 0.0, 0.0

        def get_score(name: str) -> float:
            for b in blendshapes:
                if getattr(b, "category_name", None) == name:
                    return float(getattr(b, "score", 0.0))
            return 0.0

        # 左右（yaw）: out - in（両目平均）
        left_out = get_score("eyeLookOutLeft")
        left_in = get_score("eyeLookInLeft")
        right_out = get_score("eyeLookOutRight")
        right_in = get_score("eyeLookInRight")
        eye_lr = ((left_out - left_in) + (right_out - right_in)) / 2.0

        # 上下（pitch）: up - down（両目平均）
        left_up = get_score("eyeLookUpLeft")
        left_down = get_score("eyeLookDownLeft")
        right_up = get_score("eyeLookUpRight")
        right_down = get_score("eyeLookDownRight")
        eye_ud = ((left_up - left_down) + (right_up - right_down)) / 2.0

        yaw_deg = eye_lr * self.EYE_MAX_YAW_DEG
        pitch_deg = eye_ud * self.EYE_MAX_PITCH_DEG

        return float(yaw_deg), float(pitch_deg)

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

            # フレームをデータと一緒に保存（表示用）
            with self.lock:
                self.latest_frame = frame.copy()

            # 画像をAIに渡す (IMAGE モード：同期処理)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = self.landmarker.detect(mp_image)
            self._analyze_result(result)
            
            # 負荷調整（PCスペックに合わせて調整）
            time.sleep(0.03) 

    def get_current_data(self) -> SensingData:
        """外部（UIやロジック）から最新データを取得するためのメソッド"""
        with self.lock:
            return self.latest_data
    
    def get_latest_frame(self):
        """最新フレーム（顔表示用）を取得するためのメソッド"""
        with self.lock:
            return self.latest_frame
    
    def get_latest_landmarks(self):
        """最新ランドマーク（描画用）を取得するためのメソッド"""
        with self.lock:
            return self.latest_landmarks
            
    def stop(self):
        """detectorのループを安全に停止し、スレッドの終了を待つ"""
        print("Detector: ループを停止しています...")
        self.running = False
        
        # スレッドが実行中の場合、その終了を待つ
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2.0)  # 最大2秒待機
            print("Detector: スレッドの終了を確認しました")
        
        # カメラをリリース
        if self.cap.isOpened():
            self.cap.release()
            print("Detector: カメラをリリースしました")