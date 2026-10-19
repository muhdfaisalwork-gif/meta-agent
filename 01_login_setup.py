#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 1: Persistent Session Setup (01_login_setup.py)
- Launches Chrome with user_data_dir="G:\\Meta agent\\chrome_profile" and --disable-blink-features=AutomationControlled
- Opens instagram.com in Tab 1 and facebook.com in Tab 2
- Log in manually once and click "Save Login Info"
- Closes browser cleanly to lock cookies into chrome_profile + cookies.txt for yt-dlp
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.browser.meta_browser import MetaBrowserEngine
from core.config_loader import get_logger

logger = get_logger("01_login_setup")


def run_interactive_login(wait_seconds: int = 180) -> Dict[str, Any]:
    """
    Launches headed Chrome with persistent profile, opens Instagram in Tab 1
    and Facebook in Tab 2 so the user can log in once.
    """
    engine = MetaBrowserEngine(headless=False)
    if not engine.is_playwright_available():
        return {"status": "error", "message": "Playwright is not installed. Run: pip install playwright && playwright install chromium"}

    print("=" * 70)
    print("  META NEXUS AGENT - PHASE 1: PERSISTENT LOGIN SETUP")
    print(f"  Profile Directory: {engine.chrome_profile_dir}")
    print("=" * 70)
    print("\n[1/3] Launching Chrome with --disable-blink-features=AutomationControlled...")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        context = engine.launch_persistent_context(p, headless=False)
        pages = context.pages
        tab_ig = pages[0] if pages else context.new_page()
        tab_fb = context.new_page()

        print("[2/3] Opening Instagram (Tab 1) and Facebook (Tab 2)...")
        try:
            tab_ig.goto("https://www.instagram.com/", timeout=45000)
        except Exception as e:
            logger.warning(f"Instagram load warning: {e}")

        try:
            tab_fb.goto("https://www.facebook.com/", timeout=45000)
        except Exception as e:
            logger.warning(f"Facebook load warning: {e}")

        print("\n>>> ACTION REQUIRED:")
        print("    1. Log into Instagram in Tab 1 and click 'Save Login Info'.")
        print("    2. Log into Facebook in Tab 2 and save session.")
        print(f"    3. Close the browser window when done (or wait up to {wait_seconds}s).\n")

        start_t = time.time()
        while time.time() - start_t < wait_seconds:
            try:
                if len(context.pages) == 0:
                    break
                cookies = context.cookies()
                # Check if logged in on either platform and persist cookies live
                if cookies:
                    with open(engine.storage_state_path, "w", encoding="utf-8") as f:
                        json.dump({"cookies": cookies, "origins": []}, f, indent=2)
                    engine.export_cookies_for_ytdlp(cookies)
                time.sleep(2.0)
            except Exception:
                break

        try:
            cookies = context.cookies()
            if cookies:
                with open(engine.storage_state_path, "w", encoding="utf-8") as f:
                    json.dump({"cookies": cookies, "origins": []}, f, indent=2)
                engine.export_cookies_for_ytdlp(cookies)
            context.close()
        except Exception:
            pass

    status = engine.get_auth_status()
    print("[3/3] Browser closed cleanly. Session state locked into chrome_profile!")
    print(f"      Instagram Authenticated: {status['instagram_authenticated']}")
    print(f"      Facebook Authenticated : {status['facebook_authenticated']}")
    print(f"      yt-dlp cookies.txt     : {status['cookies_txt_ready']}")
    return {"status": "success", "auth": status}


def main():
    parser = argparse.ArgumentParser(description="Phase 1: Persistent Login Setup for Instagram & Facebook")
    parser.add_argument("--ig-sessionid", type=str, help="Directly inject Instagram sessionid cookie")
    parser.add_argument("--fb-c-user", type=str, help="Directly inject Facebook c_user cookie")
    parser.add_argument("--fb-xs", type=str, help="Directly inject Facebook xs cookie")
    parser.add_argument("--status", action="store_true", help="Check current authentication status")
    parser.add_argument("--timeout", type=int, default=180, help="Max seconds to wait for manual login")
    args = parser.parse_args()

    engine = MetaBrowserEngine()
    if args.status:
        print(json.dumps(engine.get_auth_status(), indent=2))
        return

    if args.ig_sessionid or (args.fb_c_user and args.fb_xs):
        res = engine.save_platform_cookies(
            ig_sessionid=args.ig_sessionid,
            fb_c_user=args.fb_c_user,
            fb_xs=args.fb_xs
        )
        print(json.dumps(res, indent=2))
        return

    run_interactive_login(wait_seconds=args.timeout)


if __name__ == "__main__":
    main()
