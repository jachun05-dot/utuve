"""Upload to YouTube (Data API v3). Each channel has its own login token."""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .config import ROOT

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SECRETS = ROOT / "secrets"


def _credentials(channel_id: str) -> Credentials:
    token = SECRETS / f"token_{channel_id}.json"
    client_secret = SECRETS / "client_secret.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not client_secret.exists():
            raise SystemExit("secrets/client_secret.json 이 없습니다. README의 '업로드 설정'을 보세요.")
        print(f"브라우저에서 [{channel_id}] 채널의 구글 계정으로 로그인하세요.")
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0)
        SECRETS.mkdir(exist_ok=True)
        token.write_text(creds.to_json())
    return creds


def upload(video: Path, meta: dict, channel: dict) -> str:
    youtube = build("youtube", "v3", credentials=_credentials(channel["id"]))
    tags = list(dict.fromkeys(meta.get("tags", []) + channel.get("default_tags", [])))
    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta["description"][:4900],
            "tags": tags[:30],
            "categoryId": channel.get("category_id", "22"),
            "defaultLanguage": "ko",
            "defaultAudioLanguage": "ko",
        },
        "status": {
            "privacyStatus": channel.get("privacy", "private"),
            "selfDeclaredMadeForKids": bool(channel["made_for_kids"]),
        },
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=-1, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return f"https://youtube.com/shorts/{resp['id']}"
