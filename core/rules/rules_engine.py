import re
from typing import Dict, Any, List

BANNED_AI_WORDS = [
    "delve", "delves", "delving", "tapestry", "robust", "pivotal", "game-changer",
    "landscape", "foster", "fosters", "fostering", "testament", "beacon", "paramount",
    "leverage", "leverages", "leveraging", "vibrant", "unleash", "unleashing",
    "embark", "embarking", "synergy", "synergies", "paradigm", "multifaceted",
    "groundbreaking", "revolutionary", "seamless", "seamlessly", "invaluable",
    "furthermore", "moreover", "in conclusion", "ultimately", "indeed"
]


class RulesEngine:
    """
    82-Rule Humanizer Auditor for Instagram & Facebook Reels, Captions, and Comments.
    Scores readability, detects AI slop vocabulary, and verifies mobile formatting.
    """

    @staticmethod
    def calculate_flesch_score(text: str) -> float:
        words = re.findall(r"\b[a-zA-Z]+\b", text)
        if not words:
            return 80.0
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        num_sentences = max(1, len(sentences))
        num_words = len(words)

        def count_syllables(w: str) -> int:
            w = w.lower()
            if len(w) <= 3:
                return 1
            w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
            w = re.sub(r"^y", "", w)
            vowels = re.findall(r"[aeiouy]{1,2}", w)
            return max(1, len(vowels))

        syllables = sum(count_syllables(w) for w in words)
        score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllables / num_words)
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def audit_text(text: str) -> Dict[str, Any]:
        lower_text = text.lower()
        tells_found: List[str] = []
        for word in BANNED_AI_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", lower_text):
                tells_found.append(word)

        flesch = RulesEngine.calculate_flesch_score(text)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        mobile_friendly = all(len(p.split()) <= 45 for p in paragraphs) if paragraphs else True

        passed = len(tells_found) == 0
        return {
            "passed": passed,
            "ai_tell_count": len(tells_found),
            "ai_tells_found": tells_found,
            "flesch_score": flesch,
            "mobile_friendly": mobile_friendly,
            "word_count": len(re.findall(r"\b\w+\b", text)),
            "char_count": len(text)
        }
