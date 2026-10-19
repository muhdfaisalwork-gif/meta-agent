import os
import sqlite3
from typing import Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(ROOT_DIR, "storage")
DB_PATH = os.path.join(DB_DIR, "meta_agent.db")

os.makedirs(DB_DIR, exist_ok=True)


_DB_INITIALIZED = False


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(force: bool = False) -> None:
    global _DB_INITIALIZED
    if _DB_INITIALIZED and not force and os.path.exists(DB_PATH):
        return
    conn = get_connection()
    conn.execute("PRAGMA journal_mode = WAL;")
    cursor = conn.cursor()

    # 1. Saved & Processed Videos Master Table (Mirrors saved_videos_log.xlsx)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL DEFAULT 'Instagram',
            video_name_hook TEXT NOT NULL,
            full_caption TEXT DEFAULT '',
            ai_caption TEXT DEFAULT '',
            creator_handle TEXT DEFAULT '@unknown',
            original_url TEXT UNIQUE NOT NULL,
            local_mp4_path TEXT DEFAULT '',
            ready_mp4_path TEXT DEFAULT '',
            music_used TEXT DEFAULT 'Original Audio',
            duration_sec REAL DEFAULT 0.0,
            repost_status TEXT DEFAULT 'Scraped',
            posted_url TEXT DEFAULT '',
            flesch_score REAL DEFAULT 75.0,
            ai_tell_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            published_at TEXT DEFAULT ''
        )
    ''')

    # 2. Comments & Auto-Reply Log (Mode 1: Inbox/Post Reply & Mode 2: Niche Outreach)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL DEFAULT 'Instagram',
            mode TEXT NOT NULL DEFAULT 'auto_reply',
            target_url TEXT DEFAULT '',
            author_name TEXT DEFAULT '',
            post_context TEXT DEFAULT '',
            comment_text TEXT DEFAULT '',
            reply_text TEXT NOT NULL,
            status TEXT DEFAULT 'posted',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Anti-Ban Rate Limit Ledger
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            action_type TEXT NOT NULL,
            detail TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Story Bank (Cognitive Brain Receipts & Metrics)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS story_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL,
            metrics_receipts TEXT,
            url TEXT,
            year_or_date TEXT,
            tags TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Voice Profile & 82-Rule Humanizer Fingerprint
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tone TEXT DEFAULT 'Direct, candid, punchy visual storyteller & builder',
            cadence TEXT DEFAULT 'Short 1-line hooks for Reels & mobile-first captions',
            preferred_phrases TEXT DEFAULT 'built, shipped, measured, cut, tested, real numbers',
            banned_phrases TEXT DEFAULT 'delve, pivotal, robust, game-changer, landscape, foster, leverage, tapestry',
            cta_style TEXT DEFAULT 'Specific builder question or save-worthy takeaway, zero generic engagement bait',
            author_bio TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 6. Brain Heuristics (Reels & Post Hook Formulas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS heuristics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_code TEXT UNIQUE NOT NULL,
            formula_name TEXT NOT NULL,
            category TEXT DEFAULT 'reel_hook',
            weight REAL DEFAULT 1.0,
            usage_count INTEGER DEFAULT 0,
            avg_engagement_rate REAL DEFAULT 0.0,
            notes TEXT,
            last_evolved TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 7. Settings Key-Value Store
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    seed_initial_data(conn)
    conn.close()
    _DB_INITIALIZED = True


def seed_initial_data(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    # Seed Story Bank with verified builder receipts
    cursor.execute("SELECT COUNT(*) FROM story_bank")
    if cursor.fetchone()[0] == 0:
        initial_stories = [
            (
                "Product / Systems",
                "Sultrix Trade OS",
                "Engineered Sultrix Trade OS, a high-performance trading operating system with automated order routing and real-time risk analytics.",
                "Cut order execution latency from 1.2s to 420ms; zero dropped ticks under spike load",
                "https://sultrixtrade.com",
                "2025-2026",
                "trading, fintech, latency, architecture, execution"
            ),
            (
                "Product / Media",
                "Shadow Stream Video Platform & App",
                "Designed and deployed the Shadow Stream high-concurrency video streaming platform and cross-platform mobile application.",
                "Sub-second video start time, adaptive HLS/DASH bitrate streaming, 99.95% uptime",
                "https://ssmovietvs.site",
                "2025-2026",
                "streaming, video, reels, mobile-app, scalability"
            ),
            (
                "AI Agents",
                "Shadow Voice AI Agent",
                "Architected Shadow Voice, a real-time conversational voice AI agent with sub-500ms voice-to-voice turnaround.",
                "Sub-500ms WebRTC voice latency, interruption handling, local + cloud hybrid inference",
                "https://raulfinternational.com",
                "2026",
                "voice-ai, agents, webrtc, low-latency, automation"
            ),
            (
                "Enterprise Systems",
                "Enterprise CRM Dashboard",
                "Built full-stack CRM dashboard for real-time customer pipeline management, telemetry, and automated follow-ups.",
                "Automated lead pipeline, cut manual sales ops by 14 hours/week per rep",
                "https://crm.rmsol.org/preview",
                "2025-2026",
                "crm, enterprise, b2b, automation"
            ),
            (
                "Company / Agency",
                "The Raulf International LLC Platform",
                "Launched The Raulf International LLC enterprise software engineering studio delivering custom AI agents, web systems, and cloud architecture.",
                "Full-cycle delivery across fintech, streaming media, and autonomous AI workflows",
                "https://raulfinternational.com",
                "2025-2026",
                "enterprise, agency, software, ai-agents"
            ),
            (
                "Open Source / Agents",
                "Meta & LinkedIn Autonomous Nexus Agents",
                "Built 100% local, zero-API browser agents combining Playwright Persistent Context, yt-dlp, FFmpeg, and an 82-Rule Humanizer Gate.",
                "$0/mo API cost, 100% local cookie persistence, automated Reel mixing & Excel sync",
                "https://github.com/muhdfaisalwork-gif",
                "2026",
                "meta-agent, instagram, facebook, playwright, ytdlp, ffmpeg"
            )
        ]
        cursor.executemany('''
            INSERT INTO story_bank (category, title, detail, metrics_receipts, url, year_or_date, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', initial_stories)

    # Seed Voice Profile
    cursor.execute("SELECT COUNT(*) FROM voice_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO voice_profile (tone, cadence, preferred_phrases, banned_phrases, cta_style, author_bio)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            "Direct, candid, high-retention visual builder & founder",
            "Punchy 1-line Reel hook, 1-2 sentence mobile blocks, zero fluff",
            "built, shipped, measured, cut, tested, broke, fixed, real numbers",
            "delve, pivotal, robust, game-changer, landscape, foster, leverage, tapestry, embark, unleash",
            "Specific technical/founder question or 'Save this for your next build' takeaway",
            "Founder & Systems Architect building Sultrix Trade OS, Shadow Stream, Shadow Voice AI, and autonomous local agents at The Raulf International LLC."
        ))

    # Seed Heuristics for IG/FB Reels & Posts
    cursor.execute("SELECT COUNT(*) FROM heuristics")
    if cursor.fetchone()[0] == 0:
        heuristics_seed = [
            ("R1", "3-Second Visual Counter-Intuitive Hook", "reel_hook", 1.35, 6, 7.8, "Stop scrolling: Why 90% of AI wrappers fail in production"),
            ("R2", "Before / After Latency & Cost Receipt", "reel_hook", 1.45, 9, 8.6, "We cut streaming costs by 62% and latency to 420ms. Here is the exact stack."),
            ("R3", "Zero-API Local Build Walkthrough", "reel_hook", 1.40, 8, 8.2, "How to run a full Instagram & Facebook agent locally for $0/month"),
            ("R4", "Contrarian Architecture Breakdown", "reel_hook", 1.25, 5, 6.9, "Stop paying $99/mo for schedulers when FFmpeg + Playwright does it locally"),
            ("R5", "Founder Scar / Production Bug Story", "reel_hook", 1.30, 7, 7.4, "The bug that almost took down our video stream at 2 AM")
        ]
        cursor.executemany('''
            INSERT INTO heuristics (formula_code, formula_name, category, weight, usage_count, avg_engagement_rate, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', heuristics_seed)

    # Seed Default Settings
    default_settings = {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "ollama"),
        "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "qwen2.5:latest"),
        "OPENROUTER_MODEL": os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free"),
        "IG_USERNAME": os.getenv("IG_USERNAME", "your_ig_username"),
        "FB_USERNAME": os.getenv("FB_USERNAME", "your_fb_username"),
        "ORIGINAL_VIDEO_VOLUME": "0.20",
        "MUSIC_OVERLAY_VOLUME": "0.85",
        "MAX_REELS_PER_DAY": "5",
        "MAX_COMMENTS_PER_SESSION": "20"
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
