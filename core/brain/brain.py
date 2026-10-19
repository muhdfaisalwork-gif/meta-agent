from typing import List, Dict, Any, Optional
from core.db.database import get_connection, init_db


class BrainManager:
    """
    Cognitive Brain & Story Bank Manager for Meta Nexus Agent:
    Provides real project receipts (Sultrix Trade OS, Shadow Stream, Shadow Voice, etc.),
    voice fingerprint rules, and Reel hook formulas to ground captions and comments.
    """

    def __init__(self):
        init_db()

    def get_story_bank(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor()
        if query:
            q = f"%{query.lower()}%"
            cur.execute('''
                SELECT * FROM story_bank
                WHERE LOWER(title) LIKE ? OR LOWER(detail) LIKE ? OR LOWER(tags) LIKE ? OR LOWER(category) LIKE ?
                ORDER BY id ASC
            ''', (q, q, q, q))
        else:
            cur.execute("SELECT * FROM story_bank ORDER BY id ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def add_story_receipt(
        self,
        category: str,
        title: str,
        detail: str,
        metrics_receipts: str = "",
        url: str = "",
        year_or_date: str = "2026",
        tags: str = ""
    ) -> Dict[str, Any]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO story_bank (category, title, detail, metrics_receipts, url, year_or_date, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (category, title, detail, metrics_receipts, url, year_or_date, tags))
        new_id = cur.lastrowid
        conn.commit()
        cur.execute("SELECT * FROM story_bank WHERE id = ?", (new_id,))
        row = dict(cur.fetchone())
        conn.close()
        return row

    def get_voice_profile(self) -> Dict[str, Any]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM voice_profile ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else {}

    def get_heuristics(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM heuristics ORDER BY weight DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
