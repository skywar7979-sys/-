"""Tracks which content_queue items have already been published so the
scheduler never posts the same short twice."""

import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state.json")


def load_posted_ids() -> set:
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f).get("posted_ids", []))


def mark_posted(item_id: str) -> None:
    posted = load_posted_ids()
    posted.add(item_id)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"posted_ids": sorted(posted)}, f, ensure_ascii=False, indent=2)
