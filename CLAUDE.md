# utuve — notes for Claude

YouTube Shorts generator for two channels. Entry point: `make_short.py`.
User is Korean-speaking; reply in Korean, simply. Target PC: Windows, RTX 2070 Super (8GB VRAM).

## Layout
- `channels/*.yaml` — per-channel settings. `kids_edu` must keep `made_for_kids: true`.
- `shorts/script.py` Claude script (needs ANTHROPIC_API_KEY) · `tts.py` edge-tts (free)
- `shorts/comfy.py` local ComfyUI backend · `aivideo.py` backend dispatch (+ fal.ai)
- `shorts/visuals.py` Pexels / gradient / headline · `subtitles.py` ASS captions · `render.py` ffmpeg
- `workflows/*.json` ComfyUI API-format workflows; `{{PROMPT}}` and `"{{SEED}}"` are placeholders.
- `.env` holds keys (copy from `.env.example`). Never commit `.env`, `secrets/`, `output/`, `cache/`.

## Windows setup checklist
- Python 3.10+, `pip install -r requirements.txt`
- `winget install Gyan.FFmpeg` (needs libass; check `ffmpeg -filters | findstr ass`)
- Font: NanumSquareRound (free, Naver) — used by captions and headlines
- ComfyUI Desktop (comfy.org/download), default API at http://127.0.0.1:8188
- Models (see README): SDXL base → models/checkpoints; Wan 2.1 1.3B fp16 → models/diffusion_models,
  umt5_xxl_fp8_e4m3fn_scaled → models/text_encoders, wan_2.1_vae → models/vae
- 8GB VRAM: if Wan OOMs, lower `length` in the workflow or use low-VRAM mode.
  If a workflow fails validation, re-export from ComfyUI's built-in template (README explains).

## Smoke test
`python make_short.py --channel kids_edu --script-file examples/kids_octopus.json`
→ `output/kids_edu/<timestamp>_문어/final.mp4`. Pass = ~47s 1080x1920 video with voice + captions.
