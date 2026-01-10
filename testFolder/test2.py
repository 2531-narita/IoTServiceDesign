import mediapipe
import os

print("現在のバージョン:", mediapipe.__version__)
print("読み込み元パス:", mediapipe.__file__)

# solutionsフォルダがあるか確認
solutions_path = os.path.join(os.path.dirname(mediapipe.__file__), 'python', 'solutions')
print("solutionsの想定パス:", solutions_path)
print("フォルダは存在するか:", os.path.exists(solutions_path))