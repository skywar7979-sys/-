"""CLI entrypoint.

  python -m src.main run       generate + publish the next un-posted queue item
  python -m src.main generate  render the next un-posted item, don't publish
"""

import os
import sys

import yaml
from dotenv import load_dotenv

from src.generate import render_item
from src.state import load_posted_ids, mark_posted

load_dotenv()

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "content_queue.yaml")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

PLATFORM_MODULES = {}


def _load_platform(name: str):
    if name not in PLATFORM_MODULES:
        if name == "youtube":
            from src.platforms import youtube as mod
        elif name == "instagram":
            from src.platforms import instagram as mod
        elif name == "tiktok":
            from src.platforms import tiktok as mod
        else:
            raise ValueError(f"Unknown platform: {name}")
        PLATFORM_MODULES[name] = mod
    return PLATFORM_MODULES[name]


def _next_item() -> dict | None:
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = yaml.safe_load(f)["items"]
    posted = load_posted_ids()
    for item in queue:
        if item["id"] not in posted:
            return item
    return None


def generate() -> str | None:
    item = _next_item()
    if item is None:
        print("No un-posted items left in the queue.")
        return None
    path = render_item(item, OUTPUT_DIR)
    print(f"Rendered {item['id']} -> {path}")
    return path


def run() -> None:
    item = _next_item()
    if item is None:
        print("No un-posted items left in the queue.")
        return

    video_path = render_item(item, OUTPUT_DIR)
    platforms = item.get("platforms") or os.environ.get("PLATFORMS", "youtube").split(",")

    for platform_name in platforms:
        platform_name = platform_name.strip()
        if not platform_name:
            continue
        module = _load_platform(platform_name)
        post_id = module.upload(
            video_path=video_path,
            title=item["title"],
            description=item["script"],
            hashtags=item.get("hashtags", []),
        )
        print(f"Published {item['id']} to {platform_name}: {post_id}")

    mark_posted(item["id"])


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "run"
    if command == "run":
        run()
    elif command == "generate":
        generate()
    else:
        print("Usage: python -m src.main [run|generate]")
        sys.exit(1)


if __name__ == "__main__":
    main()
