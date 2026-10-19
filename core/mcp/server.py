import os
import sys
import json
import importlib
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.db.database import init_db
from core.llm.client import UniversalLLMClient
from core.brain.brain import BrainManager
from core.excel.sheet_manager import MasterSheetManager
from core.mixer.media_mixer import MediaMusicMixer
from core.ytdlp.extractor import YtDlpExtractor
from core.guardrails.anti_ban import AntiBanGuardrails
from core.browser.meta_browser import MetaBrowserEngine

mod_02 = importlib.import_module("02_saved_extractor")
mod_04 = importlib.import_module("04_ig_publisher_commenter")
mod_05 = importlib.import_module("05_fb_publisher_commenter")


class MetaNexusMCPServer:
    """
    Model Context Protocol (MCP 2024-11-05) Server for Meta Nexus Agent.
    Exposes Facebook & Instagram Saved extraction, yt-dlp downloading, FFmpeg audio mixing,
    82-Rule caption humanization, Master Excel Sheet sync, and UI publishing to Claude/Cursor/Antigravity.
    """

    def __init__(self):
        init_db()
        self.llm = UniversalLLMClient()
        self.brain = BrainManager()
        self.sheet = MasterSheetManager()
        self.mixer = MediaMusicMixer()
        self.ytdlp = YtDlpExtractor()
        self.guardrails = AntiBanGuardrails()
        self.browser = MetaBrowserEngine()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "extract_saved_video_ytdlp",
                "description": "Downloads an Instagram or Facebook Reel/Video via yt-dlp using chrome_profile cookies, rewrites caption with the 82-Rule Humanizer, and updates saved_videos_log.xlsx.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Instagram or Facebook Reel/Video URL to extract and download"},
                        "platform": {"type": "string", "enum": ["Instagram", "Facebook"], "default": "Instagram"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "mix_media_music",
                "description": "Runs FFmpeg Media & Music Studio: Scenario A (Video + MP3 at 20%/85% volume), Scenario B (Static Image + MP3 -> 15s 1080x1920 Reel), or Scenario C (Flag Native UI Audio).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scenario": {"type": "string", "enum": ["a", "b", "c"], "default": "a"},
                        "video_id": {"type": "integer", "description": "Optional row ID in saved_videos_log.xlsx"},
                        "video_path": {"type": "string", "description": "Path to .mp4 for Scenario A"},
                        "hook_text": {"type": "string", "description": "Hook text for Scenario B 9:16 visual card"},
                        "mp3_name": {"type": "string", "description": "MP3 track filename in music_library"},
                        "native_song": {"type": "string", "description": "Song name for Scenario C Native UI attachment"}
                    },
                    "required": ["scenario"]
                }
            },
            {
                "name": "draft_meta_caption",
                "description": "Drafts or rewrites an Instagram/Facebook Reel caption strictly passing the 82-Rule Humanizer Gate and grounded in verified Story Bank receipts.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic_or_title": {"type": "string", "description": "Core hook or topic of the Reel/Post"},
                        "platform": {"type": "string", "enum": ["Instagram", "Facebook"], "default": "Instagram"},
                        "hook_formula": {"type": "string", "default": "R2"}
                    },
                    "required": ["topic_or_title"]
                }
            },
            {
                "name": "publish_instagram_reel",
                "description": "Publishes a processed Reel/Post to Instagram via Playwright persistent Chrome context and marks saved_videos_log.xlsx as Published.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "video_id": {"type": "integer", "description": "Row ID in saved_videos_log.xlsx"},
                        "caption": {"type": "string", "description": "Optional custom caption"},
                        "dry_run": {"type": "boolean", "default": False}
                    }
                }
            },
            {
                "name": "publish_facebook_reel",
                "description": "Publishes a processed Reel/Video to Facebook via Playwright persistent Chrome context and marks saved_videos_log.xlsx as Published.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "video_id": {"type": "integer", "description": "Row ID in saved_videos_log.xlsx"},
                        "caption": {"type": "string", "description": "Optional custom description"},
                        "dry_run": {"type": "boolean", "default": False}
                    }
                }
            },
            {
                "name": "auto_reply_meta_comments",
                "description": "Drafts and posts authentic human replies to Instagram or Facebook comments using Local Ollama / 82-Rule Humanizer and 50-90ms keystroke simulation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "enum": ["Instagram", "Facebook"], "default": "Instagram"},
                        "post_context": {"type": "string", "description": "Caption or topic of the post"},
                        "comment_text": {"type": "string", "description": "Comment text to reply to"},
                        "author_name": {"type": "string", "default": "@builder"}
                    },
                    "required": ["comment_text"]
                }
            },
            {
                "name": "get_master_sheet_rows",
                "description": "Returns all rows from saved_videos_log.xlsx (ID, Platform, Video Name / Hook, Full Caption, Creator Handle, Original URL, Local MP4 Path, Music Used, Repost Status, Posted URL).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Optional filter: Instagram or Facebook"},
                        "status": {"type": "string", "description": "Optional filter: Downloaded, Ready to Post, Published"}
                    }
                }
            },
            {
                "name": "check_meta_agent_status",
                "description": "Returns Meta Nexus Agent health, IG/FB cookie authentication status, active LLM model, music library tracks, and daily anti-ban rate limits.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "audit_github_seo",
                "description": "Audits Meta Nexus Agent repository discoverability, MIT license, CI workflow, keyword density, and returns a 0-100 GitHub SEO health score.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "generate_github_launch_pack",
                "description": "Generates tailored viral launch copy for Hacker News (Show HN), Reddit (r/LocalLLaMA, r/selfhosted), Twitter/X thread, or GitHub Release notes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel": {
                            "type": "string",
                            "enum": ["all", "hacker_news", "reddit_localllama", "reddit_selfhosted", "twitter_thread", "release_notes"],
                            "default": "all"
                        }
                    }
                }
            }
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        from core.seo.github_seo import MetaNexusGitHubSEO
        if name == "audit_github_seo":
            return MetaNexusGitHubSEO().audit_repository()
        elif name == "generate_github_launch_pack":
            return MetaNexusGitHubSEO().generate_launch_pack(channel=arguments.get("channel", "all"))
        elif name == "extract_saved_video_ytdlp":
            ext = mod_02.SavedVideoExtractor(headless=True)
            return ext.process_video_url(
                url=arguments["url"],
                platform=arguments.get("platform")
            )
        elif name == "mix_media_music":
            sc = arguments.get("scenario", "a").lower()
            tracks = self.mixer.list_music_tracks()
            mp3_name = arguments.get("mp3_name") or (tracks[0]["path"] if tracks else "")
            if sc == "a":
                vpath = arguments.get("video_path")
                vid = arguments.get("video_id")
                if not vpath and vid:
                    matches = [r for r in self.sheet.get_all_rows() if r["id"] == vid]
                    if matches:
                        vpath = matches[0].get("local_mp4_path")
                return self.mixer.mix_video_with_mp3(vpath or "", mp3_name, video_id=vid)
            elif sc == "b":
                hook = arguments.get("hook_text", "We cut order routing latency from 1.2s to 420ms")
                img_path = self.mixer.generate_quote_card_image(hook_text=hook)
                return self.mixer.image_and_mp3_to_reel(img_path, mp3_name, video_id=arguments.get("video_id"))
            else:
                return self.mixer.flag_native_ui_music(
                    video_id=int(arguments.get("video_id", 1)),
                    native_song_query=arguments.get("native_song", "Trending Audio")
                )
        elif name == "draft_meta_caption":
            return self.llm.rewrite_reel_caption(
                original_title=arguments["topic_or_title"],
                platform=arguments.get("platform", "Instagram"),
                hook_formula=arguments.get("hook_formula", "R2")
            )
        elif name == "publish_instagram_reel":
            ig = mod_04.InstagramPublisherCommenter(headless=True)
            return ig.publish_reel_or_post(
                video_id=arguments.get("video_id"),
                caption=arguments.get("caption"),
                dry_run=arguments.get("dry_run", False)
            )
        elif name == "publish_facebook_reel":
            fb = mod_05.FacebookPublisherCommenter(headless=True)
            return fb.publish_reel_or_post(
                video_id=arguments.get("video_id"),
                caption=arguments.get("caption"),
                dry_run=arguments.get("dry_run", False)
            )
        elif name == "auto_reply_meta_comments":
            plat = arguments.get("platform", "Instagram")
            inc = [{"author": arguments.get("author_name", "@user"), "text": arguments["comment_text"]}]
            if plat.lower() == "facebook":
                fb = mod_05.FacebookPublisherCommenter(headless=True)
                return fb.auto_reply_comments(post_context=arguments.get("post_context", ""), incoming_comments=inc)
            ig = mod_04.InstagramPublisherCommenter(headless=True)
            return ig.auto_reply_comments(post_context=arguments.get("post_context", ""), incoming_comments=inc)
        elif name == "get_master_sheet_rows":
            rows = self.sheet.get_all_rows(
                platform=arguments.get("platform"),
                status=arguments.get("status")
            )
            return {"excel_path": self.sheet.excel_path, "count": len(rows), "rows": rows}
        elif name == "check_meta_agent_status":
            return {
                "auth": self.browser.get_auth_status(),
                "llm_provider": self.llm.active_provider,
                "llm_model": self.llm.current_model,
                "music_tracks": self.mixer.list_music_tracks(),
                "rate_limits": self.guardrails.get_daily_usage(),
                "excel_path": self.sheet.excel_path
            }
        raise ValueError(f"Unknown MCP tool: {name}")

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = req.get("method", "")
        req_id = req.get("id")
        params = req.get("params", {}) or {}

        if method == "notifications/initialized":
            return None
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "meta-nexus-agent", "version": "1.0.0"}
                }
            }
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tool_definitions()}
            }
        if method == "tools/call":
            t_name = params.get("name", "")
            t_args = params.get("arguments", {}) or {}
            try:
                out = self.call_tool(t_name, t_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(out, indent=2)}],
                        "isError": False
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True
                    }
                }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }


def run_stdio_server():
    server = MetaNexusMCPServer()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = server.handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()
