"""Assemble scenes into a vertical Short with ffmpeg."""
import random
import subprocess
from pathlib import Path

from .config import FPS, H, ROOT, W

TAIL = 0.25  # short pause after each scene's narration


def _run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg 실패:\n{' '.join(cmd)}\n{p.stderr[-2000:]}")


def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(out.stdout.strip())


def render_scene(workdir: Path, idx: int, bg: str, bg_is_video: bool,
                 overlay: str, audio: str, ass: str) -> str:
    """All inputs are file names relative to workdir (keeps ffmpeg filter paths simple)."""
    dur = duration(str(workdir / audio)) + TAIL
    frames = int(dur * FPS) + 1
    out = f"scene_{idx:02d}.mp4"
    if bg_is_video:
        # Short clip + longer narration: slow it down a little (up to 1.4x) before looping.
        stretch = min(max(dur / duration(bg), 1.0), 1.4)
        bg_in = ["-stream_loop", "-1", "-i", bg]
        bg_f = (f"[0:v]setpts={stretch:.3f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},fps={FPS},setsar=1[bg]")
    else:
        bg_in = ["-i", bg]
        bg_f = (f"[0:v]scale={int(W*1.15)}:{int(H*1.15)},zoompan=z='min(zoom+0.0007,1.15)'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},setsar=1[bg]")
    cmd = ["ffmpeg", "-y", *bg_in, "-i", overlay, "-i", audio,
           "-filter_complex", f"{bg_f};[bg][1:v]overlay=0:0,ass={ass}[v];[2:a]apad[a]",
           "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "160k", out]
    _run(cmd, workdir)
    return out


def concat(workdir: Path, scenes: list[str], channel: dict, out_name: str = "final.mp4") -> Path:
    (workdir / "scenes.txt").write_text("".join(f"file '{s}'\n" for s in scenes))
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "scenes.txt",
          "-c", "copy", "joined.mp4"], workdir)

    music_dir = ROOT / "assets" / "music" / channel["id"]
    tracks = [p for p in music_dir.glob("*") if p.suffix.lower() in (".mp3", ".m4a", ".wav")]
    if not tracks:
        (workdir / "joined.mp4").replace(workdir / out_name)
        return workdir / out_name
    track = str(random.choice(tracks).resolve())
    vol = channel.get("music_volume", 0.1)
    _run(["ffmpeg", "-y", "-i", "joined.mp4", "-stream_loop", "-1", "-i", track,
          "-filter_complex", f"[1:a]volume={vol}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
          "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
          "-shortest", out_name], workdir)
    return workdir / out_name
