"""SQLite を使った簡易データベース管理 (修正版)
main.py の集計ロジックに対応
"""
import sqlite3
from datetime import datetime
# common.data_struct の場所に合わせて調整してください
try:
    from common.data_struct import OneSecData, ScoreData
except ImportError:
    from common.data_struct import OneSecData, ScoreData

class DBManager:
    def __init__(self, db_path: str = "focusmonitor.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """テーブルが存在しない場合に作成する"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # 既存テーブルを確認し、スキーマが変わった場合は再作成
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='score_logs'")
            if c.fetchone():
                # 既存のscore_logsテーブルを確認
                c.execute("PRAGMA table_info(score_logs)")
                columns = [row[1] for row in c.fetchall()]
                if 'reaving_ratio' not in columns:
                    # reaving_ratio列がない場合は古いスキーマ。テーブルを削除して再作成
                    c.execute("DROP TABLE IF EXISTS score_logs")
                    c.execute("DROP TABLE IF EXISTS detail_logs")
            
            # 1秒ごとの集計ログ用テーブル（main.pyの構造に合わせました）
            c.execute("""
                CREATE TABLE IF NOT EXISTS detail_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    looking_away_count INTEGER,
                    sleeping_count INTEGER,
                    no_face_count INTEGER,
                    nose_movement REAL
                )
            """)

            # 1分ごとのスコア用テーブル
            c.execute("""
                CREATE TABLE IF NOT EXISTS score_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    score REAL,
                    reaving_ratio REAL,
                    note TEXT
                )
            """)
            conn.commit()

    def save_detail_log(self, data: OneSecData):
        """1秒ごとの集計データを保存"""
        # main.py から渡される datetime オブジェクトを文字列に変換
        ts_str = data.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
        
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO detail_logs (
                    timestamp, 
                    looking_away_count, 
                    sleeping_count, 
                    no_face_count, 
                    nose_movement
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                ts_str,
                data.looking_away_count,
                data.sleeping_count,
                data.no_face_count,
                data.nose_coord_std_ave
            ))
            conn.commit()

    def save_score_log(self, data: ScoreData):
        """1分ごとのスコアを保存"""
        print(f"\n[DB Save] Score: {data.concentration_score}")
        
        # data.timestamp が datetime型か float型かで処理を分ける（念のため）
        if isinstance(data.timestamp, datetime):
            ts_str = data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            ts_str = str(data.timestamp)

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO score_logs (timestamp, score, reaving_ratio, note) 
                VALUES (?, ?, ?, ?)
            """, (
                ts_str, 
                data.concentration_score,
                data.reaving_ratio,
                "" # note
            ))
            conn.commit()

    # 分析用メソッド
    def get_recent_details(self, limit: int = 100):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM detail_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in c.fetchall()]

    def get_recent_scores(self, limit: int = 100):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM score_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in c.fetchall()]