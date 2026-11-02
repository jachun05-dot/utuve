# utuve — 유튜브 쇼츠 자동 생성기

주제 → AI 대본 → 무료 AI 음성 → 스톡 영상/배경 → 자막 → 세로 쇼츠(1080x1920) → (선택) 유튜브 업로드

채널 두 개를 따로 운영하도록 설정되어 있어요.

| 채널 설정 | 대상 | 아동용 | 스타일 |
|---|---|---|---|
| `channels/kids_edu.yaml` | 3~7세 | **예** | 차분한 교육형 (동물, 숫자, 색깔…) |
| `channels/teen_facts.yaml` | 13세 이상 | 아니요 | 빠른 템포 "몰랐던 사실" |

## 설치

```bash
sudo apt install ffmpeg fonts-nanum      # 맥: brew install ffmpeg (폰트는 assets/fonts/font.ttf 에 넣기)
pip install -r requirements.txt
cp .env.example .env                      # 키 입력
```

- `ANTHROPIC_API_KEY`: 대본 자동 작성 (영상 1개에 몇십 원 수준)
- `PEXELS_API_KEY`: 무료 스톡 영상 (pexels.com/api 에서 무료 발급). **없으면 단색 배경이라 꼭 받으세요.**
- 음성(edge-tts)은 무료, 키 필요 없음

## 사용법

```bash
python make_short.py --channel kids_edu --topic "문어"
python make_short.py --channel teen_facts --count 5          # 주제 자동 선택, 5개
python make_short.py --channel kids_edu --script-file examples/kids_octopus.json   # 직접 쓴 대본 (API 키 불필요)
```

결과물은 `output/<채널>/<날짜_주제>/final.mp4` 에 생기고, `script.json` 에 제목·설명·태그가 저장돼요.
이미 만든 주제는 `history.json` 에 기록되어 다음에 겹치지 않게 골라요.

배경음악: `assets/music/kids_edu/`, `assets/music/teen_facts/` 에 mp3를 넣으면 자동으로 깔려요.
**유튜브 오디오 보관함**처럼 저작권 문제가 없는 음악만 쓰세요.

## 업로드 설정 (선택)

1. Google Cloud Console에서 프로젝트 생성 → **YouTube Data API v3** 사용 설정
2. OAuth 클라이언트 ID(데스크톱 앱) 생성 → JSON을 `secrets/client_secret.json` 으로 저장
3. `python make_short.py --channel kids_edu --upload` → 브라우저에서 **그 채널 계정**으로 로그인
   (채널마다 토큰이 `secrets/token_<채널>.json` 으로 따로 저장돼요)

- 구글 앱 심사 전에는 API 업로드 영상이 **비공개로 고정**돼요. 스튜디오에서 확인 후 직접 공개로 바꾸세요.
- 아동용 여부(`made_for_kids`)는 채널 설정대로 자동 지정돼요. 키즈 채널은 절대 false로 바꾸지 마세요(COPPA 벌금).

## 수익화 체크리스트

- YPP 조건: 구독자 1,000명 + (쇼츠 90일 조회수 1,000만 **또는** 롱폼 12개월 시청 4,000시간)
- 유튜브는 **반복적·대량생산 콘텐츠**의 수익화를 막아요. 올리기 전에 매번
  - 대본 사실 확인 (특히 숫자, 역사, 과학)
  - 영상이 주제와 맞는지 확인 (스톡 영상이 엉뚱할 수 있음)
  - 하루 1~3개 정도로, 양보다 질
- 키즈 채널은 광고 단가가 낮아요. 수익은 teen_facts 쪽이 더 빨리 날 가능성이 높아요.
