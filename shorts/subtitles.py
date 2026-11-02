"""Word-timed, big centered captions as an ASS file."""
from .config import H, W


def _ts(sec: float) -> str:
    sec = max(0.0, sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _clean(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", " ")


def write_ass(words: list[dict], channel: dict, duration: float, out_path: str) -> str:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{channel['font']},{channel['font_size']},{channel['caption_color']},&H00FFFFFF,{channel['caption_outline']},&H80000000,-1,0,0,0,100,100,0,0,1,8,3,2,60,60,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    n = max(1, int(channel.get("words_per_caption", 2)))
    groups = [words[i:i + n] for i in range(0, len(words), n)]
    pop = r"{\fscx70\fscy70\t(0,90,\fscx100\fscy100)}" if channel.get("caption_pop") else ""
    lines = []
    for i, g in enumerate(groups):
        start = g[0]["start"]
        end = groups[i + 1][0]["start"] if i + 1 < len(groups) else min(duration, g[-1]["end"] + 0.4)
        text = _clean(" ".join(w["text"] for w in g))
        lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Cap,,0,0,0,,{pop}{text}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines) + "\n")
    return out_path
