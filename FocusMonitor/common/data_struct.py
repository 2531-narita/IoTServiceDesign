"""データ構造定義（モジュール間で受け渡す値の型）

重要: ここに書いた型は他モジュールのインターフェースとなるため、安易に変更しないでください。
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime
import numpy as np



@dataclass
class SensingData:
    """センサーから取得した生データ"""
    timestamp: datetime = None
    face_detected: bool = False         # 顔認識の有無
    eye_closedness: float = 0.0         # 両目の閉じ具合の平均値 (0.0〜1.0)
    gaze_angle_yaw: float = 0.0         # 視線の横方向角度 (度)
    gaze_angle_pitch: float = 0.0       # 視線の縦方向角度 (度)
    nose_x: float = 0.0                 # 鼻のX座標
    nose_y: float = 0.0                 # 鼻のY座標

@dataclass
class ScoreData:
    """計算後の集中度データ"""
    timestamp: datetime
    concentration_score: int    # 0-100
    reaving_ratio: int          # 離席率　0-100

@dataclass
class CalibrationData:
    """キャリブレーションによる閾値データ"""
    eye_closedness_threshold: float # 目の閉じ具合の閾値
    gaze_angle_threshold: float     # 画面外視線角度の閾値

@dataclass
class OneSecData:
    """1秒ごとの集計データ"""
    timestamp: datetime
    looking_away_count: int    # 目線が画面外にあったフレーム数 (0-5)
    sleeping_count: int        # 目を閉じていたフレーム数 (0-5)
    no_face_count: int         # 顔認識できなかったフレーム数 (0-5)
    nose_coord_std_ave: float  # 鼻の座標の標準偏差 (顔の動きの激しさ)

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
