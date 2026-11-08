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

## One-time setup

1. Install ffmpeg: on Mac, `brew install ffmpeg`. On Windows, `winget install ffmpeg`.
2. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Add your Claude API key to a `.env` file in this folder:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

The first run downloads the speech-to-text model (~500 MB for `small`). Transcription runs on your computer for free. Only the text transcript goes to Claude, never the video.

## Make a reel

```bash
python reels_engine.py make take1.mov take2.mov --brief "Vitamin C goes on in the morning. CTA: link in bio" --length 30 --name vitamin-c
```

Useful options:

| Option | What it does |
|---|---|
| `--brief "..."` | Topic, brand voice and call to action. More context gives a better edit. |
| `--industry 2` | Uses the tone of one of the 10 marketing agents (2 = Beauty). |
| `--length 30` | Target length in seconds. |
| `--language fr` | Spoken language. It's detected automatically if you leave this out. |
| `--whisper medium` | Better transcription and slower. Use `tiny` for speed. |
| `--max-pause 0.5` | Less aggressive jump cuts. |
| `--studio` | Opens the visual editor when it's done. |

In Claude Code you can also type `/reels take1.mov --brief "..."`.

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
