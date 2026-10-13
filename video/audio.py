"""Synthesises the full soundtrack (score + sound design) to a stereo WAV.

Everything is generated from scratch with numpy/scipy, so there are no
licensing questions. The arrangement follows the scene cues in config.py.

    python3 audio.py out/soundtrack.wav
"""
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

import config as C

SR = 48000
N = int(C.DURATION * SR)
rng = np.random.default_rng(7)
B = C.BEAT


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def note(name):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
             "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    pc, octave = name[:-1], int(name[-1])
    midi = 12 * (octave + 1) + names[pc]
    return 440.0 * 2 ** ((midi - 69) / 12)


def sos(kind, freq, order=2):
    return signal.butter(order, freq, btype=kind, fs=SR, output="sos")


def filt(x, kind, freq, order=2):
    return signal.sosfilt(sos(kind, freq, order), x)


def sweep_filter(x, f0, f1, kind="bandpass", width=0.6, block=512):
    """Time-varying filter: exponential cutoff sweep from f0 to f1."""
    out = np.zeros_like(x)
    zi = None
    nb = int(np.ceil(len(x) / block))
    for i in range(nb):
        f = f0 * (f1 / f0) ** (i / max(1, nb - 1))
        if kind == "bandpass":
            s = sos("bandpass", [f * (1 - width / 2), min(f * (1 + width / 2), SR / 2 - 100)])
        else:
            s = sos(kind, min(f, SR / 2 - 100))
        if zi is None or zi.shape[0] != s.shape[0]:
            zi = np.zeros((s.shape[0], 2))
        seg = x[i * block:(i + 1) * block]
        out[i * block:(i + 1) * block], zi = signal.sosfilt(s, seg, zi=zi)
    return out


class Bus:
    def __init__(self):
        self.L = np.zeros(N + SR * 4)
        self.R = np.zeros(N + SR * 4)

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i < 0:
            sig, i = sig[-i:], 0
        n = min(len(sig), len(self.L) - i)
        if n <= 0:
            return
        lg = gain * np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
        rg = gain * np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
        self.L[i:i + n] += sig[:n] * lg
        self.R[i:i + n] += sig[:n] * rg

    def stereo(self):
        return np.stack([self.L, self.R])


# ---------------------------------------------------------------- instruments
def kick(dur=0.45, f0=150, f1=45, punch=1.0):
    t = tt(dur)
    freq = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(ph) * np.exp(-t * 7)
    click = filt(rng.standard_normal(len(t)), "highpass", 3000) * np.exp(-t * 400) * 0.25
    return np.tanh((body + click) * 1.6 * punch) * 0.9


def clap(dur=0.35):
    t = tt(dur)
    n = rng.standard_normal(len(t))
    env = np.zeros_like(t)
    for k, d in enumerate([0, 0.011, 0.022]):
        env += (t >= d) * np.exp(-(t - d).clip(0) * (180 if k < 2 else 22))
    return filt(n * env, "bandpass", [900, 2600]) * 1.4


def hat(dur=0.08, open_=False):
    t = tt(dur if not open_ else 0.3)
    n = filt(rng.standard_normal(len(t)), "highpass", 7000)
    return n * np.exp(-t * (60 if not open_ else 12)) * 0.6


def sub(freq, dur):
    t = tt(dur)
    env = np.minimum(1, t / 0.01) * np.exp(-t * 1.2) * np.minimum(1, (dur - t) / 0.03).clip(0)
    x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return np.tanh(x * 1.5) * env * 0.8


def supersaw(freqs, dur, cutoff=1800, attack=0.4, release=0.6):
    t = tt(dur + release)
    x = np.zeros_like(t)
    for f in freqs:
        for d in (-0.12, -0.05, 0, 0.06, 0.13):
            ff = f * 2 ** (d / 12)
            x += signal.sawtooth(2 * np.pi * ff * t + rng.uniform(0, 6.28))
    x /= len(freqs) * 5
    env = np.minimum(1, t / attack) * np.where(t > dur, np.exp(-(t - dur) * 5), 1)
    return filt(x, "lowpass", cutoff, 2) * env


