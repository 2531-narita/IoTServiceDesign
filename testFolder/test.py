import cv2
import mediapipe as mp
import time

# Tasks APIのモジュールを読み込み
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# 検出結果を格納する変数を準備
detection_result_list = []

# コールバック関数（AIが分析を終えたら呼ばれる関数）
def result_callback(result, output_image, timestamp_ms):
    detection_result_list.clear()
    detection_result_list.append(result)

# オプション設定
options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='./testFolder/face_landmarker.task'), # モデルファイルのパス
    running_mode=VisionRunningMode.LIVE_STREAM, # Webカメラ用モード
    result_callback=result_callback,            # 結果を受け取る関数
    num_faces=1,                                # 検出する顔の数
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    output_face_blendshapes=True,               # まばたき等の判定に使うブレンドシェイプを出力
    output_facial_transformation_matrixes=True
)

def draw_landmarks_on_image(rgb_image, detection_result):
    """OpenCVを使って顔のランドマークを描画する関数"""
    face_landmarks_list = detection_result.face_landmarks
    
    # 描画用に画像をコピー
    annotated_image = rgb_image.copy()
    annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    # 顔が見つかった場合
    for face_landmarks in face_landmarks_list:
        # 478個の点をすべて描画
        for idx, landmark in enumerate(face_landmarks):
            # 座標をピクセル単位に変換
            x = int(landmark.x * annotated_image.shape[1])
            y = int(landmark.y * annotated_image.shape[0])
            
            # 点を描画 (黄色)
            cv2.circle(annotated_image, (x, y), 1, (0, 255, 255), -1)

    return annotated_image

# メイン処理
def main():
    cap = cv2.VideoCapture(0)
    
    # AIエンジンの起動
    with FaceLandmarker.create_from_options(options) as landmarker:
        print("起動中... 'ESC'キーで終了")
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("カメラ抜き差ししてください")
                break

            # MediaPipe用にRGB変換
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # 現在時刻をミリ秒で計算（LIVE_STREAMモードに必須）
            frame_timestamp_ms = int(time.time() * 1000)
            
            # 推論実行（非同期）
            landmarker.detect_async(mp_image, frame_timestamp_ms)
            
            # 結果があれば描画
            if detection_result_list:
                # 最新の結果を取得
                result = detection_result_list[0]
                # 描画関数を呼び出し
                frame = draw_landmarks_on_image(mp_image.numpy_view(), result)
            else:
                # 結果がまだない場合は元の映像を表示
                pass

            # 画面表示
            cv2.imshow('MediaPipe Tasks Demo', frame)

            # ESCキーで終了
            if cv2.waitKey(5) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()