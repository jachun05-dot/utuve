"""Generative AI video clips via fal.ai (one key, many models: Kling, Veo, Hailuo, Wan...)."""
import hashlib
import json
import os
import time

import requests

from .config import ROOT

CACHE = ROOT / "cache" / "ai_video"
QUEUE = "https://queue.fal.run"


def _headers():
    return {"Authorization": f"Key {os.environ['FAL_KEY']}", "Content-Type": "application/json"}


def generate(prompt: str, channel: dict, timeout: int = 900) -> str | None:
    """Return a local mp4 path, or None if AI video is off / fails (caller falls back)."""
    if not os.environ.get("FAL_KEY"):
        return None
    model = channel.get("ai_model", "fal-ai/kling-video/v3/turbo/standard/text-to-video")
    full_prompt = f"{prompt}. {channel.get('ai_style', '')}".strip(". ")
    body = {"prompt": full_prompt, "aspect_ratio": "9:16",
            "duration": str(channel.get("ai_duration", "5")),
            **channel.get("ai_extra_params", {})}

    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(json.dumps([model, body], sort_keys=True).encode()).hexdigest()[:16]
    path = CACHE / f"{key}.mp4"
    if path.exists():
        return str(path)

    try:
        r = requests.post(f"{QUEUE}/{model}", headers=_headers(), json=body, timeout=30)
        r.raise_for_status()
        job = r.json()
        deadline = time.time() + timeout
        while True:
            s = requests.get(job["status_url"], headers=_headers(), timeout=30).json()
            if s.get("status") == "COMPLETED":
                if s.get("error"):
                    raise RuntimeError(s["error"])
                break
            if time.time() > deadline:
                raise TimeoutError("AI 영상 생성 시간 초과")
            time.sleep(4)
        result = requests.get(job["response_url"], headers=_headers(), timeout=30).json()
        url = result["video"]["url"]
        with requests.get(url, stream=True, timeout=120) as d:
            d.raise_for_status()
            with open(path, "wb") as f:
                for part in d.iter_content(1 << 20):
                    f.write(part)
        return str(path)
    except Exception as e:  # never kill the whole video for one clip
        print(f"  ! AI 영상 생성 실패, 다른 배경으로 대체: {e}")
        return None
