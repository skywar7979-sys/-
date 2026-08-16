"""Publishes a rendered video to Instagram as a Reel via the Meta Graph API.

Instagram's API does not accept a raw file upload for video — it needs a
public HTTPS URL it can fetch from. This module expects PUBLIC_VIDEO_HOST_UPLOAD_URL
to point at an endpoint (e.g. an S3 pre-signed upload, or your own storage API)
that accepts a POST of the file bytes and returns the resulting public URL as
plain text. Wire up whatever host you use for that in _host_video().

Requires:
  - An Instagram professional account linked to a Facebook Page
  - A long-lived Page access token with instagram_content_publish permission
  - IG_BUSINESS_ACCOUNT_ID, IG_ACCESS_TOKEN in the environment
"""

import os
import time

import requests

GRAPH_API = "https://graph.facebook.com/v20.0"


def _host_video(video_path: str) -> str:
    upload_url = os.environ["PUBLIC_VIDEO_HOST_UPLOAD_URL"]
    with open(video_path, "rb") as f:
        resp = requests.post(upload_url, data=f.read(), timeout=120)
    resp.raise_for_status()
    return resp.text.strip()


def upload(video_path: str, title: str, description: str, hashtags: list[str]) -> str:
    ig_user_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]

    video_url = _host_video(video_path)
    caption_tags = " ".join(f"#{tag.replace(' ', '')}" for tag in hashtags)
    caption = f"{title}\n\n{description}\n\n{caption_tags}"

    create_resp = requests.post(
        f"{GRAPH_API}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=60,
    )
    create_resp.raise_for_status()
    container_id = create_resp.json()["id"]

    status = "IN_PROGRESS"
    while status == "IN_PROGRESS":
        time.sleep(5)
        status_resp = requests.get(
            f"{GRAPH_API}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json()["status_code"]

    if status != "FINISHED":
        raise RuntimeError(f"Instagram media container failed to process: {status}")

    publish_resp = requests.post(
        f"{GRAPH_API}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
        timeout=60,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]
