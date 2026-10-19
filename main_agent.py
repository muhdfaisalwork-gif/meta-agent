#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Master CLI & Autonomous Orchestrator (main_agent.py)
Orchestrates all 6 phases of G:\\Meta agent:
  01_login_setup.py            - Persistent Chrome login for Instagram & Facebook
  02_saved_extractor.py        - Saved video scraper + yt-dlp downloader + saved_videos_log.xlsx
  03_media_music_mixer.py      - FFmpeg audio/video mixer (20%/85% pre-mix, 15s Image+MP3 Reel, Native UI flag)
  04_ig_publisher_commenter.py - Instagram Reel publisher + AI Commenter & Auto-Replier
  05_fb_publisher_commenter.py - Facebook Reel publisher + AI Commenter & Auto-Replier
  Phase 6                      - Anti-Ban Guardrails (3.5-9.2s jitter, 50-90ms typing delay, daily caps)
"""

import os
import sys
import json
import importlib
import argparse
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db.database import init_db
from core.config_loader import load_config
from core.browser.meta_browser import MetaBrowserEngine
from core.excel.sheet_manager import MasterSheetManager
from core.mixer.media_mixer import MediaMusicMixer
from core.guardrails.anti_ban import AntiBanGuardrails
from core.llm.client import UniversalLLMClient

mod_01 = importlib.import_module("01_login_setup")
mod_02 = importlib.import_module("02_saved_extractor")
mod_03 = importlib.import_module("03_media_music_mixer")
mod_04 = importlib.import_module("04_ig_publisher_commenter")
mod_05 = importlib.import_module("05_fb_publisher_commenter")


class MetaMasterOrchestrator:
    """Master controller that ties together Phases 1 through 6 of Meta Nexus Agent."""

    def __init__(self):
        init_db()
        self.cfg = load_config()
        self.browser = MetaBrowserEngine()
        self.sheet = MasterSheetManager()
        self.mixer = MediaMusicMixer()
        self.guardrails = AntiBanGuardrails()
        self.llm = UniversalLLMClient()

    def get_system_status(self) -> Dict[str, Any]:
        auth = self.browser.get_auth_status()
        rows = self.sheet.get_all_rows()
        tracks = self.mixer.list_music_tracks()
        limits = self.guardrails.get_daily_usage()
        return {
            "project": self.cfg.get("project_name"),
            "auth": auth,
            "llm": {
                "active_provider": self.llm.active_provider,
                "current_model": self.llm.current_model,
                "ollama_online": self.llm.is_ollama_online(),
                "humanizer_82_rules": True
            },
            "master_sheet": {
                "excel_path": self.sheet.excel_path,
                "total_videos": len(rows),
                "downloaded": sum(1 for r in rows if r["repost_status"] == "Downloaded"),
                "ready_to_post": sum(1 for r in rows if r["repost_status"] == "Ready to Post"),
                "published": sum(1 for r in rows if r["repost_status"] == "Published")
            },
            "music_library": {
                "tracks_count": len(tracks),
                "tracks": [t["name"] for t in tracks]
            },
            "guardrails": limits
        }

    def run_full_autonomous_cycle(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Executes a complete end-to-end cycle:
        1. Extracts Saved Videos from IG & FB via yt-dlp -> updates saved_videos_log.xlsx
        2. Mixes downloaded videos with local MP3 tracks (20% original / 85% music) -> ready_to_post/
        3. Publishes 1 Instagram Reel and 1 Facebook Reel -> marks "Published" in saved_videos_log.xlsx
        4. Runs AI Auto-Reply on pending comments with 82-Rule Humanizer & 50-90ms typing delay
        """
        extractor = mod_02.SavedVideoExtractor(headless=True)
        step1_extract = extractor.run_extraction_pipeline(platform="both", max_items=2)

        step2_mix = mod_03.process_pending_sheet_videos()

        ig_bot = mod_04.InstagramPublisherCommenter(headless=True)
        step3_ig_pub = ig_bot.publish_reel_or_post(dry_run=dry_run)
        step4_ig_reply = ig_bot.auto_reply_comments()

        fb_bot = mod_05.FacebookPublisherCommenter(headless=True)
        step5_fb_pub = fb_bot.publish_reel_or_post(dry_run=dry_run)
        step6_fb_reply = fb_bot.auto_reply_comments()

        return {
            "status": "success",
            "cycle": "Full Autonomous Meta Agent Pipeline",
            "step_1_saved_extraction": {
                "processed_count": step1_extract.get("processed_count", 0),
                "excel_sheet": step1_extract.get("excel_sheet")
            },
            "step_2_media_music_mixer": {
                "mixed_count": step2_mix.get("mixed_count", 0)
            },
            "step_3_instagram_publish": step3_ig_pub,
            "step_4_instagram_auto_reply": step4_ig_reply,
            "step_5_facebook_publish": step5_fb_pub,
            "step_6_facebook_auto_reply": step6_fb_reply
        }


