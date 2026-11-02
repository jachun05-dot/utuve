"""Free local generation through ComfyUI (runs on your own GPU).

Workflows are ComfyUI "API format" JSON files. Any string value containing
{{PROMPT}} gets the scene prompt, and any value equal to "{{SEED}}" gets a seed.
"""
import hashlib
import json
import time
import uuid

import requests

from .config import ROOT

CACHE = ROOT / "cache" / "comfy"
MEDIA = (".mp4", ".webm", ".gif", ".webp", ".png", ".jpg", ".jpeg")
VIDEO = (".mp4", ".webm", ".gif", ".webp")


def _fill(node, prompt, seed):
    if isinstance(node, dict):
        return {k: _fill(v, prompt, seed) for k, v in node.items()}
    if isinstance(node, list):
        return [_fill(v, prompt, seed) for v in node]
    if node == "{{SEED}}":
        return seed
    if isinstance(node, str) and "{{PROMPT}}" in node:
        return node.replace("{{PROMPT}}", prompt)
    return node


def generate(prompt: str, workflow_file: str, url: str, timeout: int = 3600):
    """Return (local_path, is_video) or None on failure."""
    wf_path = ROOT / workflow_file
    workflow_text = wf_path.read_text(encoding="utf-8")
    key = hashlib.sha256((workflow_text + prompt).encode()).hexdigest()[:16]
    CACHE.mkdir(parents=True, exist_ok=True)
    for ext in MEDIA:
        cached = CACHE / f"{key}{ext}"
        if cached.exists():
            return str(cached), ext in VIDEO

    seed = int(key[:8], 16)  # same prompt -> same seed -> reproducible
    workflow = _fill(json.loads(workflow_text), prompt, seed)
    try:
        r = requests.post(f"{url}/prompt", json={"prompt": workflow, "client_id": str(uuid.uuid4())},
                          timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"워크플로 오류: {r.text[:500]}")
        pid = r.json()["prompt_id"]
        deadline = time.time() + timeout
        while True:
            hist = requests.get(f"{url}/history/{pid}", timeout=30).json()
            if pid in hist:
                entry = hist[pid]
                if entry.get("status", {}).get("status_str") == "error":
                    raise RuntimeError("ComfyUI 실행 중 오류 (ComfyUI 창의 로그를 확인하세요)")
                break
            if time.time() > deadline:
                raise TimeoutError("ComfyUI 생성 시간 초과")
            time.sleep(3)

        files = [f for out in entry["outputs"].values() for lst in out.values()
                 if isinstance(lst, list) for f in lst
                 if isinstance(f, dict) and str(f.get("filename", "")).lower().endswith(MEDIA)]
        if not files:
            raise RuntimeError("ComfyUI 결과물에 이미지/영상이 없습니다")
        files.sort(key=lambda f: not f["filename"].lower().endswith(VIDEO))  # prefer video
        f = files[0]
        ext = "." + f["filename"].rsplit(".", 1)[-1].lower()
        data = requests.get(f"{url}/view", params={"filename": f["filename"],
                            "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")},
                            timeout=120)
        data.raise_for_status()
        path = CACHE / f"{key}{ext}"
        path.write_bytes(data.content)
        return str(path), ext in VIDEO
    except requests.ConnectionError:
        print(f"  ! ComfyUI({url})에 연결할 수 없습니다. ComfyUI를 먼저 켜 주세요.")
        return None
    except Exception as e:
        print(f"  ! ComfyUI 생성 실패, 다른 배경으로 대체: {e}")
        return None
