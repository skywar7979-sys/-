"""Renders a queue item into a vertical (1080x1920) short video with
narrated text over a solid background, ready for upload."""

import os

from gtts import gTTS
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
)

WIDTH, HEIGHT = 1080, 1920
BACKGROUND_COLOR = (17, 17, 24)
FONT = "DejaVu-Sans-Bold"


def _narration_clip(script: str, out_dir: str) -> AudioFileClip:
    audio_path = os.path.join(out_dir, "narration.mp3")
    gTTS(text=script, lang="ko").save(audio_path)
    return AudioFileClip(audio_path)


def _text_clip(text: str, duration: float, fontsize: int, y_pos) -> TextClip:
    clip = TextClip(
        text,
        fontsize=fontsize,
        font=FONT,
        color="white",
        method="caption",
        size=(WIDTH - 120, None),
        align="center",
    )
    return clip.set_position(("center", y_pos)).set_duration(duration)


def render_item(item: dict, out_dir: str) -> str:
    """Renders one content_queue item to an mp4 and returns its path."""
    os.makedirs(out_dir, exist_ok=True)

    narration = _narration_clip(item["script"], out_dir)
    duration = narration.duration + 0.6

    background = ColorClip(size=(WIDTH, HEIGHT), color=BACKGROUND_COLOR).set_duration(duration)
    title = _text_clip(item["title"], duration, fontsize=72, y_pos=HEIGHT * 0.32)
    body = _text_clip(item["script"], duration, fontsize=48, y_pos=HEIGHT * 0.55)

    video = CompositeVideoClip([background, title, body]).set_audio(narration)

    out_path = os.path.join(out_dir, f"{item['id']}.mp4")
    video.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=2,
        logger=None,
    )
    return out_path
