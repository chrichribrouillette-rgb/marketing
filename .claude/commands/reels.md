Edit raw talking-head footage into an Instagram Reel with Claude, ready to finish in CapCut.

**Usage:** `/reels <video files> [--brief "<what it's about>"] [--industry <1-10>] [--length <seconds>] [--name <project>]`

**Examples:**
- `/reels ~/Movies/take1.mov ~/Movies/take2.mov --brief "Why vitamin C goes on in the morning, CTA: shop the serum" --length 30`
- `/reels footage/*.mp4 --industry 3 --name morning-routine`

Run the following command and show the user the summary it prints, including where the CapCut files are and how to open the studio:

```bash
cd "$(git rev-parse --show-toplevel)" && python reels_engine.py make $ARGUMENTS
```

If the user wants to adjust the edit afterwards, run `python reels_engine.py studio reels_projects/<name>` and tell them to open http://127.0.0.1:8765.
