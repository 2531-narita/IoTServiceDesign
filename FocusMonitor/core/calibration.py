import numpy as np
from common.data_struct import CalibrationData, SensingData

class Calibration:
    def __init__(self):
        self.collected_data = [] # データ保存用リスト
        self.required_samples = 50

    def start(self):
        """キャリブレーション開始前の初期化"""
        self.collected_data = []
        print("キャリブレーションを開始します")

    def add_data(self, sensing_data: SensingData) -> bool:
        """
        データを1つ追加する。
        戻り値: 完了したら True, まだなら False
        """
        if sensing_data.face_detected:
            self.collected_data.append(sensing_data)

            print(f"Calib progress: {len(self.collected_data)}/{self.required_samples}")
        
        # データが溜まったかチェック
        return len(self.collected_data) >= self.required_samples

    def calculate(self) -> CalibrationData:
        """溜まったデータから計算を行う"""
        if not self.collected_data:
            return None # データがない場合

        # 目の閉じ具合
        # ※ eye_closedness が SensingData にある前提
        eye_vals = [d.eye_closedness for d in self.collected_data]
        eye_closedness_ave = np.mean(eye_vals)

        # 視線角度 (Yaw/Pitch)
        yaw_vals = [d.gaze_angle_yaw for d in self.collected_data]
        pitch_vals = [d.gaze_angle_pitch for d in self.collected_data]

        yaw_max = np.max(yaw_vals)
        yaw_min = np.min(yaw_vals)
        pitch_max = np.max(pitch_vals)
        pitch_min = np.min(pitch_vals)

        # 閾値計算
        # 目の閾値: 平均値と「完全に閉じた状態(1.0)」の中間など、ロジックに合わせて調整
        # ここでは前のコードのロジックを踏襲
        eye_th = eye_closedness_ave + (1.0 - eye_closedness_ave) / 3
        
        # 角度の閾値: 最大と最小の振れ幅の半分
        yaw_th = (yaw_max - yaw_min) / 2
        pitch_th = (pitch_max - pitch_min) / 2

        return CalibrationData(
            eye_closedness_threshold=eye_th,
            gaze_angle_yaw_threshold=yaw_th,
            gaze_angle_pitch_threshold=pitch_th
        )