def pluck(freq, dur=0.6, bright=1.0):
    t = tt(dur)
    x = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 6)
         + 0.35 * bright * np.sin(2 * np.pi * freq * 4.0 * t) * np.exp(-t * 18)
         + 0.15 * bright * np.sin(2 * np.pi * freq * 9.2 * t) * np.exp(-t * 40))
    return x * np.minimum(1, t / 0.002) * 0.5


def bell(freq, dur=2.5):
    t = tt(dur)
    x = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t * dcy)
            for r, a, dcy in [(1, 1, 1.6), (2.76, 0.4, 3), (5.4, 0.2, 6), (8.93, 0.1, 9)])
    return x * np.minimum(1, t / 0.003) * 0.25


def noise_burst(dur, lo=200, hi=8000, decay=8):
    t = tt(dur)
    return filt(rng.standard_normal(len(t)), "bandpass", [lo, hi]) * np.exp(-t * decay)


def impact(size=1.0):
    t = tt(2.5)
    boom_f = 38 + 70 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(boom_f) / SR) * np.exp(-t * 1.6)
    crack = noise_burst(2.5, 80, 5000, 5) * 0.5
    return np.tanh((boom * 1.2 + crack) * size) * 0.9


def riser(dur, f0=300, f1=9000):
    t = tt(dur)
    n = sweep_filter(rng.standard_normal(len(t)), f0, f1, "bandpass", 0.5)
    tone_f = 110 * (8 ** (t / dur))
    tone = signal.sawtooth(2 * np.pi * np.cumsum(tone_f) / SR) * 0.12
    tone = filt(tone, "lowpass", 4000)
    env = (t / dur) ** 2.2
    return (n * 1.4 + tone) * env


def whoosh(dur=0.45, up=True):
    t = tt(dur)
    n = rng.standard_normal(len(t))
    n = sweep_filter(n, 400 if up else 5000, 5000 if up else 400, "bandpass", 0.9)
    env = np.sin(np.pi * t / dur) ** 2
    return n * env * 1.6


def reverse_cymbal(dur=1.6):
    t = tt(dur)
    c = filt(rng.standard_normal(len(t)), "highpass", 4500) * np.exp(-t * 2.4)
    return c[::-1] * 0.8


def tick():
    t = tt(0.05)
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120) * 0.5


