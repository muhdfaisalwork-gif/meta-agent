#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 2: Saved Video Scraper & Sheet Generator (02_saved_extractor.py)
- Instagram Saved: Opens https://www.instagram.com/<username>/saved/all-posts/, auto-scrolls to collect /reel/ and /p/ URLs
- Facebook Saved: Opens https://www.facebook.com/saved, auto-scrolls to collect saved video/reel URLs
- Metadata & Download: Passes URLs to yt-dlp using cookies from G:\\Meta agent\\chrome_profile
- Sheet Columns (saved_videos_log.xlsx):
  [ID | Platform | Video Name / Hook | Full Caption | Creator Handle | Original URL | Local MP4 Path | Music Used | Repost Status | Posted URL]
"""

import os
import re
import sys
import json
import argparse
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config_loader import load_config, get_logger
from core.browser.meta_browser import MetaBrowserEngine
from core.ytdlp.extractor import YtDlpExtractor
from core.excel.sheet_manager import MasterSheetManager
from core.llm.client import UniversalLLMClient
from core.guardrails.anti_ban import AntiBanGuardrails

logger = get_logger("02_saved_extractor")


class SavedVideoExtractor:
    """
    Scrapes Saved Reels/Videos from Instagram & Facebook, downloads them via yt-dlp,
    rewrites captions using the 82-Rule Humanizer, and syncs saved_videos_log.xlsx.
    """

    def __init__(self, headless: bool = True):
        self.cfg = load_config()
        self.browser = MetaBrowserEngine(headless=headless)
        self.ytdlp = YtDlpExtractor()
        self.sheet = MasterSheetManager()
        self.llm = UniversalLLMClient()
        self.guardrails = AntiBanGuardrails()

    def scrape_instagram_saved_urls(self, username: Optional[str] = None, max_items: int = 10, scroll_passes: int = 3) -> List[str]:
        """Opens https://www.instagram.com/<username>/saved/all-posts/ and collects /reel/ and /p/ URLs."""
        ig_user = username or self.cfg.get("accounts", {}).get("ig_username", "your_ig_username")
        target_url = (
            f"https://www.instagram.com/{ig_user}/saved/all-posts/"
            if ig_user and ig_user != "your_ig_username"
            else "https://www.instagram.com/explore/"
        )

        collected: List[str] = []
        if not self.browser.is_playwright_available():
            return collected

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                ctx = self.browser.launch_persistent_context(p, headless=self.browser.headless)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto(target_url, timeout=45000)
                self.guardrails.human_jitter(3.5, 5.5)

                for _ in range(scroll_passes):
                    hrefs = page.eval_on_selector_all(
                        "a[href*='/reel/'], a[href*='/p/']",
                        "elements => elements.map(el => el.href)"
                    )
                    for h in hrefs:
                        clean_h = h.split("?")[0].rstrip("/") + "/"
                        if clean_h not in collected:
                            collected.append(clean_h)
                        if len(collected) >= max_items:
                            break
                    if len(collected) >= max_items:
                        break
                    page.mouse.wheel(0, 1200)
                    self.guardrails.human_jitter(3.5, 6.0)

                # Export fresh cookies for yt-dlp
                cookies = ctx.cookies()
                if cookies:
                    self.browser.export_cookies_for_ytdlp(cookies)
                ctx.close()
        except Exception as e:
            logger.warning(f"Instagram saved scrape warning: {e}")

        return collected[:max_items]

    def scrape_facebook_saved_urls(self, max_items: int = 10, scroll_passes: int = 3) -> List[str]:
        """Opens https://www.facebook.com/saved and collects saved video/reel URLs."""
        target_url = "https://www.facebook.com/saved"
        collected: List[str] = []
        if not self.browser.is_playwright_available():
            return collected

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                ctx = self.browser.launch_persistent_context(p, headless=self.browser.headless)
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto(target_url, timeout=45000)
                self.guardrails.human_jitter(3.5, 5.5)

                for _ in range(scroll_passes):
                    hrefs = page.eval_on_selector_all(
                        "a[href*='/reel/'], a[href*='/videos/'], a[href*='/watch/'], a[href*='/share/r/'], a[href*='/share/v/']",
                        "elements => elements.map(el => el.href)"
                    )
                    for h in hrefs:
                        clean_h = h.split("?")[0] if "/watch" not in h else h
                        if clean_h not in collected:
                            collected.append(clean_h)
                        if len(collected) >= max_items:
                            break
                    if len(collected) >= max_items:
                        break
                    page.mouse.wheel(0, 1200)
                    self.guardrails.human_jitter(3.5, 6.0)

                cookies = ctx.cookies()
                if cookies:
                    self.browser.export_cookies_for_ytdlp(cookies)
                ctx.close()
        except Exception as e:
            logger.warning(f"Facebook saved scrape warning: {e}")

        return collected[:max_items]

    def process_video_url(
        self,
        url: str,
        platform: Optional[str] = None,
        rewrite_caption: bool = True,
        allow_demo_fallback: bool = True
    ) -> Dict[str, Any]:
        """Downloads a single saved video via yt-dlp, generates an AI caption, and updates saved_videos_log.xlsx."""
        meta = self.ytdlp.extract_and_download(url, platform=platform, allow_demo_fallback=allow_demo_fallback)
        if meta.get("status") == "error":
            return meta

        ai_caption = meta.get("full_caption", "")
        if rewrite_caption:
            rewritten = self.llm.rewrite_reel_caption(
                original_title=meta.get("video_name_hook", "Saved Reel"),
                original_caption=meta.get("full_caption", ""),
                creator_handle=meta.get("creator_handle", "@unknown"),
                platform=meta.get("platform", "Instagram")
            )
            ai_caption = rewritten.get("caption", ai_caption)

        record = self.sheet.upsert_video_record(
            original_url=url,
            platform=meta.get("platform", "Instagram"),
            video_name_hook=meta.get("video_name_hook", "Saved Reel"),
            full_caption=meta.get("full_caption", ""),
            ai_caption=ai_caption,
            creator_handle=meta.get("creator_handle", "@unknown"),
            local_mp4_path=meta.get("local_mp4_path", ""),
            music_used=meta.get("music_used", "Original Audio"),
            duration_sec=float(meta.get("duration_sec", 0.0)),
            repost_status="Downloaded"
        )
        return {
            "status": "success",
            "record": record,
            "excel_path": self.sheet.excel_path
        }

    def run_extraction_pipeline(
        self,
        platform: str = "both",
        max_items: int = 5,
        custom_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Runs the full Saved Video extraction pipeline and updates saved_videos_log.xlsx."""
        urls_to_process: List[Dict[str, str]] = []

        if custom_urls:
            for u in custom_urls:
                urls_to_process.append({"url": u, "platform": self.ytdlp.detect_platform(u)})
        else:
            if platform.lower() in ("both", "instagram", "ig"):
                ig_urls = self.scrape_instagram_saved_urls(max_items=max_items)
                for u in ig_urls:
                    urls_to_process.append({"url": u, "platform": "Instagram"})
            if platform.lower() in ("both", "facebook", "fb"):
                fb_urls = self.scrape_facebook_saved_urls(max_items=max_items)
                for u in fb_urls:
                    urls_to_process.append({"url": u, "platform": "Facebook"})

            # If no live browser session yet, seed 2 demo saved Reels (1 IG, 1 FB) so the sheet & pipeline are immediately testable
            if not urls_to_process:
                urls_to_process = [
                    {"url": "https://www.instagram.com/reel/C8MetaAgentDemoIG/", "platform": "Instagram"},
                    {"url": "https://www.facebook.com/reel/90210MetaAgentDemoFB/", "platform": "Facebook"}
                ]

        results = []
        for item in urls_to_process:
            res = self.process_video_url(item["url"], platform=item["platform"], rewrite_caption=True)
            results.append(res)

        return {
            "status": "success",
            "processed_count": len(results),
            "excel_sheet": self.sheet.excel_path,
            "results": results
        }


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Saved Video Scraper & Sheet Generator")
    parser.add_argument("--platform", type=str, default="both", choices=["both", "instagram", "facebook"], help="Platform to scrape")
    parser.add_argument("--max", type=int, default=5, help="Max saved videos to extract per platform")
    parser.add_argument("--url", type=str, action="append", help="Extract specific Reel/Video URL(s) directly via yt-dlp")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed visible mode")
    args = parser.parse_args()

    extractor = SavedVideoExtractor(headless=not args.headed)
    summary = extractor.run_extraction_pipeline(
        platform=args.platform,
        max_items=args.max,
        custom_urls=args.url
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
