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
        
        data: list[OneSecData] （1秒ごとの集計が並んでいる想定）
        実装ルール（仕様）:
        - ベーススコアは100
        - よそ見：10秒を超えたら超過秒数分だけ減点（config.SCORE_DEDUCT_LOOKING_AWAY／秒）
        - 居眠り：連続で10秒以上閉眼していたら，10秒を超えた分を減点（config.SCORE_DEDUCT_SLEEPING／秒）
        - 不安定：5秒ウィンドウの鼻座標stdの平均が閾値を超える場合、そのウィンドウ内の秒を不安定として減点（ローカル定数で調整）
        - 不在：1秒（no_face_count==5）以上連続があった場合は不在秒とみなすが，離席率の集計では「no_face_count==5 が連続した場合のみ」集計（単発1秒は除外）
          不在による減点は「基準点（減点前の100点）×不在割合」で計算して最初に差し引く
        """
        # early exit
        if not data:
            return ScoreData(timestamp=datetime.now(), concentration_score=100, reaving_ratio=0)

        total_seconds = len(data)
        baseline = 100

        # ローカル閾値・パラメータ（必要に応じて調整）
        LOOKING_AWAY_FRAME_THRESH = 3      # 1秒あたりのフレーム中、これ以上ならその秒を「よそ見」とみなす
        SLEEPING_FRAME_THRESH = 3          # 1秒あたりのフレーム中、これ以上ならその秒を「閉眼」とみなす
        MIN_LOOKING_AWAY_SECONDS = 10      # この秒数を超えたら減点開始
        MIN_SLEEPING_CONSECUTIVE = 10      # 連続秒数がこれを超えたら減点開始
        NOSE_STD_THRESHOLD = 0.015         # 鼻の座標std平均の閾値（不安定判定）
        UNSTABLE_DEDUCT_PER_SEC = 1        # 不安定の減点／秒（ローカル定数）
        # 離席率集計時に、no_face_count==5 が何秒以上連続した場合にカウントするか
        MIN_CONSECUTIVE_ABSENT_SECONDS_FOR_COUNT = 2

        # 1 よそ見秒数（閾値以上のフレームがあった秒を1秒としてカウント）
        looking_away_seconds = sum(1 for s in data if getattr(s, 'looking_away_count', 0) >= LOOKING_AWAY_FRAME_THRESH)
        looking_away_deduction = 0
        if looking_away_seconds > MIN_LOOKING_AWAY_SECONDS:
            extra = looking_away_seconds - MIN_LOOKING_AWAY_SECONDS
            looking_away_deduction = extra * getattr(config, 'SCORE_DEDUCT_LOOKING_AWAY', 1)

        # 2 居眠り（連続閉眼秒数を判定し、10秒超過分を減点）
        sleeping_consec = 0
        extra_sleep_seconds = 0
        for s in data:
            if getattr(s, 'sleeping_count', 0) >= SLEEPING_FRAME_THRESH:
                sleeping_consec += 1
                if sleeping_consec > MIN_SLEEPING_CONSECUTIVE:
                    extra_sleep_seconds += 1
            else:
                sleeping_consec = 0
        sleeping_deduction = extra_sleep_seconds * getattr(config, 'SCORE_DEDUCT_SLEEPING', 5)

        # 3 不安定（5秒ウィンドウの平均stdで判定）
        unstable_flags = [False] * total_seconds
        for i in range(0, max(0, total_seconds - 4)):
            window = data[i:i+5]
            avg_std = sum(getattr(w, 'nose_coord_std_ave', 0.0) for w in window) / 5.0
            if avg_std > NOSE_STD_THRESHOLD:
                for j in range(i, i+5):
                    unstable_flags[j] = True
        unstable_seconds = sum(1 for f in unstable_flags if f)
        unstable_deduction = unstable_seconds * UNSTABLE_DEDUCT_PER_SEC

        # 4 不在判定（1秒＝no_face_count==5 の秒を不在とみなす）
        absent_flags = [getattr(s, 'no_face_count', 0) >= 5 for s in data]
        # 離席率集計では単発1秒のみの不在は除外する（要件）
        counted_absent_seconds = 0
        i = 0
        while i < total_seconds:
            if absent_flags[i]:
                j = i
                while j < total_seconds and absent_flags[j]:
                    j += 1
                run_len = j - i
                if run_len >= MIN_CONSECUTIVE_ABSENT_SECONDS_FOR_COUNT:
                    counted_absent_seconds += run_len
                i = j
            else:
                i += 1

        reaving_ratio = int(round((counted_absent_seconds / total_seconds) * 100))

        # 不在による減点は「基準点（減点前の100点）×不在割合」で計算（仕様）
        absent_deduction = int(round(baseline * (reaving_ratio / 100.0)))

        # 最終スコア算出（基準点 - 不在減点 - その他の減点）
        score = baseline - absent_deduction - looking_away_deduction - sleeping_deduction - unstable_deduction
        score = max(0, min(100, int(round(score))))

        return ScoreData(
            timestamp=datetime.now(),
            concentration_score=score,
            reaving_ratio=reaving_ratio
        )

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
