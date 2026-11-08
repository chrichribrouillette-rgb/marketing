"""
Reels Editing Engine - raw talking-head footage in, CapCut-ready reel out.

    1. Transcribes your clips locally (faster-whisper, word timestamps)
    2. Claude picks the hook, the best takes and the order, and writes the post copy
    3. Dead air is cut automatically (jump cuts) and captions are timed word by word
    4. Exports a 9:16 rough cut + captions file for CapCut, and a captioned preview
    5. The Reels Studio (local web page) lets you tweak cuts and captions, then re-export

Usage:
    python reels_engine.py make clip1.mov clip2.mov --brief "Glow serum launch, playful" --length 30
    python reels_engine.py make footage/*.mp4 --industry 2 --name serum-launch --studio
    python reels_engine.py studio reels_projects/serum-launch
    python reels_engine.py export reels_projects/serum-launch

Needs ffmpeg installed and ANTHROPIC_API_KEY set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECTS_DIR = Path(__file__).parent / "reels_projects"

CAPCUT_STEPS = """# Finish this reel in CapCut

Files in this folder:
- rough_cut.mp4 - the edited reel, 9:16, no captions (this is what goes into CapCut)
- captions.srt - captions timed to rough_cut.mp4
- preview_with_captions.mp4 - a ready-to-post version with captions burned in
- post.md - hook, cover text, music idea, b-roll ideas, Instagram caption and hashtags

## CapCut desktop (Mac / Windows) - recommended
1. New project -> Import -> rough_cut.mp4 -> drag it onto the timeline.
2. Captions: open Captions (or Text) -> "Import captions" / "Local captions" -> pick captions.srt.
   Then select all captions and apply a caption template or style you like.
   (No import button in your version? Use Captions -> Auto captions instead: the audio is
   already clean, so auto captions come out accurate.)
3. Text -> add the hook from post.md over the first 3 seconds.
4. Audio -> search the music vibe from post.md, set music volume to about 10-15%.
5. Drop b-roll on the track above the video where post.md suggests.
6. Export 1080x1920, 30 fps.

## CapCut mobile
CapCut mobile can't import .srt files. Import rough_cut.mp4, then Captions -> Auto captions.
Or post preview_with_captions.mp4 as is.

