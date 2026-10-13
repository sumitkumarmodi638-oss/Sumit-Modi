"""Render the picture track of the Varnik Labs brand film.

Usage:
  python3 video.py                    # full render -> build/picture.mp4
  python3 video.py --stills 0.8 3.5   # preview frames -> build/stills/*.png
"""
import math
import os
import re
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from timeline import (BEAT, CLOUD, DURATION, FPS, H, INK, LAVENDER, LIME, MIDNIGHT,
                      MONTAGE, PURPLE, SCENES, W)

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
WHITE = (255, 255, 255)


def C(c):
    return np.array(c, np.float32) / 255.0


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, t0, dur):
    return clamp((t - t0) / dur)


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def ease_in_cubic(p):
    return p ** 3


def ease_in_out(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out_expo(p):
    return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)


def ease_out_back(p, s=1.9):
    p -= 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


def lerp(a, b, p):
    return a + (b - a) * p


# ---------------------------------------------------------------- photos
# Clean (text-free) regions of the brand-book photography: x, y, width (16:9)
CROPS = {
    0: (1300, 0, 1580), 1: (1250, 300, 1630), 2: (1300, 150, 1580), 4: (900, 0, 1955),
    5: (1200, 0, 1680), 7: (1300, 200, 1580), 8: (1100, 0, 1780), 9: (1150, 400, 1730),
    10: (1150, 250, 1700), 15: (880, 0, 2000), 16: (1250, 450, 1630), 17: (302, 0, 2276),
    30: (480, 0, 2400), 31: (516, 0, 2364), 32: (580, 0, 2300), 33: (580, 0, 2300),
    34: (580, 0, 2300), 36: (580, 0, 2300), 48: (570, 640, 1740), 49: (1400, 100, 1480),
}


@lru_cache(None)
def photo(n):
    return cv2.imread(os.path.join(BUILD, "img", f"b-{n:03d}.jpg"))[:, :, ::-1].copy()


def shot(n, z=1.0, focus=None, f=0.0, pan=(0.0, 0.0), out=(W, H)):
    """Camera on photo n: zoom z (>=1) inside its clean crop, drifting toward focus."""
    x, y, w = CROPS[n]
    h = w * 9 / 16
    img = photo(n)
    vw, vh = w / z, h / z
    cx, cy = x + w / 2, y + h / 2
    if focus is not None:
        cx, cy = lerp(cx, focus[0], f), lerp(cy, focus[1], f)
    cx += pan[0] * (w - vw) / 2
    cy += pan[1] * (h - vh) / 2
    cx = clamp(cx, vw / 2, img.shape[1] - vw / 2)
    cy = clamp(cy, vh / 2, img.shape[0] - vh / 2)
    s = out[0] / vw
    M = np.float32([[s, 0, -(cx - vw / 2) * s], [0, s, -(cy - vh / 2) * s]])
    o = cv2.warpAffine(img, M, out, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return o.astype(np.float32) / 255.0


def grade(f, sat=1.0, exp=1.0, tint=0.06):
    lum = f @ np.float32([0.299, 0.587, 0.114])
    f = lum[..., None] + (f - lum[..., None]) * sat
    f *= exp
    # lift shadows toward brand purple so every photo sits in one world
    f += C(PURPLE) * tint * (1 - lum[..., None]) ** 2
    return f


# ---------------------------------------------------------------- canvases
@lru_cache(None)
def radial(c_in, c_out, cx=0.5, cy=0.45, r=0.95):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx / W - cx) * 1.6) ** 2 + (yy / H - cy) ** 2) / r
    k = np.clip(d, 0, 1)[..., None] ** 1.3
    return C(c_in) * (1 - k) + C(c_out) * k


def bg(c_in, c_out=None, **kw):
    return radial(c_in, c_out or c_in, **kw).copy()


@lru_cache(None)
def grad(kind, reach=0.62, power=1.6):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = {"left": xx / W, "bottom": 1 - yy / H, "top": yy / H}[kind]
    return (np.clip(1 - v / reach, 0, 1) ** power)[..., None]


def scrim(f, kind, s=0.8, reach=0.62):
    g = grad(kind, reach) * s
    return f * (1 - g) + C(MIDNIGHT) * g


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return (1 - 0.32 * np.clip(d - 0.45, 0, 1) ** 1.4)[..., None]


@lru_cache(None)
def grain_bank():
    rng = np.random.default_rng(3)
    return [cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.7)[..., None]
            for _ in range(6)]


# ---------------------------------------------------------------- compositing
def blit(dst, src, x, y, alpha=1.0, mask=None):
    """Composite premultiplied RGBA src with its top-left at (x, y)."""
    h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * alpha
    d = dst[y0:y1, x0:x1]
    d *= 1 - a
    d[..., :3] += s[..., :3] * alpha
    if d.shape[2] == 4:  # compositing onto another RGBA layer
        d[..., 3:] += a
    if mask is not None:
        np.maximum(mask[y0:y1, x0:x1], a[..., 0], out=mask[y0:y1, x0:x1])


