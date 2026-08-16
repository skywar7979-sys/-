"""Publishes a rendered video to TikTok via the Content Posting API.

Requires a TikTok developer app with the Content Posting API scope approved
(this is a manual review process on TikTok's side, separate from writing this
code) and a user access token with video.publish scope.
"""

import os

import requests

API_BASE = "https://open.tiktokapis.com/v2"


def upload(video_path: str, title: str, description: str, hashtags: list[str]) -> str:
    access_token = os.environ["TIKTOK_ACCESS_TOKEN"]
    headers = {"Authorization": f"Bearer {access_token}"}

    caption_tags = " ".join(f"#{tag.replace(' ', '')}" for tag in hashtags)
    caption = f"{title} {description} {caption_tags}".strip()[:2200]

    video_size = os.path.getsize(video_path)
    init_resp = requests.post(
        f"{API_BASE}/post/publish/video/init/",
        headers=headers,
        json={
            "post_info": {
                "title": caption,
                "privacy_level": "PUBLIC_TO_EVERYONE",
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,
                "total_chunk_count": 1,
            },
        },
        timeout=30,
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()["data"]
    upload_url = init_data["upload_url"]
    publish_id = init_data["publish_id"]

    with open(video_path, "rb") as f:
        video_bytes = f.read()
    put_resp = requests.put(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
        },
        timeout=120,
    )
    put_resp.raise_for_status()

    return publish_id