Changed your mind on a cut? Run the studio, adjust, click "Export for CapCut", and re-import.
"""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "reel"


def check_ffmpeg() -> None:
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        sys.exit("ffmpeg is not installed. Mac: `brew install ffmpeg`, Windows: `winget install ffmpeg`.")


def industry_brief(number: str | None) -> str:
    if not number:
        return ""
    from agents import INDUSTRY_AGENTS
    agent = INDUSTRY_AGENTS.get(number)
    if not agent:
        sys.exit(f"Unknown industry '{number}'. Run `python cli.py x --list` to see the numbers.")
    return f"Industry: {agent.INDUSTRY}. {agent.INDUSTRY_PROMPT}".strip()


def cmd_make(args) -> None:
    check_ffmpeg()
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Run: export ANTHROPIC_API_KEY='your-key-here'")

    from reels.plan import build_plan, save_plan
    from reels.planner import make_plan
    from reels.render import export_all, probe
    from reels.transcribe import transcribe_clip, transcript_for_prompt

    clip_paths = [Path(p) for p in args.clips]
    missing = [str(p) for p in clip_paths if not p.is_file()]
    if missing:
        sys.exit(f"Can't find: {', '.join(missing)}")

    name = args.name or f"{datetime.now():%Y%m%d-%H%M}-{slugify(clip_paths[0].stem)}"
    project = PROJECTS_DIR / slugify(name)
    project.mkdir(parents=True, exist_ok=True)

    print(f"1/4  Reading {len(clip_paths)} clip(s)...")
    clips = [probe(p) for p in clip_paths]

    print(f"2/4  Transcribing (first run downloads the '{args.whisper}' speech model)...")
    words = []
    for p in clip_paths:
        w = transcribe_clip(p, PROJECTS_DIR / ".cache", model_size=args.whisper, language=args.language)
        print(f"     {p.name}: {len(w)} words")
        words.append(w)
    transcript = transcript_for_prompt(words)
    (project / "transcript.txt").write_text(transcript, encoding="utf-8")
    (project / "words.json").write_text(json.dumps(words), encoding="utf-8")

    print("3/4  Claude is editing (picking the hook, best takes and order)...")
    brief = " ".join(filter(None, [args.brief, industry_brief(args.industry)]))
    claude_plan = make_plan(transcript, [p.name for p in clip_paths], brief, args.length)
    plan = build_plan(claude_plan, clips, words, {"max_pause": args.max_pause})
    save_plan(plan, project / "plan.json")

    print("4/4  Rendering for CapCut...")
    out = project / "capcut"
    export_all(plan, out, preview=not args.no_preview)
    (out / "CAPCUT_STEPS.md").write_text(CAPCUT_STEPS, encoding="utf-8")

    summary(plan, project)
    if args.studio:
        from reels.server import serve
        serve(project, port=args.port)


def cmd_export(args) -> None:
    check_ffmpeg()
    from reels.plan import load_plan
    from reels.render import export_all
    project = Path(args.project)
    plan = load_plan(project / "plan.json")
    export_all(plan, project / "capcut", preview=not args.no_preview)
    (project / "capcut" / "CAPCUT_STEPS.md").write_text(CAPCUT_STEPS, encoding="utf-8")
    summary(plan, project)


def cmd_studio(args) -> None:
    check_ffmpeg()
    from reels.server import serve
    project = Path(args.project)
    if not (project / "plan.json").is_file():
        sys.exit(f"No plan.json in {project}. Run `python reels_engine.py make ...` first.")
    serve(project, port=args.port, open_browser=not args.no_browser)


def summary(plan: dict, project: Path) -> None:
    from reels.plan import timeline
    parts = timeline(plan)
    length = sum(s["end"] - s["start"] for s, _ in parts)
    print(f"\nDone: \"{plan['title']}\" - {length:.1f} s, {len(parts)} cuts")
    print(f"Hook: {plan['hook_text']}")
    print(f"CapCut files: {project / 'capcut'}")
    print(f"Tweak it:     python reels_engine.py studio {project}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reels Editing Engine (Claude + CapCut)")
    sub = parser.add_subparsers(dest="command", required=True)

    make = sub.add_parser("make", help="Edit raw clips into a reel")
    make.add_argument("clips", nargs="+", help="Video files, in the order you filmed them")
    make.add_argument("--brief", default="", help="What the reel is about, brand voice, call to action")
    make.add_argument("--industry", help="Industry number from the marketing agents (1-10) for tone")
    make.add_argument("--length", type=int, default=30, help="Target length in seconds (default 30)")
    make.add_argument("--name", help="Project name (folder under reels_projects/)")
    make.add_argument("--whisper", default="small", help="Speech model: tiny, base, small, medium, large-v3")
    make.add_argument("--language", help="Spoken language code, e.g. en or fr (auto-detected if omitted)")
    make.add_argument("--max-pause", type=float, default=0.35, help="Cut silences longer than this (seconds)")
    make.add_argument("--no-preview", action="store_true", help="Skip the captioned preview video")
    make.add_argument("--studio", action="store_true", help="Open the studio when done")
    make.add_argument("--port", type=int, default=8765)
    make.set_defaults(func=cmd_make)

    export = sub.add_parser("export", help="Re-render CapCut files from plan.json")
    export.add_argument("project")
    export.add_argument("--no-preview", action="store_true")
    export.set_defaults(func=cmd_export)

    studio = sub.add_parser("studio", help="Open the visual editor for a project")
    studio.add_argument("project")
    studio.add_argument("--port", type=int, default=8765)
    studio.add_argument("--no-browser", action="store_true")
    studio.set_defaults(func=cmd_studio)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
