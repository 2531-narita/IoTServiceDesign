import sys
import time
import numpy as np

from core.detector import FaceDetector
from common.data_struct import CalibrationData, SensingData

class Calibration:
    def __init__(self):
        
        pass

    def get_calibration_data(self) -> CalibrationData:
        
        select_sensing_data = []

        while(select_sensing_data >= 10):

            sensingData:SensingData = FaceDetector.get_current_data()

            select_sensing_data.append([sensingData.face_detected, sensingData.eye_closedness, sensingData.gaze_angle_yaw, sensingData.gaze_angle_pitch])

            time.sleep(0.20)

        # 目の閉じ具合の平均
        eye_closedness_ave = np.mean([d.eye_closedness for d in select_sensing_data])

        # 視線角度のそれぞれの最大値
        gaze_angle_max_and_min = [3]    # 0:横方向の最大角度 1:横方向の最小角度 2:縦方向の最大角度 3:縦方向の最小角度
        gaze_angle_max_and_min[0] = np.max([d.gaze_angle_yaw for d in select_sensing_data])
        gaze_angle_max_and_min[1] = np.min([d.gaze_angle_yaw for d in select_sensing_data])
        gaze_angle_max_and_min[2] = np.max([d.gaze_angle_pitch for d in select_sensing_data])
        gaze_angle_max_and_min[3] = np.min([d.gaze_angle_pitch for d in select_sensing_data])

        # 目の閉じ具合の平均から閾値を算出
        

        return