def main():
    parser = argparse.ArgumentParser(description="Meta Nexus Agent - Master CLI & Autonomous Controller")
    parser.add_argument("--status", action="store_true", help="Show full Meta Agent status, sheet counts, and rate limits")
    parser.add_argument("--login", action="store_true", help="Run Phase 1: Interactive Chrome Login Setup (IG + FB)")
    parser.add_argument("--extract", action="store_true", help="Run Phase 2: Scrape Saved Videos + yt-dlp + Update Excel Sheet")
    parser.add_argument("--mix", action="store_true", help="Run Phase 3: Mix Downloaded Videos with Local MP3 Tracks")
    parser.add_argument("--publish-ig", action="store_true", help="Run Phase 4: Publish Next Ready Reel to Instagram")
    parser.add_argument("--publish-fb", action="store_true", help="Run Phase 4: Publish Next Ready Reel to Facebook")
    parser.add_argument("--reply-ig", action="store_true", help="Run Phase 5: Auto-Reply to Instagram Comments")
    parser.add_argument("--reply-fb", action="store_true", help="Run Phase 5: Auto-Reply to Facebook Comments")
    parser.add_argument("--auto", action="store_true", help="Execute Full End-to-End Autonomous Cycle (Extract -> Mix -> Publish -> Reply)")
    parser.add_argument("--dry-run", action="store_true", help="Run publish actions in safe verification mode")
    args = parser.parse_args()

    orchestrator = MetaMasterOrchestrator()

    if args.login:
        res = mod_01.run_interactive_login()
        print(json.dumps(res, indent=2))
    elif args.extract:
        extractor = mod_02.SavedVideoExtractor(headless=True)
        res = extractor.run_extraction_pipeline()
        print(json.dumps(res, indent=2))
    elif args.mix:
        res = mod_03.process_pending_sheet_videos()
        print(json.dumps(res, indent=2))
    elif args.publish_ig:
        ig = mod_04.InstagramPublisherCommenter(headless=False)
        res = ig.publish_reel_or_post(dry_run=args.dry_run)
        print(json.dumps(res, indent=2))
    elif args.publish_fb:
        fb = mod_05.FacebookPublisherCommenter(headless=False)
        res = fb.publish_reel_or_post(dry_run=args.dry_run)
        print(json.dumps(res, indent=2))
    elif args.reply_ig:
        ig = mod_04.InstagramPublisherCommenter(headless=True)
        res = ig.auto_reply_comments()
        print(json.dumps(res, indent=2))
    elif args.reply_fb:
        fb = mod_05.FacebookPublisherCommenter(headless=True)
        res = fb.auto_reply_comments()
        print(json.dumps(res, indent=2))
    elif args.auto:
        res = orchestrator.run_full_autonomous_cycle(dry_run=args.dry_run)
        print(json.dumps(res, indent=2))
    else:
        print(json.dumps(orchestrator.get_system_status(), indent=2))


if __name__ == "__main__":
    main()
