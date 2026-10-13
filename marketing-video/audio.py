"""Synthesize the soundtrack: 120 BPM score + sound design on the shared cue sheet.

Everything is generated from oscillators and noise (no samples), so the track
is fully owned and license-free. Output: build/soundtrack.wav (48 kHz stereo).

Score:  0-2 s   no music, heartbeat + impact (hook)
        2-10.5  "lights off": dark D-minor drone, half-time kick, pulsing bass
        10.5-13.5 music cuts out (power down, switch click, riser)
        13.5    DROP into D major (Bm-G-D-A), four-on-the-floor, sidechained bass
        22-23   drums break for the logo fly-in / snap
        34-37   breakdown under the city shot, builds back into the CTA
        41      final chord hit, reverb tail
"""
import os

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

from timeline import BEAT, CUES, DURATION

SR = 48000
N = int(DURATION * SR)
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(5)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def env(dur, a=0.005, d=0.1, s=0.0, r=0.05, hold=None):
    """ADSR; `hold` = time before release (defaults to dur - r)."""
    t = tvec(dur)
    hold = dur - r if hold is None else hold
    e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-6)))
    rel = np.clip(1 - (t - hold) / max(r, 1e-6), 0, 1)
    return e * np.where(t > hold, rel, 1)


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR / 2 - 100), "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def sweep_filter(x, f0, f1, kind="band", q=0.35, blocks=64):
    """Filter with a moving cutoff (processed in blocks)."""
    out = np.zeros_like(x)
    edges = np.linspace(0, len(x), blocks + 1).astype(int)
    for i in range(blocks):
        fc = f0 * (f1 / f0) ** (i / max(blocks - 1, 1))
        seg = x[edges[i]:edges[i + 1]]
        if kind == "band":
            out[edges[i]:edges[i + 1]] = bp(seg, fc * (1 - q), min(fc * (1 + q), SR / 2 - 200))
        else:
            out[edges[i]:edges[i + 1]] = lp(seg, fc)
    return out


def osc_saw(freq, dur, phase=None):
    f = np.broadcast_to(freq, (int(dur * SR),)) if np.ndim(freq) == 0 else freq
    ph = np.cumsum(f / SR) + (rng.random() if phase is None else phase)
    return 2 * (ph % 1) - 1


def osc_sin(freq, dur, phase=0.0):
    f = np.broadcast_to(freq, (int(dur * SR),)) if np.ndim(freq) == 0 else freq
    return np.sin(2 * np.pi * (np.cumsum(f / SR) + phase))


def supersaw(m, dur, voices=5, detune=0.14):
    out = np.zeros(int(dur * SR))
    for v in range(voices):
        cents = (v - (voices - 1) / 2) * detune / (voices - 1) * 100
        out += osc_saw(mtof(m) * 2 ** (cents / 1200), dur)
    return out / voices


def noise(dur):
    return rng.standard_normal(int(dur * SR))


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N:
            return
        if i < 0:
            sig, i = sig[-i:], 0
        sig = sig[: N - i]
        if sig.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l, sig * r], 1) * 1.414
        self.x[i:i + len(sig)] += sig * gain


music, drums, sfx, verb_send = Bus(), Bus(), Bus(), Bus()

# ------------------------------------------------------------------ instruments


def kick(gain=1.0):
    d = 0.42
    t = tvec(d)
    f = 45 + 110 * np.exp(-t / 0.035)
    body = osc_sin(f, d) * np.exp(-t / 0.16)
    click = hp(noise(d), 3000) * np.exp(-t / 0.004) * 0.3
    return np.tanh((body + click) * 1.6) * gain


def clap():
    d = 0.35
    t = tvec(d)
    e = np.zeros_like(t)
    for k, off in enumerate((0, 0.011, 0.022)):
        e += (t >= off) * np.exp(-np.clip(t - off, 0, None) / (0.006 if k < 2 else 0.09))
    return bp(noise(d), 900, 4500) * e * 0.8


def hat(open_=False):
    d = 0.22 if open_ else 0.05
    return hp(noise(d), 7000) * np.exp(-tvec(d) / (0.07 if open_ else 0.012))


def crash(d=2.5):
    return hp(noise(d), 4000) * np.exp(-tvec(d) / 0.7) * 0.5


def bass_note(m, d):
    s = osc_saw(mtof(m), d) * 0.7 + osc_sin(mtof(m) / 2, d) * 0.6
    return lp(s, 420) * env(d, 0.004, 0.12, 0.55, 0.03)


def pluck(m, d=0.22):
    s = osc_saw(mtof(m), d) + 0.5 * osc_saw(mtof(m) * 1.005, d)
    t = tvec(d)
    cutoff_env = np.exp(-t / 0.05)
    return lp(s, 5000) * (0.25 + 0.75 * cutoff_env) * env(d, 0.002, 0.07, 0.0, 0.02)


