"""Write a Shorts script with Claude (structured JSON output)."""
import json
import os

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
                },
                "required": ["narration", "on_screen_text", "visual_query"],
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
- title: 40자 이내, 클릭하고 싶지만 낚시가 아닌 제목.
- description: 2~3문장 요약 + 마지막 줄에 해시태그 3개(#shorts 포함).
- tags: 8~12개.
- 매번 새로운 각도와 구성으로 쓰세요. 다른 영상과 똑같은 틀을 반복하지 마세요."""


def write_script(channel: dict, topic: str | None, recent_topics: list[str]) -> dict:
    client = anthropic.Anthropic()
    model = os.environ.get("CLAUDE_MODEL") or "claude-opus-5-5"

    if topic:
        ask = f"주제: {topic}"
    else:
        avoid = ", ".join(recent_topics[-60:]) or "없음"
        ask = (f"다음 범위에서 새 주제를 하나 골라 쓰세요: {channel['topic_pool']}\n"
               f"이미 다룬 주제(피하세요): {avoid}")

    user = (f"{ask}\n\n장면 수: {channel['scene_count']}개, "
            f"전체 길이: 약 {channel['target_seconds']}초 분량.")

    response = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        system=BASE_RULES + "\n\n[채널 지침]\n" + channel["audience_prompt"],
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
