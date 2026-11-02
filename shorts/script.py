"""Write a Shorts script with Claude.

Two ways, picked automatically (or set SCRIPT_BACKEND=api|cli in .env):
- api: Anthropic API key (ANTHROPIC_API_KEY), billed per use
- cli: the Claude Code CLI logged in with a Pro/Max subscription (no extra cost,
       counts toward the subscription's usage limits)
"""
import json
import os
import shutil
import subprocess
import tempfile

import anthropic

SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string"},
                    "on_screen_text": {"type": "string"},
                    "visual_query": {"type": "string"},
                    "video_prompt": {"type": "string"},
                },
                "required": ["narration", "on_screen_text", "visual_query", "video_prompt"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["topic", "title", "description", "tags", "scenes"],
    "additionalProperties": False,
}

BASE_RULES = """당신은 유튜브 쇼츠 전문 작가입니다. 한국어 세로 쇼츠 대본을 씁니다.
- narration: 성우가 읽을 문장. 장면당 1~2문장, 말하듯 자연스럽게. 숫자는 한글로 읽기 쉽게 씁니다.
- on_screen_text: 화면 위쪽에 크게 띄울 짧은 문구(12자 이내).
- visual_query: 무료 스톡 영상 검색어. 영어 1~3단어의 구체적인 명사(예: "octopus", "night sky").
- video_prompt: AI 영상 생성용 영어 프롬프트. 한 장면(5초)을 구체적으로 묘사합니다:
  주인공, 동작, 배경, 카메라 움직임. 글자·자막·로고는 넣지 않습니다. 장면끼리 등장인물과 분위기가 이어지게 씁니다.
- title: 40자 이내, 클릭하고 싶지만 낚시가 아닌 제목.
- description: 2~3문장 요약 + 마지막 줄에 해시태그 3개(#shorts 포함).
- tags: 8~12개.
- 매번 새로운 각도와 구성으로 쓰세요. 다른 영상과 똑같은 틀을 반복하지 마세요."""


def _prompts(channel, topic, recent_topics):
    if topic:
        ask = f"주제: {topic}"
    else:
        avoid = ", ".join(recent_topics[-60:]) or "없음"
        ask = (f"다음 범위에서 새 주제를 하나 골라 쓰세요: {channel['topic_pool']}\n"
               f"이미 다룬 주제(피하세요): {avoid}")

    user = (f"{ask}\n\n장면 수: {channel['scene_count']}개, "
            f"전체 길이: 약 {channel['target_seconds']}초 분량.")
    system = BASE_RULES + "\n\n[채널 지침]\n" + channel["audience_prompt"]
    return system, user


def write_script(channel: dict, topic: str | None, recent_topics: list[str]) -> dict:
    backend = os.environ.get("SCRIPT_BACKEND", "").lower()
    if not backend:
        backend = "api" if os.environ.get("ANTHROPIC_API_KEY") else "cli"
    system, user = _prompts(channel, topic, recent_topics)
    if backend == "cli":
        return _via_cli(system, user)
    return _via_api(system, user)


def _via_api(system, user):
    client = anthropic.Anthropic()
    model = os.environ.get("CLAUDE_MODEL") or "claude-opus-5-5"
    response = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": "medium",
                       "format": {"type": "json_schema", "schema": SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"대본 생성이 거절되었습니다: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("대본이 너무 길어 잘렸습니다. 장면 수를 줄여 보세요.")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def _valid(data) -> bool:
    if not isinstance(data, dict) or not all(k in data for k in SCHEMA["required"]):
        return False
    need = SCHEMA["properties"]["scenes"]["items"]["required"]
    return bool(data["scenes"]) and all(
        isinstance(sc, dict) and all(isinstance(sc.get(k), str) and sc[k] for k in need)
        for sc in data["scenes"])


def _via_cli(system, user):
    exe = shutil.which("claude")
    if not exe:
        raise SystemExit("대본을 쓸 방법이 없습니다. Claude Code(구독)를 설치·로그인하거나 "
                         ".env 에 ANTHROPIC_API_KEY 를 넣어 주세요. 또는 --script-file 을 쓰세요.")
    prompt = (f"{system}\n\n{user}\n\n"
              "출력 형식: 아래 JSON 스키마에 맞는 JSON 객체 하나만 출력하세요. "
              "코드블록, 설명, 다른 말은 쓰지 마세요. 파일을 만들거나 도구를 쓰지 마세요.\n"
              + json.dumps(SCHEMA, ensure_ascii=False))
    last_err = ""
    for _ in range(3):
        # Run in an empty folder so the CLI doesn't pick up this project's files.
        with tempfile.TemporaryDirectory() as tmp:
            p = subprocess.run([exe, "-p", "--output-format", "json"], input=prompt,
                               capture_output=True, text=True, encoding="utf-8",
                               cwd=tmp, timeout=900)
        try:
            outer = json.loads(p.stdout)
            if outer.get("is_error"):
                raise ValueError(outer.get("result") or p.stderr)
            text = outer["result"]
            data = json.loads(text[text.index("{"):text.rindex("}") + 1])
            if _valid(data):
                return data
            last_err = "대본 형식이 맞지 않음"
        except (ValueError, KeyError) as e:
            last_err = str(e)[:300] or p.stderr[:300]
    raise RuntimeError(f"Claude Code로 대본 작성 실패: {last_err}")
