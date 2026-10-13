"""Music edit: cut a real cinematic score to each film, the way a music editor would.

Every film gets a licensed track (Mixkit Stock Music Free License: commercial use, no
attribution needed). The track is not redistributed in this repo; it is downloaded by URL into
voiceover/music_cache/ the first time it is needed.

For each film:
  1. conform  the track's tempo to the film's 120 BPM cut grid with Rubber Band (pitch kept),
              only when it is within 8% (a bigger stretch starts to sound processed)
  2. sync     slide the track so its big lift lands exactly on the film's drop frame
              (the lift is measured, then snapped to the sharpest onset within +-150 ms)
  3. breathe  a 4 dB dip in the 300 ms before the drop, so the hit feels bigger
  4. backtime the track's own ending onto the last frame: the body crossfades on a beat into
              the track's natural ending, so the music resolves instead of fading out
  5. level    matched to the old synthesized score, so the balance with the SFX stem stays put
"""
import os
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "music_cache")
SR = 48000
GRID_BPM = 120.0
MAX_CONFORM = 0.08

# id: (title, artist, detected bpm, lift time in source s, last full-energy s, end of the decay s)
TRACKS = {
    543: ("A New Life", "Eugenio Mininni", 129.2, 24.65, 75.9, 87.9),
    544: ("Kids on the Beach", "Eugenio Mininni", 123.0, 72.3, 108.2, 119.0),
    546: ("The Farewell", "Eugenio Mininni", 129.2, 18.8, 88.0, 93.7),
    607: ("Forest Walk", "Eugenio Mininni", 117.5, 16.5, 147.1, 164.2),
    715: ("Classical 8", "Jonny S.", 80.7, 72.4, 122.8, 134.6),
    723: ("Other World", "Lily J", 143.6, 9.2, 91.2, 92.6),
}

# film: (track id, drop time in the film s)
SCORE = {
    "brand-film": (546, 13.5),      # quiet build under the problem, full strings on the drop
    "scroll-stopper": (607, 12.5),  # pulses under the scroll, hard drop after STOP
    "healthcare": (543, 11.0),      # gentle, reassuring lift
    "food": (544, 11.0),            # warm; the track's dip sits under the "empty tables" beat
    "realestate": (546, 11.0),      # grand
    "education": (543, 11.0),
    "fitness": (607, 11.0),         # driving electronic drop
    "retail": (723, 11.0),          # modern, punchy
    "travel": (544, 11.0),
    "finance": (723, 11.0),
    "industry": (715, 11.0),        # big orchestral hit out of silence
}


def url(tid):
    return f"https://assets.mixkit.co/music/{tid}/{tid}.mp3"


def decode(path, chain=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-i", path]
    if chain:
        cmd += ["-af", chain]
    cmd += ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    r = subprocess.run(cmd, capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()


def fetch(tid):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"{tid}.mp3")
    if not os.path.exists(p):
        subprocess.run(["curl", "-sS", "-f", "-L", "--max-time", "120", "-o", p, url(tid)], check=True)
    return p


def conform_ratio(bpm):
    """Tempo factor that puts the track on the 120 BPM grid (or 1.0 if that would be too far)."""
    f = min((g / bpm for g in (GRID_BPM / 2, GRID_BPM, GRID_BPM * 2)), key=lambda f: abs(f - 1))
    return f if abs(f - 1) <= MAX_CONFORM else 1.0


def refine_onset(x, t, win=0.15):
    """Snap a rough lift time to the sharpest energy rise within +-win s."""
    h = int(0.01 * SR)
    a, b = max(0, int((t - win - 0.05) * SR)), int((t + win) * SR)
    seg = x[a:b].mean(1)
    n = len(seg) // h
    e = 10 * np.log10(np.mean(seg[: n * h].reshape(n, h) ** 2, 1) + 1e-10)
    rise = e[5:] - e[:-5]
    return (a + (int(np.argmax(rise)) + 5) * h) / SR


def score(film, n, ref=None, drop_override=None):
    """Return the edited (n, 2) music for a film. ref = the old music stem, for level matching."""
    tid, drop = SCORE[film]
    drop = drop_override if drop_override is not None else drop
    _title, _artist, bpm, lift, last_full, end = TRACKS[tid]
    f = conform_ratio(bpm)
    chain = f"rubberband=tempo={f:.5f}:pitchq=quality" if abs(f - 1) > 1e-4 else None
    x = decode(fetch(tid), chain)
    lift, last_full, end = lift / f, last_full / f, end / f
    lift = refine_onset(x, lift)

    dur = n / SR
    out = np.zeros((n, 2), np.float32)
    beat = 60.0 / GRID_BPM

    # backtimed ending: the track's decay ends just after the last frame
    tail_len = float(np.clip(end - last_full + 2.0, 4.0, 10.0))
    xf = round((dur - tail_len) / beat) * beat  # crossfade point, on the film's beat grid
    tail_src = end + 0.3 - (dur - xf)           # where in the source the tail starts

    # body: the track slid so its lift lands on the drop
    off = lift - drop
    t = np.arange(n) / SR
    src = np.round((t + off) * SR).astype(np.int64)
    ok = (src >= 0) & (src < len(x))
    body = np.zeros((n, 2), np.float32)
    body[ok] = x[src[ok]]

    tsrc = np.round((t - xf + tail_src) * SR).astype(np.int64)
    ok = (tsrc >= 0) & (tsrc < len(x)) & (t >= xf - beat)
    tail = np.zeros((n, 2), np.float32)
    tail[ok] = x[tsrc[ok]]

    # equal-power crossfade over one beat, centred on xf
    g = np.clip((t - (xf - beat / 2)) / beat, 0, 1)
    out = body * np.cos(g * np.pi / 2)[:, None] + tail * np.sin(g * np.pi / 2)[:, None]

    # if the source starts after film start (lift earlier than the drop), fade it in softly
    if off < 0:
        s = int(-off * SR)
        ramp = np.clip((np.arange(n) - s) / (0.05 * SR), 0, 1)
        out *= ramp[:, None]

    # a breath before the drop
    dip = 1 - 0.37 * np.clip(1 - np.abs(t - (drop - 0.15)) / 0.15, 0, 1)
    out *= dip[:, None]
    # soft out on the last 250 ms so nothing is cut mid-note
    out *= np.clip((dur - t) / 0.25, 0, 1)[:, None]

    if ref is not None:  # match the old score's post-drop loudness
        a, b = int(drop * SR), int(min(dur - 1, drop + 12) * SR)
        r = np.sqrt(np.mean(ref[a:b] ** 2)) + 1e-9
        m = np.sqrt(np.mean(out[a:b] ** 2)) + 1e-9
        out *= r / m
    info = (f"  music: {TRACKS[tid][0]} by {TRACKS[tid][1]} (Mixkit #{tid}), tempo x{f:.3f}, "
            f"lift {lift:.2f}s -> drop {drop:.2f}s, ending crossfade at {xf:.2f}s")
    return out.astype(np.float32), info


def credits():
    lines = ["| Film | Track | Artist | Source |", "|---|---|---|---|"]
    for film, (tid, _d) in SCORE.items():
        title, artist = TRACKS[tid][:2]
        lines.append(f"| {film} | {title} | {artist} | [mixkit.co #{tid}]({url(tid)}) |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(credits())
