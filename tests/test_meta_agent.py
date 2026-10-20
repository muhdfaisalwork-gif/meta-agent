import os
import sys
import importlib
import pandas as pd
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.database import init_db
from core.excel.sheet_manager import MasterSheetManager, SHEET_COLUMNS
from core.mixer.media_mixer import MediaMusicMixer
from core.ytdlp.extractor import YtDlpExtractor
from core.rules.humanizer import Humanizer
from core.guardrails.anti_ban import AntiBanGuardrails
from core.browser.meta_browser import MetaBrowserEngine
from core.mcp.server import MetaNexusMCPServer
from main_agent import MetaMasterOrchestrator
from api.app import app

mod_02 = importlib.import_module("02_saved_extractor")
mod_03 = importlib.import_module("03_media_music_mixer")
mod_04 = importlib.import_module("04_ig_publisher_commenter")
mod_05 = importlib.import_module("05_fb_publisher_commenter")


def test_database_and_master_sheet_columns():
    init_db()
    sheet = MasterSheetManager()
    excel_path = sheet.ensure_sheet_exists()
    assert os.path.exists(excel_path)

    df = pd.read_excel(excel_path)
    assert list(df.columns) == SHEET_COLUMNS


def test_cookie_injection_and_ytdlp_export():
    browser = MetaBrowserEngine()
    res = browser.save_platform_cookies(
        ig_sessionid="1234567890%3Aabcdef123456%3A28",
        fb_c_user="100099887766",
        fb_xs="44%3Axyz987654321%3A2%3A1700000000"
    )
    assert res["status"] == "success"
    assert res["auth"]["instagram_authenticated"] is True
    assert res["auth"]["facebook_authenticated"] is True
    assert res["auth"]["cookies_txt_ready"] is True
    assert os.path.exists(browser.cookies_txt_path)


def test_saved_extractor_and_excel_sync():
    extractor = mod_02.SavedVideoExtractor(headless=True)
    res = extractor.process_video_url(
        url="https://www.instagram.com/reel/TestMetaReel001/",
        platform="Instagram",
        rewrite_caption=True,
        allow_demo_fallback=True
    )
    assert res["status"] == "success"
    rec = res["record"]
    assert rec["platform"] == "Instagram"
    assert os.path.exists(rec["local_mp4_path"])
    assert os.path.exists(res["excel_path"])

    df = pd.read_excel(res["excel_path"])
    assert len(df) >= 1
    assert "https://www.instagram.com/reel/TestMetaReel001/" in df["Original URL"].values


def test_ffmpeg_media_music_mixer_scenarios():
    mixer = MediaMusicMixer()
    tracks = mixer.list_music_tracks()
    assert len(tracks) >= 1

    # Scenario A: Mix video with local MP3 (20% original / 85% music)
    sheet = MasterSheetManager()
    rows = sheet.get_all_rows()
    assert len(rows) >= 1
    first_row = rows[0]

    res_a = mixer.mix_video_with_mp3(
        video_path=first_row["local_mp4_path"],
        mp3_name_or_path=tracks[0]["path"],
        video_id=first_row["id"]
    )
    assert res_a["status"] == "success"
    assert os.path.exists(res_a["output_path"])

    # Scenario B: Static Image / Quote Card + MP3 -> 5s 1080x1920 Reel
    card_img = mixer.generate_quote_card_image("We cut order execution latency from 1.2s to 420ms")
    assert os.path.exists(card_img)
    res_b = mixer.image_and_mp3_to_reel(
        image_path=card_img,
        mp3_name_or_path=tracks[0]["path"],
        duration_sec=4
    )
    assert res_b["status"] == "success"
    assert os.path.exists(res_b["output_path"])

    # Scenario C: Flag row with Native UI Audio
    res_c = mixer.flag_native_ui_music(first_row["id"], "Hans Zimmer Time")
    assert res_c["status"] == "success"
    assert res_c["music_used"] == "NATIVE_UI:Hans Zimmer Time"


