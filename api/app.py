import os
import sys
import threading
import importlib
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.database import init_db, get_connection
from core.config_loader import load_config, save_config, get_abs_path
from core.browser.meta_browser import MetaBrowserEngine
from core.excel.sheet_manager import MasterSheetManager
from core.mixer.media_mixer import MediaMusicMixer
from core.llm.client import UniversalLLMClient
from core.brain.brain import BrainManager
from core.guardrails.anti_ban import AntiBanGuardrails
from core.mcp.server import MetaNexusMCPServer
from main_agent import MetaMasterOrchestrator
from api.routes import seo

mod_01 = importlib.import_module("01_login_setup")
mod_02 = importlib.import_module("02_saved_extractor")
mod_03 = importlib.import_module("03_media_music_mixer")
mod_04 = importlib.import_module("04_ig_publisher_commenter")
mod_05 = importlib.import_module("05_fb_publisher_commenter")

mcp_server = MetaNexusMCPServer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    MasterSheetManager().ensure_sheet_exists()
    MediaMusicMixer().ensure_sample_music_library()
    yield


app = FastAPI(
    title="Meta Nexus Agent - Zero-API Facebook & Instagram Autonomous Studio",
    description="100% Local Autonomous Meta Agent powered by Playwright Persistent Context, yt-dlp, FFmpeg, 82-Rule Humanizer, and Local Ollama.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(seo.router)


class CookiePayload(BaseModel):
    ig_sessionid: Optional[str] = None
    fb_c_user: Optional[str] = None
    fb_xs: Optional[str] = None


class ExtractPayload(BaseModel):
    platform: str = "both"
    url: Optional[str] = None
    max_items: int = 3


class MixerPayload(BaseModel):
    scenario: str = "batch"
    video_id: Optional[int] = None
    video_path: Optional[str] = None
    hook_text: Optional[str] = "How we cut order execution latency from 1.2s to 420ms"
    mp3_name: Optional[str] = None
    duration_sec: int = 15
    native_song: Optional[str] = "Trending Synthwave Audio"


class CaptionDraftPayload(BaseModel):
    topic_or_title: str
    original_caption: str = ""
    creator_handle: str = "@raulfinternational"
    platform: str = "Instagram"
    hook_formula: str = "R2"


class PublishPayload(BaseModel):
    platform: str = "Instagram"
    video_id: Optional[int] = None
    media_path: Optional[str] = None
    caption: Optional[str] = None
    native_music_query: Optional[str] = None
    dry_run: bool = False


class CommentPayload(BaseModel):
    platform: str = "Instagram"
    mode: str = "auto_reply"
    post_context: str = "Shipping our Zero-API Meta Agent with Playwright, yt-dlp, and FFmpeg."
    comment_text: Optional[str] = None
    author_name: Optional[str] = "@builder"
    hashtag_or_topic: str = "aiagents"


class StoryReceiptPayload(BaseModel):
    category: str
    title: str
    detail: str
    metrics_receipts: str = ""
    url: str = ""
    tags: str = ""


@app.get("/api/status")
def get_status():
    orch = MetaMasterOrchestrator()
    status = orch.get_system_status()
    brain = BrainManager()
    status["brain_receipts_count"] = len(brain.get_story_bank())
    return status


@app.post("/api/auth/cookies")
def save_cookies(payload: CookiePayload):
    engine = MetaBrowserEngine()
    return engine.save_platform_cookies(
        ig_sessionid=payload.ig_sessionid,
        fb_c_user=payload.fb_c_user,
        fb_xs=payload.fb_xs
    )


@app.post("/api/auth/launch-browser")
def launch_interactive_login():
    threading.Thread(target=mod_01.run_interactive_login, kwargs={"wait_seconds": 180}, daemon=True).start()
    return {
        "status": "launched",
        "message": "Launched Chrome Persistent Context with Instagram (Tab 1) and Facebook (Tab 2). Log in and close the window to lock cookies."
    }


@app.get("/api/sheet")
def get_sheet_rows(platform: Optional[str] = None, status: Optional[str] = None):
    sheet = MasterSheetManager()
    rows = sheet.get_all_rows(platform=platform, status=status)
    return {
        "excel_path": sheet.excel_path,
        "count": len(rows),
        "rows": rows
    }


@app.get("/api/sheet/download")
def download_excel_sheet():
    sheet = MasterSheetManager()
    path = sheet.sync_db_to_excel()
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="saved_videos_log.xlsx"
    )


@app.post("/api/extract")
def run_extractor(payload: ExtractPayload):
    extractor = mod_02.SavedVideoExtractor(headless=True)
    if payload.url and payload.url.strip():
        return extractor.process_video_url(payload.url.strip(), platform=payload.platform if payload.platform != "both" else None)
    return extractor.run_extraction_pipeline(platform=payload.platform, max_items=payload.max_items)


@app.get("/api/music")
def list_music():
    mixer = MediaMusicMixer()
    return {"tracks": mixer.list_music_tracks()}


