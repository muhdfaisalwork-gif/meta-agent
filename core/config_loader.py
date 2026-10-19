import os
import json
import logging
from typing import Dict, Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

DEFAULT_CONFIG: Dict[str, Any] = {
    "project_name": "Meta Nexus Agent (Zero-API Facebook & Instagram Autonomous Studio)",
    "version": "1.0.0",
    "paths": {
        "chrome_profile": "chrome_profile",
        "saved_videos_ig": "saved_videos/instagram",
        "saved_videos_fb": "saved_videos/facebook",
        "music_library": "music_library",
        "ready_to_post": "ready_to_post",
        "logs": "logs",
        "master_sheet": "saved_videos_log.xlsx",
        "sqlite_db": "storage/meta_agent.db"
    },
    "accounts": {
        "ig_username": "your_ig_username",
        "fb_username": "your_fb_username",
        "niche_hashtags": [
            "aiagents",
            "softwareengineering",
            "saasfounder",
            "buildinpublic",
            "automation",
            "fintech"
        ],
        "competitor_handles": [
            "levelsio",
            "alexhormozi",
            "ycombinator"
        ]
    },
    "llm": {
        "provider": "ollama",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "qwen2.5:latest",
        "openrouter_model": "google/gemma-4-31b-it:free",
        "temperature": 0.7,
        "enforce_82_humanizer_rules": True
    },
    "audio_mixer": {
        "original_video_volume": 0.20,
        "music_overlay_volume": 0.85,
        "static_image_duration_sec": 15,
        "target_resolution": "1080x1920",
        "target_fps": 30
    },
    "guardrails": {
        "human_jitter_min_sec": 3.5,
        "human_jitter_max_sec": 9.2,
        "typing_delay_min_ms": 50,
        "typing_delay_max_ms": 90,
        "watch_reel_min_sec": 5.0,
        "watch_reel_max_sec": 8.0,
        "max_reels_per_day": 5,
        "max_comments_per_session": 20,
        "cooldown_minutes_between_posts": 45
    },
    "schedule": {
        "auto_extract_saved_interval_hours": 12,
        "Preferred_posting_times": ["09:30", "14:15", "19:45"],
        "auto_reply_inbox_enabled": True,
        "outreach_commenting_enabled": False
    }
}


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        for k, v in data.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k] = {**merged[k], **v}
            else:
                merged[k] = v
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_abs_path(rel_or_key: str) -> str:
    cfg = load_config()
    paths = cfg.get("paths", {})
    rel = paths.get(rel_or_key, rel_or_key)
    if os.path.isabs(rel):
        return rel
    return os.path.normpath(os.path.join(ROOT_DIR, rel))


def get_logger(name: str = "meta_agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        log_file = os.path.join(LOGS_DIR, "meta_agent.log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(sh)
    return logger
