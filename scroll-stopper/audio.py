"""Soundtrack for "The Scroll Stopper": score + sound design, all synthesized.

  0-3 s     clock ticks counting down, buzzer + impact at zero
  4.5-10 s  cheesy "phone speaker" music under the doom-scroll; it tape-stops
            when the thumb stops on the post
  12.5 s    drop: half-time trap beat in Ab (Fm-Db-Ab-Eb), 808 glides,
            hat rolls, future-bass chord stabs
  38 s      final chord + reverb tail

Output: build/soundtrack.wav (48 kHz stereo).
"""
import os
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

from timeline import BEAT, CUES, DROP, DURATION

SR = 48000
N = int(DURATION * SR)
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(9)


# ------------------------------------------------------------------ dsp basics
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def env(d, a=0.005, dec=0.1, s=0.0, r=0.05):
    t = tvec(d)
    e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(dec, 1e-6)))
    return e * np.clip((d - t) / max(r, 1e-6), 0, 1)


def lp(x, fc, o=2):
    return sosfilt(butter(o, min(fc, SR / 2 - 100), "low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, o=2):
    return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, min(hi, SR / 2 - 200)], "band", fs=SR, output="sos"), x, axis=0)


def sweep(x, f0, f1, q=0.35, blocks=64):
    out = np.zeros_like(x)
    e = np.linspace(0, len(x), blocks + 1).astype(int)
    for i in range(blocks):
        fc = f0 * (f1 / f0) ** (i / max(blocks - 1, 1))
        out[e[i]:e[i + 1]] = bp(x[e[i]:e[i + 1]], fc * (1 - q), fc * (1 + q))
    return out


def osc(freq, d, kind="sin", phase=None):
    n = int(d * SR)
    f = np.broadcast_to(freq, (n,)) if np.ndim(freq) == 0 else freq[:n]
    ph = np.cumsum(f / SR) + (rng.random() if phase is None else phase)
    if kind == "sin":
        return np.sin(2 * np.pi * ph)
    if kind == "saw":
        return 2 * (ph % 1) - 1
    if kind == "sq":
        return np.sign(np.sin(2 * np.pi * ph))
    if kind == "tri":
        return 2 * np.abs(2 * (ph % 1) - 1) - 1


def noise(d):
    return rng.standard_normal(int(d * SR))


def supersaw(m, d, voices=7, detune=0.22):
    return sum(osc(mtof(m) * 2 ** ((v - (voices - 1) / 2) * detune / (voices - 1) / 12), d, "saw")
               for v in range(voices)) / voices


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N:
            return
        if i < 0:
            sig, i = sig[-i:], 0
        sig = sig[:N - i]
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l, sig * r], 1) * 1.414
        self.x[i:i + len(sig)] += sig * gain


music, drums, sfx, verb = Bus(), Bus(), Bus(), Bus()


def beats(t0, t1, step=BEAT):
    return np.arange(t0, t1 - 1e-6, step)


# ------------------------------------------------------------------ instruments
def kick808(m, d, glide_to=None):
    t = tvec(d)
    f0 = mtof(m)
    f = f0 + 160 * np.exp(-t / 0.03)
    if glide_to is not None:
        f = f + (mtof(glide_to) - f0) * np.clip((t - d * 0.55) / (d * 0.3), 0, 1)
    s = osc(f, d, phase=0) * env(d, 0.002, 0.9, 0.35, 0.08)
    return np.tanh(s * 2.2) * 0.8


def kick_punch():
    d = 0.35
    t = tvec(d)
    return np.tanh(osc(50 + 120 * np.exp(-t / 0.03), d, phase=0) * np.exp(-t / 0.12) * 2)


def snare():
    d = 0.4
    t = tvec(d)
    body = osc(190 * (1 + 0.5 * np.exp(-t / 0.01)), d, phase=0) * np.exp(-t / 0.06)
    nz = bp(noise(d), 1200, 9000) * np.exp(-t / 0.13)
    clap = bp(noise(d), 900, 4000) * sum((t >= o) * np.exp(-np.clip(t - o, 0, None) / 0.008) for o in (0, 0.012, 0.024))
    return body * 0.5 + nz * 0.6 + clap * 0.5


