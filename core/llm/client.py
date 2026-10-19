import os
import re
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from core.config_loader import load_config, get_logger
from core.db.database import get_connection
from core.rules.humanizer import Humanizer
from core.brain.brain import BrainManager

load_dotenv()
logger = get_logger("llm_client")


def _get_db_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ? LIMIT 1", (key,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
    except Exception:
        pass
    return default


class UniversalLLMClient:
    """
    Universal Multi-Model Engine for Meta Nexus Agent:
    1. Local Ollama (default: qwen2.5:latest / llama3.2:latest at http://localhost:11434)
    2. OpenRouter Free Models Chain (google/gemma-4-31b-it:free, etc.)
    3. Google Gemini / OpenAI / Anthropic
    4. Built-in Offline Cognitive Brain Synthesizer (zero-dependency fallback so the agent never stalls)
    """

    OPENROUTER_FALLBACKS = [
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3.5-lightning:free",
        "google/gemma-4-26b-a4b-it:free",
        "qwen/qwen3.8-27b:free"
    ]

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self._explicit_provider = provider
        self._explicit_model = model
        self.brain = BrainManager()

    @property
    def active_provider(self) -> str:
        if self._explicit_provider:
            return self._explicit_provider.lower()
        cfg = load_config().get("llm", {})
        return (_get_db_setting("LLM_PROVIDER") or os.getenv("LLM_PROVIDER") or cfg.get("provider", "ollama")).lower()

    @property
    def current_model(self) -> str:
        if self._explicit_model:
            return self._explicit_model
        prov = self.active_provider
        cfg = load_config().get("llm", {})
        if prov == "ollama":
            return _get_db_setting("OLLAMA_MODEL") or os.getenv("OLLAMA_MODEL") or cfg.get("ollama_model", "qwen2.5:latest")
        elif prov == "openrouter":
            return _get_db_setting("OPENROUTER_MODEL") or os.getenv("OPENROUTER_MODEL") or cfg.get("openrouter_model", "google/gemma-4-31b-it:free")
        elif prov == "gemini":
            return _get_db_setting("GEMINI_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        elif prov == "openai":
            return _get_db_setting("OPENAI_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return "qwen2.5:latest"

    def is_ollama_online(self) -> bool:
        base_url = (_get_db_setting("OLLAMA_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        try:
            r = requests.get(f"{base_url}/api/version", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def list_ollama_models(self) -> List[str]:
        base_url = (_get_db_setting("OLLAMA_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=2)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", []) if "name" in m]
                if models:
                    return models
        except Exception:
            pass
        return ["qwen2.5:latest", "llama3.2:latest", "gemma2:latest", "deepseek-r1:8b"]

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        res = self.chat_completion(messages, temperature=temperature)
        text, _ = Humanizer.humanize_text(res.get("content", ""))
        return text

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        prov = self.active_provider

        # 1. Try Local Ollama
        if prov == "ollama" or self.is_ollama_online():
            try:
                base_url = (_get_db_setting("OLLAMA_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
                installed = self.list_ollama_models()
                target_model = self.current_model if self.current_model in installed else installed[0]
                r = requests.post(
                    f"{base_url}/api/chat",
                    json={
                        "model": target_model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature, "num_predict": max_tokens}
                    },
                    timeout=35
                )
                if r.status_code == 200:
                    content = r.json().get("message", {}).get("content", "")
                    if content:
                        return {"content": content, "model_used": target_model, "provider": "ollama"}
            except Exception as e:
                logger.debug(f"Ollama fallback check: {e}")

        # 2. Try OpenRouter if key is configured
        or_key = _get_db_setting("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if or_key and or_key != "your_openrouter_api_key_here":
            for candidate in [self.current_model] + self.OPENROUTER_FALLBACKS:
                try:
                    r = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {or_key}",
                            "Content-Type": "application/json",
                            "X-Title": "Meta Nexus Agent"
                        },
                        json={
                            "model": candidate,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        },
                        timeout=25
                    )
                    if r.status_code == 200:
                        choices = r.json().get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            if content:
                                return {"content": content, "model_used": candidate, "provider": "openrouter"}
                except Exception:
                    continue

        # 3. Deterministic Offline Cognitive Brain Synthesizer
        user_msg = messages[-1]["content"] if messages else ""
        synthesized = self._offline_brain_synthesize(user_msg)
        return {
            "content": synthesized,
            "model_used": "cognitive-brain-local",
            "provider": "offline_brain"
        }

    def _offline_brain_synthesize(self, prompt: str) -> str:
        """Synthesizes 82-rule compliant captions or replies using local Story Bank receipts when offline."""
        p_lower = prompt.lower()
        stories = self.brain.get_story_bank()
        top_story = stories[0] if stories else {
            "title": "Sultrix Trade OS",
            "metrics_receipts": "Cut execution latency from 1.2s to 420ms"
        }

        if "reply" in p_lower or "comment" in p_lower:
            # Extract context if present
            if "?" in prompt:
                return f"Good question. When we built {top_story['title']}, we tested this directly in production ({top_story['metrics_receipts']}). Running the pipeline locally keeps latency flat and cuts API overhead to $0."
            return f"Spot on. We saw the exact same pattern while shipping {top_story['title']} ({top_story['metrics_receipts']}). Keeping the execution stack simple and local always wins under real load."

        # Caption generation
        hook_line = "Most builders overcomplicate automation with brittle API wrappers."
        m = re.search(r"Title/Hook:\s*(.+)", prompt)
        if m and m.group(1).strip():
            hook_line = m.group(1).strip()

        return (
            f"{hook_line}\n\n"
            f"When we engineered {top_story['title']}, we focused on raw execution speed ({top_story['metrics_receipts']}).\n\n"
            f"Running 100% locally with Playwright, yt-dlp, and FFmpeg means zero API fees and full control over every frame.\n\n"
            f"What part of your stack are you simplifying this week?\n\n"
            f"#buildinpublic #aiagents #softwareengineering #saasfounder #automation"
        )

    def rewrite_reel_caption(
        self,
        original_title: str,
        original_caption: str = "",
        creator_handle: str = "",
        platform: str = "Instagram",
        hook_formula: str = "R2"
    ) -> Dict[str, Any]:
        """Rewrites a scraped Reel/Video caption into an original, 82-Rule compliant builder caption with hashtags."""
        stories = self.brain.get_story_bank()
        receipts_summary = "\n".join([f"- {s['title']}: {s['metrics_receipts']}" for s in stories[:3]])

        sys_prompt = (
            "You are a candid technical founder writing a high-retention Instagram/Facebook Reel caption. "
            "Follow the 82 Humanizer Rules strictly: NEVER use delve, tapestry, robust, pivotal, game-changer, "
            "landscape, foster, leverage, seamless, or robotic transitions. "
            "Use short 1-2 sentence mobile paragraphs, ground insights in real builder metrics, and end with 5 niche hashtags."
        )
        user_prompt = (
            f"Platform: {platform}\n"
            f"Hook Formula: {hook_formula}\n"
            f"Title/Hook: {original_title}\n"
            f"Original Context: {original_caption[:400]}\n"
            f"Creator Credit: {creator_handle}\n"
            f"Verified Builder Receipts:\n{receipts_summary}\n\n"
            f"Write only the final {platform} Reel caption ready to publish."
        )

        res = self.chat_completion(
            [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.7
        )
        clean_caption, audit = Humanizer.humanize_text(res["content"])
        return {
            "caption": clean_caption,
            "model_used": res["model_used"],
            "provider": res["provider"],
            "audit": audit
        }

    def generate_authentic_comment(
        self,
        post_caption: str,
        user_comment: str = "",
        author_name: str = "",
        platform: str = "Instagram",
        mode: str = "auto_reply"
    ) -> Dict[str, Any]:
        """
        Generates a short (1-2 sentences), authentic human reply or niche outreach comment
        passing all 82 Humanizer rules.
        """
        stories = self.brain.get_story_bank()
        receipts_summary = "; ".join([f"{s['title']} ({s['metrics_receipts']})" for s in stories[:2]])

        if mode == "auto_reply":
            sys_prompt = (
                f"You are replying to a comment on your {platform} Reel/Post as a real human builder. "
                "Write 1-2 natural, conversational sentences. Never say 'Thanks for sharing!' or use AI clichés."
            )
            user_prompt = (
                f"Post context: {post_caption[:300]}\n"
                f"Commenter ({author_name}) wrote: {user_comment}\n"
                f"Your builder background: {receipts_summary}\n"
                "Draft a direct, authentic reply (max 35 words):"
            )
        else:
            sys_prompt = (
                f"You are leaving a value-add builder comment on a niche {platform} Reel. "
                "Write 1-2 sharp, specific sentences adding a real engineering insight or metric. Zero generic praise."
            )
            user_prompt = (
                f"Reel caption/topic: {post_caption[:350]}\n"
                f"Creator: {author_name}\n"
                f"Your builder receipts: {receipts_summary}\n"
                "Draft a natural comment (max 35 words):"
            )

        res = self.chat_completion(
            [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.7,
            max_tokens=180
        )
        clean_comment, audit = Humanizer.humanize_text(res["content"])
        return {
            "comment": clean_comment,
            "model_used": res["model_used"],
            "provider": res["provider"],
            "audit": audit
        }


def get_llm_client() -> UniversalLLMClient:
    return UniversalLLMClient()
