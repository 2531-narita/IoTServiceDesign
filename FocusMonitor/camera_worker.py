import cv2
import time
import mediapipe as mp
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

class CameraWorker(QThread):
    # numpyの画像ではなく、Qtで表示できるQImageを直接送る
    image_data = Signal(QImage)
    finished = Signal()

    def run(self):
        # パスを絶対パスにするのが一番確実です
        model_path = 'testFolder/face_landmarker.task' 

        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO)

        with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
            cap = cv2.VideoCapture(0)
            start_time = time.time()
            
            while (time.time() - start_time) < 10:
                ret, frame = cap.read()
                if not ret: break

                # MediaPipe解析
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = landmarker.detect_for_video(mp_image, int(time.time() * 1000))

                # ランドマーク描画 (黄色い点)
                if result.face_landmarks:
                    for landmarks in result.face_landmarks:
                        for lm in landmarks:
                            ih, iw, _ = frame.shape
                            cv2.circle(frame, (int(lm.x * iw), int(lm.y * ih)), 1, (0, 255, 255), -1)

                # OpenCVのBGR画像をQt用のRGB画像に変換
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                
                # GUIスレッドに映像を送信
                self.image_data.emit(qt_img)
                time.sleep(0.01)
            
            cap.release()
            self.finished.emit()