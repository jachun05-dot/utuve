"""Backgrounds: free Pexels stock video, or a generated gradient. Plus headline overlay."""
import hashlib
import os
import random
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from .config import H, ROOT, W

CACHE = ROOT / "cache" / "pexels"
FONT_PATHS = [
    "/usr/share/fonts/truetype/nanum/NanumSquareRoundEB.ttf",
    "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    str(ROOT / "assets" / "fonts" / "font.ttf"),
    "C:/Windows/Fonts/malgunbd.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]


def _font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise SystemExit("한글 폰트를 찾을 수 없습니다. assets/fonts/font.ttf 에 폰트를 넣어 주세요.")


def pexels_video(query: str, used: set) -> str | None:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    try:
        r = requests.get("https://api.pexels.com/videos/search",
                         headers={"Authorization": key},
                         params={"query": query, "orientation": "portrait",
                                 "per_page": 15, "size": "medium"}, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  ! Pexels 검색 실패({query}): {e}")
        return None
    for video in r.json().get("videos", []):
        if video["id"] in used:
            continue
        files = [f for f in video["video_files"]
                 if f.get("width") and f.get("height") and f["height"] > f["width"]
                 and f["height"] >= 1280 and f.get("file_type") == "video/mp4"]
        if not files:
            continue
        best = min(files, key=lambda f: abs(f["width"] - W))
        used.add(video["id"])
        CACHE.mkdir(parents=True, exist_ok=True)
        path = CACHE / f"{video['id']}_{best['width']}.mp4"
        if not path.exists():
            with requests.get(best["link"], stream=True, timeout=60) as d:
                d.raise_for_status()
                with open(path, "wb") as f:
                    for part in d.iter_content(1 << 20):
                        f.write(part)
        return str(path)
    return None


def gradient_background(channel: dict, seed: str, out_path: str) -> str:
    rnd = random.Random(hashlib.md5(seed.encode()).hexdigest())
    top, bottom = rnd.choice(channel["background_colors"])
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        draw.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    for _ in range(14):  # soft bubbles for some motion texture under zoom
        r = rnd.randint(40, 180)
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=tuple(min(255, c + 25) for c in rnd.choice([top, bottom])))
    img.save(out_path)
    return out_path


def headline_overlay(text: str, channel: dict, out_path: str) -> str:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if text.strip():
        draw = ImageDraw.Draw(img)
        font = _font(108)
        lines = textwrap.wrap(text.strip(), width=9) or [text]
        y = 260
        for line in lines[:2]:
            w = draw.textlength(line, font=font)
            draw.text(((W - w) / 2, y), line, font=font, fill=tuple(channel["headline_color"]),
                      stroke_width=10, stroke_fill=(0, 0, 0))
            y += 135
    img.save(out_path)
    return out_path
