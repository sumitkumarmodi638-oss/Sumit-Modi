"""Per-industry soundtrack: score + sound design, all synthesized (no samples).

Usage: python3 audio.py healthcare   -> build/healthcare.wav

Every film shares the arc (tense night -> toggle click -> drop at 9.5 s) but gets
its own key, chord progression and groove so the series doesn't sound copy-pasted.
"""
import os
import sys
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from film import DROP, DURATION, cues_for  # noqa: E402
from stories import ORDER, STORIES  # noqa: E402

SR = 48000
N = int(DURATION * SR)
BEAT = 0.5
rng = np.random.default_rng(21)


# ------------------------------------------------------------------ dsp
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


def sweep(x, f0, f1, q=0.35, blocks=48):
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
    return 2 * np.abs(2 * (ph % 1) - 1) - 1


def noise(d):
    return rng.standard_normal(int(d * SR))


def psum(*xs):
    out = np.zeros(max(len(x) for x in xs))
    for x in xs:
        out[:len(x)] += x
    return out


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


def beats(t0, t1, step=BEAT):
    return np.arange(t0, t1 - 1e-6, step)


# ------------------------------------------------------------------ instruments
def kick():
    d = 0.38
    t = tvec(d)
    return np.tanh(osc(48 + 120 * np.exp(-t / 0.03), d, phase=0) * np.exp(-t / 0.14) * 2)


def bass808(m, d, glide_to=None):
    t = tvec(d)
    f = mtof(m) + 140 * np.exp(-t / 0.03)
    if glide_to is not None:
        f = f + (mtof(glide_to) - mtof(m)) * np.clip((t - d * 0.55) / (d * 0.3), 0, 1)
    return np.tanh(osc(f, d, phase=0) * env(d, 0.002, 0.9, 0.35, 0.08) * 2.2) * 0.8


def bass_pluck(m, d):
    return lp(osc(mtof(m), d, "saw") * 0.7 + osc(mtof(m) / 2, d) * 0.6, 500) * env(d, 0.004, 0.12, 0.5, 0.03)


def snare():
    d = 0.4
    t = tvec(d)
    body = osc(190 * (1 + 0.5 * np.exp(-t / 0.01)), d, phase=0) * np.exp(-t / 0.06)
    nz = bp(noise(d), 1200, 9000) * np.exp(-t / 0.13)
    return body * 0.5 + nz * 0.7


def clap():
    d = 0.3
    t = tvec(d)
    e = sum((t >= o) * np.exp(-np.clip(t - o, 0, None) / (0.008 if k < 2 else 0.08)) for k, o in enumerate((0, 0.011, 0.022)))
    return bp(noise(d), 900, 4500) * e * 0.8


def hat(d=0.04, dec=0.012):
    return hp(noise(d), 7500) * np.exp(-tvec(d) / dec)


def pluck(m, d=0.25):
    s = osc(mtof(m), d, "saw") + 0.6 * osc(mtof(m) * 1.004, d, "saw") + 0.4 * osc(mtof(m + 12), d, "tri")
    return lp(s, 6000) * (0.3 + 0.7 * np.exp(-tvec(d) / 0.05)) * env(d, 0.002, 0.08, 0.0, 0.02)


def stab(ms, d=0.22):
    return lp(sum(supersaw(m, d) for m in ms) / len(ms), 5000) * env(d, 0.003, 0.12, 0.35, 0.06)


def pad(ms, d, bright=2000, a=0.4):
    return lp(sum(supersaw(m, d, 5, 0.15) for m in ms) / len(ms), bright) * env(d, a, 1.5, 1.0, 0.5)


def bell(m, d=0.6):
    t = tvec(d)
    f = mtof(m)
    return (osc(f, d, phase=0) + 0.4 * osc(f * 2.76, d, phase=0) * np.exp(-t / 0.08)
            + 0.2 * osc(f * 5.4, d, phase=0) * np.exp(-t / 0.04)) * np.exp(-t / 0.25)


def marimba(m, d=0.3):
    t = tvec(d)
    return (osc(mtof(m), d, phase=0) + 0.3 * osc(mtof(m) * 4, d, phase=0) * np.exp(-t / 0.02)) * np.exp(-t / 0.09)


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


def click(d=0.015, fc=2000):
    return hp(noise(d), fc) * np.exp(-tvec(d) / (d / 4))


def seq(notes, step, fn, total):
    out = np.zeros(int(total * SR))
    for k, m in enumerate(notes):
        x = fn(m)
        i = int(k * step * SR)
        out[i:i + len(x)] += x[:len(out) - i]
    return out