def test_ig_and_fb_publishers_and_commenters():
    ig = mod_04.InstagramPublisherCommenter(headless=True)
    pub_ig = ig.publish_reel_or_post(dry_run=True)
    assert pub_ig["status"] == "success"
    assert pub_ig["platform"] == "Instagram"

    rep_ig = ig.auto_reply_comments()
    assert rep_ig["status"] == "success"
    assert rep_ig["replies_count"] >= 1

    fb = mod_05.FacebookPublisherCommenter(headless=True)
    pub_fb = fb.publish_reel_or_post(dry_run=True)
    assert pub_fb["status"] == "success"
    assert pub_fb["platform"] == "Facebook"

    rep_fb = fb.auto_reply_comments()
    assert rep_fb["status"] == "success"
    assert rep_fb["replies_count"] >= 1


def test_humanizer_82_rules_and_guardrails():
    raw_slop = "Let's delve into this groundbreaking, pivotal game-changer in today's digital landscape to leverage synergies."
    cleaned, audit = Humanizer.humanize_text(raw_slop)
    assert "delve" not in cleaned.lower()
    assert "pivotal" not in cleaned.lower()
    assert "game-changer" not in cleaned.lower()
    assert audit["passed"] is True

    guard = AntiBanGuardrails()
    delay = guard.get_typing_delay_ms()
    assert 50 <= delay <= 90


def test_fastapi_studio_and_mcp_server():
    client = TestClient(app)

    r_status = client.get("/api/status")
    assert r_status.status_code == 200
    assert "master_sheet" in r_status.json()

    r_sheet = client.get("/api/sheet")
    assert r_sheet.status_code == 200
    assert r_sheet.json()["count"] >= 1

    r_mcp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert r_mcp.status_code == 200
    tools = r_mcp.json()["result"]["tools"]
    assert any(t["name"] == "extract_saved_video_ytdlp" for t in tools)
    assert any(t["name"] == "audit_github_seo" for t in tools)


def test_github_seo_agent_and_license():
    from core.seo.github_seo import MetaNexusGitHubSEO
    seo_engine = MetaNexusGitHubSEO()

    # Install MIT LICENSE, CI workflow, issue templates, CONTRIBUTING.md, SECURITY.md
    comm_res = seo_engine.generate_community_health_files()
    assert comm_res["status"] == "success"
    assert os.path.exists(os.path.join(seo_engine.repo_dir, "LICENSE"))
    assert os.path.exists(os.path.join(seo_engine.repo_dir, "CONTRIBUTING.md"))
    assert os.path.exists(os.path.join(seo_engine.repo_dir, "SECURITY.md"))
    assert os.path.exists(os.path.join(seo_engine.repo_dir, ".github", "workflows", "ci.yml"))

    # Write 100/100 SEO README.md
    readme_text = seo_engine.generate_optimized_readme()
    with open(os.path.join(seo_engine.repo_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_text)

    # Audit repository -> must achieve 100/100 Grade A+
    audit = seo_engine.audit_repository()
    assert audit["score"] == 100
    assert audit["grade"] == "A+"

    # Verify launch packs
    packs = seo_engine.generate_launch_pack("all")
    assert "hacker_news" in packs
    assert "reddit_localllama" in packs
    assert "release_notes" in packs


def test_seo_api_routes():
    client = TestClient(app)
    r_audit = client.get("/api/seo/audit")
    assert r_audit.status_code == 200
    assert r_audit.json()["score"] == 100

    r_pack = client.post("/api/seo/launch-pack", json={"channel": "hacker_news"})
    assert r_pack.status_code == 200
    assert "hacker_news" in r_pack.json()["packs"]


def test_github_packages_npm_config():
    import json
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pkg_json_path = os.path.join(root_dir, "package.json")
    npmrc_path = os.path.join(root_dir, ".npmrc")
    workflow_path = os.path.join(root_dir, ".github", "workflows", "npm-publish.yml")

    assert os.path.exists(pkg_json_path)
    assert os.path.exists(npmrc_path)
    assert os.path.exists(workflow_path)

    with open(pkg_json_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg["name"] == "@muhdfaisalwork-gif/meta-agent"
    assert pkg["publishConfig"]["registry"] == "https://npm.pkg.github.com"
    assert pkg["repository"]["url"] == "https://github.com/muhdfaisalwork-gif/meta-agent.git"

    with open(npmrc_path, "r", encoding="utf-8") as f:
        npmrc = f.read()
    assert "@muhdfaisalwork-gif:registry=https://npm.pkg.github.com" in npmrc


