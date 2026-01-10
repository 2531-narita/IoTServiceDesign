"""データ構造定義（モジュール間で受け渡す値の型）

重要: ここに書いた型は他モジュールのインターフェースとなるため、安易に変更しないでください。
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime



@dataclass
class SensingData:
    """センサーから取得した生データ"""
    timestamp: datetime
    face_detected: bool
    face_angle_x: float = 0.0  # 顔の向き(左右)
    face_angle_y: float = 0.0  # 顔の向き(上下)
    eye_openness: float = 0.0  # 目の開き具合 (0.0〜1.0)
    gaze_vector: dict = None   # 視線ベクトル

@dataclass
class ScoreData:
    """計算後の集中度データ"""
    timestamp: datetime
    concentration_score: int   # 0-100
    is_sleeping: bool          # 居眠り判定
    is_looking_away: bool      # よそ見判定

# @dataclass
# class Frame:
#     """カメラから取得した生フレーム

#     frame: ndarray（OpenCV 形式を想定）
#     timestamp: float  # 秒のタイムスタンプ
#     """
#     frame: object
#     timestamp: float


# @dataclass
# class DetectionResult:
#     """画像解析の結果をまとめる型

#     - face_bbox: (x, y, w, h)（ノーマライズ or ピクセル）
#     - gaze: Optional[Tuple[float, float]] （x, y で視線方向の推定）
#     - landmarks_present: bool
#     """

#     face_bbox: Optional[Tuple[int, int, int, int]]
#     gaze: Optional[Tuple[float, float]]
#     landmarks_present: bool


# @dataclass
# class FocusScore:
#     timestamp: float
#     score: float  # 0.0 〜 1.0 の範囲
#     note: Optional[str] = None
