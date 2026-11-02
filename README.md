# utuve — 유튜브 쇼츠 자동 생성기

주제 → AI 대본 → 무료 AI 음성 → AI 그림·영상(내 그래픽카드, 무료) / 스톡 영상 → 자막 → 세로 쇼츠(1080x1920) → (선택) 유튜브 업로드

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
- `FAL_KEY`: (선택) 유료 AI 영상. 기본은 무료 ComfyUI라 필요 없어요.
- 음성(edge-tts)은 무료, 키 필요 없음

## 무료 AI 그림·영상: ComfyUI (내 그래픽카드 사용)

기본 설정은 **ComfyUI** 로 내 PC에서 공짜로 생성해요. 배경 순서: **AI → Pexels 스톡 → 단색**

| 채널 | 기본 방식 | RTX 2070 Super(8GB) 기준 속도 |
|---|---|---|
| 키즈 | SDXL 그림 + 카메라 움직임(줌인/줌아웃/패닝) 전 장면 | 장면당 20~40초 |
| 10대 | Wan 2.1 AI 영상 앞 2장면 + 나머지 스톡 | 클립당 5~15분 |

### 설치 (Windows 기준)

1. **ComfyUI 데스크톱** 설치: https://www.comfy.org/download
2. 모델 파일 내려받아 ComfyUI `models` 폴더에 넣기
   - 그림(SDXL): `sd_xl_base_1.0.safetensors` → `models/checkpoints/`
     (huggingface.co/stabilityai/stable-diffusion-xl-base-1.0)
   - 영상(Wan 2.1 1.3B, huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged 의 split_files 안)
     - `wan2.1_t2v_1.3B_fp16.safetensors` → `models/diffusion_models/`
     - `umt5_xxl_fp8_e4m3fn_scaled.safetensors` → `models/text_encoders/`
     - `wan_2.1_vae.safetensors` → `models/vae/`
3. ComfyUI를 켜 둔 상태에서 `python make_short.py ...` 실행 (같은 PC)
4. 그 외 필요한 것: `winget install ffmpeg`, 폰트 **나눔스퀘어라운드** 설치 (네이버 무료 폰트)

### 잘 안 될 때

- **메모리 부족(out of memory):** ComfyUI 설정에서 low VRAM 모드를 켜거나, `workflows/wan21_t2v_1.3b.json` 의 `length` 를 33으로 줄이세요.
- **워크플로 오류:** ComfyUI 버전에 따라 노드 이름이 다를 수 있어요. 그럴 땐
  ComfyUI 기본 템플릿(Wan 2.1 텍스트→영상)을 열고, 프롬프트 칸에 `{{PROMPT}}` 를 적은 뒤
  **Export (API)** 로 저장 → JSON 안의 `seed` 값을 `"{{SEED}}"` 로 바꾸고 → 채널 설정의 `comfy_workflow` 에 그 파일 경로를 넣으세요.
- **키즈 그림체:** SDXL 기본 모델 대신 만화풍 SDXL 모델을 쓰면 훨씬 귀여워요. 이때는 **상업적 이용 허용** 라이선스인지 꼭 확인하세요. 파일 이름을 `workflows/sdxl_image.json` 의 `ckpt_name` 에 넣으면 돼요.
- 같은 프롬프트 결과는 `cache/comfy/` 에 저장돼서 다시 만들 때 빨라요.

## (선택) 유료 AI 영상: fal.ai

장면마다 AI가 5초짜리 클립을 새로 만들어요. 배경은 아래 순서로 정해져요.
**AI 영상 → (실패하거나 꺼져 있으면) Pexels 스톡 → 단색 배경**

채널 설정에서 `ai_backend: fal` 로 바꾸고 `.env` 에 `FAL_KEY` 를 넣으면 돼요.

| 설정 | 뜻 |
|---|---|
| `ai_model` | fal.ai 모델 ID. 예: `fal-ai/kling-video/v3/turbo/standard/text-to-video`(기본), `fal-ai/kling-video/v1.6/standard/text-to-video`(더 저렴), `fal-ai/veo3.1` |
| `ai_video_scenes` | `all` 또는 숫자. 숫자면 앞 장면만 AI로 만들고 나머지는 스톡 영상 |
| `ai_style` | 모든 장면에 붙는 그림체 설명 (키즈: 귀여운 3D 만화 / 10대: 시네마틱 실사) |
| `ai_extra_params` | 모델별 추가 옵션 (선택) |

**비용 (기본 모델 기준, 초당 약 $0.112)**
- 키즈 (7장면 모두 AI): 영상 1개에 약 $3.9 (약 5,500원)
- 10대 (앞 3장면만 AI): 영상 1개에 약 $1.7 (약 2,400원)
- 같은 프롬프트는 `cache/ai_video/` 에 저장돼서 다시 만들 때 돈이 안 들어요.
- 가격은 자주 바뀌니 fal.ai/pricing 에서 확인하세요.

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