def hat(d=0.04, dec=0.012):
    return hp(noise(d), 7500) * np.exp(-tvec(d) / dec)


def pluck(m, d=0.25, bright=6000):
    s = osc(mtof(m), d, "saw") + 0.6 * osc(mtof(m) * 1.004, d, "saw") + 0.4 * osc(mtof(m + 12), d, "tri")
    t = tvec(d)
    return lp(s, bright) * (0.3 + 0.7 * np.exp(-t / 0.05)) * env(d, 0.002, 0.08, 0.0, 0.02)


def chord_stab(ms, d=0.3, bright=5000):
    s = sum(supersaw(m, d) for m in ms) / len(ms)
    return lp(s, bright) * env(d, 0.003, 0.12, 0.35, 0.06)


def pad(ms, d, bright=2000, a=0.4):
    s = sum(supersaw(m, d, 5, 0.15) for m in ms) / len(ms)
    return lp(s, bright) * env(d, a, 1.5, 1.0, 0.5)


def bell(m, d=0.6):
    t = tvec(d)
    f = mtof(m)
    return (osc(f, d, phase=0) + 0.4 * osc(f * 2.76, d, phase=0) * np.exp(-t / 0.08)
            + 0.2 * osc(f * 5.4, d, phase=0) * np.exp(-t / 0.04)) * np.exp(-t / 0.25)


def marimba(m, d=0.3):
    t = tvec(d)
    f = mtof(m)
    return (osc(f, d, phase=0) + 0.3 * osc(f * 4, d, phase=0) * np.exp(-t / 0.02)) * np.exp(-t / 0.09)


# ------------------------------------------------------------------ 0-3 s hook: tension under the countdown
d = 2.5
tt = tvec(d)
drone = osc(55 * (1 + 0.5 * tt / d), d, "saw")
edges = np.linspace(0, len(drone), 33).astype(int)
drone = np.concatenate([lp(drone[a:b], 300 + 900 * k / 32) for k, (a, b) in enumerate(zip(edges[:-1], edges[1:]))])
music.add(drone * (tt / d) ** 1.5 * 0.5, 0.0)

# ------------------------------------------------------------------ 4.5-10 s: muzak through a phone speaker, tape-stop
MUZAK_T0, STOP_T0, STOP_T1 = 4.5, 9.6, 10.0
seg = 6.0
mz = np.zeros(int(seg * SR))
prog_c = [(48, [60, 64, 67]), (53, [60, 65, 69]), (55, [59, 62, 67]), (48, [60, 64, 67])]
for k, b in enumerate(beats(0, seg, 0.25)):
    root, ch = prog_c[int(b) % 4]
    i = int(b * SR)
    if k % 2 == 0:
        x = marimba(root if k % 4 == 0 else root + 7, 0.25) * 0.8
    else:
        x = sum(marimba(m, 0.2) for m in ch) / 3
    mz[i:i + len(x)] += x[:len(mz) - i]
for k, b in enumerate(beats(0, seg, 0.5)):  # bouncy melody
    m = [72, 76, 79, 76, 77, 74, 71, 74, 72, 79, 77, 76][k % 12]
    x = osc(mtof(m), 0.22, "sq") * env(0.22, 0.003, 0.08, 0.3, 0.04) * 0.25
    i = int(b * SR)
    mz[i:i + len(x)] += x[:len(mz) - i]
    i2 = int((b + 0.25) * SR)
    h = hat(0.03, 0.008) * 0.4
    mz[i2:i2 + len(h)] += h[:len(mz) - i2]
# tape stop: playback rate falls to zero between STOP_T0 and STOP_T1
out_t = tvec(STOP_T1 - MUZAK_T0)
rate = np.ones_like(out_t)
k0 = (STOP_T0 - MUZAK_T0)
m_ = out_t > k0
rate[m_] = np.clip(1 - (out_t[m_] - k0) / (STOP_T1 - STOP_T0), 0, 1) ** 1.5
src_pos = np.cumsum(rate) - 1
mz_stopped = np.interp(src_pos, np.arange(len(mz)), mz)
mz_stopped = bp(mz_stopped, 450, 3800, 3)  # tiny phone speaker
fade_in = np.clip(out_t / 0.4, 0, 1)
music.add(np.tanh(mz_stopped * 2.5) * fade_in * 0.5, MUZAK_T0, 1.0, pan=0.0)

