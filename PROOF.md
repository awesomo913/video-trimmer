# Video Trimmer — Proof

## What this thing is
A small program for a Windows computer that cuts video files into smaller pieces.

## What it does for you
- Opens almost any video file you have
- Lets you mark a start point and an end point and save just that piece
- Lets you point at a whole folder of videos and split every one of them into halves, thirds, fourths, or any number of equal parts at once
- Lets you split videos into fixed-time pieces (for example, every 60 seconds)
- Saves the new pieces next to your originals, in a folder called `split_output`
- Never sends your videos anywhere. Everything happens on your computer.

## How it was made
The user designed it. They said what it should do and how it should look and feel. An AI helper wrote the code to match. The user tested it and decided when it was ready to share.

It uses two free tools under the hood:
- **FFmpeg** — a program that knows how to read and write almost every video format ever made
- **OpenCV** — a library that lets the program show video frames on the screen

Both run on your computer. Neither sends data to anyone else.

## What it costs / what it gives back
- **Money:** zero. The program is free. The tools it uses are free.
- **Time:** about one second to start. Cutting a piece is near-instant if you keep the same format. Re-encoding (changing format) takes about as long as the video itself.
- **Data:** nothing leaves your computer. No accounts. No sign-in. No telemetry.
- **Control:** you pick every file, every setting, every output location. The program never deletes or changes your originals.

## Who is responsible
The designer is the user (owner of this computer). Last review: 2026-04-21.

If something goes wrong, look at the file `logs/crash_*.log` next to the program. That file records what happened in plain words.

## What proof exists that it works
- `Desktop/AI/docs/2026-04-15_video-trimmer.md` — full technical write-up
- `Desktop/AI/docs/2026-04-15_video-trimmer_tutorial.md` — step-by-step guide for any user
- `Desktop/AI/docs/2026-04-15_video-trimmer_handoff.md` — history of every work session, dated, with what changed
- Tested on 2026-04-15: opened a 1080p phone video, cut a 10-second piece, output played back correctly
- Tested on 2026-04-21: ran the batch-split feature on three test videos (12 seconds, 30 seconds, 60 seconds). Split each into 4 equal parts. Twelve output files all played correctly with the right durations.
- Tested on 2026-04-21: ran the batch-split in duration mode (20-second chunks). 60-second video became three 20-second pieces. 30-second video became one 20-second piece and one 10-second piece. 12-second video was correctly skipped because it was shorter than 20 seconds.
- Live on GitHub at https://github.com/awesomo913/video-trimmer

## Changelog
- **On April 21, 2026** — added the ability to point at a whole folder of videos and split every one of them at once into equal parts or fixed-time pieces. This is for when you have a lot of videos and need them smaller for an AI tool. The program saves the pieces in a folder called `split_output` next to the originals.
- **On April 15, 2026** — first release. You could open any common video, watch it, mark a start and end point, and save just that piece. Worked on every file we tested.

- **2026-07-18** — Added OS drag-and-drop (drop a video file onto the window to load it). Wired `tkinterdnd2` into the CustomTkinter root, made the drop handler multi-file/spaces-safe, and bundled the native tkdnd files into the exe (spec). Also removed a dead `diagnostics_logger.py` data entry that was breaking the build. New VideoTrimmer.exe is in My Apps.

- **2026-07-18** — Quality pass (9 fixes): audio now loops with the video and respects the trim region; no audio when scrubbing paused; Batch mode no longer crashes on open; setting OUT before IN no longer pins the CPU; playback thread is joined before releasing the video (fixes a file-switch race); ffplay no longer orphaned on kill failure; audio-start failures are logged; thumbnail capture no longer leaks on error; export refuses to overwrite the source file; fixed an invalid hover color that crashed on hover.
