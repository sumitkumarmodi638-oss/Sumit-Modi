"""Final mix: voiceover + music + SFX onto the silent picture, like a finishing editor would.

Usage:
  python3 mix.py                     # every film whose takes are all present
  python3 mix.py healthcare food     # just these
  python3 mix.py --scratch           # pipeline test with placeholder 'scratch' VO (never ship these)

Takes go in voiceover/takes/<film>/<NN>.<wav|mp3|m4a>, NN = line index in scripts.py.

Per line (VO chain):
  trim head/tail silence -> high-pass 85 Hz -> cut mud 200 Hz, add presence 3.2 kHz and air
  10 kHz -> de-ess -> 3:1 compression -> level-match every line to the same loudness
  -> if a take overruns its slot, time-fit with Rubber Band (pitch kept) up to 12% faster.
Mix:
  music ducks -10 dB under the voice (80 ms look-ahead, so it dips just BEFORE each word),
  SFX duck only -3 dB so hits and whooshes still land, a touch of short room on the voice,
  then look-ahead limiter + EBU R128 loudness to -14 LUFS / -2 dBTP for social platforms.
Also writes an .srt per film with the spoken lines (for YouTube/LinkedIn closed captions).
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

from scripts import FILMS, ORDER, estimate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SR = 48000
TAKES = os.path.join(HERE, "takes")
OUT = os.path.join(ROOT, "final")
MAX_SPEEDUP = 1.12
NAMES = {"brand-film": "varnik-labs-brand-film", "scroll-stopper": "varnik-labs-scroll-stopper"}

VO_CHAIN = ",".join([
    "aresample=48000", "aformat=sample_fmts=flt:channel_layouts=mono",
    "highpass=f=85", "lowpass=f=15000",
    "equalizer=f=200:t=q:w=1:g=-2.5", "equalizer=f=3200:t=q:w=1.2:g=2.5", "equalizer=f=10000:t=q:w=1:g=1.5",
    "deesser=i=0.4:m=0.5:f=0.5",
    "acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=3",
])


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr.strip()[-800:]}")


def read_wav(path):
    sr, x = wavfile.read(path)
    if x.dtype.kind == "i":
        x = x.astype(np.float32) / np.iinfo(x.dtype).max
    assert sr == SR, (path, sr)
    return x.astype(np.float32)


def ffmpeg_audio(src, chain, dst):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", chain, "-ar", str(SR), "-c:a", "pcm_f32le", dst])
    return read_wav(dst)


def find_take(film, i):
    d = os.path.join(TAKES, film)
    for ext in ("wav", "mp3", "m4a", "flac", "ogg"):
        p = os.path.join(d, f"{i:02d}.{ext}")
        if os.path.exists(p):
            return p
    return None


def scratch_take(text, path):
    """Placeholder 'speech': band-limited noise pulsing at syllable rate, for testing the mix only."""
    rng = np.random.default_rng(abs(hash(text)) % 2 ** 32)
    d = estimate(text) * 0.9
    t = np.arange(int(d * SR)) / SR
    n = sosfilt(butter(2, [250, 3200], "band", fs=SR, output="sos"), rng.standard_normal(len(t)))
    syl = 0.5 + 0.5 * np.sin(2 * np.pi * 4.2 * t) ** 2
    x = n * syl * np.clip(t / 0.03, 0, 1) * np.clip((d - t) / 0.05, 0, 1)
    wavfile.write(path, SR, (x / np.max(np.abs(x)) * 0.5).astype(np.float32))
    return path


def dialogue_edit(x, max_gap=0.22, floor_db=-32):
    """Edit a take the way a dialogue editor would:
    - trim to the first/last real syllable (ignores room tone and stray clicks under 60 ms),
    - tighten any pause longer than `max_gap` down to `max_gap` (short crossfades, no clicks).
    """
    f = int(0.02 * SR)
    frames = len(x) // f
    if frames < 3:
        return x
    rms = np.sqrt(np.mean(x[: frames * f].reshape(frames, f) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-9)
    voiced = db > db.max() + floor_db
    runs, k = [], 0  # voiced runs, dropping blips shorter than 3 frames (60 ms)
    while k < frames:
        if voiced[k]:
            j = k
            while j < frames and voiced[j]:
                j += 1
            if j - k >= 3:
                runs.append((k, j))
            k = j
        else:
            k += 1
    if not runs:
        return x
    head, tail, fade = int(0.04 * SR), int(0.12 * SR), int(0.008 * SR)
    pieces, gap_keep = [], int(max_gap * SR)
    for i, (a, b) in enumerate(runs):
        s0 = a * f - (head if i == 0 else 0)
        s1 = b * f + (tail if i == len(runs) - 1 else 0)
        if i:  # the pause before this run: keep at most max_gap of it
            prev_end = runs[i - 1][1] * f
            gap = a * f - prev_end
            keep = min(gap, gap_keep)
            s0 = a * f - keep // 2
            pieces[-1] = (pieces[-1][0], prev_end + (keep - keep // 2))
        pieces.append((max(0, s0), min(len(x), s1)))
    out = []
    for s0, s1 in pieces:
        seg = x[s0:s1].copy()
        n = min(fade, len(seg) // 2)
        if n:
            ramp = np.linspace(0, 1, n, dtype=np.float32)
            seg[:n] *= ramp
            seg[-n:] *= ramp[::-1]
        out.append(seg)
    return np.concatenate(out)


def rms_db(x):
    a = np.abs(x)
    active = x[a > 0.02 * a.max()] if a.max() > 0 else x
    return 20 * np.log10(np.sqrt(np.mean(active ** 2)) + 1e-9)


def moving_sum(x, w):
    """Centred running sum over w samples (O(n), unlike a long np.convolve)."""
    c = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    lo = np.clip(np.arange(len(x)) - w // 2, 0, len(x))
    hi = np.clip(np.arange(len(x)) + (w - w // 2), 0, len(x))
    return (c[hi] - c[lo]).astype(np.float32)


def envelope(x, attack=0.04, release=0.30, lookahead=0.08, thresh_db=-40):
    """0..1 'voice is talking' envelope, smoothed and shifted earlier by the look-ahead."""
    p = np.sqrt(moving_sum(x ** 2, int(0.02 * SR)) / int(0.02 * SR))
    gate = (20 * np.log10(p + 1e-9) > thresh_db).astype(np.float32)
    # hold through the small gaps between words so the music doesn't pump
    hold = int(0.25 * SR)
    gate = moving_sum(gate, hold) > 0
    out = np.zeros(len(gate), np.float32)
    a_up, a_dn = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    y = 0.0
    g = gate.astype(np.float32)
    for k in range(0, len(g), 64):  # block-wise one-pole, fast enough in numpy
        target = g[k]
        coef = a_up if target > y else a_dn
        y = target + (y - target) * coef ** 64
        out[k:k + 64] = y
    la = int(lookahead * SR)
    return np.concatenate([out[la:], np.zeros(la, np.float32)])


def room_ir(secs=0.35):
    rng = np.random.default_rng(4)
    t = np.arange(int(secs * SR)) / SR
    ir = rng.standard_normal(len(t)) * np.exp(-t / 0.07)
    ir = sosfilt(butter(2, [300, 6000], "band", fs=SR, output="sos"), ir)
    return ir / np.sqrt(np.sum(ir ** 2))


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


STEM_GAIN = 0.25  # export_stems.py wrote the FLAC stems at this gain


def load_stem(film, kind, n):
    """Prefer the committed FLAC stem (works from a plain git clone), else the build WAV."""
    flac = os.path.join(HERE, "stems", f"{film}_{kind}.flac")
    if os.path.exists(flac):
        with tempfile.TemporaryDirectory() as tmp:
            x = ffmpeg_audio(flac, f"volume={1 / STEM_GAIN}", os.path.join(tmp, "s.wav"))
    else:
        cfg = FILMS[film]
        x = read_wav(os.path.join(ROOT, cfg["project"], "build", f"{cfg['stem']}_{kind}.wav"))
    x = x[:n]
    return np.pad(x, ((0, n - len(x)), (0, 0)))


def mix_film(film, scratch=False):
    cfg = FILMS[film]
    proj = os.path.join(ROOT, cfg["project"])
    n = int(cfg["duration"] * SR)
    music, sfx = load_stem(film, "music", n), load_stem(film, "sfx", n)
    vo = np.zeros(n, np.float32)
    report, subs = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (start, end, text) in enumerate(cfg["lines"]):
            take = find_take(film, i)
            if take is None:
                if not scratch:
                    raise FileNotFoundError(f"{film}: missing take {i:02d} ({text!r})")
                take = scratch_take(text, os.path.join(tmp, f"s{i}.wav"))
            x = dialogue_edit(ffmpeg_audio(take, VO_CHAIN, os.path.join(tmp, f"v{i}.wav")))
            dur, slot = len(x) / SR, end - start
            speed = 1.0
            if dur > slot:
                speed = min(dur / slot, MAX_SPEEDUP)
                ed = os.path.join(tmp, f"e{i}.wav")
                wavfile.write(ed, SR, x.astype(np.float32))
                x = ffmpeg_audio(ed, f"rubberband=tempo={speed:.4f}:pitchq=quality", os.path.join(tmp, f"f{i}.wav"))
            x = x * 10 ** ((-17.0 - rms_db(x)) / 20)  # every line at the same level
            s = int(start * SR)
            seg = x[: max(0, n - s)]
            vo[s:s + len(seg)] += seg
            real_end = start + len(seg) / SR
            flag = "OVERRUN" if real_end > end + 0.02 else ""
            report.append(f"  {i:02d} {start:6.2f}-{real_end:6.2f} (slot to {end:6.2f}) x{speed:.2f} {flag} {text}")
            subs.append((start, real_end, text))

    talk = envelope(vo)
    duck_music = 10 ** (-10 * talk / 20)
    duck_sfx = 10 ** (-3 * talk / 20)
    room = fftconvolve(vo, room_ir())[:n] * 0.08
    voice = (vo + room)[:, None] * np.array([[1.0, 1.0]], np.float32)
    mix = music * duck_music[:, None] + sfx * duck_sfx[:, None] + voice * 1.15
    mix = sosfilt(butter(2, 25, "high", fs=SR, output="sos"), mix, axis=0)

    os.makedirs(OUT, exist_ok=True)
    name = NAMES.get(film, f"varnik-labs-{film}") + ("-SCRATCH" if scratch else "")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "mix.wav")
        wavfile.write(wav, SR, (mix / (np.max(np.abs(mix)) + 1e-9) * 0.9).astype(np.float32))
        pic = os.path.join(proj, cfg["video"])  # the finished film; its video is copied bit-for-bit
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-af", "alimiter=limit=0.7:attack=2:release=40:level=false,loudnorm=I=-14:TP=-2:LRA=9,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo",
             "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
             os.path.join(OUT, name + ".mp4")])
    with open(os.path.join(OUT, name + ".srt"), "w") as fh:
        for k, (a, b, t) in enumerate(subs, 1):
            fh.write(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n")
    print(f"{film}: {os.path.join(OUT, name + '.mp4')}")
    print("\n".join(report))


if __name__ == "__main__":
    scratch = "--scratch" in sys.argv
    films = [a for a in sys.argv[1:] if not a.startswith("--")] or ORDER
    for f in films:
        if not scratch and any(find_take(f, i) is None for i in range(len(FILMS[f]["lines"]))):
            print(f"{f}: skipped (takes missing in voiceover/takes/{f}/)")
            continue
        mix_film(f, scratch)