def blit_c(dst, src, cx, cy, scale=1.0, alpha=1.0, rot=0.0, mask=None):
    """Composite src centred on (cx, cy) with scale and rotation (degrees)."""
    if scale <= 0.01 or alpha <= 0:
        return
    h, w = src.shape[:2]
    if rot == 0 and abs(scale - 1) < 1e-3:
        blit(dst, src, cx - w / 2, cy - h / 2, alpha, mask)
        return
    r = math.radians(rot)
    nw = int(abs(w * math.cos(r)) * scale + abs(h * math.sin(r)) * scale) + 4
    nh = int(abs(w * math.sin(r)) * scale + abs(h * math.cos(r)) * scale) + 4
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -rot, scale)
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    out = cv2.warpAffine(src, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    blit(dst, out, cx - nw / 2, cy - nh / 2, alpha, mask)


def rgba_from_alpha(a, color):
    c = C(color)
    return np.dstack([a * c[0], a * c[1], a * c[2], a]).astype(np.float32)


def flash(f, color, a):
    if a > 0:
        f += (C(color) - f) * a
    return f


def zoom(f, z, cx=W / 2, cy=H / 2):
    if abs(z - 1) < 1e-4:
        return f
    M = np.float32([[z, 0, cx - cx * z], [0, z, cy - cy * z]])
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def zoom_blur(f, amount, n=6):
    if amount < 0.004:
        return f
    acc = f.copy()
    for k in range(1, n):
        acc += zoom(f, 1 + amount * k / (n - 1))
    return acc / n


def shake(f, amp, t, seed=0):
    if amp < 0.5:
        return f
    rng = np.random.default_rng(int(t * FPS) * 31 + seed)
    dx, dy = rng.uniform(-amp, amp, 2)
    z = 1 + 2.4 * amp / W
    M = np.float32([[z, 0, W / 2 - W / 2 * z + dx], [0, z, H / 2 - H / 2 * z + dy]])
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def glitch(f, t, strength, seed=0):
    """Datamosh-style slice displacement + RGB split."""
    if strength <= 0:
        return f
    rng = np.random.default_rng(int(t * FPS) * 7 + seed)
    out = f.copy()
    for _ in range(int(6 + 10 * strength)):
        y0 = rng.integers(0, H - 10)
        hh = int(rng.integers(6, 90))
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(rng.integers(-160, 160) * strength), axis=1)
    sh = int(18 * strength)
    out[..., 0] = np.roll(out[..., 0], sh, axis=1)
    out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    if rng.random() < 0.6 * strength:  # brand-coloured block
        x0, y0 = rng.integers(0, W - 300), rng.integers(0, H - 60)
        out[y0:y0 + int(rng.integers(8, 50)), x0:x0 + int(rng.integers(100, 600))] = C(
            LIME if rng.random() < 0.5 else PURPLE)
    return out


def eyelid(f, closed):
    """Close the frame like an eyelid (closed: 0 open -> 1 shut)."""
    if closed <= 0:
        return f
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    shape = np.sqrt(np.clip(1 - ((xx - W / 2) / (W * 0.62)) ** 2, 0, 1))
    half = (1 - closed) * H * 0.62 * shape
    d = np.abs(yy - H / 2) - half
    m = np.clip(d / 6 + 0.5, 0, 1)[..., None]
    return f * (1 - m)


def add_glow(f, mask, color, strength, sigma=28):
    small = cv2.resize(mask, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / 4)
    g = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return f + g * C(color) * strength


def light_sweep(f, mask, p, width=90, strength=0.85):
    if not 0 < p < 1:
        return f
    pos = lerp(-400, W + 400, ease_in_out(p))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    band = np.exp(-(((xx + (yy - H / 2) * 0.45) - pos) / width) ** 2)
    return f + (band * mask)[..., None] * strength


# ---------------------------------------------------------------- type
@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(os.path.join(BUILD, "fonts", name + ".ttf"), size)