def glitch(dur):
    """Stuttered, bit-crushed digital chatter."""
    t = tt(dur)
    out = np.zeros_like(t)
    seg = int(SR * 0.0625)
    base = signal.square(2 * np.pi * 180 * t[:seg]) * 0.3 + rng.standard_normal(seg) * 0.2
    for i in range(0, len(t), seg):
        k = (i // seg) % 4
        piece = base * (1 if k != 2 else 0.4)
        if k == 3:
            piece = np.repeat(piece[::4], 4)[:seg]
        out[i:i + seg] = piece[:len(out[i:i + seg])]
    crushed = np.round(out * 8) / 8
    return filt(crushed, "bandpass", [300, 6000]) * 0.9


def reverb_ir(dur=2.2, decay=3.2):
    t = tt(dur)
    l = rng.standard_normal(len(t)) * np.exp(-t * decay)
    r = rng.standard_normal(len(t)) * np.exp(-t * decay)
    l, r = filt(l, "lowpass", 6000), filt(r, "lowpass", 6000)
    return l / np.abs(l).sum() * 40, r / np.abs(r).sum() * 40


# ------------------------------------------------------------------ arrange
def build():
    drums, music, fx, verb_send = Bus(), Bus(), Bus(), Bus()
    kicks = []

    chords = [["B3", "D4", "F#4"], ["G3", "B3", "D4"], ["D4", "F#4", "A4"], ["A3", "C#4", "E4"]]
    roots = ["B1", "G1", "D2", "A1"]
    bar = 4 * B

    # ---- HOOK 0-3 s: drone, word impacts, glitch, riser into the drop
    t_h = tt(3.0)
    drone = (np.sin(2 * np.pi * note("B1") * t_h) * 0.5 + supersaw([note("B2"), note("F#3")], 3.0, 600, 0.8, 0)[:len(t_h)])
    music.add(drone * np.minimum(1, t_h / 0.3) * 0.35, 0)
    for i in range(3):
        fx.add(impact(0.55), i * B, 0.55)
        fx.add(tick(), i * B, 0.6)
        verb_send.add(impact(0.4), i * B, 0.25)
    fx.add(glitch(0.5), 1.5, 0.45)
    fx.add(whoosh(0.6), 1.9, 0.5, -0.3)
    fx.add(riser(2.0), 1.0, 0.5)
    fx.add(reverse_cymbal(1.6), 3.0 - 1.6, 0.6)
    kicks.append(3.0)

    # ---- the drop
    fx.add(impact(1.2), 3.0, 0.95)
    verb_send.add(impact(1.0), 3.0, 0.5)
    for f in ["D6", "F#6", "A6", "D7"]:
        verb_send.add(bell(note(f), 3.0), 3.0 + 0.02 * rng.random(), 0.5)
    fx.add(hat(0.3, True) * 1.4, 3.0, 0.5)

    def groove(t0, t1, kick_on=True, clap_on=True, hats=True, half=False):
        n_beats = int(round((t1 - t0) / B))
        for b in range(n_beats):
            t = t0 + b * B
            if kick_on and (not half or b % 4 == 0):
                drums.add(kick(), t, 0.95)
                kicks.append(t)
            if clap_on and b % 2 == 1 and not half:
                drums.add(clap(), t, 0.42)
                verb_send.add(clap(), t, 0.25)
            if hats:
                drums.add(hat(), t + B / 2, 0.28, 0.25)
                drums.add(hat(0.05), t + B / 4 * 3, 0.10, -0.25)

    def harmony(t0, t1, cutoff=2200, pad_gain=0.30, arp=True, bass=True):
        tb = t0
        while tb < t1 - 1e-6:
            k = int(round((tb - C.REVEAL[0]) / bar)) % 4
            dur = min(bar, t1 - tb)
            freqs = [note(n) for n in chords[k]]
            music.add(supersaw(freqs + [freqs[0] / 2], dur, cutoff, 0.25, 0.5), tb, pad_gain)
            if bass:
                for b in range(int(round(dur / B))):
                    music.add(sub(note(roots[k]), B * 0.95), tb + b * B, 0.55)
            if arp:
                seq = freqs + [freqs[0] * 2] + freqs[::-1]
                for s in range(int(round(dur / (B / 2)))):
                    f = seq[s % len(seq)] * 2
                    pan = 0.35 * np.sin(s * 1.3)
                    music.add(pluck(f, 0.5), tb + s * B / 2, 0.22, pan)
                    verb_send.add(pluck(f, 0.5), tb + s * B / 2, 0.12)
            tb += bar

    # ---- REVEAL 3-7: pad + arp, drums enter at 5
    harmony(3.0, 7.0, cutoff=1600, bass=False)
    groove(5.0, 7.0, clap_on=False)
    for i, ch in enumerate(C.BRAND):
        fx.add(tick(), 3.6 + i * 0.06, 0.18, -0.4 + 0.1 * i)
    for f in ["A6", "D7", "F#7"]:
        verb_send.add(bell(note(f), 2.0), 4.5, 0.35)   # logo light sweep shimmer
    fx.add(whoosh(0.5, up=False), 4.9, 0.25, 0.4)       # tagline

    # ---- FEATURES 7-15: full groove + whip-pan whooshes
    fx.add(impact(0.8), 7.0, 0.6)
    harmony(7.0, 15.0, cutoff=2600)
    groove(7.0, 15.0)
    for i in range(4):
        t = C.FEATURES_T[0] + 2 * i
        fx.add(tick(), t + 0.15, 0.4)
        if i:
            fx.add(whoosh(0.4), t - 0.2, 0.75, -0.8 if i % 2 else 0.8)

    # ---- FIELD 15-21: cinematic half-time, filtered pad, riser to drop
    fx.add(whoosh(0.9, up=False), 14.6, 0.5)
    harmony(15.0, 21.0, cutoff=1100, pad_gain=0.42, bass=True)
    groove(15.0, 19.0, clap_on=False, hats=False, half=True)
    for t in np.arange(19.0, 21.0, B / 2):
        rate = 1 if t < 20.0 else 2
        for s in range(rate):
            drums.add(clap(0.2), t + s * B / 4, 0.12 + 0.18 * (t - 19.0) / 2)
    fx.add(riser(2.0, 400, 12000), 19.0, 0.55)
    fx.add(reverse_cymbal(1.2), 21.0 - 1.2, 0.5)

    # ---- MONTAGE 21-25: impacts on every cut, full groove
    for i in range(4):
        fx.add(impact(0.9 if i == 0 else 0.6), 21.0 + i * B, 0.75 if i == 0 else 0.5)
        fx.add(whoosh(0.25), 21.0 + i * B - 0.12, 0.35, (-1) ** i * 0.6)
    harmony(21.0, 25.0, cutoff=3200)
    groove(21.0, 25.0)
    for i in range(4):
        fx.add(tick(), 23.0 + 0.15 + i * 0.12, 0.35, -0.5 + i / 3)

    # ---- CTA 25-30: lockup, button pulses, final hit at 29
    fx.add(impact(1.0), 25.0, 0.8)
    verb_send.add(impact(0.9), 25.0, 0.4)
    harmony(25.0, 29.0, cutoff=2800)
    groove(25.0, 29.0)
    for f in ["D6", "A6", "D7"]:
        verb_send.add(bell(note(f), 2.5), 26.0, 0.3)
    fx.add(riser(1.0, 800, 10000), 28.0, 0.35)
    fx.add(impact(1.3), 29.0, 1.0)
    final = supersaw([note("D3"), note("A3"), note("D4"), note("F#4")], 1.0, 3000, 0.01, 1.5)
    music.add(final, 29.0, 0.5)
    verb_send.add(final, 29.0, 0.4)
    for f in ["D6", "F#6", "A6"]:
        verb_send.add(bell(note(f), 2.0), 29.0, 0.4)

    # ---- sidechain: duck music bus on kicks
    t_all = np.arange(len(music.L)) / SR
    duck = np.ones_like(t_all)
    for k in kicks:
        m = t_all >= k
        duck[m] = np.minimum(duck[m], 1 - 0.55 * np.exp(-(t_all[m] - k) / 0.11))
    music.L *= duck
    music.R *= duck

    # ---- reverb
    irl, irr = reverb_ir()
    vl = signal.fftconvolve(verb_send.L + music.L * 0.15, irl)[:len(music.L)]
    vr = signal.fftconvolve(verb_send.R + music.R * 0.15, irr)[:len(music.R)]

    mix = drums.stereo() + music.stereo() + fx.stereo() + np.stack([vl, vr]) * 0.9
    mix = mix[:, :N]
    # glue: gentle low cut, soft clip, fade tail
    mix = signal.sosfilt(sos("highpass", 28), mix, axis=1)
    mix = np.tanh(mix * 0.9) / np.tanh(0.9)
    fade = np.ones(N)
    fl = int(0.6 * SR)
    fade[-fl:] = np.linspace(1, 0, fl) ** 2
    mix *= fade
    mix /= np.abs(mix).max() / 0.89
    return mix


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "out/soundtrack.wav"
    mix = build()
    wavfile.write(out, SR, (mix.T * 32767).astype(np.int16))
    print("wrote", out, mix.shape[1] / SR, "s")