def pad_chord(ms, d, bright=2400, a=0.25):
    s = sum(supersaw(m, d) for m in ms) / len(ms)
    return lp(s, bright, 2) * env(d, a, 1.0, 1.0, 0.4)


def bell(m, d=0.6):
    t = tvec(d)
    f = mtof(m)
    s = osc_sin(f, d) + 0.4 * osc_sin(f * 2.76, d) * np.exp(-t / 0.08) + 0.2 * osc_sin(f * 5.4, d) * np.exp(-t / 0.04)
    return s * np.exp(-t / 0.25)


# ------------------------------------------------------------------ score
DROP = 13.5
PROG = [  # (bass root, pad chord) in D major, one chord per 2 s bar: Bm G D A
    (35, [59, 62, 66, 71]), (31, [55, 59, 62, 67]), (38, [57, 62, 66, 69]), (33, [57, 61, 64, 69])]
DARK = [38, 41, 45, 50]  # D minor: lights off


def chord_at(t):
    return PROG[int((t - DROP) // 2) % 4]


def beats(t0, t1, step=BEAT):
    return np.arange(t0, t1 - 1e-6, step)


def in_breaks(t):
    return 22.0 <= t < 23.0 or 34.0 <= t < 37.0 or t >= 41.0


# Lights off (2 - 10.5): drone + half-time kick + muted bass pulse


def heartbeat():
    out = np.zeros(int(0.6 * SR))
    for off, g in ((0, 1.0), (0.26, 0.75)):
        tt = tvec(0.25)
        beat = osc_sin(48 + 30 * np.exp(-tt / 0.03), 0.25) * np.exp(-tt / 0.08) * g
        s0 = int(off * SR)
        out[s0:s0 + len(beat)] += beat
    return out * 1.4


for b in (2.0, 3.0):  # the hook's heartbeat keeps pulsing under "That's all the time you get"
    music.add(heartbeat(), b, 0.6)
drone = pad_chord(DARK, 8.6, bright=900, a=1.2) * 0.5 + osc_sin(mtof(26), 8.6) * 0.25 * env(8.6, 1.5, 1, 1, 0.3)
music.add(drone, 2.0, 0.55)
for b in beats(4.0, 8.5, 1.0):
    drums.add(kick(0.8), b)
for b in beats(4.0, 10.5, 0.25):
    music.add(bass_note(26, 0.2), b, 0.35)
for b in beats(8.5, 10.5):  # strobe: every beat
    drums.add(kick(), b)
for b in beats(4.0, 10.5, 0.25):
    drums.add(hat(), b + 0.125, 0.12, pan=0.3)

# Switch on (13.5 - 41)
for b in beats(DROP, 41.0):
    if not in_breaks(b):
        drums.add(kick(), b)
        if int(round((b - DROP) / BEAT)) % 2 == 1:
            drums.add(clap(), b, 0.55)
        drums.add(hat(True), b + 0.25, 0.18, pan=-0.2)
for b in beats(DROP, 41.0, 0.125):
    if not in_breaks(b):
        drums.add(hat(), b, 0.08 + 0.05 * (int(b * 8) % 2), pan=0.25)

for bar in beats(DROP, 41.0, 2.0):
    root, ch = chord_at(bar + 0.01)
    music.add(pad_chord(ch, 2.05, bright=2600 if bar < 34 else 1500), bar, 0.28)
    for k, b in enumerate(beats(bar, bar + 2.0, 0.25)):
        if not (34.0 <= b < 36.0) and b < 41:  # bass sits out of the first half of the breakdown
            music.add(bass_note(root + (12 if k % 2 else 0), 0.22), b, 0.5)
    if bar >= 16.0 - 0.6:  # arp enters with the sparks
        tones = sorted(ch) + [m + 12 for m in sorted(ch)]
        for k, b in enumerate(beats(bar, bar + 2.0, 0.125)):
            if b >= 41:
                break
            m = tones[[0, 2, 4, 6, 7, 5, 3, 1][k % 8]] + 12
            music.add(pluck(m), b, 0.13, pan=0.35 * np.sin(k))
            verb_send.add(pluck(m), b, 0.06)

# Final chord: D major, big and wide, long tail
final = pad_chord([50, 57, 62, 66, 69, 74], 4.0, bright=4000, a=0.01) * env(4.0, 0.005, 1.2, 0.4, 2.0)
music.add(final, 41.0, 0.6)
verb_send.add(final, 41.0, 0.4)
music.add(bass_note(26, 2.5) * np.exp(-tvec(2.5) / 1.0), 41.0, 0.8)

# ------------------------------------------------------------------ sound design


def whoosh(d=0.45, f0=300, f1=4000):
    n = sweep_filter(noise(d), f0, f1)
    t = tvec(d)
    return n * np.sin(np.pi * t / d) ** 2 * 0.9


def impact(d=1.6):
    t = tvec(d)
    boom = osc_sin(30 + 70 * np.exp(-t / 0.06), d) * np.exp(-t / 0.45)
    crack = hp(noise(d), 1500) * np.exp(-t / 0.03)
    body = lp(noise(d), 300) * np.exp(-t / 0.12) * 0.8
    return np.tanh((boom * 1.2 + crack * 0.6 + body) * 1.3)


def riser(d):
    t = tvec(d)
    p = t / d
    n = sweep_filter(noise(d), 300, 9000, q=0.25)
    tone = osc_saw(110 * 2 ** (p * 3), d) * 0.25
    return lp(tone, 4000) * p ** 2 + n * p ** 2.5 * 0.9


def sfx_for(kind, i):
    t = None
    if kind == "heartbeat":
        return heartbeat()
    if kind.startswith("riser@"):
        return riser(float(kind[6:]))
    if kind.startswith("revcrash@"):
        d = float(kind[9:])
        return (hp(noise(d), 3000) * (tvec(d) / d) ** 3)
    if kind in ("impact", "drop", "final_hit"):
        s = impact(2.2 if kind != "impact" else 1.6)
        if kind != "impact":
            c = crash(3.0)
            s = np.pad(s, (0, max(0, len(c) - len(s)))) + c[: max(len(s), len(c))] * 0.8
        return s
    if kind == "hit":
        return np.tanh(kick(1.2) * 1.2 + np.pad(hp(noise(0.12), 2000) * np.exp(-tvec(0.12) / 0.02), (0, int(0.3 * SR))) * 0.5)
    if kind == "hit_low":
        return impact(1.0) * 0.8
    if kind == "shutter":  # eyelid blink: two soft clicks over a falling whoosh
        out = whoosh(0.3, 2500, 400) * 0.5
        clk = hp(noise(0.02), 2500) * np.exp(-tvec(0.02) / 0.004)
        for off, g in ((0.0, 1.0), (0.08, 0.7)):
            s0 = int(off * SR)
            out[s0:s0 + len(clk)] += clk * g
        return out
    if kind == "whoosh":
        return whoosh(0.5, 250, 5000)
    if kind == "tick":
        return osc_sin(2400, 0.03) * np.exp(-tvec(0.03) / 0.005)
    if kind == "swipe":
        return sweep_filter(noise(0.28), 1500, 6000) * np.sin(np.pi * tvec(0.28) / 0.28) * 0.8
    if kind == "glitch":
        d = 0.24
        s = np.sign(osc_sin(rng.uniform(80, 300), d)) * 0.4 + noise(d) * 0.5
        s = np.repeat(s[::24], 24)[: int(d * SR)]  # sample-rate crush
        gate = np.repeat(rng.random(int(d * 60) + 2) > 0.35, int(SR / 60) + 1)[: len(s)]
        return lp(s * gate, 6000) * 0.7
    if kind == "stab":
        ch = [50, 53, 57, 62]
        s = pad_chord(ch, 0.35, bright=3000, a=0.003) * env(0.35, 0.003, 0.12, 0.2, 0.1)
        return s * 1.4
    if kind == "power_down":
        d = 0.7
        tt = tvec(d)
        f = 420 * np.exp(-tt / 0.18) + 25
        zap = hp(noise(0.08), 3000) * np.exp(-tvec(0.08) / 0.02)
        s = lp(osc_saw(f, d), 1800) * np.exp(-tt / 0.3) * 0.6
        s[: len(zap)] += zap * 0.5
        return s
    if kind == "switch_click":
        d = 0.35
        tt = tvec(d)
        snap = hp(noise(d), 1800) * np.exp(-tt / 0.005)
        ping = osc_sin(3100, d) * np.exp(-tt / 0.03) * 0.3
        body = osc_sin(140, d) * np.exp(-tt / 0.04) * 0.6
        s = snap + ping + body
        s2 = np.pad(s * 0.45, (int(0.045 * SR), 0))[: len(s)]
        return (s + s2) * 1.1
    if kind == "glow_swell":
        d = 0.75
        s = pad_chord([62, 66, 69, 74], d, bright=6000, a=0.6) * (tvec(d) / d) ** 1.5
        return s * 0.8
    if kind == "sparkle":
        out = np.zeros(int(1.2 * SR))
        notes = [86, 88, 90, 93, 95, 98]
        for k in range(7):
            b = bell(notes[(k * 3 + i) % len(notes)], 0.6) * (0.6 ** (k * 0.4))
            s = int(k * 0.055 * SR)
            out[s:s + len(b)] += b[: len(out) - s]
        return out * 0.35
    if kind == "digital":
        out = np.zeros(int(0.6 * SR))
        for k in range(8):
            d = 0.04
            f = mtof(int(rng.choice([74, 79, 81, 86, 88, 93])))
            b = np.sign(osc_sin(f, d)) * np.exp(-tvec(d) / 0.015) * 0.25
            s = int(k * 0.06 * SR)
            out[s:s + len(b)] += b
        return lp(out, 7000)
    if kind == "fly_in":
        out = np.zeros(int(0.8 * SR))
        for k, f0 in enumerate((350, 300, 250)):
            w = whoosh(0.55, f0, 6000)
            s = int(k * 0.04 * SR)
            out[s:s + len(w)] += w
        return out
    if kind == "pop":
        d = 0.09
        f = 380 * 2 ** (((i % 10) / 10) * 1.2) + 500 * tvec(d) / d
        return osc_sin(f, d) * np.exp(-tvec(d) / 0.025)
    if kind == "shimmer":
        out = np.zeros(int(1.4 * SR))
        for k, m in enumerate([86, 90, 93, 98, 102, 105, 110]):
            b = bell(m, 0.7)
            s = int(k * 0.07 * SR)
            out[s:s + len(b)] += b[: len(out) - s] * 0.6
        return out * 0.3 + np.pad(sweep_filter(noise(0.8), 3000, 12000, q=0.2) * np.sin(np.pi * tvec(0.8) / 0.8) * 0.3,
                                  (0, int(0.6 * SR)))
    if kind == "camera":
        clk = hp(noise(0.015), 2000) * np.exp(-tvec(0.015) / 0.003)
        return np.concatenate([clk, np.zeros(int(0.07 * SR)), clk * 0.8])
    if kind == "count":
        out = np.zeros(int(0.8 * SR))
        times = 0.6 * (1 - (1 - np.linspace(0, 1, 12)) ** 2)  # accelerating ticks easing out
        for k, tk in enumerate(times):
            b = osc_sin(1800 + 60 * k, 0.02) * np.exp(-tvec(0.02) / 0.004) * 0.6
            s = int(tk * SR)
            out[s:s + len(b)] += b
        ding = bell(93, 0.4)
        s = int(0.6 * SR)
        out[s:s + len(ding)] += ding[: len(out) - s] * 0.5
        return out
    if kind == "pad_swell":
        d = 3.0
        return pad_chord([59, 62, 66, 71], d, bright=1800, a=1.5) * 0.6
    if kind == "notify":
        out = np.zeros(int(0.5 * SR))
        for k, m in enumerate((88, 93)):
            b = bell(m, 0.35)
            s = int(k * 0.11 * SR)
            out[s:s + len(b)] += b
        return out * 0.6
    raise ValueError(kind)


for i, (t, kind, g) in enumerate(CUES):
    s = sfx_for(kind, i)
    start = t - len(s) / SR if "@" in kind else t
    pan = {"fly_in": 0.0, "camera": 0.3 * (-1) ** i, "pop": -0.4 + 0.08 * (i % 10), "whoosh": 0.3 * (-1) ** i}.get(kind, 0.0)
    sfx.add(s, start, g, pan)
    if kind in ("impact", "drop", "final_hit", "switch_click", "sparkle", "shimmer", "stab", "notify", "heartbeat"):
        verb_send.add(s, start, g * 0.35, pan)

# ------------------------------------------------------------------ mix


def reverb(x, secs=2.4):
    t = tvec(secs)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(len(t)) * np.exp(-t / (secs / 5))
        ir = hp(ir, 250)
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return out


# Sidechain: music ducks under every kick of the drop
duck = np.ones(N)
for b in beats(DROP, 41.0):
    if not in_breaks(b):
        i = int(b * SR)
        k = 1 - 0.55 * np.exp(-tvec(0.4) / 0.09)
        duck[i:i + len(k)] = np.minimum(duck[i:i + len(k)], k[: N - i])
for b in beats(8.5, 10.5):
    i = int(b * SR)
    k = 1 - 0.4 * np.exp(-tvec(0.4) / 0.09)
    duck[i:i + len(k)] = np.minimum(duck[i:i + len(k)], k[: N - i])

mus = music.x * duck[:, None]
mix = mus * 0.9 + drums.x * 0.8 + sfx.x * 0.85 + reverb(verb_send.x + mus * 0.15) * 0.5
mix = hp(mix.T, 25).T

# Gentle bus glue + soft limiter, then normalise to -1 dBFS peak
mix /= np.percentile(np.abs(mix), 99.9) + 1e-9
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
fade = np.ones(N)
fade[-int(0.6 * SR):] = np.linspace(1, 0, int(0.6 * SR)) ** 2
mix *= fade[:, None]
mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))

out = os.path.join(HERE, "build", "soundtrack.wav")
pcm = (mix * 32767).astype("<i2")
import wave

with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("wrote", out)
