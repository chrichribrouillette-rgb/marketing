"""Render the plan with ffmpeg and write the CapCut hand-off files."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .plan import timed_captions, timeline


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(out.stdout)
    return {
        "path": str(Path(path).resolve()),
        "duration": round(float(info["format"]["duration"]), 3),
        "has_audio": any(s.get("codec_type") == "audio" for s in info.get("streams", [])),
    }


def render_video(plan: dict, out_path: Path, burn_captions: bool = False, work_dir: Path | None = None) -> Path:
    """Cut, reframe to 9:16 and join every enabled segment into one MP4."""
    s = plan["settings"]
    W, H, fps = s["width"], s["height"], s["fps"]
    parts = timeline(plan)
    if not parts:
        raise ValueError("Nothing to render: every segment is disabled.")

    used = sorted({seg["clip"] for seg, _ in parts})
    input_index = {clip: i for i, clip in enumerate(used)}
    args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for clip in used:
        args += ["-i", plan["clips"][clip]["path"]]

    filters, labels = [], []
    for n, (seg, _) in enumerate(parts):
        i = input_index[seg["clip"]]
        a, b = seg["start"], seg["end"]
        dur = b - a
        filters.append(
            f"[{i}:v]trim={a}:{b},setpts=PTS-STARTPTS,"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={fps}[v{n}]"
        )
        if plan["clips"][seg["clip"]].get("has_audio", True):
            fade = min(0.03, dur / 4)
            filters.append(
                f"[{i}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,"
                f"afade=t=in:d={fade},afade=t=out:st={dur - fade:.3f}:d={fade}[a{n}]"
            )
        else:
            filters.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur}[a{n}]")
        labels.append(f"[v{n}][a{n}]")

    filters.append(f"{''.join(labels)}concat=n={len(parts)}:v=1:a=1[vcat][aout]")
    video_label = "[vcat]"
    if burn_captions:
        ass = (work_dir or out_path.parent) / f"{out_path.stem}.ass"
        write_ass(plan, ass)
        escaped = str(ass.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        filters.append(f"[vcat]subtitles='{escaped}'[vout]")
        video_label = "[vout]"

    args += [
        "-filter_complex", ";".join(filters),
        "-map", video_label, "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(out_path),
    ]
    subprocess.run(args, check=True)
    return out_path


def _ts_srt(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def _ts_ass(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def write_srt(plan: dict, path: Path) -> Path:
    lines = []
    for n, cap in enumerate(timed_captions(plan), 1):
        lines += [str(n), f"{_ts_srt(cap['start'])} --> {_ts_srt(cap['end'])}", cap["text"], ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ass(plan: dict, path: Path) -> Path:
    """Styled captions for the preview: bold, centred, key words highlighted, plus the hook."""
    W, H = plan["settings"]["width"], plan["settings"]["height"]
    emphasis = {w.lower().strip(".,!?") for w in plan.get("emphasis_words", [])}
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,80,80,620,1
Style: Hook,Arial,78,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,90,90,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    if plan.get("hook_text"):
        events.append(f"Dialogue: 1,{_ts_ass(0)},{_ts_ass(2.8)},Hook,,0,0,0,,{plan['hook_text']}")
    for cap in timed_captions(plan):
        words = []
        for w in cap["text"].split():
            if w.lower().strip(".,!?") in emphasis:
                words.append(r"{\c&H00D7FF&}" + w.upper() + r"{\c&HFFFFFF&}")  # yellow
            else:
                words.append(w.upper())
        text = r"{\fscx85\fscy85\t(0,90,\fscx100\fscy100)}" + " ".join(words)
        events.append(f"Dialogue: 0,{_ts_ass(cap['start'])},{_ts_ass(cap['end'])},Caption,,0,0,0,,{text}")
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return path


def write_post_notes(plan: dict, path: Path) -> Path:
    total = sum(seg["end"] - seg["start"] for seg, _ in timeline(plan))
    broll = "\n".join(f"- When you say \"{b['at_words']}\": {b['idea']}" for b in plan.get("broll", []))
    hashtags = " ".join(f"#{h.lstrip('#')}" for h in plan.get("hashtags", []))
    path.write_text(f"""# {plan['title']}

Length: {total:.1f} s, {len(timeline(plan))} cuts

## Hook text (first 3 seconds)
{plan['hook_text']}

## Cover text
{plan['cover_text']}

## Music to search in CapCut
{plan['music_vibe']}

## B-roll ideas
{broll or '- none'}

## Instagram caption
{plan['post_caption']}

{hashtags}
""", encoding="utf-8")
    return path


def export_all(plan: dict, out_dir: Path, preview: bool = True) -> dict[str, Path]:
    """Everything CapCut needs, in one folder."""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "rough_cut": render_video(plan, out_dir / "rough_cut.mp4"),
        "captions": write_srt(plan, out_dir / "captions.srt"),
        "notes": write_post_notes(plan, out_dir / "post.md"),
    }
    if preview:
        files["preview"] = render_video(plan, out_dir / "preview_with_captions.mp4", burn_captions=True)
    return files
