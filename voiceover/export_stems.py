"""Copy each film's music + SFX stems into voiceover/stems/ as 24-bit FLAC (x STEM_GAIN for headroom),
so the final mix can run anywhere with just a git clone (mix.py reads these when build/ is absent)."""
import os
import subprocess

from scripts import FILMS, ORDER

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STEM_GAIN = 0.25  # mix.py divides this back out

for film in ORDER:
    cfg = FILMS[film]
    for kind in ("music", "sfx"):
        src = os.path.join(ROOT, cfg["project"], "build", f"{cfg['stem']}_{kind}.wav")
        dst = os.path.join(HERE, "stems", f"{film}_{kind}.flac")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", f"volume={STEM_GAIN}",
                        "-c:a", "flac", "-sample_fmt", "s32", "-bits_per_raw_sample", "24", dst], check=True)
        print(dst, os.path.getsize(dst) // 1024, "KB")
