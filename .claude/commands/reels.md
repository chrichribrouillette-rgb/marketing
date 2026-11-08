Edit raw talking-head footage into an Instagram Reel, ready to finish in CapCut. No API key needed: you (Claude Code) make the editing decisions.

**Usage:** `/reels <video files> [--brief "<what it's about + call to action>"] [--industry <1-10>] [--length <seconds>] [--name <project>]`

**Examples:**
- `/reels inbox/take1.mov inbox/take2.mov --brief "Why vitamin C goes on in the morning, CTA: shop the serum" --length 30`
- `/reels footage/*.mp4 --industry 3 --name morning-routine`

Arguments: $ARGUMENTS

## Steps

Use `python3` if `python` is not found (common on Mac).

1. Transcribe the clips (from the repository root):
   ```bash
   python reels_engine.py prepare $ARGUMENTS
   ```
   It prints the project folder, for example `reels_projects/<name>`.

2. Read `<project>/EDIT_INSTRUCTIONS.md` in full. Edit the reel yourself, as a senior short-form editor, following its rules:
   - Put the strongest line first.
   - Keep only the best take of anything said twice.
   - Cut flubs, filler and tangents.
   - End on the payoff or the call to action.
   - Use only timestamps from the transcript.

   Write your decisions to `<project>/edit.json`, matching the schema in that file exactly. Write the post caption, hook and hashtags in the speaker's language and brand voice.

3. Render:
   ```bash
   python reels_engine.py finish <project>
   ```
   If it reports that edit.json doesn't match the format, fix the file and run it again.

4. Tell the user:
   - the reel's length and number of cuts
   - the hook you chose and why
   - what you cut (in a sentence)
   - where the files are (`<project>/capcut/`)

   Offer to open the studio with `python reels_engine.py studio <project>`. In a cloud session, start the studio with `--no-browser` in the background and share the port.
