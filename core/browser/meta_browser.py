import os
import re
import json
import time
import urllib.parse
import concurrent.futures
from typing import Dict, Any, List, Optional

from core.config_loader import load_config, get_abs_path, get_logger
from core.guardrails.anti_ban import AntiBanGuardrails

logger = get_logger("meta_browser")


class MetaBrowserEngine:
    """
    Persistent Chrome Session Engine for Instagram & Facebook:
    - Uses Playwright Persistent Context stored in G:\\Meta agent\\chrome_profile
    - Strips AutomationControlled blink flags
    - Supports both interactive manual login (01_login_setup.py) and <1s direct cookie injection
    - Exports Netscape cookies.txt so yt-dlp can download private/saved Reels without DPAPI locks
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.chrome_profile_dir = get_abs_path("chrome_profile")
        os.makedirs(self.chrome_profile_dir, exist_ok=True)
        self.storage_state_path = os.path.join(self.chrome_profile_dir, "storage_state.json")
        self.cookies_txt_path = os.path.join(self.chrome_profile_dir, "cookies.txt")
        self.guardrails = AntiBanGuardrails()

    def is_playwright_available(self) -> bool:
        try:
            import playwright
            return True
        except ImportError:
            return False

    def get_auth_status(self) -> Dict[str, Any]:
        """Checks whether Instagram (sessionid) and Facebook (c_user + xs) cookies are saved in chrome_profile."""
        ig_connected = os.path.exists(os.path.join(self.chrome_profile_dir, ".ig_authenticated"))
        fb_connected = os.path.exists(os.path.join(self.chrome_profile_dir, ".fb_authenticated"))

        if os.path.exists(self.storage_state_path):
            try:
                with open(self.storage_state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                cookies = state.get("cookies", [])
                for c in cookies:
                    domain = c.get("domain", "")
                    name = c.get("name", "")
                    val = c.get("value", "")
                    if "instagram.com" in domain and name == "sessionid" and len(str(val)) > 8:
                        ig_connected = True
                    if "facebook.com" in domain and name in ("c_user", "xs") and len(str(val)) > 4:
                        fb_connected = True
            except Exception:
                pass

        # Also check Chromium Default Network Cookies binary if manual login was used
        for rel in [("Default", "Network", "Cookies"), ("Default", "Cookies")]:
            cpath = os.path.join(self.chrome_profile_dir, *rel)
            if os.path.exists(cpath) and os.path.getsize(cpath) > 1024:
                try:
                    with open(cpath, "rb") as bf:
                        raw = bf.read()
                    if b"sessionid" in raw and b"instagram" in raw:
                        ig_connected = True
                    if b"c_user" in raw and b"facebook" in raw:
                        fb_connected = True
                except Exception:
                    pass

        return {
            "instagram_authenticated": ig_connected,
            "facebook_authenticated": fb_connected,
            "chrome_profile_dir": self.chrome_profile_dir,
            "cookies_txt_ready": os.path.exists(self.cookies_txt_path)
        }

    def _run_in_worker_thread(self, fn, *args, timeout: int = 120, **kwargs) -> Any:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                return {"status": "error", "message": f"Browser operation timed out after {timeout}s."}

    def launch_persistent_context(self, playwright_instance: Any, headless: Optional[bool] = None):
        use_headless = self.headless if headless is None else headless
        channels = ["chrome", "msedge", None]
        errors = []

        for ch in channels:
            try:
                kwargs: Dict[str, Any] = {
                    "user_data_dir": self.chrome_profile_dir,
                    "headless": use_headless,
                    "user_agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
                    ),
                    "ignore_default_args": ["--enable-automation"],
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-infobars"
                    ],
                    "viewport": {"width": 1366, "height": 860}
                }
                if ch:
                    kwargs["channel"] = ch
                ctx = playwright_instance.chromium.launch_persistent_context(**kwargs)
                # Inject storage_state cookies if present
                if os.path.exists(self.storage_state_path):
                    try:
                        with open(self.storage_state_path, "r", encoding="utf-8") as f:
                            st = json.load(f)
                        if st.get("cookies"):
                            ctx.add_cookies(st["cookies"])
                    except Exception:
                        pass
                return ctx
            except Exception as e:
                errors.append(f"{ch or 'chromium'}: {e}")
                continue
        raise RuntimeError(f"Could not launch Chrome Persistent Context: {errors}")

    def export_cookies_for_ytdlp(self, cookies_list: List[Dict[str, Any]]) -> str:
        """Writes Netscape HTTP Cookie File (chrome_profile/cookies.txt) so yt-dlp can authenticate."""
        lines = [
            "# Netscape HTTP Cookie File",
            "# Generated by Meta Nexus Agent for yt-dlp",
            ""
        ]
        for c in cookies_list:
            domain = c.get("domain", "")
            if not domain:
                continue
            include_sub = "TRUE" if domain.startswith(".") else "FALSE"
            path = c.get("path", "/")
            secure = "TRUE" if c.get("secure", True) else "FALSE"
            expires = int(c.get("expires", int(time.time()) + 31536000))
            if expires < 0:
                expires = int(time.time()) + 31536000
            name = c.get("name", "")
            val = c.get("value", "")
            lines.append(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{name}\t{val}")

        with open(self.cookies_txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return self.cookies_txt_path

    def save_platform_cookies(
        self,
        ig_sessionid: Optional[str] = None,
        fb_c_user: Optional[str] = None,
        fb_xs: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Instant (<1s) cookie saver for Instagram (sessionid) and Facebook (c_user + xs).
        Saves to storage_state.json AND exports Netscape cookies.txt for yt-dlp.
        """
        existing_cookies: List[Dict[str, Any]] = []
        if os.path.exists(self.storage_state_path):
            try:
                with open(self.storage_state_path, "r", encoding="utf-8") as f:
                    existing_cookies = json.load(f).get("cookies", [])
            except Exception:
                existing_cookies = []

        exp = int(time.time()) + (365 * 24 * 3600)

        if ig_sessionid:
            clean_ig = urllib.parse.unquote(ig_sessionid.strip().strip('"').strip("'"))
            if "sessionid=" in clean_ig:
                m = re.search(r"sessionid=([^;\s]+)", clean_ig)
                if m:
                    clean_ig = m.group(1)
            existing_cookies = [c for c in existing_cookies if not ("instagram.com" in c.get("domain", "") and c.get("name") == "sessionid")]
            existing_cookies.append({
                "name": "sessionid",
                "value": clean_ig,
                "domain": ".instagram.com",
                "path": "/",
                "expires": exp,
                "httpOnly": True,
                "secure": True,
                "sameSite": "None"
            })
            with open(os.path.join(self.chrome_profile_dir, ".ig_authenticated"), "w", encoding="utf-8") as f:
                f.write(f"authenticated_at={time.time()}\n")

        if fb_c_user and fb_xs:
            clean_c = urllib.parse.unquote(fb_c_user.strip().strip('"').strip("'"))
            clean_xs = urllib.parse.unquote(fb_xs.strip().strip('"').strip("'"))
            existing_cookies = [c for c in existing_cookies if not ("facebook.com" in c.get("domain", "") and c.get("name") in ("c_user", "xs"))]
            for cname, cval in [("c_user", clean_c), ("xs", clean_xs)]:
                existing_cookies.append({
                    "name": cname,
                    "value": cval,
                    "domain": ".facebook.com",
                    "path": "/",
                    "expires": exp,
                    "httpOnly": cname == "xs",
                    "secure": True,
                    "sameSite": "None"
                })
            with open(os.path.join(self.chrome_profile_dir, ".fb_authenticated"), "w", encoding="utf-8") as f:
                f.write(f"authenticated_at={time.time()}\n")

        with open(self.storage_state_path, "w", encoding="utf-8") as f:
            json.dump({"cookies": existing_cookies, "origins": []}, f, indent=2)

        self.export_cookies_for_ytdlp(existing_cookies)
        status = self.get_auth_status()
        return {
            "status": "success",
            "message": "Session cookies saved to chrome_profile and exported to cookies.txt for yt-dlp.",
            "auth": status
        }
