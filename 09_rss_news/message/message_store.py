"""消息存储：SQLite - 支持会话管理"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class MessageStore:
    """消息存储：SQLite"""

    def __init__(self, db_path: str = "messages.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT DEFAULT 'default'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_created 
                ON messages(session_id, created_at)
            """)

    def add(self, role: str, content: str, session_id: str = "default"):
        """添加消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (role, content, session_id) VALUES (?, ?, ?)",
                (role, content, session_id),
            )

    def get_recent(self, limit: int = 20, session_id: str = "default") -> list[dict]:
        """获取最近的 N 条消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT role, content 
                FROM messages 
                WHERE session_id = ?
                ORDER BY id DESC 
                LIMIT ?
            """,
                (session_id, limit),
            )
            rows = cursor.fetchall()
            return [
                {"role": r["role"], "content": r["content"]} for r in reversed(rows)
            ]

    def get_all(self, session_id: str = "default") -> list[dict]:
        """获取会话的所有消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT role, content 
                FROM messages 
                WHERE session_id = ?
                ORDER BY id ASC
            """,
                (session_id,),
            )
            return [{"role": r["role"], "content": r["content"]} for r in cursor]

    def count(self, session_id: str = "default") -> int:
        """统计消息数量"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)
            )
            return cursor.fetchone()[0]

    def list_sessions(self) -> list[dict]:
        """列出所有会话及其消息数量"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT session_id, COUNT(*) as msg_count, MAX(created_at) as last_active
                FROM messages 
                GROUP BY session_id 
                ORDER BY last_active DESC
            """)
            return [
                {
                    "session_id": r["session_id"],
                    "msg_count": r["msg_count"],
                    "last_active": r["last_active"],
                }
                for r in cursor
            ]

    def clear(self, session_id: str = "default"):
        """清空会话消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
