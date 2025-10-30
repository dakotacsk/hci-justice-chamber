# justice_agents/memory.py
import sqlite3
import time
from typing import List, Dict

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  agent TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_session_time
  ON messages(session_id, created_at);
"""

class ChatMemory:
    """SQLite-backed memory (~30-minute rolling window)."""
    def __init__(self, db_path="./justice_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.executescript(_SCHEMA)
        self.conn.commit()
        self.clear_all()

    def clear_all(self):
        """Clears all messages from the database."""
        self.conn.execute("DELETE FROM messages")
        self.conn.commit()

    def add(self, session_id: str, agent: str, role: str, content: str):
        self.conn.execute(
            "INSERT INTO messages (session_id, agent, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, agent, role, content, time.time()),
        )
        self.conn.commit()

    def get_recent(self, session_id: str, minutes: int = 30) -> List[Dict[str, str]]:
        cutoff = time.time() - minutes * 60
        rows = self.conn.execute(
            """SELECT agent, role, content FROM messages
               WHERE session_id = ? AND created_at >= ?
               ORDER BY created_at ASC""",
            (session_id, cutoff),
        ).fetchall()
        return [{"agent": a, "role": r, "content": c} for (a, r, c) in rows]

    def delete_session(self, session_id: str):
        self.conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.conn.commit()
