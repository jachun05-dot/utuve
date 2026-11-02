"""Free Korean TTS via edge-tts, with word timings for captions."""
import asyncio
import os
import ssl

import aiohttp
import edge_tts


def _ssl_context():
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    return ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()


async def _speak(text, voice, rate, pitch, out_path):
    comm = edge_tts.Communicate(
        text, voice, rate=rate, pitch=pitch, boundary="WordBoundary",
        connector=aiohttp.TCPConnector(ssl=_ssl_context()),
        proxy=os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"),
    )
    words = []
    with open(out_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7  # 100ns units -> seconds
                words.append({"text": chunk["text"], "start": start,
                              "end": start + chunk["duration"] / 1e7})
    return words


def speak(text: str, channel: dict, out_path: str) -> list[dict]:
    for attempt in range(3):
        try:
            return asyncio.run(_speak(text, channel["voice"], channel["rate"],
                                      channel["pitch"], out_path))
        except Exception:
            if attempt == 2:
                raise
    return []