def sfx_for(kind, i):
    if kind.startswith("riser@"):
        return riser(float(kind[6:]))
    if kind.startswith("revcrash@"):
        d = float(kind[9:])
        return hp(noise(d), 3000) * (tvec(d) / d) ** 3
    if kind in ("impact", "drop", "final_hit"):
        s = impact(2.0 if kind != "impact" else 1.5)
        if kind != "impact":
            s = psum(s, hp(noise(2.5), 4000) * np.exp(-tvec(2.5) / 0.7) * 0.45)
        return s
    if kind == "hit":
        return psum(np.tanh(kick() * 1.3), hp(noise(0.1), 2000) * np.exp(-tvec(0.1) / 0.02) * 0.5)
    if kind == "pop":
        d = 0.09
        return osc(420 * 2 ** ((i % 7) / 7) + 600 * tvec(d) / d, d, phase=0) * np.exp(-tvec(d) / 0.025)
    if kind == "whoosh":
        return whoosh(0.4, 500, 6000)
    if kind == "whip":
        return whoosh(0.25, 6000, 600) * 1.2
    if kind == "ping":  # message notification
        return seq([86, 91], 0.08, lambda m: bell(m, 0.35), 0.5) * 0.6
    if kind == "buzz":  # phone vibrating for a missed call
        d = 0.45
        g = (np.sin(2 * np.pi * 6 * tvec(d)) > 0).astype(float)
        return lp(osc(150, d, "sq"), 900) * g * 0.35
    if kind == "toggle":
        t = tvec(0.3)
        return psum(click(0.015, 1800) * 1.2, osc(1200 * np.exp(-t / 0.02) + 300, 0.3, phase=0) * np.exp(-t / 0.04) * 0.5,
                    osc(110, 0.3, phase=0) * np.exp(-t / 0.05) * 0.6)
    if kind == "glow_swell":
        d = 0.8
        return pad([62, 66, 69, 74], d, 6000, 0.6) * (tvec(d) / d) ** 1.5 * 0.8
    if kind == "snap":
        t = tvec(0.5)
        return psum(osc(80 + 200 * np.exp(-t / 0.02), 0.5, phase=0) * np.exp(-t / 0.08), click(0.02, 1500), bell(91, 0.5) * 0.3)
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
        return psum(osc(900 * np.exp(-t / 0.02) + 200, 0.12, phase=0) * np.exp(-t / 0.03), click(0.008, 3000) * 0.6)
    if kind == "notify":
        return seq([84, 91], 0.1, lambda m: bell(m, 0.4), 0.6) * 0.7
    if kind == "msg_out":
        d = 0.12
        return osc(700 + 900 * tvec(d) / d, d, phase=0) * np.exp(-tvec(d) / 0.04) * 0.6
    if kind == "msg_in":
        return seq([79, 84], 0.07, lambda m: osc(mtof(m), 0.12, phase=0) * np.exp(-tvec(0.12) / 0.04), 0.3) * 0.6
    if kind == "typing":
        return seq([0] * 6, 0.08, lambda m: click(0.01, 2500) * 0.4, 0.5)
    if kind == "ding":
        return bell(88, 0.8) * 0.8
    if kind == "key":
        return psum(click(0.012, 1800 + 400 * (i % 3)) * 0.8, osc(160, 0.012, phase=0) * np.exp(-tvec(0.012) / 0.004) * 0.3)
    if kind == "slide_up":
        return psum(whoosh(0.5, 400, 3000) * 0.8, seq([72, 76, 79], 0.1, lambda m: marimba(m, 0.25), 0.5) * 0.5)
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


# ------------------------------------------------------------------ score
PROGS = {  # chord roots as scale steps of a major key: vi-IV-I-V and I-V-vi-IV
    "pop": [(9, "m"), (5, ""), (0, ""), (7, "")],
    "anthem": [(0, ""), (7, ""), (9, "m"), (5, "")],
}


def triad(root, q):
    third = 3 if q == "m" else 4
    return [root, root + third, root + 7]


