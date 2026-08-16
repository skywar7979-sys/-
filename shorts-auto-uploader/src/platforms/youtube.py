"""Uploads a rendered video to YouTube as a Short.

Setup (one-time, done locally — not in CI):
  1. Create an OAuth client (type: Desktop) in Google Cloud Console with the
     YouTube Data API v3 enabled, download it as config/youtube_client_secret.json.
  2. Run `python -m src.oauth_bootstrap youtube` to complete the browser
     consent flow; this writes config/youtube_token.json.
  3. Store both files' contents as GitHub Actions secrets so CI can restore
     them before running (see .github/workflows/auto_upload.yml).
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _load_credentials() -> Credentials:
    token_file = os.environ["YOUTUBE_TOKEN_FILE"]
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def bootstrap_token() -> None:
    """Interactive, local-only: runs the OAuth consent flow and saves a token."""
    client_secret_file = os.environ["YOUTUBE_CLIENT_SECRET_FILE"]
    token_file = os.environ["YOUTUBE_TOKEN_FILE"]
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(token_file, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def upload(video_path: str, title: str, description: str, hashtags: list[str]) -> str:
    creds = _load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    tags_line = " ".join(f"#{tag.replace(' ', '')}" for tag in hashtags + ["shorts"])
    body = {
        "snippet": {
            "title": title[:100],
            "description": f"{description}\n\n{tags_line}",
            "tags": hashtags,
            "categoryId": "22",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response["id"]
