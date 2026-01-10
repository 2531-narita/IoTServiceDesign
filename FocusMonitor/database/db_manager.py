"""SQLite を使った簡易データベース管理

用途: 集中度スコアの永続化（保存・読み出し）
"""
import sqlite3
import time
from typing import List
from common.data_struct import FocusScore


class DBManager:
    def __init__(self, db_path: str = "focusmonitor.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS focus_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    score REAL NOT NULL,
                    note TEXT
                )
                """
            )
            conn.commit()

    def save_score(self, score: FocusScore):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO focus_scores (timestamp, score, note) VALUES (?, ?, ?)",
                (score.timestamp, score.score, score.note),
            )
            conn.commit()

    def get_recent(self, limit: int = 100) -> List[FocusScore]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT timestamp, score, note FROM focus_scores ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = c.fetchall()
        return [FocusScore(timestamp=r[0], score=r[1], note=r[2]) for r in rows]
