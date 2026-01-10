"""設定: 閾値や定数をまとめて管理する場所

チーム全員が触ることを想定して、分かりやすく整理してください。
"""
# カメラ
FRAME_RATE = 30
CAMERA_DEVICE_INDEX = 0

# 検出器
DETECTION_CONF_THRESHOLD = 0.5

# 集中度判定
ATTENTION_SCORE_THRESHOLD = 0.6  # 0..1 のスコアで閾値を設定

# データベース
DB_PATH = "focusmonitor.db"