def build(key):
    st = STORIES[key]
    idx = ORDER.index(key)
    tonic = 60 + [0, 2, -3, 5, -1, 3, -2, 1, 4][idx]
    groove = "trap" if idx % 2 == 0 else "house"
    prog = PROGS["pop" if idx % 3 != 1 else "anthem"]
    music, drums, sfx, verb = Bus(), Bus(), Bus(), Bus()

    # 0-3 hook: soft pad + pulse; 3-8 night: minor drone + clock; 8-9.5 hush
    music.add(pad([tonic - 12 + n for n in triad(9, "m")], 3.0, 1800, 0.3), 0.0, 1.1)
    for b in beats(0.0, 3.0, 0.5):
        drums.add(kick(), b, 0.85 if (b * 2) % 2 == 0 else 0.5)
    drone = pad([tonic - 15, tonic - 12, tonic - 8], 5.2, 700, 1.0) + osc(mtof(tonic - 27), 5.2) * 0.3 * env(5.2, 1, 1, 1, 0.4)
    music.add(drone, 3.0, 0.5)
    for b in beats(3.0, 8.0):
        drums.add(osc(2400, 0.03, phase=0) * np.exp(-tvec(0.03) / 0.005), b, 0.18)  # clock
    for b in beats(5.0, 8.0, 0.25):
        music.add(bass_pluck(tonic - 27, 0.2), b, 0.25)

    # 9.5-29: the drop
    end = 29.0
    for bar_i, bar in enumerate(beats(DROP, end, 2.0)):
        step, q = prog[bar_i % 4]
        nstep, _ = prog[(bar_i + 1) % 4]
        root = tonic + step
        ch = [n + 12 for n in triad(root - 12, q)] + [root + 12]
        if groove == "trap":
            for off, d, glide in ((0.0, 0.7, None), (0.75, 0.45, None), (1.25, 0.75, tonic + nstep - 36)):
                drums.add(kick(), bar + off, 0.7)
                music.add(bass808(root - 36, d, glide), bar + off, 0.9)
            drums.add(snare(), bar + 1.0, 0.75)
            for b in beats(bar, bar + 2.0, 0.25):
                if not (bar_i % 2 == 1 and b >= bar + 1.5):
                    drums.add(hat(), b, 0.25, pan=0.25)
            if bar_i % 2 == 1:
                for k, b in enumerate(beats(bar + 1.5, bar + 2.0, 0.5 / 6)):
                    drums.add(hat(0.03, 0.008), b, 0.12 + 0.03 * k, pan=0.25)
        else:
            for b in beats(bar, bar + 2.0):
                drums.add(kick(), b, 0.8)
                if int(round((b - bar) / BEAT)) % 2 == 1:
                    drums.add(clap(), b, 0.55)
                drums.add(hat(0.2, 0.06), b + 0.25, 0.18, pan=-0.2)
            for k, b in enumerate(beats(bar, bar + 2.0, 0.25)):
                music.add(bass_pluck(root - 24 + (12 if k % 2 else 0), 0.22), b, 0.5)
            for b in beats(bar, bar + 2.0, 0.125):
                drums.add(hat(), b, 0.07, pan=0.25)
        for off in ((0.25, 0.75, 1.25, 1.5, 1.75) if groove == "trap" else (0.5, 1.0, 1.75)):
            music.add(stab(ch, 0.22), bar + off, 0.3)
        music.add(pad([n - 12 for n in ch], 2.05, 1600), bar, 0.18)
        motif = [ch[3] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 12]
        for k, off in enumerate((0.0, 0.375, 0.75, 1.0, 1.375, 1.75)):
            p = pluck(motif[k], 0.3)
            music.add(p, bar + off, 0.15, pan=-0.3 if k % 2 else 0.3)
            verb.add(p, bar + off, 0.08)
    final = pad([tonic - 12, tonic - 5, tonic, tonic + 4, tonic + 7, tonic + 12], 3.0, 5000, 0.01) * env(3.0, 0.005, 1.0, 0.3, 1.8)
    music.add(final, end, 0.7)
    verb.add(final, end, 0.5)
    music.add(bass808(tonic - 36, 2.5), end, 0.9)

    for i, (t, kind, g) in enumerate(cues_for(st)):
        s = sfx_for(kind, i)
        start = t - len(s) / SR if "@" in kind else t
        pan = {"pop": -0.4 + 0.12 * (i % 7), "key": 0.15 * ((i % 3) - 1), "card": -0.5 + 0.25 * (i % 5),
               "msg_in": -0.35, "msg_out": 0.35}.get(kind, 0.0)
        sfx.add(s, start, g, pan)
        if kind in ("impact", "drop", "final_hit", "shimmer", "sparkle", "ding", "notify", "ping", "toggle"):
            verb.add(s, start, g * 0.3, pan)

    # sidechain on the drop's kicks
    duck = np.ones(N)
    kicks = []
    for bar in beats(DROP, end, 2.0):
        kicks += [bar + o for o in ((0.0, 0.75, 1.25) if groove == "trap" else (0.0, 0.5, 1.0, 1.5))]
    for kt in kicks:
        j = int(kt * SR)
        k = 1 - 0.55 * np.exp(-tvec(0.4) / 0.09)
        duck[j:j + len(k)] = np.minimum(duck[j:j + len(k)], k[:N - j])
    low = lp(music.x, 150)
    high = music.x - low
    mus = low + high * duck[:, None]

    def reverb(x, secs=2.2):
        t = tvec(secs)
        out = np.zeros_like(x)
        for ch in range(2):
            ir = hp(rng.standard_normal(len(t)) * np.exp(-t / (secs / 5)), 250)
            out[:, ch] = fftconvolve(x[:, ch], ir / np.sqrt(np.sum(ir ** 2)))[:len(x)]
        return out

    mix = mus * 0.85 + drums.x * 0.8 + sfx.x * 0.9 + reverb(verb.x + high * 0.1) * 0.45
    mix = hp(mix, 28)
    mix /= np.percentile(np.abs(mix), 99.9) + 1e-9
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)
    fade = np.ones(N)
    fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR)) ** 2
    mix *= fade[:, None]
    mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    out = os.path.join(HERE, "build", f"{key}.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print("wrote", out)


if __name__ == "__main__":
    for k in (sys.argv[1:] or ORDER):
        build(k)