@lru_cache(None)
def text_rgba(text, fname, size, color, tracking=0):
    f = font(fname, size)
    asc, desc = f.getmetrics()
    if tracking:
        width = sum(f.getlength(ch) for ch in text) + tracking * (len(text) - 1)
    else:
        width = f.getlength(text)
    pad = int(size * 0.12) + 2
    img = Image.new("L", (int(math.ceil(width)) + 2 * pad, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(img)
    if tracking:
        x = pad
        for ch in text:
            d.text((x, pad), ch, font=f, fill=255)
            x += f.getlength(ch) + tracking
    else:
        d.text((pad, pad), text, font=f, fill=255)
    a = np.asarray(img, np.float32) / 255.0
    return rgba_from_alpha(a, color), pad, width


class Text:
    """Laid-out headline; words wrapped in *stars* get the accent colour."""

    def __init__(self, lines, fname="Sora-800", size=100, color=WHITE, accent=LIME,
                 lh=1.06, align="left", tracking=0):
        self.size, self.words, self.width = size, [], 0
        space = font(fname, size).getlength(" ") + tracking
        y = 0
        for li, line in enumerate(lines):
            row, x = [], 0
            for word in line.split(" "):
                if not word:  # double space = extra gap
                    x += space
                    continue
                # "*word*" or "Blink*.*": starred segments take the accent colour
                for seg in [g for g in re.split(r"(\*[^*]+\*)", word) if g]:
                    acc = seg.startswith("*")
                    rgba, pad, ww = text_rgba(seg.strip("*"), fname, size, accent if acc else color, tracking)
                    row.append([x, y, rgba, pad, li, ww])
                    x += ww
                x += space
            lw = x - space
            self.width = max(self.width, lw)
            if align == "center":
                for r in row:
                    r[0] -= lw / 2
            elif align == "right":
                for r in row:
                    r[0] -= lw
            self.words += row
            y += size * lh
        self.height = y

    def draw(self, dst, ox, oy, t, t0=0.0, stagger=0.06, dur=0.4, style="rise",
             alpha=1.0, line_delay=None, mask=None):
        for i, (x, y, rgba, pad, li, ww) in enumerate(self.words):
            start = t0 + i * stagger + (line_delay[li] if line_delay else 0)
            p = prog(t, start, dur)
            if p <= 0:
                continue
            sc, dy, a = 1.0, 0.0, 1.0
            if style == "rise":
                dy, a = (1 - ease_out_expo(p)) * self.size * 0.55, min(1, p * 2.5)
            elif style == "pop":
                sc, a = 0.4 + 0.6 * ease_out_back(p), min(1, p * 3)
            elif style == "slam":
                sc, a = 1 + 1.4 * (1 - ease_out_expo(p)), min(1, p * 5)
            elif style == "fade":
                a = ease_out_cubic(p)
            h, w = rgba.shape[:2]
            blit_c(dst, rgba, ox + x - pad + w / 2, oy + y - pad + h / 2 + dy, sc, a * alpha, mask=mask)


def eyebrow(dst, text, x, y, t, t0, color=LIME, size=26, align="left", alpha=1.0):
    Text([text], "DMSans-700", size, color, color, tracking=5, align=align).draw(
        dst, x, y, t, t0, stagger=0, dur=0.5, style="fade", alpha=alpha)


def pill(w, h, fill, border=None, bw=3):
    s = 3  # supersample for smooth corners
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=h * s // 2, fill=fill,
                        outline=border, width=bw * s if border else 0)
    a = np.asarray(img.resize((w, h), Image.LANCZOS), np.float32) / 255.0
    rgb = a[..., :3] * a[..., 3:4]
    return np.dstack([rgb, a[..., 3:4]])


@lru_cache(None)
def chip(text, size=30, fill=(28, 24, 48, 235), border=LAVENDER, color=WHITE):
    rgba, pad, ww = text_rgba(text, "DMSans-700", size, color)
    w, h = int(ww + size * 1.6), int(size * 2.0)
    base = pill(w, h, fill, border + (255,) if border else None)
    blit(base, rgba, (w - rgba.shape[1]) / 2, (h - rgba.shape[0]) / 2 - size * 0.06)
    return base


# ---------------------------------------------------------------- logo
@lru_cache(None)
def logo_meta():
    import json
    m = json.load(open(os.path.join(BUILD, "logo", "logo.json")))
    pieces = [m["design"], m["tech"], m["growth"]] + m["letters"]
    xs = [p["x"] for p in pieces] + [p["x"] + p["w"] for p in pieces]
    ys = [p["y"] for p in pieces] + [p["y"] + p["h"] for p in pieces]
    m["center"] = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    mk = [m["design"], m["tech"], m["growth"]]
    m["mark_center"] = ((min(p["x"] for p in mk) + max(p["x"] + p["w"] for p in mk)) / 2,
                        (min(p["y"] for p in mk) + max(p["y"] + p["h"] for p in mk)) / 2)
    m["width"] = max(xs) - min(xs)
    return m


@lru_cache(None)
def piece_alpha(name):
    return cv2.imread(os.path.join(BUILD, "logo", name + ".png"), 0).astype(np.float32) / 255.0


@lru_cache(maxsize=512)
def piece_rgba(name, scale, color):
    a = piece_alpha(name)
    a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return rgba_from_alpha(a, color)


def draw_piece(dst, p, anchor, ref, scale, color, alpha=1.0, rot=0.0, off=(0, 0), extra=1.0, mask=None):
    """Draw logo piece p; `ref` (logo-space) maps to screen `anchor` at `scale`."""
    pcx, pcy = p["x"] + p["w"] / 2, p["y"] + p["h"] / 2
    sx = anchor[0] + (pcx - ref[0]) * scale + off[0]
    sy = anchor[1] + (pcy - ref[1]) * scale + off[1]
    q = round(scale * extra, 3)
    blit_c(dst, piece_rgba(p["name"], q, color), sx, sy, 1.0, alpha, rot, mask)


def draw_logo(dst, cx, cy, width, mark_color=LIME, word_color=LIME, alpha=1.0, mask=None):
    m = logo_meta()
    s = width / m["width"]
    for p in (m["design"], m["tech"], m["growth"]):
        draw_piece(dst, p, (cx, cy), m["center"], s, mark_color, alpha, mask=mask)
    for p in m["letters"]:
        draw_piece(dst, p, (cx, cy), m["center"], s, word_color, alpha, mask=mask)


@lru_cache(None)
def weave_alpha():
    """The 'Varna weave': the mark on a staggered lattice (brand pattern)."""
    m = logo_meta()
    tile = np.zeros((logo_meta()["H"], 1000), np.float32)
    for p in (m["design"], m["tech"], m["growth"]):
        a = piece_alpha(p["name"])
        tile[p["y"]:p["y"] + a.shape[0], p["x"]:p["x"] + a.shape[1]] = np.maximum(
            tile[p["y"]:p["y"] + a.shape[0], p["x"]:p["x"] + a.shape[1]], a)
    tile = tile[50:820, 60:970]
    tile = cv2.resize(tile, (66, 56), interpolation=cv2.INTER_AREA)
    sx, sy = 170, 130
    big = np.zeros((H + 2 * sy, W + 2 * sx), np.float32)
    for j, y in enumerate(range(0, big.shape[0] - 56, sy)):
        for x in range((sx // 2) * (j % 2), big.shape[1] - 66, sx):
            big[y:y + 56, x:x + 66] = tile
    return big


def weave(f, t, color, a, speed=18):
    w = weave_alpha()
    ox = int(t * speed) % 340
    oy = int(t * speed * 0.6) % 260
    m = w[oy:oy + H, ox:ox + W][..., None] * a
    return f * (1 - m) + C(color) * m


# ---------------------------------------------------------------- scenes
def sc_hook_blink(t, lt):
    if lt < 0.5:
        f = bg(MIDNIGHT, (0, 0, 0))
        # heartbeat: a lime ember pulses twice in the dark
        for t0 in (0.0, 0.26):
            p = prog(lt, t0, 0.22)
            if 0 < p < 1:
                r = 6 + 30 * ease_out_cubic(p)
                ov = np.zeros((H, W), np.float32)
                cv2.circle(ov, (W // 2, H // 2), int(r), 1.0, -1, cv2.LINE_AA)
                f = add_glow(f, ov, LIME, 1.6 * (1 - p), 18)
        return f
    p = lt - 0.5
    z = 1.0 + 0.32 * (1 - ease_out_expo(prog(p, 0, 0.45))) + 0.05 * p
    f = grade(shot(1, z, focus=(2250, 760), f=0.3), sat=1.05)
    f = scrim(f, "left", 0.85, 0.55)
    Text(["Blink*.*"], size=230).draw(f, 140, 360, lt, 0.62, dur=0.22, style="slam")
    Text(["That's all the time you get"], "DMSans-500", 46, CLOUD).draw(f, 150, 640, lt, 0.95, 0.03)
    f = flash(f, WHITE, 0.8 * (1 - prog(lt, 0.5, 0.18)))
    f = shake(f, 22 * (1 - prog(lt, 0.78, 0.25)) * (lt > 0.78), lt, 1)
    # the eye opens at 0.5 and blinks shut at the end of the scene
    closed = 1 - ease_out_cubic(prog(lt, 0.5, 0.2)) if lt < 1.0 else ease_in_cubic(prog(lt, 1.55, 0.2))
    return eyelid(f, closed)


def sc_noticed(t, lt):
    z = 1.25 + 0.04 * lt
    f = cv2.GaussianBlur(shot(1, z, focus=(2250, 760), f=0.5), (0, 0), 18) * 0.35
    f = f * 0.6 + bg(PURPLE, MIDNIGHT, r=1.1) * 0.4 * 0.5
    txt = Text(["That's all the time", "you get to be *noticed.*"], size=104, align="center")
    words_t0 = 0.05
    # highlighter swipe behind "noticed."
    x, y, rgba, pad, li, ww = txt.words[-1]
    ox, oy = W / 2, H / 2 - txt.height / 2
    sp = ease_out_expo(prog(lt, 1.3, 0.3))
    if sp > 0:
        x0, y0 = int(ox + x - 18), int(oy + y + 8)
        x1 = int(x0 + (ww + 36) * sp)
        f[y0:y0 + int(txt.size * 1.08), x0:x1] = C(LIME)
        txt.words[-1][2] = text_rgba("noticed.", "Sora-800", 104, INK)[0] if sp > 0.5 else rgba
    txt.draw(f, ox, oy, lt, words_t0, stagger=0.16, dur=0.3, style="pop")
    f = zoom(f, 1 + 0.025 * (1 - ease_out_expo(prog(lt, 1.3, 0.3))) if lt > 1.3 else 1)
    return eyelid(f, 1 - ease_out_cubic(prog(lt, 0, 0.18)))


def problem_shot(n, lt, z0, z1, focus=None, sat=0.55, exp=0.8, punch=0.12, glitchy=False):
    z = lerp(z0, z1, lt / 1.5) + punch * (1 - ease_out_expo(prog(lt, 0, 0.35)))
    f = grade(shot(n, z, focus=focus, f=0.2), sat=sat, exp=exp)
    return f


def sc_great_product(t, lt):
    f = problem_shot(2, lt, 1.0, 1.12, focus=(2300, 700))
    f = scrim(f, "left", 0.9, 0.62)
    eyebrow(f, "CHAPTER 1  ·  LIGHTS OFF", 140, 330, lt, 0.0)
    Text(["Great product."], size=118).draw(f, 140, 390, lt, 0.05, 0.07)
    Text(["Nobody *knows.*"], size=118).draw(f, 140, 520, lt, 0.75, 0.0, 0.25, "slam")
    f = shake(f, 14 * (1 - prog(lt, 0.8, 0.25)) * (lt > 0.8), t, 2)
    return f


def sc_sign_1998(t, lt):
    f = problem_shot(4, lt, 1.0, 1.1, focus=(1900, 500), sat=0.7, exp=0.85)
    f = scrim(f, "bottom", 0.92, 0.6)
    Text(["Your sign says *1998.*"], size=118).draw(f, 140, 690, lt, 0.05, 0.07)
    Text(["Your customers live in 2026."], "DMSans-500", 52, CLOUD).draw(f, 146, 840, lt, 0.75, 0.05)
    f = glitch(f, t, 1 - prog(lt, 0, 0.2), 4)
    if 0.75 <= lt < 0.85:
        f = glitch(f, t, 0.5, 5)
    return f


def sc_five_agencies(t, lt):
    f = problem_shot(5, lt, 1.0, 1.12, focus=(2300, 450))
    f = scrim(f, "left", 0.9, 0.6)
    Text(["Five agencies."], size=118).draw(f, 140, 390, lt, 0.05, 0.07)
    Text(["Zero *clarity.*"], size=118).draw(f, 140, 520, lt, 0.75, 0.0, 0.25, "slam")
    chips = [("Designer", 1180, 220), ("Developer", 1480, 360), ("Marketer", 1150, 760), ("Printer", 1530, 860)]
    for i, (label, x, y) in enumerate(chips):
        p = prog(lt, 0.12 + i * 0.12, 0.3)
        fall = ease_in_cubic(prog(lt, 0.78, 0.6))
        blit_c(f, chip(label), x + (i - 1.5) * 60 * fall, y + 700 * fall,
               0.4 + 0.6 * ease_out_back(p) if p < 1 else 1, min(1, p * 3) * (1 - fall), rot=(i - 1.5) * 25 * fall)
    f = glitch(f, t, 1 - prog(lt, 0, 0.2), 6)
    f = shake(f, 14 * (1 - prog(lt, 0.8, 0.25)) * (lt > 0.8), t, 3)
    return f


STROBE = [
    (MIDNIGHT, ["Nobody *finds* you."], WHITE, LIME, "PROBLEM 01"),
    (PURPLE, ["Visits. No *enquiries.*"], WHITE, LIME, "PROBLEM 03"),
    (MIDNIGHT, ["Leads go *cold.*"], WHITE, LIME, "PROBLEM 04"),
    (LIME, ["Nobody stops *scrolling.*"], INK, PURPLE, "PROBLEM 05"),
]


def sc_strobe(t, lt):
    i = min(int(lt / 0.5), 3)
    k = lt - i * 0.5
    col, lines, tc, ac, tag = STROBE[i]
    f = bg(col, tuple(int(c * 0.7) for c in col))
    if col != LIME:
        f = weave(f, t, LAVENDER, 0.05)
    eyebrow(f, tag, W / 2, 380, k, 0.0, color=ac if col != LIME else PURPLE, align="center")
    Text(lines, size=124, color=tc, accent=ac, align="center").draw(f, W / 2, 450, k, 0.0, 0.0, 0.14, "slam")
    f = zoom_blur(f, 0.12 * (1 - ease_out_expo(prog(k, 0, 0.15))))
    if k < 0.07:
        f = glitch(f, t, 0.8, 9 + i)
    return shake(f, 16 * (1 - prog(k, 0.05, 0.25)), t, 4 + i)


def sc_sound_familiar(t, lt):
    f = np.zeros((H, W, 3), np.float32)
    p = prog(lt, 0, 0.28)
    if p < 1:  # CRT power-off of the last card
        last = sc_strobe(t, 1.99)
        sy = max(1 - ease_in_cubic(min(1, p * 1.6)), 0.004)
        sx = 1 - ease_in_cubic(clamp((p - 0.55) / 0.45))
        if sx > 0.002:
            hh, ww = max(2, int(H * sy)), max(2, int(W * sx))
            small = cv2.resize(last, (ww, hh), interpolation=cv2.INTER_AREA)
            small = small + (1 - small) * (1 - sy) * 0.8
            blit(f, np.dstack([small, np.ones((hh, ww, 1), np.float32)]), (W - ww) / 2, (H - hh) / 2)
        return f
    # failing-neon flicker
    a = ease_out_cubic(prog(lt, 0.35, 0.3)) * (1 - prog(lt, 1.2, 0.25))
    rng = np.random.default_rng(int(t * FPS))
    if 0.35 < lt < 0.7 or 1.05 < lt < 1.3:
        a *= 0.3 + 0.7 * (rng.random() > 0.35)
    Text(["Sound familiar?"], "Sora-600", 76, CLOUD, align="center").draw(f, W / 2, H / 2 - 50, lt, 0.35, 0, 0.3, "fade",
                                                                         alpha=a)
    return f


SWITCH = (1830, 500)


def sc_switch(t, lt):
    z = 1.0 + 0.55 * ease_in_out(prog(lt, 0, 1.5))
    f = grade(shot(49, z, focus=SWITCH, f=ease_in_out(prog(lt, 0, 1.2))), sat=1.0)
    glow = ease_in_cubic(prog(lt, 0.6, 0.9))
    f *= 0.45 + 0.9 * glow
    # lime glow blooming out of the switch
    ov = np.zeros((H, W), np.float32)
    cv2.circle(ov, (W // 2 - 60, H // 2 + 20), int(80 + 500 * glow), 1.0, -1, cv2.LINE_AA)
    f = add_glow(f, ov, LIME, 1.1 * glow, 90)
    f = shake(f, 10 * (1 - prog(lt, 0, 0.18)), t, 7)
    return flash(f, WHITE, ease_in_cubic(prog(lt, 1.2, 0.3)))


def sc_one_team(t, lt):
    hits = [0.0, 1.0, 1.5, 2.0]
    since = min(lt - h for h in hits if lt >= h)
    f = bg(PURPLE, (58, 18, 140), r=1.0)
    f = weave(f, t, LAVENDER, 0.08)
    Text(["One team."], size=190, align="center").draw(f, W / 2, 300, lt, 0.0, 0.0, 0.22, "slam")
    row = Text(["Design.  Tech.  *Growth.*"], "Sora-700", 104, align="center")
    for j, wd in enumerate(row.words):
        x, y, rgba, pad, li, ww = wd
        p = prog(lt, hits[j + 1], 0.2)
        if p > 0:
            h_, w_ = rgba.shape[:2]
            blit_c(f, rgba, W / 2 + x - pad + w_ / 2, 600 - pad + h_ / 2, 1 + 1.3 * (1 - ease_out_expo(p)), min(1, p * 5))
    f = zoom(f, 1 + 0.04 * (1 - ease_out_expo(prog(since, 0, 0.3))))
    f = flash(f, WHITE, 1 - ease_out_cubic(prog(lt, 0, 0.35)))
    return shake(f, 18 * (1 - prog(since, 0, 0.25)), t, 8)


SPARKS = {
    "spark_design": (7, (2150, 900), "SPARK 01  ·  DESIGN", ["Make people", "look *twice.*"]),
    "spark_tech": (8, (1900, 450), "SPARK 02  ·  TECH", ["Make it work", "while you *sleep.*"]),
    "spark_growth": (9, (2250, 900), "SPARK 03  ·  GROWTH", ["Make the", "phone *ring.*"]),
}


def sc_spark(name):
    n, focus, tag, lines = SPARKS[name]

    def scene(t, lt):
        z = 1.0 + 0.12 * lt / 1.5 + 0.25 * (1 - ease_out_expo(prog(lt, 0, 0.4)))
        f = grade(shot(n, z, focus=focus, f=0.25), sat=1.1, exp=1.05)
        f = scrim(f, "left", 0.85, 0.6)
        eyebrow(f, tag, 140, 380, lt, 0.05)
        Text(lines, size=112).draw(f, 140, 440, lt, 0.1, 0.06)
        f = zoom_blur(f, 0.22 * (1 - ease_out_expo(prog(lt, 0, 0.25))))
        return f

    return scene


def sc_three_sparks(t, lt):
    z = 1.0 + 0.2 * ease_in_cubic(lt / 1.5)
    f = grade(shot(10, z, focus=(2050, 800), f=0.5), sat=1.1)
    f = scrim(f, "left", 0.8, 0.55)
    eyebrow(f, "NOW, SWITCH THEM ON TOGETHER", 140, 400, lt, 0.05)
    Text(["Three sparks.", "One *shape.*"], size=112).draw(f, 140, 460, lt, 0.1, 0.1)
    p = prog(lt, 1.1, 0.4)
    f = zoom_blur(f, 0.35 * ease_in_cubic(p) + 0.18 * (1 - ease_out_expo(prog(lt, 0, 0.25))))
    return f * (1 - ease_in_cubic(p))


# logo choreography (brand motion page: fly in, snap, say the name, shine)
FLY = {"design": ((-950, -650), -160), "tech": ((1050, -380), 170), "growth": ((80, 720), -110)}
SPARK_RNG = np.random.default_rng(11)
SPARK_P = [(SPARK_RNG.uniform(0, 2 * math.pi), SPARK_RNG.uniform(450, 1700), SPARK_RNG.uniform(0.35, 0.95),
            SPARK_RNG.integers(2, 5), SPARK_RNG.random() < 0.6) for _ in range(80)]


def logo_reveal_frame(lt, t):
    m = logo_meta()
    snap = 0.6
    s_lock = 1150 / m["width"]
    lock_c = (W / 2, H / 2 - 40)
    mark_lock = (lock_c[0] + (m["mark_center"][0] - m["center"][0]) * s_lock, lock_c[1])
    ps = ease_in_out(prog(lt, 0.9, 0.45))
    s_mark = lerp(0.6, s_lock, ps)
    mc = (lerp(W / 2, mark_lock[0], ps), lerp(H / 2 - 40, mark_lock[1], ps))

    on = ease_out_cubic(prog(lt, snap, 0.3))
    f = bg(MIDNIGHT, (6, 3, 14)) * (1 - on) + bg(PURPLE, (48, 14, 120), r=1.0) * on
    f = weave(f, t, LAVENDER, 0.07 * on)

    mask = np.zeros((H, W), np.float32)
    pf = prog(lt, 0, snap)
    for name in ("design", "tech", "growth"):
        p = m[name]
        (ox, oy), rot = FLY[name]
        for g in (3, 2, 1, 0):  # motion trail ghosts
            q = ease_in_cubic(clamp(pf - g * 0.05)) if pf < 1 else 1
            if g and (pf >= 1 or pf <= g * 0.05):
                continue
            e = 1 - q
            draw_piece(f, p, mc, m["mark_center"], s_mark, LIME, alpha=1.0 if g == 0 else 0.22 / g,
                       rot=rot * e, off=(ox * e, oy * e), extra=1 + 0.6 * e, mask=mask if g == 0 else None)
    # letters pop in once the mark slides aside
    for i, p in enumerate(m["letters"]):
        q = prog(lt, 1.0 + i * 0.05, 0.38)
        if q <= 0:
            continue
        e = ease_out_back(q, 2.4)
        draw_piece(f, p, lock_c, m["center"], s_lock, LIME, alpha=min(1, q * 3),
                   off=(0, (1 - e) * 70), extra=0.5 + 0.5 * e, mask=mask)

    f = add_glow(f, mask, LIME, 0.35 + 0.9 * (1 - prog(lt, snap, 0.6)) * (lt > snap * 0.6), 30)

    # snap: flash + shockwave + sparks
    k = lt - snap
    if k >= 0:
        ov = np.zeros((H, W, 3), np.float32)
        q = prog(k, 0, 0.55)
        if q < 1:
            r = int(40 + 1150 * ease_out_expo(q))
            cv2.circle(ov, (int(mc[0]), int(mc[1])), r, tuple(float(c) for c in C(LIME) * (1 - q)),
                       max(1, int(30 * (1 - q))), cv2.LINE_AA)
        for ang, sp, life, sz, lime in SPARK_P:
            if k > life:
                continue
            d0 = sp * (1 - math.exp(-3.2 * max(k - 0.035, 0))) / 3.2
            d1 = sp * (1 - math.exp(-3.2 * k)) / 3.2
            a = 1 - k / life
            col = C(LIME if lime else WHITE) * a
            p0 = (int(mc[0] + math.cos(ang) * (d0 + 60)), int(mc[1] + math.sin(ang) * (d0 + 60) + 300 * k * k))
            p1 = (int(mc[0] + math.cos(ang) * (d1 + 60)), int(mc[1] + math.sin(ang) * (d1 + 60) + 300 * k * k))
            cv2.line(ov, p0, p1, tuple(float(c) for c in col), int(sz), cv2.LINE_AA)
        small = cv2.GaussianBlur(cv2.resize(ov, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 3)
        f += ov + cv2.resize(small, (W, H)) * 1.5
        f = flash(f, (240, 255, 210), 0.9 * (1 - ease_out_cubic(prog(k, 0, 0.3))))
        f = shake(f, 26 * (1 - prog(k, 0, 0.3)), t, 12)

    Text(["DESIGN.  TECH.  GROWTH."], "DMSans-700", 34, WHITE, tracking=9, align="center").draw(
        f, W / 2, H / 2 + 150, lt, 2.4, 0.0, 0.6, "rise")
    f = light_sweep(f, mask, prog(lt, 2.0, 0.8))
    return f


def sc_logo_reveal(t, lt):
    return logo_reveal_frame(lt, t)


def corner_logo(f, alpha=1.0):
    draw_logo(f, 140 + 125, 92, 250, LIME, WHITE, alpha)
    return f


def sc_lights(t, lt):
    i = min(int(lt / BEAT), len(MONTAGE) - 1)
    k = lt - i * BEAT
    n = MONTAGE[i]
    z = 1.04 + 0.04 * k / BEAT + 0.14 * (1 - ease_out_expo(prog(k, 0, 0.3)))
    f = grade(shot(n, z, pan=((-1) ** i * 0.3 * k / BEAT, 0)), sat=1.12, exp=1.05, tint=0.03)
    f = scrim(f, "bottom", 0.95, 0.62)
    f = scrim(f, "top", 0.55, 0.25)
    if i in (0, 4):
        f = flash(f, WHITE, 0.6 * (1 - prog(k, 0, 0.12)))
    corner_logo(f)
    eyebrow(f, "CHAPTER 3  ·  LIGHTS EVERYWHERE", 140, 700, lt, 0.0)
    Text(["Same shop."], size=96).draw(f, 140, 750, lt, 0.05, 0.06)
    Text(["Now *impossible* to ignore."], size=96).draw(f, 140, 860, lt, 1.0, 0.07)
    return f


STATS = [("20+", 20, "+", "brands switched on"), ("4", 4, "", "countries"),
         ("16", 16, "", "services, one roof"), ("1,200+", 1200, "+", "patient enquiries in 60 days")]


def sc_proof(t, lt):
    f = bg(INK, MIDNIGHT, r=1.0)
    f = weave(f, t, PURPLE, 0.25)
    corner_logo(f)
    eyebrow(f, "THE LIGHTS ARE ON", W / 2, 250, lt, 0.0, align="center")
    Text(["Proof, not *promises.*"], size=84, align="center").draw(f, W / 2, 300, lt, 0.05, 0.06)
    cols = [330, 730, 1100, 1560]
    for i, (_, val, suf, label) in enumerate(STATS):
        t0 = i * 0.5
        p = prog(lt, t0, 0.7)
        if p <= 0:
            continue
        v = int(round(val * ease_out_expo(p)))
        s = f"{v:,}{suf}"
        cx = cols[i]
        pop = prog(lt, t0, 0.3)
        rgba = text_rgba(s, "Sora-800", 136, LIME)[0]
        blit_c(f, rgba, cx, 590, 0.5 + 0.5 * ease_out_back(pop), min(1, pop * 3))
        Text([label], "DMSans-500", 34, CLOUD, align="center").draw(f, cx, 680, lt, t0 + 0.15, 0, 0.4, "rise")
        if i:
            x = int((cols[i - 1] + cols[i]) / 2) + (40 if i == 3 else 0)
            f[520:720, x:x + 2] = f[520:720, x:x + 2] * 0.6 + C(LAVENDER) * 0.4 * min(1, pop * 2)
    Text(["Healthcare · Travel · Food · Finance · Industry  —  India · UK · UAE · USA"], "DMSans-500", 30,
         LAVENDER, align="center").draw(f, W / 2, 830, lt, 2.2, 0, 0.6, "fade")
    return zoom_blur(f, 0.15 * (1 - ease_out_expo(prog(lt, 0, 0.25))))


def sc_city(t, lt):
    z = 1.0 + 0.14 * lt / 3
    f = grade(shot(48, z, pan=(0, 0.6)), sat=1.15, exp=0.95 + 0.15 * lt / 3, tint=0.03)
    f = scrim(f, "top", 0.85, 0.55)
    Text(["One shop lit up the street."], "Sora-700", 72, CLOUD, align="center").draw(f, W / 2, 200, lt, 0.1, 0.06)
    Text(["Imagine the *whole city.*"], size=120, align="center").draw(f, W / 2, 300, lt, 1.5, 0.1, 0.5)
    return flash(f, PURPLE, 0.5 * (1 - prog(lt, 0, 0.3)))


@lru_cache(None)
def panel_mask(w, h, r):
    img = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], radius=r * 2, fill=255)
    return np.asarray(img.resize((w, h), Image.LANCZOS), np.float32)[..., None] / 255.0


@lru_cache(None)
def button():
    rgba, pad, ww = text_rgba("Book a free 15-minute audit  →", "DMSans-700", 40, INK)
    w, h = int(ww + 100), 96
    b = pill(w, h, LIME + (255,))
    blit(b, rgba, (w - rgba.shape[1]) / 2, (h - rgba.shape[0]) / 2 - 3)
    return b


def sc_cta(t, lt):
    f = bg(PURPLE, (52, 16, 128), cx=0.3, r=1.1)
    f = weave(f, t, LAVENDER, 0.07)
    # photo panel: the switch, glowing
    pw, ph = 700, 820
    sl = ease_out_expo(prog(lt, 0.0, 0.6))
    px, py = int(lerp(W + 40, W - 140 - pw, sl)), 130
    panel = grade(shot(49, 1.25 + 0.08 * lt / 4, focus=(SWITCH[0] + 120, SWITCH[1] + 150), f=1.0, out=(ph * 16 // 9, ph)), sat=1.1, exp=1.15)
    panel = panel[:, (panel.shape[1] - pw) // 2:(panel.shape[1] - pw) // 2 + pw]
    m = panel_mask(pw, ph, 36)
    pm = np.zeros((H, W), np.float32)
    blit(f, np.dstack([panel * m, m]), px, py, mask=pm)
    f = add_glow(f, pm, LIME, 0.25 * sl, 40)
    eyebrow(f, "THE SWITCH IS RIGHT HERE", 140, 250, lt, 0.1)
    Text(["Your *turn.*"], size=180).draw(f, 140, 300, lt, 0.0, 0.12, 0.25, "slam")
    Text(["One conversation is all it takes."], "DMSans-500", 44, CLOUD).draw(f, 146, 520, lt, 0.5, 0.04)
    bp = prog(lt, 1.0, 0.35)
    if bp > 0:
        b = button()
        pulse = 1 + 0.03 * math.sin(max(0, lt - 1.4) * 2 * math.pi / BEAT) * (lt > 1.4)
        blit_c(f, b, 140 + b.shape[1] / 2, 660, (0.5 + 0.5 * ease_out_back(bp)) * pulse, min(1, bp * 3))
        rp = ((lt - 1.4) % 1.0) if lt > 1.4 else -1
        if 0 <= rp < 1:
            ring = pill(int(b.shape[1] * (1 + 0.15 * rp)), int(b.shape[0] * (1 + 0.5 * rp)), (0, 0, 0, 0), LIME, 3)
            blit_c(f, ring, 140 + b.shape[1] / 2, 660, 1, 1 - rp)
    rows = [("WhatsApp", "+91 73659 77561"), ("Email", "support@varniklabs.com"), ("Web", "varniklabs.com")]
    for i, (k, v) in enumerate(rows):
        Text([k.upper()], "DMSans-700", 24, LIME, tracking=4).draw(f, 146, 780 + i * 62, lt, 1.5 + i * 0.12, 0, 0.4, "rise")
        Text([v], "DMSans-500", 38, WHITE).draw(f, 340, 772 + i * 62, lt, 1.55 + i * 0.12, 0, 0.4, "rise")
    f = zoom(f, 1 + 0.05 * (1 - ease_out_expo(prog(lt, 0, 0.3))))
    return shake(f, 16 * (1 - prog(lt, 0.05, 0.25)), t, 14)


def sc_endcard(t, lt):
    f = bg(PURPLE, (48, 14, 120), r=1.0)
    f = weave(f, t, LAVENDER, 0.06)
    mask = np.zeros((H, W), np.float32)
    sc = 1 + 0.12 * (1 - ease_out_expo(prog(lt, 0, 0.6)))
    draw_logo(f, W / 2, H / 2 - 50, 1100 * sc, mask=mask)
    f = add_glow(f, mask, LIME, 0.35, 30)
    Text(["DESIGN.  TECH.  GROWTH."], "DMSans-700", 36, WHITE, tracking=10, align="center").draw(
        f, W / 2, H / 2 + 140, lt, 0.4, 0, 0.6, "rise")
    Text(["varniklabs.com   ·   +91 73659 77561"], "DMSans-500", 30, LAVENDER, align="center").draw(
        f, W / 2, H - 170, lt, 0.8, 0, 0.6, "fade")
    f = light_sweep(f, mask, prog(lt, 1.0, 0.9))
    f = flash(f, WHITE, 0.85 * (1 - ease_out_cubic(prog(lt, 0, 0.35))))
    return f * (1 - ease_in_cubic(prog(lt, 3.3, 0.7)))


SCENE_FN = {
    "hook_blink": sc_hook_blink, "noticed": sc_noticed, "great_product": sc_great_product,
    "sign_1998": sc_sign_1998, "five_agencies": sc_five_agencies, "strobe_problems": sc_strobe,
    "sound_familiar": sc_sound_familiar, "switch": sc_switch, "one_team": sc_one_team,
    "spark_design": sc_spark("spark_design"), "spark_tech": sc_spark("spark_tech"),
    "spark_growth": sc_spark("spark_growth"), "three_sparks": sc_three_sparks,
    "logo_reveal": sc_logo_reveal, "lights_everywhere": sc_lights, "proof": sc_proof,
    "whole_city": sc_city, "cta": sc_cta, "endcard": sc_endcard,
}


def render(i):
    t = i / FPS
    for s, e, name in SCENES:
        if s <= t < e:
            f = SCENE_FN[name](t, t - s)
            break
    else:
        f = np.zeros((H, W, 3), np.float32)
    f = f * vignette() + grain_bank()[i % 6] * 0.022
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


def warm():
    for n in CROPS:
        photo(n)
    vignette(), grain_bank(), weave_alpha(), logo_meta()
    for v in ((MIDNIGHT, (0, 0, 0)), (MIDNIGHT, (6, 3, 14)), (PURPLE, (48, 14, 120))):
        radial(*v)


if __name__ == "__main__":
    warm()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
        for ts in sys.argv[2:]:
            img = render(int(round(float(ts) * FPS)))
            cv2.imwrite(os.path.join(BUILD, "stills", f"{float(ts):05.2f}.png"), img[:, :, ::-1])
        sys.exit()
    from multiprocessing import Pool
    n = int(DURATION * FPS)
    out = os.path.join(BUILD, "picture.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, frame in enumerate(pool.imap(render, range(n), chunksize=4)):
            ff.stdin.write(frame.tobytes())
            if k % 150 == 0:
                print(f"frame {k}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)
