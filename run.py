import os
import sys
import time
import threading
import webbrowser
import uvicorn
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

from core.db.database import init_db
from core.excel.sheet_manager import MasterSheetManager
from core.mixer.media_mixer import MediaMusicMixer


def open_browser(port: int):
    time.sleep(1.3)
    webbrowser.open(f"http://localhost:{port}")


def main():
    print("=" * 70)
    print("  [Meta Nexus Agent] Zero-API Facebook & Instagram Autonomous Studio")
    print("  [Engine] Playwright Persistent Context + yt-dlp + FFmpeg + Ollama")
    print("  [Brain] Cognitive Brain Receipts + 82-Rule Strict Humanizer Gate")
    print("=" * 70)

    print("\n[1/4] Initializing SQLite database and seeding Story Bank...")
    init_db()

    print("[2/4] Verifying Automated Master Sheet (saved_videos_log.xlsx)...")
    sheet_path = MasterSheetManager().ensure_sheet_exists()
    print(f"      [OK] Master Sheet ready at: {sheet_path}")

    print("[3/4] Initializing FFmpeg Music Library (music_library/)...")
    tracks = MediaMusicMixer().ensure_sample_music_library()
    print(f"      [OK] {len(tracks)} MP3 tracks ready in music_library/")

    port = int(os.getenv("PORT", 8005))
    host = os.getenv("HOST", "127.0.0.1")

    print(f"\n[4/4] Launching Meta Nexus Studio Dashboard at http://localhost:{port}...")
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    uvicorn.run("api.app:app", host=host, port=port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
