#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3: Music & Reel Processor (03_media_music_mixer.py)
- Scenario A (Reel + Local MP3): Lower original video volume to 20%, overlay selected .mp3 from music_library at 85% volume using FFmpeg.
- Scenario B (Static Image Post + Music): Loop static .jpg/.png into a 15-second 1080x1920 .mp4 container merged with .mp3 audio track.
- Scenario C (Native Platform Audio): Flag row in saved_videos_log.xlsx with a specific song name for native UI "Add Music" attachment.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.mixer.media_mixer import MediaMusicMixer
from core.excel.sheet_manager import MasterSheetManager
from core.config_loader import get_logger

logger = get_logger("03_media_music_mixer")


def process_pending_sheet_videos(default_mp3: Optional[str] = None) -> Dict[str, Any]:
    """Finds all 'Downloaded' rows in saved_videos_log.xlsx and mixes them with local MP3 tracks into ready_to_post/."""
    mixer = MediaMusicMixer()
    sheet = MasterSheetManager()
    tracks = mixer.list_music_tracks()
    chosen_mp3 = default_mp3 or (tracks[0]["path"] if tracks else "")

    pending = sheet.get_all_rows(status="Downloaded")
    processed = []
    for idx, row in enumerate(pending):
        local_mp4 = row.get("local_mp4_path", "")
        if not local_mp4 or not os.path.exists(local_mp4):
            continue
        track_to_use = chosen_mp3
        if tracks and not default_mp3:
            track_to_use = tracks[idx % len(tracks)]["path"]

        res = mixer.mix_video_with_mp3(
            video_path=local_mp4,
            mp3_name_or_path=track_to_use,
            video_id=row["id"]
        )
        processed.append(res)

    return {
        "status": "success",
        "mixed_count": len(processed),
        "results": processed,
        "excel_sheet": sheet.excel_path
    }


def main():
    parser = argparse.ArgumentParser(description="Phase 3: Music & Reel Processor (FFmpeg + Native UI Audio)")
    parser.add_argument("--scenario", type=str, default="batch", choices=["a", "b", "c", "batch"], help="Scenario A (Video+MP3), B (Image+MP3), C (Native UI Flag), or batch")
    parser.add_argument("--video", type=str, help="Path to input .mp4 for Scenario A")
    parser.add_argument("--image", type=str, help="Path to input .jpg/.png for Scenario B (or auto-generates a 9:16 quote card)")
    parser.add_argument("--hook-text", type=str, default="How we cut order execution latency from 1.2s to 420ms", help="Hook text if auto-generating a 9:16 quote card in Scenario B")
    parser.add_argument("--mp3", type=str, help="MP3 filename in music_library or full path")
    parser.add_argument("--duration", type=int, default=15, help="Duration in seconds for Scenario B static image Reel")
    parser.add_argument("--video-id", type=int, help="Row ID in saved_videos_log.xlsx to update")
    parser.add_argument("--native-song", type=str, default="Trending Synthwave Audio", help="Song title to search in IG/FB native UI for Scenario C")
    args = parser.parse_args()

    mixer = MediaMusicMixer()
    tracks = mixer.list_music_tracks()
    mp3_target = args.mp3 or (tracks[0]["path"] if tracks else "")

    if args.scenario == "a":
        if not args.video:
            print(json.dumps({"status": "error", "message": "Provide --video <path_to_mp4> for Scenario A"}, indent=2))
            return
        res = mixer.mix_video_with_mp3(args.video, mp3_target, video_id=args.video_id)
        print(json.dumps(res, indent=2))
    elif args.scenario == "b":
        img_path = args.image
        if not img_path or not os.path.exists(img_path):
            img_path = mixer.generate_quote_card_image(hook_text=args.hook_text)
        res = mixer.image_and_mp3_to_reel(img_path, mp3_target, duration_sec=args.duration, video_id=args.video_id)
        print(json.dumps(res, indent=2))
    elif args.scenario == "c":
        if not args.video_id:
            print(json.dumps({"status": "error", "message": "Provide --video-id <ID> for Scenario C"}, indent=2))
            return
        res = mixer.flag_native_ui_music(args.video_id, args.native_song)
        print(json.dumps(res, indent=2))
    else:
        res = process_pending_sheet_videos(default_mp3=args.mp3)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
