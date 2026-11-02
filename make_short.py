"""Make YouTube Shorts automatically.

예시:
  python make_short.py --channel kids_edu --topic "문어"
  python make_short.py --channel teen_facts --count 3
  python make_short.py --channel kids_edu --script-file examples/kids_octopus.json
  python make_short.py --channel teen_facts --upload
"""
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from shorts import aivideo, render, subtitles, tts, visuals
from shorts.config import ROOT, load_channel, load_env


def history_path(cid):
    return ROOT / "output" / cid / "history.json"


def load_history(cid):
    p = history_path(cid)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_history(cid, items):
    p = history_path(cid)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def make_one(channel, topic=None, script_file=None, upload=False):
    history = load_history(channel["id"])
    if script_file:
        meta = json.loads(Path(script_file).read_text(encoding="utf-8"))
    else:
        from shorts.script import write_script
        print("대본 작성 중...")
        meta = write_script(channel, topic, [h["topic"] for h in history])
    print(f"주제: {meta['topic']} / 제목: {meta['title']}")

    slug = re.sub(r"[^\w가-힣]+", "_", meta["topic"])[:30].strip("_")
    workdir = ROOT / "output" / channel["id"] / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}"
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "script.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    used, scene_files = set(), []
    for i, sc in enumerate(meta["scenes"]):
        print(f"  장면 {i + 1}/{len(meta['scenes'])}: {sc['narration'][:30]}")
        audio = f"voice_{i:02d}.mp3"
        words = tts.speak(sc["narration"], channel, str(workdir / audio))
        dur = render.duration(str(workdir / audio)) + render.TAIL
        ass = subtitles.write_ass(words, channel, dur, str(workdir / f"sub_{i:02d}.ass"))
        overlay = visuals.headline_overlay(sc["on_screen_text"], channel, str(workdir / f"head_{i:02d}.png"))
        bg, is_video = None, False
        ai_limit = channel.get("ai_video_scenes", "all")
        if ai_limit == "all" or i < int(ai_limit):
            got = aivideo.generate(sc.get("video_prompt") or sc["visual_query"], channel)
            if got:
                bg, is_video = got
        if not bg:
            bg = visuals.pexels_video(sc["visual_query"], used)
            is_video = bool(bg)
        if not bg:
            bg = visuals.gradient_background(channel, f"{meta['topic']}{i}", str(workdir / f"bg_{i:02d}.png"))
        scene_files.append(render.render_scene(
            workdir, i, str(Path(bg).resolve()), is_video,
            Path(overlay).name, audio, Path(ass).name))

    final = render.concat(workdir, scene_files, channel)
    print(f"완성: {final} ({render.duration(str(final)):.1f}초)")

    entry = {"topic": meta["topic"], "title": meta["title"], "file": str(final),
             "made_for_kids": channel["made_for_kids"], "created": datetime.now().isoformat()}
    if upload:
        from shorts.upload import upload as yt_upload
        entry["url"] = yt_upload(final, meta, channel)
        print(f"업로드 완료({channel.get('privacy', 'private')}): {entry['url']}")
    save_history(channel["id"], history + [entry])
    return final


def main():
    ap = argparse.ArgumentParser(description="유튜브 쇼츠 자동 생성")
    ap.add_argument("--channel", required=True, help="channels/ 폴더의 설정 이름 (kids_edu, teen_facts)")
    ap.add_argument("--topic", help="주제 (생략하면 자동 선택)")
    ap.add_argument("--count", type=int, default=1, help="만들 영상 개수")
    ap.add_argument("--script-file", help="직접 쓴 대본 JSON (AI 대본 생략)")
    ap.add_argument("--upload", action="store_true", help="유튜브에 업로드 (기본 비공개)")
    args = ap.parse_args()

    load_env()
    channel = load_channel(args.channel)
    for n in range(args.count):
        if args.count > 1:
            print(f"\n=== {n + 1}/{args.count} ===")
        make_one(channel, args.topic, args.script_file, args.upload)


if __name__ == "__main__":
    main()
