import os
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

from core.config_loader import load_config, get_abs_path, get_logger
from core.excel.sheet_manager import MasterSheetManager

logger = get_logger("media_mixer")


class MediaMusicMixer:
    """
    Phase 3: Music & Reel Studio (FFmpeg + Pillow Visual Card Engine)
    - Scenario A (Reel + Local MP3): Lowers original video volume to 20%, overlays selected .mp3 at 85% volume.
    - Scenario B (Static Image + Music): Loops static .jpg/.png into a 15-second 1080x1920 .mp4 merged with .mp3.
    - Scenario C (Native Platform Audio): Flags row in saved_videos_log.xlsx with NATIVE_UI:<song_name> for browser UI search.
    """

    def __init__(self):
        self.cfg = load_config().get("audio_mixer", {})
        self.orig_vol = float(self.cfg.get("original_video_volume", 0.20))
        self.music_vol = float(self.cfg.get("music_overlay_volume", 0.85))
        self.default_img_dur = int(self.cfg.get("static_image_duration_sec", 15))
        self.music_dir = get_abs_path("music_library")
        self.ready_dir = get_abs_path("ready_to_post")
        os.makedirs(self.music_dir, exist_ok=True)
        os.makedirs(self.ready_dir, exist_ok=True)
        self.sheet = MasterSheetManager()
        self.ensure_sample_music_library()

    def ensure_sample_music_library(self) -> List[str]:
        """Generates 3 playable royalty-free ambient MP3 tracks in music_library/ if empty."""
        existing = [f for f in os.listdir(self.music_dir) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
        if existing:
            return existing

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            return []

        sample_tracks = [
            ("synthwave_builder_beat.mp3", "sine=frequency=220:sample_rate=44100:duration=16"),
            ("deep_focus_ambient.mp3", "sine=frequency=330:sample_rate=44100:duration=16"),
            ("midnight_launch_pulse.mp3", "sine=frequency=440:sample_rate=44100:duration=16")
        ]
        created = []
        for fname, filter_src in sample_tracks:
            out_path = os.path.join(self.music_dir, fname)
            try:
                subprocess.run(
                    [
                        ffmpeg_bin, "-y",
                        "-f", "lavfi", "-i", filter_src,
                        "-af", "volume=0.4,afade=t=in:st=0:d=1,afade=t=out:st=14:d=2",
                        "-c:a", "libmp3lame", "-b:a", "192k",
                        out_path
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                created.append(fname)
            except Exception as e:
                logger.warning(f"Could not synthesize sample track {fname}: {e}")
        return created

    def list_music_tracks(self) -> List[Dict[str, Any]]:
        tracks = []
        for fname in sorted(os.listdir(self.music_dir)):
            if fname.lower().endswith((".mp3", ".wav", ".m4a")):
                fpath = os.path.join(self.music_dir, fname)
                tracks.append({
                    "name": fname,
                    "path": os.path.abspath(fpath),
                    "size_kb": round(os.path.getsize(fpath) / 1024, 1)
                })
        return tracks

    def _has_audio_stream(self, video_path: str) -> bool:
        ffprobe_bin = shutil.which("ffprobe")
        if not ffprobe_bin:
            return True
        try:
            res = subprocess.run(
                [
                    ffprobe_bin, "-v", "error", "-select_streams", "a",
                    "-show_entries", "stream=index", "-of", "csv=p=0", video_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return bool(res.stdout.strip())
        except Exception:
            return True

    def mix_video_with_mp3(
        self,
        video_path: str,
        mp3_name_or_path: str,
        orig_volume: Optional[float] = None,
        music_volume: Optional[float] = None,
        video_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scenario A (Reel + Local MP3):
        Lowers original video volume to 20% (0.20) and overlays selected .mp3 from music_library at 85% (0.85) volume.
        Outputs 9:16 ready-to-post MP4 into ready_to_post/.
        """
        if not os.path.exists(video_path):
            return {"status": "error", "message": f"Input video not found: {video_path}"}

        mp3_path = mp3_name_or_path
        if not os.path.exists(mp3_path):
            mp3_path = os.path.join(self.music_dir, os.path.basename(mp3_name_or_path))
        if not os.path.exists(mp3_path):
            tracks = self.list_music_tracks()
            if not tracks:
                return {"status": "error", "message": "No MP3 track found in music_library."}
            mp3_path = tracks[0]["path"]

        v_vol = orig_volume if orig_volume is not None else self.orig_vol
        m_vol = music_volume if music_volume is not None else self.music_vol

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        song_base = os.path.splitext(os.path.basename(mp3_path))[0]
        output_filename = f"{base_name}_mixed_{song_base}.mp4"
        output_path = os.path.join(self.ready_dir, output_filename)

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            return {"status": "error", "message": "FFmpeg binary not found on PATH."}

        has_audio = self._has_audio_stream(video_path)
        if has_audio:
            filter_complex = (
                f"[0:a]volume={v_vol}[a0];"
                f"[1:a]volume={m_vol}[a1];"
                f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            cmd = [
                ffmpeg_bin, "-y",
                "-i", video_path,
                "-stream_loop", "-1", "-i", mp3_path,
                "-filter_complex", filter_complex,
                "-map", "0:v:0",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                output_path
            ]
        else:
            cmd = [
                ffmpeg_bin, "-y",
                "-i", video_path,
                "-stream_loop", "-1", "-i", mp3_path,
                "-filter_complex", f"[1:a]volume={m_vol}[aout]",
                "-map", "0:v:0",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                output_path
            ]

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            return {"status": "error", "message": f"FFmpeg mix failed: {res.stderr[-300:]}"}

        music_label = f"Local MP3: {os.path.basename(mp3_path)} ({int(m_vol*100)}% / Orig {int(v_vol*100)}%)"
        if video_id:
            self.sheet.update_status_by_id(
                video_id=video_id,
                repost_status="Ready to Post",
                ready_mp4_path=os.path.abspath(output_path),
                music_used=music_label
            )

        return {
            "status": "success",
            "scenario": "Scenario A (Reel + Local MP3)",
            "input_video": os.path.abspath(video_path),
            "mp3_used": os.path.basename(mp3_path),
            "original_volume": v_vol,
            "music_volume": m_vol,
            "output_path": os.path.abspath(output_path)
        }

    def generate_quote_card_image(
        self,
        hook_text: str,
        sub_text: str = "Built 100% locally with Meta Nexus Agent",
        author_handle: str = "@raulfinternational",
        output_image_path: Optional[str] = None
    ) -> str:
        """Generates a crisp 1080x1920 (9:16) dark-mode visual card for Scenario B (Image + Music -> Reel)."""
        if not output_image_path:
            slug = abs(hash(hook_text)) % 100000
            output_image_path = os.path.join(self.ready_dir, f"card_{slug}.png")

        img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)

        # Subtle border frame
        draw.rounded_rectangle([(60, 180), (1020, 1740)], radius=36, outline=(56, 189, 248), width=3)

        try:
            title_font = ImageFont.truetype("arialbd.ttf", 54)
            sub_font = ImageFont.truetype("arial.ttf", 36)
            tag_font = ImageFont.truetype("arialbd.ttf", 32)
        except Exception:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
            tag_font = ImageFont.load_default()

        draw.text((110, 260), "META NEXUS STUDIO // RECEIPT", fill=(56, 189, 248), font=tag_font)

        # Wrap hook text
        words = hook_text.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(" ".join(cur_line)) > 26:
                lines.append(" ".join(cur_line[:-1]))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        y = 480
        for line in lines[:10]:
            draw.text((110, y), line, fill=(248, 250, 252), font=title_font)
            y += 76

        draw.text((110, 1420), sub_text[:65], fill=(148, 163, 184), font=sub_font)
        draw.text((110, 1600), author_handle, fill=(52, 211, 153), font=tag_font)

        img.save(output_image_path)
        return os.path.abspath(output_image_path)

    def image_and_mp3_to_reel(
        self,
        image_path: str,
        mp3_name_or_path: str,
        duration_sec: Optional[int] = None,
        music_volume: Optional[float] = None,
        video_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scenario B (Static Image Post + Music):
        Loops static .jpg/.png into a 15-second 1080x1920 .mp4 container merged with .mp3 audio track.
        """
        if not os.path.exists(image_path):
            return {"status": "error", "message": f"Image not found: {image_path}"}

        mp3_path = mp3_name_or_path
        if not os.path.exists(mp3_path):
            mp3_path = os.path.join(self.music_dir, os.path.basename(mp3_name_or_path))
        if not os.path.exists(mp3_path):
            tracks = self.list_music_tracks()
            if not tracks:
                return {"status": "error", "message": "No MP3 track found in music_library."}
            mp3_path = tracks[0]["path"]

        dur = duration_sec if duration_sec is not None else self.default_img_dur
        m_vol = music_volume if music_volume is not None else self.music_vol

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        song_base = os.path.splitext(os.path.basename(mp3_path))[0]
        output_path = os.path.join(self.ready_dir, f"{base_name}_reel_{dur}s_{song_base}.mp4")

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            return {"status": "error", "message": "FFmpeg binary not found on PATH."}

        vf_scale_pad = (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x0f172a,setsar=1"
        )
        cmd = [
            ffmpeg_bin, "-y",
            "-loop", "1", "-i", image_path,
            "-stream_loop", "-1", "-i", mp3_path,
            "-vf", vf_scale_pad,
            "-af", f"volume={m_vol}",
            "-c:v", "libx264", "-t", str(dur), "-pix_fmt", "yuv420p", "-r", "30", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            return {"status": "error", "message": f"FFmpeg image-to-reel failed: {res.stderr[-300:]}"}

        if video_id:
            self.sheet.update_status_by_id(
                video_id=video_id,
                repost_status="Ready to Post",
                ready_mp4_path=os.path.abspath(output_path),
                music_used=f"Image+MP3 ({dur}s): {os.path.basename(mp3_path)}"
            )

        return {
            "status": "success",
            "scenario": "Scenario B (Static Image + Music -> 1080x1920 Reel)",
            "image_path": os.path.abspath(image_path),
            "mp3_used": os.path.basename(mp3_path),
            "duration_sec": dur,
            "output_path": os.path.abspath(output_path)
        }

    def flag_native_ui_music(
        self,
        video_id: int,
        native_song_query: str
    ) -> Dict[str, Any]:
        """
        Scenario C (Native Platform Audio):
        Flags row in saved_videos_log.xlsx with NATIVE_UI:<song_name> so the Playwright browser
        uploader searches and attaches it inside Instagram/Facebook's native 'Add Music' modal.
        """
        rows = [r for r in self.sheet.get_all_rows() if r["id"] == video_id]
        if not rows:
            return {"status": "error", "message": f"Video ID {video_id} not found in Master Sheet."}

        row = rows[0]
        src_mp4 = row.get("local_mp4_path", "")
        ready_mp4 = row.get("ready_mp4_path", "")
        if src_mp4 and os.path.exists(src_mp4) and not ready_mp4:
            dest = os.path.join(self.ready_dir, os.path.basename(src_mp4))
            if os.path.abspath(src_mp4) != os.path.abspath(dest):
                shutil.copy2(src_mp4, dest)
            ready_mp4 = os.path.abspath(dest)

        flag_str = f"NATIVE_UI:{native_song_query.strip()}"
        updated = self.sheet.update_status_by_id(
            video_id=video_id,
            repost_status="Ready to Post",
            ready_mp4_path=ready_mp4,
            music_used=flag_str
        )
        return {
            "status": "success",
            "scenario": "Scenario C (Native Platform Audio Flagged)",
            "video_id": video_id,
            "music_used": flag_str,
            "ready_mp4_path": ready_mp4,
            "row": updated
        }
