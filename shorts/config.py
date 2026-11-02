import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30


def load_env(path: Path = ROOT / ".env") -> None:
    """Load KEY=VALUE lines from .env without overriding real env vars."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if value.strip():
            os.environ.setdefault(key.strip(), value.strip())


def load_channel(channel_id: str) -> dict:
    path = ROOT / "channels" / f"{channel_id}.yaml"
    if not path.exists():
        raise SystemExit(f"채널 설정이 없습니다: {path}")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg["id"] = channel_id
    return cfg
