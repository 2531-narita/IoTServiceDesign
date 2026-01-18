import cv2
import mediapipe as mp
import numpy as np
import time

# --- 設定 ---
MODEL_PATH = './testFolder/face_landmarker.task'

# 判定の厳しさ設定
THRESHOLD_GAZE_ANGLE = 25.0  # 最終的な視線が正面から何ズレたらアウトか（度）
EYE_MOVEMENT_GAIN = 40.0     # 目の動き(0~1)を角度に換算する係数（個人差あり、30~50くらい）

# --- MediaPipeの準備 ---
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

FONT = cv2.FONT_HERSHEY_SIMPLEX

class GazeCorrectionDemo:
    def __init__(self):
        self.result = None
        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=self.update_result,
            num_faces=1,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True
        )
        self.landmarker = FaceLandmarker.create_from_options(options)

    def update_result(self, result, output_image, timestamp_ms):
        self.result = result

    def calculate_head_yaw(self, matrix):
        """顔の向き(Yaw)だけを計算"""
        r31, r32, r33 = matrix[2, 0], matrix[2, 1], matrix[2, 2]
        # Yaw: Y軸回転 (左右)
        yaw = np.degrees(np.arctan2(-r31, np.sqrt(r32**2 + r33**2)))
        return yaw

    def run(self):
        cap = cv2.VideoCapture(0)
        print("開始します... 'ESC'キーで終了")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            # 鏡のように反転
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            self.landmarker.detect_async(mp_image, int(time.time() * 1000))

            if self.result and self.result.face_blendshapes:
                # 1. 顔の角度 (Head Yaw)
                head_yaw = 0.0
                if self.result.facial_transformation_matrixes:
                    matrix = np.array(self.result.facial_transformation_matrixes[0])
                    head_yaw = self.calculate_head_yaw(matrix)

                # 2. 目の動き (Eye Offset)
                blendshapes = self.result.face_blendshapes[0]
                def get_bs(name):
                    return next((b.score for b in blendshapes if b.category_name == name), 0.0)

                # 左方向を見る動き (LookOutLeft + LookInRight)
                # ※ LookInは鼻側、LookOutは耳側
                # 自分から見て左＝左目はOut、右目はIn
                look_left_score = (get_bs('eyeLookOutLeft') + get_bs('eyeLookInRight')) / 2.0
                
                # 右方向を見る動き
                look_right_score = (get_bs('eyeLookInLeft') + get_bs('eyeLookOutRight')) / 2.0

                # 目の相対位置 (-1.0:左 〜 +1.0:右)
                eye_relative_pos = look_right_score - look_left_score
                
                # 目の角度に換算 (例: 0.5 * 40度 = 20度右を向いている)
                eye_angle_correction = eye_relative_pos * EYE_MOVEMENT_GAIN

                # 3. 最終的な視線角度 (顔 + 目)
                # 注意: MediaPipeの座標系やflipによって符号(+/-)が逆になることがあります。
                # 実際に動かして、「顔を右に向け、目を左に向けた」ときに total_angle が 0 に近づくよう、
                # 足すか引くかを調整してください。今回は「足し算」で相殺されると仮定します。
                total_gaze_angle = head_yaw - eye_angle_correction

                # --- 判定 ---
                is_looking_away = abs(total_gaze_angle) > THRESHOLD_GAZE_ANGLE
                
                # --- 描画 ---
                color = (0, 0, 255) if is_looking_away else (0, 255, 0)
                status = "LOOKING AWAY" if is_looking_away else "FOCUSED"
                
                cv2.rectangle(frame, (0, 0), (w, h), color, 10 if is_looking_away else 2)
                
                # 情報表示
                cv2.putText(frame, f"STATUS: {status}", (30, 50), FONT, 1.2, color, 3)
                
                # 数値デバッグ（ここを見ながら係数を調整します）
                info_x = 30
                cv2.putText(frame, f"Head Yaw: {head_yaw:.1f}", (info_x, 100), FONT, 0.7, (255,255,255), 2)
                cv2.putText(frame, f"Eye Corr: {eye_angle_correction:.1f}", (info_x, 130), FONT, 0.7, (200,200,200), 2)
                cv2.putText(frame, f"Total   : {total_gaze_angle:.1f}", (info_x, 170), FONT, 1.0, (0,255,255), 2)

                # ガイドライン
                cv2.line(frame, (w//2, 0), (w//2, h), (100,100,100), 1)

            cv2.imshow('Gaze Correction Logic', frame)
            if cv2.waitKey(5) & 0xFF == 27: break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    demo = GazeCorrectionDemo()
    demo.run()