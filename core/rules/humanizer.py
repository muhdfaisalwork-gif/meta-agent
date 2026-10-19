import re
from typing import Dict, Any, Tuple
from .rules_engine import RulesEngine

REPLACEMENT_MAP = {
    r"\butilize\b": "use",
    r"\butilizes\b": "uses",
    r"\butilized\b": "used",
    r"\butilizing\b": "using",
    r"\bfacilitate\b": "help",
    r"\bfacilitates\b": "helps",
    r"\bshowcase\b": "show",
    r"\bshowcases\b": "shows",
    r"\bshowcasing\b": "showing",
    r"\bleverage\b": "use",
    r"\bleverages\b": "uses",
    r"\bleveraged\b": "used",
    r"\bleveraging\b": "using",
    r"\bharness\b": "use",
    r"\bstreamline\b": "simplify",
    r"\bfoster\b": "build",
    r"\bfostering\b": "building",
    r"\bpivotal\b": "key",
    r"\brobust\b": "solid",
    r"\bgroundbreaking\b": "new",
    r"\bgame-changer\b": "real shift",
    r"\bdeep dive\b": "breakdown",
    r"\bseamless\b": "smooth",
    r"\bseamlessly\b": "smoothly",
    r"\bdelve into\b": "break down",
    r"\bdelves into\b": "breaks down",
    r"\bdelving into\b": "breaking down",
    r"\bdelve\b": "look",
    r"\blandscape\b": "space",
    r"\btapestry\b": "mix",
    r"\bparadigm\b": "model",
    r"\bsynergies\b": "alignment",
    r"\bsynergy\b": "fit",
    r"\btestament\b": "proof",
    r"\bbeacon\b": "signal",
    r"\bparamount\b": "critical",
    r"\bvibrant\b": "active",
    r"\binvaluable\b": "useful",
    r"\bmultifaceted\b": "complex",
    r"\btransformative\b": "practical",
    r"\bcomprehensive\b": "full",
    r"\brevolutionary\b": "new",
    r"\binnovative\b": "practical",
    r"\bcutting-edge\b": "modern",
    r"\bunleashing\b": "running",
    r"\bunleash\b": "run",
    r"\bembarking\b": "starting",
    r"\bembark\b": "start",
    r"\bfurthermore,?\b": "Plus,",
    r"\bmoreover,?\b": "Also,",
    r"\bin conclusion,?\b": "Bottom line,",
    r"\bultimately,?\b": "In practice,",
    r"\bindeed,?\b": "In fact,"
}


class Humanizer:
    """
    4-Pass Humanizer Pipeline for Instagram & Facebook Reels captions and comments.
    Strips LLM preambles, replaces AI buzzwords with plain builder verbs, and enforces mobile spacing.
    """

    @staticmethod
    def extract_clean_candidate(text: str) -> str:
        cleaned = (text or "").strip()
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
        if "</think>" in cleaned:
            cleaned = cleaned.split("</think>")[-1].strip()

        code_fence = re.search(r"```(?:markdown|text)?\s*\n(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
        if code_fence:
            cleaned = code_fence.group(1).strip()

        lines = []
        for l in cleaned.split("\n"):
            s = l.strip()
            if re.match(
                r"^(here is|here's|sure,|okay,|caption:|draft:|comment:|reply:)\s*",
                s,
                re.IGNORECASE
            ) and len(s) < 60:
                continue
            lines.append(s)
        cleaned = "\n".join(lines).strip()
        if cleaned.startswith('"') and cleaned.endswith('"') and len(cleaned) > 12:
            cleaned = cleaned[1:-1].strip()
        return cleaned

    @staticmethod
    def humanize_text(text: str) -> Tuple[str, Dict[str, Any]]:
        cleaned = Humanizer.extract_clean_candidate(text)
        changes = []

        for pattern, repl in REPLACEMENT_MAP.items():
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned, count = re.subn(pattern, repl, cleaned, flags=re.IGNORECASE)
                changes.append(f"Replaced '{pattern}' -> '{repl}' ({count}x)")

        # Normalize excess em-dashes
        cleaned = re.sub(r"\s*—\s*", " - ", cleaned)

        audit = RulesEngine.audit_text(cleaned)
        audit["changes_made"] = changes
        return cleaned, audit
