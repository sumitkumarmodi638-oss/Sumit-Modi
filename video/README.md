# Sunflour — 30s promo video

Ready-to-post exports are in [`exports/`](exports/):

| File | Size | Use |
|---|---|---|
| `sunflour_vertical.mp4` | 1080×1920 | Reels / Shorts / TikTok / Stories |
| `sunflour_landscape.mp4` | 1920×1080 | YouTube, website hero, pre-roll |
| `sunflour_square.mp4` | 1080×1080 | Feed posts |

H.264 at 30 fps with AAC 320k audio, mastered to −14 LUFS / −1 dBTP (the social-platform loudness target).

> ⚠️ **The copy is placeholder.** sunflour.in did not resolve when this was built, so the brand
> story (a flour/atta brand, "sunshine in every grain") is inferred from the name.
> Every line of text lives in [`config.py`](config.py). Edit it and re-run `./build.sh`.

## Edit decision list (120 BPM, cuts on the beat)

| Time | Scene | Techniques |
|---|---|---|
| 0.0–1.5 | **Hook:** "FLOUR / IS JUST / FLOUR." punched in on beats 1-3 | scale-punch typography, camera shake, flour-burst particles, chromatic-aberration hits, impact SFX |
| 1.5–2.0 | **Pattern interrupt:** "...right?" | RGB-split glitch, slice displacement, invert flash frames, bit-crushed stutter SFX |
| 2.0–3.0 | Giant serif FLOUR, **camera flies through the "O"** into the sun | match-cut zoom-through (the counter of the O is a window into the next scene), exponential zoom ramp, radial zoom blur, riser + reverse cymbal |
| 3.0–7.0 | **Drop / reveal:** sunrise, "Introducing Sunflour", tagline | white flash on the drop, rotating god-rays, bokeh dust, per-letter masked rise, light sweep across the logo, slow push-in with a roll drift |
| 7.0–15.0 | **4 feature cards** (Milled fresh / Soft rotis / Wholesome / Indian kitchens) | each card uses a different text animation (mask rise, tracking-collapse punch, words from alternating sides, letter pop with overshoot), procedural animated icons, parallax background numerals, progress bar, brand bug, **whip-pans with motion blur** + whooshes |
| 15.0–21.0 | **Cinematic golden-hour wheat field** | animated letterbox, 3-layer parallax dolly, depth-of-field blur, swaying wheat, **speed ramp** (slow-mo into a fast forward pull), zoom-blur exit, half-time drums + riser |
| 21.0–23.0 | **Beat-cut montage:** Rotis / Parathas / Puris / Bakes | a hard cut on every beat, 4 motion variants (zoom, drop, rotate-snap, squash-stretch), flash frames, shake |
| 23.0–25.0 | **2×2 grid** "One flour. Every favourite." | staggered overshoot tile build, pull-out, collapse to centre |
| 25.0–30.0 | **CTA end card:** logo, "Bring the sunshine home.", ORDER NOW, sunflour.in | logo pop, light sweep, beat-synced button pulse, button shine loop, underline draw-on, final impact + fade |

The whole video gets a finishing pass of film grain, a vignette and a warm grade.

**Sound:** an original score and sound design synthesised in code, so it is royalty-free. It has a pad, a pluck
arpeggio, a sub bass, four-on-the-floor drums with sidechain ducking, and a convolution reverb. The
SFX layer has impacts, risers, whooshes panned with the whip direction, glitch stutters, ticks and shimmer bells.
Every hit is placed from the same cue sheet as the visuals.

## Rebuild

```bash
pip install numpy scipy pillow    # plus ffmpeg on PATH
./build.sh                        # all formats → out/ (master quality, CRF 15)
./build.sh vertical               # one format

python3 render.py --sheet out/sheet.png        # contact sheet for review
python3 render.py --still 4.6 --out still.png  # any single frame
```

`config.py` holds the copy, palette and scene timings. `render.py` is the visuals and `audio.py` is the soundtrack.
Fonts are Fraunces, Playfair Display and Inter Display (SIL OFL, licences in `assets/fonts/`).
