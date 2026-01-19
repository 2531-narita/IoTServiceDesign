"""集中度スコアの計算ロジック

検出結果を受け取り、集中度スコア（0~100）と離席率（0~100）を返す関数を定義します。
"""
from common.data_struct import ScoreData
from datetime import datetime
import config

class Calculator:
    def __init__(self):



        pass

    def calculate_score(self, data) -> ScoreData:
        """
        １分間分のデータからスコアと離席率を計算して返す関数
        configから減点方式に使用する定数をもってきて、使う
        """

        return 

### 以下は例
    def calculate(self, one_minute_data: list) -> ScoreData:
        """
        1分間のデータリストを受け取り、減点方式でスコアを計算する
        one_minute_data: 1秒ごとの集計辞書のリスト
        """
        # TODO: ここに要件定義書の「減点ロジック」を実装する
        # 仮の実装：ランダムではなく、データに基づいた計算の枠組み
        current_score = 100
        
        # 例: よそ見秒数の合計
        total_looking_away = sum(d['looking_away_count'] for d in one_minute_data)
        # 5秒(25フレーム)以上よそ見してたら減点...などのロジック記述
        if total_looking_away > 25: 
            current_score -= 10

        return ScoreData(
            timestamp=datetime.now(),
            concentration_score=max(0, current_score), # 0未満にはしない
            message="集中できています" if current_score > 80 else "休憩しましょう"
        )


    # def compute_score(self, result: DetectionResult) -> float:
    #     """集中度スコアを計算するメソッドの例"""
    #     return calculate_focus_score(result)


    # def calculate_focus_score(result: DetectionResult) -> float:
    #     """簡易アルゴリズムの例

    #     - ランドマークがあれば +0.6
    #     - 目線が中央に近ければ +0.4
    #     - 最終的に 0.0〜1.0 にクリップ
    #     """
    #     score = 0.0
    #     if result.landmarks_present:
    #         score += 0.6
    #     if result.gaze:
    #         gx, gy = result.gaze
    #         # 中心 (0.5, 0.5) に近いほど高スコア（簡易的）
    #         dist = ((gx - 0.5) ** 2 + (gy - 0.5) ** 2) ** 0.5
    #         score += max(0.0, 0.4 * (1.0 - dist))
    #     return max(0.0, min(1.0, score))
