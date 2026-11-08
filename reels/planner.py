"""Ask Claude to turn a raw transcript into a reel edit plan."""

from __future__ import annotations

import anthropic
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"


class KeepSegment(BaseModel):
    clip: int = Field(description="Index of the source clip")
    start: float = Field(description="Start time in seconds within that clip")
    end: float = Field(description="End time in seconds within that clip")
    reason: str = Field(description="Why this bit is kept, in a few words (e.g. 'hook', 'best take of point 2')")


class BrollIdea(BaseModel):
    at_words: str = Field(description="The spoken words this b-roll should cover")
    idea: str = Field(description="What to show, concretely")


class ClaudeEditPlan(BaseModel):
    title: str = Field(description="Short working title for the reel")
    hook_text: str = Field(description="On-screen text for the first 2-3 seconds, max 8 words")
    segments: list[KeepSegment] = Field(description="Parts to keep, in final playback order")
    emphasis_words: list[str] = Field(description="Words to highlight in captions (key nouns, numbers, payoff words)")
    broll: list[BrollIdea] = Field(description="2-5 b-roll or overlay suggestions")
    cover_text: str = Field(description="Text for the reel cover / thumbnail, max 6 words")
    music_vibe: str = Field(description="Music mood to search for in CapCut's library")
    post_caption: str = Field(description="Instagram caption for the post, with a call to action")
    hashtags: list[str] = Field(description="5-10 relevant hashtags without the # sign")


SYSTEM_PROMPT = """You are a senior short-form video editor who cuts Instagram Reels and TikToks.
You receive a timestamped transcript of raw talking-head footage (possibly several clips,
with retakes, false starts, filler and rambling). You decide what survives the edit.

Editing rules:
- Open on the strongest line. If the speaker's best hook is in the middle, move it to the front.
- When a line was said more than once, keep only the cleanest, most confident take (usually the last).
- Cut false starts, "um/uh/like/so yeah", restarts, off-topic tangents and "is it recording?" moments.
- Keep each idea once. Tight beats long: aim for the target length given by the user.
- End on the payoff or a clear call to action, never on a trailing "so... yeah".
- Segment times must come from the transcript's timestamps. Start a segment at the start of its
  first kept word and end it at the end of its last kept word. Never invent times.
- Segments may be short (a single sentence) - many small segments is normal for a jump-cut reel.
- Clips with no speech are b-roll. Don't put them in segments (that would silence the voiceover);
  suggest where they go in the b-roll list instead, naming the clip."""


def make_plan(transcript: str, clip_names: list[str], brief: str, target_seconds: int) -> ClaudeEditPlan:
    client = anthropic.Anthropic()
    clips = "\n".join(f"clip {i}: {name}" for i, name in enumerate(clip_names))
    user = (
        f"Brief / brand context: {brief or 'none given - infer from the footage'}\n"
        f"Target length: about {target_seconds} seconds\n\n"
        f"Source clips:\n{clips}\n\n"
        f"Transcript:\n{transcript}"
    )
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the request is declined, the API retries it on a fallback model
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
        output_format=ClaudeEditPlan,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to plan this edit. Try rephrasing the brief.")
    if response.parsed_output is None:
        raise RuntimeError(f"Claude did not return an edit plan (stop reason: {response.stop_reason}).")
    return response.parsed_output