@app.post("/api/mixer")
def run_mixer(payload: MixerPayload):
    mixer = MediaMusicMixer()
    tracks = mixer.list_music_tracks()
    mp3_target = payload.mp3_name or (tracks[0]["path"] if tracks else "")

    sc = payload.scenario.lower()
    if sc == "a":
        vpath = payload.video_path
        if not vpath and payload.video_id:
            matches = [r for r in MasterSheetManager().get_all_rows() if r["id"] == payload.video_id]
            if matches:
                vpath = matches[0].get("local_mp4_path")
        if not vpath:
            rows = MasterSheetManager().get_all_rows()
            if rows:
                vpath = rows[0].get("local_mp4_path")
                payload.video_id = rows[0]["id"]
        return mixer.mix_video_with_mp3(vpath or "", mp3_target, video_id=payload.video_id)
    elif sc == "b":
        img_path = mixer.generate_quote_card_image(hook_text=payload.hook_text or "Meta Nexus Agent")
        return mixer.image_and_mp3_to_reel(
            image_path=img_path,
            mp3_name_or_path=mp3_target,
            duration_sec=payload.duration_sec,
            video_id=payload.video_id
        )
    elif sc == "c":
        vid = payload.video_id or 1
        return mixer.flag_native_ui_music(video_id=vid, native_song_query=payload.native_song or "Trending Audio")
    else:
        return mod_03.process_pending_sheet_videos(default_mp3=payload.mp3_name)


@app.post("/api/caption/draft")
def draft_caption(payload: CaptionDraftPayload):
    llm = UniversalLLMClient()
    return llm.rewrite_reel_caption(
        original_title=payload.topic_or_title,
        original_caption=payload.original_caption,
        creator_handle=payload.creator_handle,
        platform=payload.platform,
        hook_formula=payload.hook_formula
    )


@app.post("/api/publish")
def publish_media(payload: PublishPayload):
    if payload.platform.lower() == "facebook":
        fb = mod_05.FacebookPublisherCommenter(headless=True)
        return fb.publish_reel_or_post(
            video_id=payload.video_id,
            media_path=payload.media_path,
            caption=payload.caption,
            native_music_query=payload.native_music_query,
            dry_run=payload.dry_run
        )
    ig = mod_04.InstagramPublisherCommenter(headless=True)
    return ig.publish_reel_or_post(
        video_id=payload.video_id,
        media_path=payload.media_path,
        caption=payload.caption,
        native_music_query=payload.native_music_query,
        dry_run=payload.dry_run
    )


@app.post("/api/comments/run")
def run_comments(payload: CommentPayload):
    inc = None
    if payload.comment_text:
        inc = [{"author": payload.author_name or "@user", "text": payload.comment_text}]

    if payload.platform.lower() == "facebook":
        fb = mod_05.FacebookPublisherCommenter(headless=True)
        if payload.mode == "outreach":
            return fb.outreach_niche_commenting(topic=payload.hashtag_or_topic)
        return fb.auto_reply_comments(post_context=payload.post_context, incoming_comments=inc)
    else:
        ig = mod_04.InstagramPublisherCommenter(headless=True)
        if payload.mode == "outreach":
            return ig.outreach_niche_commenting(hashtag=payload.hashtag_or_topic)
        return ig.auto_reply_comments(post_context=payload.post_context, incoming_comments=inc)


@app.get("/api/comments/log")
def get_comments_log():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM comments_log ORDER BY id DESC LIMIT 50")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "comments": rows}


@app.get("/api/brain")
def get_brain_data():
    brain = BrainManager()
    return {
        "story_bank": brain.get_story_bank(),
        "voice_profile": brain.get_voice_profile(),
        "heuristics": brain.get_heuristics()
    }


@app.post("/api/brain/receipt")
def add_brain_receipt(payload: StoryReceiptPayload):
    brain = BrainManager()
    row = brain.add_story_receipt(
        category=payload.category,
        title=payload.title,
        detail=payload.detail,
        metrics_receipts=payload.metrics_receipts,
        url=payload.url,
        tags=payload.tags
    )
    return {"status": "success", "receipt": row}


@app.get("/api/settings")
def get_settings():
    return load_config()


@app.post("/api/settings")
async def update_settings(request: Request):
    body = await request.json()
    cfg = load_config()
    for k, v in body.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k] = {**cfg[k], **v}
        else:
            cfg[k] = v
    save_config(cfg)
    return {"status": "success", "config": cfg}


@app.post("/api/auto-cycle")
def trigger_auto_cycle():
    orch = MetaMasterOrchestrator()
    return orch.run_full_autonomous_cycle(dry_run=False)


@app.post("/mcp")
@app.post("/api/mcp")
async def handle_mcp_http(request: Request):
    try:
        body = await request.json()
        res = mcp_server.handle_request(body)
        return res or {}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}


@app.get("/mcp")
@app.get("/api/mcp")
def get_mcp_status():
    return {
        "status": "online",
        "name": "meta-nexus-agent",
        "protocol": "Model Context Protocol (JSON-RPC 2.0)",
        "tools_available": [t["name"] for t in mcp_server.get_tool_definitions()]
    }


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
READY_DIR = get_abs_path("ready_to_post")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(READY_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/ready_to_post", StaticFiles(directory=READY_DIR), name="ready_to_post")


@app.get("/")
def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Meta Nexus Agent Studio API running."}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