# ------------------------------------------------------------------ 12.5-38 s: the drop
CHORDS = [  # (808 root, stab chord) Fm - Db - Ab - Eb, one per 2 s bar
    (29, [65, 68, 72, 77]), (25, [65, 68, 73, 77]), (32, [63, 68, 72, 75]), (27, [63, 67, 70, 75])]
END = 38.0
for bar_i, bar in enumerate(beats(DROP, END, 2.0)):
    root, ch = CHORDS[bar_i % 4]
    nxt = CHORDS[(bar_i + 1) % 4][0]
    # 808 + kick pattern (half-time): 0, 0.75, 1.25 (glide into next bar)
    for off, dur, glide in ((0.0, 0.7, None), (0.75, 0.45, None), (1.25, 0.75, nxt)):
        drums.add(kick_punch(), bar + off, 0.7)
        music.add(kick808(root + 12, dur, glide_to=(glide + 12) if glide else None), bar + off, 0.9)
    drums.add(snare(), bar + 1.0, 0.75)
    # hats: 8ths, with a triplet roll closing every second bar
    for b in beats(bar, bar + 2.0, 0.25):
        if bar_i % 2 == 1 and b >= bar + 1.5:
            continue
        drums.add(hat(), b, 0.22 if (b - bar) % 0.5 else 0.3, pan=0.25)
    if bar_i % 2 == 1:
        for k, b in enumerate(beats(bar + 1.5, bar + 2.0, 0.5 / 6)):
            drums.add(hat(0.03, 0.008), b, 0.12 + 0.03 * k, pan=0.25)
    # future-bass stabs on the off-beats + pad + pluck hook
    for off in (0.25, 0.75, 1.25, 1.5, 1.75):
        music.add(chord_stab(ch, 0.22), bar + off, 0.32, pan=0.0)
    music.add(pad([m - 12 for m in ch], 2.05, 1600), bar, 0.18)
    motif = [ch[3] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12]
    for k, off in enumerate((0.0, 0.375, 0.75, 1.0, 1.375, 1.75)):
        p = pluck(motif[k], 0.3)
        music.add(p, bar + off, 0.16, pan=-0.3 if k % 2 else 0.3)
        verb.add(p, bar + off, 0.08)

final = pad([56, 63, 68, 72, 75, 80], 3.0, 5000, a=0.01) * env(3.0, 0.005, 1.0, 0.3, 1.8)
music.add(final, END, 0.7)
verb.add(final, END, 0.5)
music.add(kick808(32, 2.5), END, 0.9)


# ------------------------------------------------------------------ sound design
def whoosh(d=0.45, f0=300, f1=5000):
    return sweep(noise(d), f0, f1) * np.sin(np.pi * tvec(d) / d) ** 2


def impact(d=1.6):
    t = tvec(d)
    boom = osc(30 + 70 * np.exp(-t / 0.06), d, phase=0) * np.exp(-t / 0.45)
    crack = hp(noise(d), 1500) * np.exp(-t / 0.03)
    return np.tanh((boom * 1.2 + crack * 0.6 + lp(noise(d), 300) * np.exp(-t / 0.12) * 0.8) * 1.3)


def riser(d):
    t = tvec(d)
    p = t / d
    return lp(osc(110 * 2 ** (p * 3), d, "saw"), 4000) * 0.25 * p ** 2 + sweep(noise(d), 300, 9000, 0.25) * p ** 2.5 * 0.9


def seq(notes, step, fn, total):
    out = np.zeros(int(total * SR))
    for k, m in enumerate(notes):
        x = fn(m)
        i = int(k * step * SR)
        out[i:i + len(x)] += x[:len(out) - i]
    return out


def psum(*xs):
    """Sum signals of different lengths (zero-padded)."""
    out = np.zeros(max(len(x) for x in xs))
    for x in xs:
        out[:len(x)] += x
    return out


def click(d=0.015, fc=2000):
    return hp(noise(d), fc) * np.exp(-tvec(d) / (d / 4))


