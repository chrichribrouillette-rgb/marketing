# Reels Editing Engine (Claude + CapCut)

Film yourself talking. Include retakes, "ums" and restarts if you like. This engine turns the raw clips into a tight 9:16 reel and hands it to CapCut for the finishing touches.

```
raw clips ──► transcribe (on your computer) ──► Claude edits ──► jump cuts + timed captions
                                                                     │
          CapCut ◄── rough_cut.mp4 + captions.srt + post.md ◄────────┘
                                ▲
                      Reels Studio (tweak cuts & captions in your browser)
```

What Claude decides:
- the **hook**: it moves your strongest line to the front
- the **best take** of anything you said twice
- what to **cut**: false starts, filler, tangents
- **on-screen hook text**, **cover text**, **highlighted words**, **b-roll ideas**, **music mood**, the **Instagram caption** and **hashtags**

What the code does precisely: it cuts each word to the exact millisecond, removes pauses over 0.35 s, splits captions into 1–3 word chunks, reframes to 1080×1920, and renders.

## Make a reel (no API key needed)

The editing decisions come from Claude Code, so they count against your normal Claude plan. Nothing is billed separately.

1. Upload your clip to the `inbox/` folder. On GitHub, go to "Add file", then "Upload files".
2. In Claude Code, type:
   ```
   /reels inbox/take1.mov --brief "Vitamin C goes on in the morning. CTA: link in bio" --length 30 --name vitamin-c
   ```

Claude Code then runs three steps:
1. `python reels_engine.py prepare ...` transcribes the clip on the machine. This is free.
2. Claude Code reads `EDIT_INSTRUCTIONS.md` and writes its decisions to `edit.json`.
3. `python reels_engine.py finish reels_projects/vitamin-c` cuts and renders the CapCut files.

Useful options:

| Option | What it does |
|---|---|
| `--brief "..."` | Topic, brand voice and call to action. More context gives a better edit. |
| `--industry 2` | Uses the tone of one of the 10 marketing agents (2 = Beauty). |
| `--length 30` | Target length in seconds. |
| `--language fr` | Spoken language. It's detected automatically if you leave this out. |
| `--whisper medium` | Better transcription and slower. Use `tiny` for speed. |
| `--max-pause 0.5` | Less aggressive jump cuts. |

The machine running it needs ffmpeg and the Python packages (`pip install -r requirements.txt`). The first run downloads the free speech-to-text model (~500 MB for `small`).

**Optional, with an API key:** `python reels_engine.py make ...` does all three steps in one command without Claude Code. It calls the Claude API, which is billed separately from a Claude plan (roughly 10 cents per reel), and needs `ANTHROPIC_API_KEY` in a `.env` file.

Everything lands in `reels_projects/<name>/capcut/`:

| File | Use |
|---|---|
| `rough_cut.mp4` | The edit with no captions. Import this into CapCut. |
| `captions.srt` | Captions timed to the rough cut |
| `preview_with_captions.mp4` | Ready to post as is, with captions and hook burned in |
| `post.md` | Hook, cover text, music, b-roll ideas, caption and hashtags |
| `CAPCUT_STEPS.md` | Step-by-step finishing guide |

## Tweak the edit in the studio

```bash
python reels_engine.py studio reels_projects/vitamin-c
```

This opens http://127.0.0.1:8765 with a phone-sized preview that plays your edit with its captions. You can:
- untick a cut to drop it
- nudge a cut's start or end by 0.1 s
- reorder cuts
- fix caption typos
- change the hook, highlighted words and post caption

Click **Export for CapCut** to re-render. Space plays or pauses, and Ctrl/Cmd+S saves.

## Finish in CapCut

**Desktop (recommended):**
1. Import `rough_cut.mp4`.
2. Go to Captions → Import captions and pick `captions.srt`. Then apply a caption template.
3. Add the hook text, music and b-roll from `post.md`.
4. Export at 1080×1920.

**Mobile:** CapCut mobile can't import `.srt` files. Import `rough_cut.mp4` and use **Auto captions**, which come out accurate because the audio is already clean. Or post `preview_with_captions.mp4` as is.

## Tips for footage that edits well
- Say your hook three different ways. Claude keeps the best one.
- If you flub a line, pause for a second and say the whole sentence again. Don't patch it mid-sentence.
- Film b-roll clips with no talking. Claude suggests where they go in `post.md`.
