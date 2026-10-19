import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.seo.github_seo import MetaNexusGitHubSEO

router = APIRouter(prefix="/api/seo", tags=["seo"])
engine = MetaNexusGitHubSEO()


class OptimizeReadmeRequest(BaseModel):
    apply: bool = False


class LaunchPackRequest(BaseModel):
    channel: str = "all"


class AILaunchRequest(BaseModel):
    channel: str = "hacker_news"
    angle: Optional[str] = None
    model: Optional[str] = None


@router.get("/audit")
def get_seo_audit():
    """Returns repository GitHub SEO health score (0-100), checklist, and recommended topics."""
    return engine.audit_repository()


@router.post("/optimize-readme")
def optimize_readme(req: OptimizeReadmeRequest):
    """Generates search-optimized README.md for Meta Nexus Agent, with optional write-to-disk."""
    content = engine.generate_optimized_readme()
    applied = False
    if req.apply:
        readme_path = os.path.join(engine.repo_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        applied = True

    return {
        "status": "success",
        "applied": applied,
        "readme_content": content,
        "byte_count": len(content)
    }


@router.post("/launch-pack")
def get_launch_pack(req: LaunchPackRequest):
    """Generates tailored launch copy for Hacker News, Reddit, Twitter/X, and GitHub Releases."""
    packs = engine.generate_launch_pack(channel=req.channel)
    return {
        "status": "success",
        "channel": req.channel,
        "packs": packs
    }


@router.post("/install-community-files")
def install_community_files():
    """Generates LICENSE, .github/workflows/ci.yml, issue templates, CONTRIBUTING.md, and SECURITY.md."""
    return engine.generate_community_health_files()


@router.post("/ai-launch")
def generate_ai_launch(req: AILaunchRequest):
    return engine.generate_ai_launch_content(
        channel=req.channel,
        angle=req.angle or "",
        model=req.model
    )