def sfx_for(kind, i):
    if kind.startswith("riser@"):
        return riser(float(kind[6:]))
    if kind.startswith("revcrash@"):
        d_ = float(kind[9:])
        return hp(noise(d_), 3000) * (tvec(d_) / d_) ** 3
    if kind == "clock":
        a = osc(2600, 0.04, phase=0) * np.exp(-tvec(0.04) / 0.006)
        return psum(a, click(0.01, 3000) * 0.4)
    if kind == "buzzer":
        d_ = 0.5
        return lp(osc(110, d_, "sq") + osc(116, d_, "sq"), 2500) * env(d_, 0.005, 1, 1, 0.08) * 0.35
    if kind in ("impact", "final_hit", "drop"):
        s = impact(2.0 if kind != "impact" else 1.5)
        if kind != "impact":
            c = hp(noise(2.5), 4000) * np.exp(-tvec(2.5) / 0.7) * 0.45
            s = np.pad(s, (0, len(c) - len(s))) + c
        return s
    if kind == "hit":
        return np.tanh(kick_punch() * 1.3 + np.pad(hp(noise(0.1), 2000) * np.exp(-tvec(0.1) / 0.02), (0, int(0.25 * SR))) * 0.5)
    if kind == "hit_soft":
        return kick_punch() * 0.6 + np.pad(bp(noise(0.1), 800, 3000) * np.exp(-tvec(0.1) / 0.03), (0, int(0.25 * SR))) * 0.3
    if kind == "pop":
        d_ = 0.09
        return osc(420 * 2 ** ((i % 7) / 7) + 600 * tvec(d_) / d_, d_, phase=0) * np.exp(-tvec(d_) / 0.025)
    if kind == "whoosh_up":
        return whoosh(0.5, 200, 4000)
    if kind == "whoosh_in":
        return whoosh(0.6, 400, 9000) * 1.1
    if kind == "whoosh":
        return whoosh(0.4, 500, 6000)
    if kind == "whip":
        return whoosh(0.25, 6000, 600) * 1.2
    if kind == "swipe":  # finger flick on glass
        return sweep(noise(0.18), 2500, 900, 0.3) * np.sin(np.pi * tvec(0.18) / 0.18) * 0.7
    if kind == "stop_thud":
        t = tvec(1.2)
        thud = osc(42 + 60 * np.exp(-t / 0.05), 1.2, phase=0) * np.exp(-t / 0.35)
        return np.tanh(thud * 2) + np.pad(click(0.02, 1200), (0, len(t) - int(0.02 * SR)))
    if kind == "tape_stop":
        return np.zeros(10)
    if kind == "snap":  # shapes lock into the badge
        t = tvec(0.5)
        thump = osc(80 + 200 * np.exp(-t / 0.02), 0.5, phase=0) * np.exp(-t / 0.08)
        return thump + np.pad(click(0.02, 1500), (0, len(t) - int(0.02 * SR))) + bell(91, 0.5) * 0.3
    if kind == "shimmer":
        return seq([84, 88, 91, 96, 100, 103], 0.06, lambda m: bell(m, 0.6) * 0.5, 1.2)
    if kind == "sparkle":
        return seq([96, 91, 100, 94, 103, 98], 0.05, lambda m: bell(m, 0.5) * 0.4, 1.0)
    if kind == "tick":
        return osc(1900, 0.03, phase=0) * np.exp(-tvec(0.03) / 0.005)
    if kind == "fill":
        return sweep(noise(0.3), 800, 5000) * np.sin(np.pi * tvec(0.3) / 0.3) * 0.6
    if kind == "tap":
        t = tvec(0.12)
        return osc(900 * np.exp(-t / 0.02) + 200, 0.12, phase=0) * np.exp(-t / 0.03) + np.pad(click(0.008, 3000), (0, len(t) - int(0.008 * SR))) * 0.6
    if kind == "notify":
        return seq([84, 91], 0.1, lambda m: bell(m, 0.4), 0.6) * 0.7
    if kind == "msg_out":  # sent: quick upward swoosh-blip
        d_ = 0.12
        return osc(700 + 900 * tvec(d_) / d_, d_, phase=0) * np.exp(-tvec(d_) / 0.04) * 0.6
    if kind == "msg_in":
        return seq([79, 84], 0.07, lambda m: osc(mtof(m), 0.12, phase=0) * np.exp(-tvec(0.12) / 0.04), 0.3) * 0.6
    if kind == "typing":
        out = np.zeros(int(0.5 * SR))
        for k in range(6):
            c = click(0.01, 2500) * 0.4
            j = int(k * 0.08 * SR)
            out[j:j + len(c)] += c
        return out
    if kind == "ding":
        return bell(88, 0.8) * 0.8
    if kind == "key":
        return click(0.012, 1800 + 400 * (i % 3)) * 0.8 + osc(160, 0.012, phase=0) * np.exp(-tvec(0.012) / 0.004) * 0.3
    if kind == "slide_up":
        return whoosh(0.5, 400, 3000) * 0.8 + seq([72, 76, 79], 0.1, lambda m: marimba(m, 0.25), 0.5) * 0.5
    if kind == "pin":
        t = tvec(0.3)
        return osc(300 + 500 * np.exp(-t / 0.05), 0.3, phase=0) * np.exp(-t / 0.08)
    if kind == "blip":
        return osc(mtof(72 + 2 * (i % 6)), 0.08, "tri") * np.exp(-tvec(0.08) / 0.03)
    if kind == "levelup":
        return seq([72, 76, 79, 84, 88], 0.06, lambda m: osc(mtof(m), 0.15, "sq") * np.exp(-tvec(0.15) / 0.05) * 0.25, 0.6)
    if kind == "card":
        return whoosh(0.18, 3000, 800) * 0.8
    raise ValueError(kind)


