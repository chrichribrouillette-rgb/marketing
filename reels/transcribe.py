"""Transcribe clips locally with faster-whisper, keeping word-level timestamps."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


def _cache_path(clip: Path, cache_dir: Path) -> Path:
    stat = clip.stat()
    key = hashlib.sha1(f"{clip.resolve()}|{stat.st_size}|{stat.st_mtime}".encode()).hexdigest()[:16]
    return cache_dir / f"{clip.stem}.{key}.words.json"


def transcribe_clip(clip: Path, cache_dir: Path, model_size: str = "small", language: str | None = None) -> list[dict]:
    """Return [{"word": str, "start": float, "end": float}, ...] for one clip.

    Results are cached, so re-running the engine on the same footage is instant.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = _cache_path(clip, cache_dir)
    if cached.exists():
        return json.loads(cached.read_text())

    from faster_whisper import WhisperModel  # imported lazily: it is slow to load

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, _info = model.transcribe(
        str(clip),
        language=language,
        word_timestamps=True,
        vad_filter=True,
    )
    words = [
        {"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
        for seg in segments
        for w in (seg.words or [])
        if w.word.strip()
    ]
    cached.write_text(json.dumps(words))
    return words


def transcript_for_prompt(all_words: list[list[dict]]) -> str:
    """Compact, timestamped transcript that Claude reads to choose cuts.

    One line per spoken phrase (split on pauses), e.g.
        [clip 0 | 3.20-7.85] so here's the thing nobody tells you
    """
    lines = []
    for clip_idx, words in enumerate(all_words):
        if not words:
            lines.append(f"[clip {clip_idx}] (no speech detected - b-roll or silent clip)")
            continue
        phrase = [words[0]]
        for prev, w in zip(words, words[1:]):
            if w["start"] - prev["end"] > 0.6 or len(phrase) >= 18:
                lines.append(_phrase_line(clip_idx, phrase))
                phrase = []
            phrase.append(w)
        lines.append(_phrase_line(clip_idx, phrase))
    return "\n".join(lines)


def _phrase_line(clip_idx: int, phrase: list[dict]) -> str:
    text = " ".join(w["word"] for w in phrase)
    return f"[clip {clip_idx} | {phrase[0]['start']:.2f}-{phrase[-1]['end']:.2f}] {text}"
