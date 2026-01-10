"""集中度スコアの計算ロジック

検出結果を受け取り、0.0〜1.0 の集中度スコアを返す関数を定義します。
"""
from common.data_struct import DetectionResult


def calculate_focus_score(result: DetectionResult) -> float:
    """簡易アルゴリズムの例

    - ランドマークがあれば +0.6
    - 目線が中央に近ければ +0.4
    - 最終的に 0.0〜1.0 にクリップ
    """
    score = 0.0
    if result.landmarks_present:
        score += 0.6
    if result.gaze:
        gx, gy = result.gaze
        # 中心 (0.5, 0.5) に近いほど高スコア（簡易的）
        dist = ((gx - 0.5) ** 2 + (gy - 0.5) ** 2) ** 0.5
        score += max(0.0, 0.4 * (1.0 - dist))
    return max(0.0, min(1.0, score))