for i, (t, kind, g) in enumerate(CUES):
    s = sfx_for(kind, i)
    start = t - len(s) / SR if "@" in kind else t
    pan = {"pop": -0.4 + 0.12 * (i % 7), "swipe": 0.2, "key": 0.15 * ((i % 3) - 1), "card": -0.5 + 0.25 * (i % 5),
           "msg_in": -0.35, "msg_out": 0.35}.get(kind, 0.0)
    sfx.add(s, start, g, pan)
    if kind in ("impact", "drop", "final_hit", "stop_thud", "shimmer", "sparkle", "ding", "notify", "buzzer"):
        verb.add(s, start, g * 0.3, pan)


# ------------------------------------------------------------------ mix
def reverb(x, secs=2.2):
    t = tvec(secs)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = hp(rng.standard_normal(len(t)) * np.exp(-t / (secs / 5)), 250)
        out[:, ch] = fftconvolve(x[:, ch], ir / np.sqrt(np.sum(ir ** 2)))[:len(x)]
    return out


duck = np.ones(N)
for bar in beats(DROP, END, 2.0):
    for off in (0.0, 0.75, 1.25):
        j = int((bar + off) * SR)
        k = 1 - 0.6 * np.exp(-tvec(0.45) / 0.1)
        duck[j:j + len(k)] = np.minimum(duck[j:j + len(k)], k[:N - j])

mus = music.x.copy()
# keep the 808 out of the duck: re-add low end unducked by splitting bands
low = lp(mus, 150)
high = mus - low
mus = low + high * duck[:, None]
verb_stem = reverb(verb.x + high * 0.1) * 0.45
music_stem = mus * 0.85 + drums.x * 0.8 + verb_stem
sfx_stem = sfx.x * 0.9
mix = music_stem + sfx_stem
mix = hp(mix, 28)
STEM = "scroll-stopper"
_g = 1 / (np.percentile(np.abs(mix), 99.9) + 1e-9)
mix *= _g
# separate stems for the voiceover mix (voiceover/mix.py ducks music under the voice, not the SFX)
from scipy.io import wavfile as _wf
os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
_wf.write(os.path.join(os.path.join(HERE, "build"), STEM + "_music.wav"), SR, (hp(music_stem, 28) * _g).astype(np.float32))
_wf.write(os.path.join(os.path.join(HERE, "build"), STEM + "_sfx.wav"), SR, (hp(sfx_stem, 28) * _g).astype(np.float32))
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
fade = np.ones(N)
fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR)) ** 2
mix *= fade[:, None]
mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))

os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
out = os.path.join(HERE, "build", "soundtrack.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote", out)
