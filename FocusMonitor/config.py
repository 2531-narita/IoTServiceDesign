"""設定: 閾値や定数をまとめて管理する場所

チーム全員が触ることを想定して、分かりやすく整理してください。
"""
# config.py

# --- カメラ設定 ---
CAMERA_ID = 0  # 内蔵カメラなら0、外付けなら1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# --- 集中度判定の閾値 (ロジック班が調整する場所) ---
# 居眠り判定 (目の開き具合がこれ以下なら閉眼とみなす)
THRESHOLD_EYE_CLOSED = 0.5 

# よそ見判定 (顔の向きがこれ以上ならよそ見とみなす)
THRESHOLD_FACE_YAW = 0.3
THRESHOLD_FACE_PITCH = 0.2

# 減点ルール
SCORE_DEDUCT_LOOKING_AWAY = 1  # よそ見の減点/秒
SCORE_DEDUCT_SLEEPING = 5      # 居眠りの減点/秒