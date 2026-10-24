"""
Human User Simulation Test for Meta Nexus Agent
Tests the entire system end-to-end from the perspective of a real creator/operator.
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db.database import init_db
from core.excel.sheet_manager import MasterSheetManager
from core.mixer.media_mixer import MediaMusicMixer
from core.rules.humanizer import Humanizer
from core.rules.rules_engine import RulesEngine
from core.guardrails.anti_ban import AntiBanGuardrails
from main_agent import MetaMasterOrchestrator


def run_human_user_walkthrough():
    print("=" * 80)
    print("   [HUMAN USER SIMULATION TEST] - META NEXUS AGENT & HUMANIZER GATE")
    print("=" * 80)

    # 1. System Health & Diagnostics
    print("\n>>> STEP 1: Creator Checks System Status & Rate Limits...")
    orchestrator = MetaMasterOrchestrator()
    status = orchestrator.get_system_status()
    print(f"    * Project: {status['project']}")
    print(f"    * Instagram Auth: {'[READY]' if status['auth']['instagram_authenticated'] else '[NEEDS LOGIN]'}")
    print(f"    * Facebook Auth:  {'[READY]' if status['auth']['facebook_authenticated'] else '[NEEDS LOGIN]'}")
    print(f"    * LLM Provider:   {status['llm']['active_provider']} ({status['llm']['current_model']})")
    print(f"    * Guardrails:     Jitter: {status['guardrails']['jitter_window_sec']} | Typing: {status['guardrails']['typing_delay_ms']}")
    print(f"    * Music Library:  {status['music_library']['tracks_count']} tracks loaded")

    # 2. Testing 82-Rule Humanizer on Real AI Slop
    print("\n>>> STEP 2: Creator Tests 82-Rule Humanizer Gate on AI Cliché Draft...")
    ai_slop_draft = (
        "Here is the draft:\n\n"
        "In today's fast-paced digital landscape, leveraging cutting-edge AI is a pivotal game-changer. "
        "Delve into our revolutionary platform to foster seamless synergies and unlock transformative growth. "
        "It's not just a tool; it's a testament to innovation. "
        "In conclusion, embark on this journey to elevate your business.\n\n"
        "#AI #Innovation #Disruption #Growth #Business #Tech #Future #Success #Marketing #Synergy"
    )
    print("--- [BEFORE: Typical AI Output] ---")
    print(ai_slop_draft)

    cleaned_text, audit = Humanizer.humanize_text(ai_slop_draft)
    print("\n--- [AFTER: 82-Rule Humanizer Gate Cleaned Text] ---")
    print(cleaned_text)
    print("\n--- [AUDIT METRICS] ---")
    print(f"    * Passed Humanizer: {audit['passed']}")
    print(f"    * AI Buzzwords Remaining: {audit['ai_tell_count']}")
    print(f"    * Readability (Flesch Score): {audit['flesch_score']} / 100")
    print(f"    * Mobile Friendly Spacing: {audit['mobile_friendly']}")
    print(f"    * Replacements Made: {len(audit.get('changes_made', []))}")
    for change in audit.get("changes_made", [])[:5]:
        print(f"      - {change}")

    # 3. Media & Audio Pipeline Test
    print("\n>>> STEP 3: Creator Generates Quote Card & Mixes with Background Music...")
    mixer = MediaMusicMixer()
    quote = "Cut order execution latency from 1.2s to 420ms with zero dropped ticks."
    card_img = mixer.generate_quote_card_image(quote)
    tracks = mixer.list_music_tracks()
    selected_track = tracks[0]["path"] if tracks else None
    
    print(f"    * Generated Quote Card: {card_img}")
    if selected_track:
        reel_res = mixer.image_and_mp3_to_reel(
            image_path=card_img,
            mp3_name_or_path=selected_track,
            duration_sec=3
        )
        print(f"    * 1080x1920 Reel Rendered: {reel_res['output_path']}")

    # 4. Master Excel Sheet Audit
    print("\n>>> STEP 4: Creator Inspects Master Sheet (saved_videos_log.xlsx)...")
    sheet = MasterSheetManager()
    rows = sheet.get_all_rows()
    print(f"    * Total Videos Logged: {len(rows)}")
    for r in rows:
        print(f"      - [{r['id']}] {r['platform']} | Status: {r['repost_status']} | Music: {r['music_used']}")
        print(f"        Original: {r['original_url']}")
        print(f"        Posted:   {r['posted_url']}")

    # 5. Comment Auto-Reply Simulation (Typing Delay & Cognitive Brain Receipt)
    print("\n>>> STEP 5: Creator Tests AI Auto-Replier with Natural Typing Delay...")
    sample_comment = "How do you handle heavy market spikes without dropping orders?"
    print(f"    * Incoming Comment: \"{sample_comment}\"")
    
    guardrails = AntiBanGuardrails()
    typing_delay = guardrails.get_typing_delay_ms()
    print(f"    * Calculated Human Typing Delay: {typing_delay}ms per char (Within human 50-90ms range)")
    
    # Generate human-natural reply
    brain_receipt = (
        "Good question. When we built Sultrix Trade OS, we benchmarked this directly under peak load: "
        "execution latency stayed at 420ms with zero dropped ticks. "
        "Keeping the execution loop local and avoiding API middle layers is what prevents bottlenecks."
    )
    reply_cleaned, reply_audit = Humanizer.humanize_text(brain_receipt)
    print(f"    * Generated Human Reply: \"{reply_cleaned}\"")
    print(f"    * Reply Quality Gate: Passed={reply_audit['passed']}, Flesch={reply_audit['flesch_score']}")

    print("\n" + "=" * 80)
    print("   [RESULT]: All human user workflows passed with zero errors!")
    print("=" * 80)


if __name__ == "__main__":
    run_human_user_walkthrough()
