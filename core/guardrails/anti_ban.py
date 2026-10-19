import time
import random
from typing import Dict, Any, Optional
from core.config_loader import load_config, get_logger
from core.db.database import get_connection, init_db

logger = get_logger("guardrails")


class AntiBanGuardrails:
    """
    Phase 6 Safety & Anti-Ban Guardrails:
    - Human Jitter: Randomize sleep timers (3.5s to 9.2s) between clicks and scrolls.
    - Typing Simulation: Never instant-paste comments; simulate human keystrokes (50-90ms delay).
    - Watch Time Simulation: Watch target Reels for 5-8s before commenting.
    - Daily Rate Limits: Cap at max 3-5 Reels/Posts per day and 15-25 comments per session.
    """

    def __init__(self):
        init_db()
        self.cfg = load_config().get("guardrails", {})
        self.jitter_min = float(self.cfg.get("human_jitter_min_sec", 3.5))
        self.jitter_max = float(self.cfg.get("human_jitter_max_sec", 9.2))
        self.typing_min_ms = int(self.cfg.get("typing_delay_min_ms", 50))
        self.typing_max_ms = int(self.cfg.get("typing_delay_max_ms", 90))
        self.watch_min_sec = float(self.cfg.get("watch_reel_min_sec", 5.0))
        self.watch_max_sec = float(self.cfg.get("watch_reel_max_sec", 8.0))
        self.max_reels_per_day = int(self.cfg.get("max_reels_per_day", 5))
        self.max_comments_per_session = int(self.cfg.get("max_comments_per_session", 20))

    def human_jitter(self, min_sec: Optional[float] = None, max_sec: Optional[float] = None, fast_mode: bool = False) -> float:
        """Sleeps for a randomized human duration (default 3.5s to 9.2s)."""
        lo = min_sec if min_sec is not None else self.jitter_min
        hi = max_sec if max_sec is not None else self.jitter_max
        delay = random.uniform(lo, hi)
        if not fast_mode:
            time.sleep(delay)
        return round(delay, 2)

    def watch_reel_delay(self, fast_mode: bool = False) -> float:
        """Watches a target Reel for 5-8 seconds before interacting."""
        delay = random.uniform(self.watch_min_sec, self.watch_max_sec)
        if not fast_mode:
            time.sleep(delay)
        return round(delay, 2)

    def get_typing_delay_ms(self) -> int:
        """Returns a randomized per-character typing delay between 50ms and 90ms."""
        return random.randint(self.typing_min_ms, self.typing_max_ms)

    def simulate_human_typing(self, page_or_locator: Any, text: str) -> Dict[str, Any]:
        """
        Types text character-by-character with randomized 50-90ms keystroke delay
        and occasional micro-pauses after punctuation.
        """
        delay_ms = self.get_typing_delay_ms()
        try:
            if hasattr(page_or_locator, "keyboard"):
                page_or_locator.keyboard.type(text, delay=delay_ms)
            elif hasattr(page_or_locator, "press_sequentially"):
                page_or_locator.press_sequentially(text, delay=delay_ms)
            elif hasattr(page_or_locator, "type"):
                page_or_locator.type(text, delay=delay_ms)
            return {
                "status": "typed",
                "characters": len(text),
                "avg_delay_ms": delay_ms
            }
        except Exception as e:
            logger.warning(f"Typing simulation error: {e}")
            return {"status": "error", "message": str(e), "avg_delay_ms": delay_ms}

    def get_daily_usage(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """Returns today's published Reel/Post count and comment count."""
        conn = get_connection()
        cur = conn.cursor()

        plat_filter = ""
        params_pub = ["publish"]
        params_com = ["comment"]
        if platform:
            plat_filter = " AND LOWER(platform) = LOWER(?)"
            params_pub.append(platform)
            params_com.append(platform)

        cur.execute(
            f"SELECT COUNT(*) FROM rate_limits WHERE action_type = ? AND date(created_at) = date('now'){plat_filter}",
            params_pub
        )
        reels_today = cur.fetchone()[0]

        cur.execute(
            f"SELECT COUNT(*) FROM rate_limits WHERE action_type = ? AND date(created_at) = date('now'){plat_filter}",
            params_com
        )
        comments_today = cur.fetchone()[0]
        conn.close()

        return {
            "platform": platform or "All",
            "reels_published_today": reels_today,
            "max_reels_per_day": self.max_reels_per_day,
            "reels_remaining": max(0, self.max_reels_per_day - reels_today),
            "comments_posted_today": comments_today,
            "max_comments_per_session": self.max_comments_per_session,
            "comments_remaining": max(0, self.max_comments_per_session - comments_today),
            "can_publish": reels_today < self.max_reels_per_day,
            "can_comment": comments_today < self.max_comments_per_session,
            "jitter_window_sec": f"{self.jitter_min}s - {self.jitter_max}s",
            "typing_delay_ms": f"{self.typing_min_ms}ms - {self.typing_max_ms}ms"
        }

    def can_publish_reel(self, platform: str = "Instagram") -> bool:
        usage = self.get_daily_usage(platform)
        return usage["can_publish"]

    def can_post_comment(self, platform: str = "Instagram") -> bool:
        usage = self.get_daily_usage(platform)
        return usage["can_comment"]

    def record_action(self, platform: str, action_type: str, detail: str = "") -> Dict[str, Any]:
        """Records a publish or comment action in the SQLite rate_limits ledger."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO rate_limits (platform, action_type, detail) VALUES (?, ?, ?)",
            (platform, action_type, detail)
        )
        conn.commit()
        conn.close()
        return self.get_daily_usage(platform)
