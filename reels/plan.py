"""Turn Claude's edit decisions into a precise, editable project plan (plan.json).

Claude picks *what* to keep. This module does the fiddly, deterministic part:
snapping cuts to word boundaries, removing dead air (jump cuts) and splitting
speech into short caption chunks. Everything is saved to plan.json, which the
studio edits and the renderer reads.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .planner import ClaudeEditPlan

DEFAULT_SETTINGS = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "max_pause": 0.35,      # silences longer than this become a jump cut
    "pad": 0.08,            # breathing room kept before/after words
    "caption_words": 3,     # max words per caption
    "caption_chars": 16,    # max characters per caption
}


def build_plan(claude: ClaudeEditPlan, clips: list[dict], words: list[list[dict]], settings: dict | None = None) -> dict:
    settings = {**DEFAULT_SETTINGS, **(settings or {})}
    segments: list[dict] = []
    captions: list[dict] = []

    for keep in claude.segments:
        if not 0 <= keep.clip < len(clips):
            continue
        duration = clips[keep.clip]["duration"]
        start, end = max(0.0, keep.start), min(duration, keep.end)
        if end - start < 0.2:
            continue
        clip_words = [w for w in words[keep.clip] if w["start"] >= start - 0.15 and w["end"] <= end + 0.15]

        if not clip_words:  # b-roll / silent piece: keep as-is
            segments.append(_segment(len(segments), keep.clip, start, end, keep.reason, ""))
            continue

        for group in _split_on_pauses(clip_words, settings["max_pause"]):
            seg_start = max(0.0, group[0]["start"] - settings["pad"])
            seg_end = min(duration, group[-1]["end"] + settings["pad"])
            seg = _segment(len(segments), keep.clip, seg_start, seg_end, keep.reason,
                           " ".join(w["word"] for w in group))
            segments.append(seg)
            for chunk in _caption_chunks(group, settings["caption_words"], settings["caption_chars"]):
                captions.append({
                    "id": f"c{len(captions)}",
                    "segment_id": seg["id"],
                    "start": chunk[0]["start"],
                    "end": chunk[-1]["end"],
                    "text": _clean_caption(" ".join(w["word"] for w in chunk)),
                })

    return {
        "version": 1,
        "title": claude.title,
        "hook_text": claude.hook_text,
        "cover_text": claude.cover_text,
        "music_vibe": claude.music_vibe,
        "post_caption": claude.post_caption,
        "hashtags": claude.hashtags,
        "emphasis_words": claude.emphasis_words,
        "broll": [b.model_dump() for b in claude.broll],
        "settings": settings,
        "clips": clips,
        "segments": segments,
        "captions": captions,
    }


def _segment(idx: int, clip: int, start: float, end: float, reason: str, text: str) -> dict:
    return {"id": f"s{idx}", "clip": clip, "start": round(start, 3), "end": round(end, 3),
            "enabled": True, "reason": reason, "text": text}


def _split_on_pauses(words: list[dict], max_pause: float) -> list[list[dict]]:
    groups = [[words[0]]]
    for prev, w in zip(words, words[1:]):
        if w["start"] - prev["end"] > max_pause:
            groups.append([])
        groups[-1].append(w)
    return groups


def _caption_chunks(words: list[dict], max_words: int, max_chars: int) -> list[list[dict]]:
    chunks: list[list[dict]] = [[]]
    for w in words:
        current = chunks[-1]
        text_len = len(" ".join(x["word"] for x in current + [w]))
        ends_sentence = bool(current) and re.search(r"[.!?,]$", current[-1]["word"])
        if current and (len(current) >= max_words or text_len > max_chars or ends_sentence):
            chunks.append([])
        chunks[-1].append(w)
    return [c for c in chunks if c]


def _clean_caption(text: str) -> str:
    return re.sub(r"[.,]+$", "", text).strip()


# --- timeline helpers shared by the renderer and the studio -------------------

def timeline(plan: dict) -> list[tuple[dict, float]]:
    """Enabled segments with their start time in the finished reel."""
    out, t = [], 0.0
    for seg in plan["segments"]:
        if seg.get("enabled", True) and seg["end"] > seg["start"]:
            out.append((seg, t))
            t += seg["end"] - seg["start"]
    return out


def timed_captions(plan: dict) -> list[dict]:
    """Captions mapped onto the finished reel's timeline, clipped to their segment."""
    offsets = {seg["id"]: (seg, t) for seg, t in timeline(plan)}
    result = []
    for cap in plan["captions"]:
        if cap["segment_id"] not in offsets or not cap["text"].strip():
            continue
        seg, t = offsets[cap["segment_id"]]
        start, end = max(cap["start"], seg["start"]), min(cap["end"], seg["end"])
        if end - start < 0.05:
            continue
        result.append({"text": cap["text"], "start": round(t + start - seg["start"], 3),
                       "end": round(t + end - seg["start"], 3)})
    # make captions run back to back so the screen never flickers empty mid-sentence
    for a, b in zip(result, result[1:]):
        if 0 < b["start"] - a["end"] < 0.3:
            a["end"] = b["start"]
    return result


def load_plan(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def save_plan(plan: dict, path: Path) -> None:
    Path(path).write_text(json.dumps(plan, indent=2, ensure_ascii=False))
