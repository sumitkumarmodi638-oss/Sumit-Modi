"""Frame-accurate motion-graphics renderer for the Sunflour promo.

Every frame is a pure function of time, so frames render in parallel and
any frame can be previewed on its own:

    python3 render.py --format vertical --out out/frames.mp4
    python3 render.py --format vertical --still 4.6 --out out/still.png
    python3 render.py --format vertical --sheet out/sheet.png
"""
import argparse
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")

W = H = S = 0
PORTRAIT = True
STATIC = {}


def setup(fmt):
    global W, H, S, PORTRAIT
    W, H = C.FORMATS[fmt]
    S = min(W, H)
    PORTRAIT = H > W
    STATIC.clear()
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    STATIC["lowgrid"] = (xx, yy)
    # vignette
    nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    v = 1 - 0.32 * np.clip(nx ** 2 * 0.8 + ny ** 2 * 0.8, 0, 1.6) ** 1.4
    STATIC["vignette"] = np.asarray(
        Image.fromarray((v * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
        dtype=np.float32)[..., None] / 255
    g = np.random.default_rng(3)
    STATIC["grain"] = [g.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]


# ------------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def ease_out(x, p=3):
    return 1 - (1 - x) ** p


def ease_in(x, p=3):
    return x ** p


def ease_in_out(x):
    return 3 * x * x - 2 * x * x * x if x < 1 else 1.0


def ease_out_expo(x):
    return 1 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_out_back(x, s=1.9):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def lerp(a, b, x):
    return a + (b - a) * x


def mix_rgb(a, b, x):
    return tuple(int(lerp(a[i], b[i], x)) for i in range(3))


def hit(t, at, decay=8.0):
    """Exponential envelope that fires at `at`."""
    return math.exp(-(t - at) * decay) if t >= at else 0.0


# ------------------------------------------------------------------ fonts
SERIF = "Fraunces.ttf"
SANS_BLACK = "InterDisplay-Black.otf"
SANS_BOLD = "InterDisplay-Bold.otf"
SANS_SEMI = "InterDisplay-SemiBold.otf"
SANS_MED = "InterDisplay-Medium.otf"
SANS_LIGHT = "InterDisplay-Light.otf"


@lru_cache(maxsize=256)
def font(name, size, wght=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), max(4, int(size)))
    if name == SERIF:
        f.set_variation_by_axes([min(144, max(9, size / 4)), wght or 600, 100, 1])
    return f


@lru_cache(maxsize=512)
def text_img(text, name, size, color, tracking=0.0, wght=None, alpha=255):
    """Tight RGBA render of a string; tracking is in em."""
    f = font(name, size, wght)
    asc, desc = f.getmetrics()
    pad = int(size * 0.15)
    widths = [f.getlength(ch) for ch in text]
    track = tracking * size
    tw = sum(widths) + track * max(0, len(text) - 1)
    img = Image.new("RGBA", (int(tw + 2 * pad) + 1, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    for ch, w in zip(text, widths):
        d.text((x, pad), ch, font=f, fill=color + (alpha,))
        x += w + track
    # anchor metadata: optical centre = middle of cap height
    cap_top = f.getbbox("H")[1]
    img.info["cy"] = pad + (cap_top + asc) / 2
    img.info["pad"] = pad
    return img


def text_width(text, name, size, tracking=0.0, wght=None):
    f = font(name, size, wght)
    return sum(f.getlength(ch) for ch in text) + tracking * size * max(0, len(text) - 1)


def wrap(text, name, size, maxw, wght=None):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if text_width(test, name, size, wght=wght) <= maxw or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def fit_size(text, name, size, maxw, wght=None):
    while text_width(text, name, size, wght=wght) > maxw and size > 10:
        size = int(size * 0.94)
    return size


# ---------------------------------------------------------- compositing ops
def place(canvas, spr, cx, cy, scale=1.0, rot=0.0, alpha=1.0, ax=0.5, ay=None, sx=None):
    """Composite sprite with sub-pixel position, scale, rotation (deg)."""
    if alpha <= 0.003 or scale <= 0.001:
        return
    sw, sh = spr.size
    ax_px = ax * sw
    ay_px = spr.info.get("cy", sh / 2) if ay is None else ay * sh
    sx = scale if sx is None else sx
    sy = scale
    r = math.radians(rot)
    cr, sr_ = math.cos(r), math.sin(r)
    corners = []
    for px, py in [(0, 0), (sw, 0), (0, sh), (sw, sh)]:
        dx, dy = (px - ax_px) * sx, (py - ay_px) * sy
        corners.append((cx + dx * cr - dy * sr_, cy + dx * sr_ + dy * cr))
    x0 = max(0, int(math.floor(min(c[0] for c in corners))))
    y0 = max(0, int(math.floor(min(c[1] for c in corners))))
    x1 = min(canvas.size[0], int(math.ceil(max(c[0] for c in corners))) + 1)
    y1 = min(canvas.size[1], int(math.ceil(max(c[1] for c in corners))) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    # output (x,y) -> input
    a = cr / sx
    b = sr_ / sx
    d = -sr_ / sy
    e = cr / sy
    ox, oy = x0 - cx, y0 - cy
    c = a * ox + b * oy + ax_px
    f = d * ox + e * oy + ay_px
    out = spr.transform((x1 - x0, y1 - y0), Image.AFFINE, (a, b, c, d, e, f),
                        resample=Image.BICUBIC)
    if alpha < 1:
        al = out.getchannel("A").point(lambda v: int(v * alpha))
        out.putalpha(al)
    canvas.alpha_composite(out, (x0, y0))


def screen_add(canvas, spr, cx, cy, gain=1.0):
    """Screen-blend an RGB light sprite centred at (cx, cy)."""
    sw, sh = spr.size
    x0, y0 = int(cx - sw / 2), int(cy - sh / 2)
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(canvas.size[0], x0 + sw), min(canvas.size[1], y0 + sh)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    region = canvas.crop((cx0, cy0, cx1, cy1)).convert("RGB")
    s = spr.crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
    if gain != 1:
        s = s.point(lambda v: int(min(255, v * gain)))
    canvas.paste(ImageChops.screen(region, s), (cx0, cy0))


def from_low(arr):
    """Upscale a quarter-res float RGB (0..1) field to a full-frame RGBA."""
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    return im.resize((W, H), Image.BICUBIC).convert("RGBA")


def camera(img, zoom=1.0, rot=0.0, dx=0.0, dy=0.0):
    if abs(zoom - 1) < 1e-4 and abs(rot) < 1e-4 and abs(dx) < 0.01 and abs(dy) < 0.01:
        return img
    out = Image.new("RGBA", img.size, (0, 0, 0, 255))
    place(out, img, W / 2 + dx, H / 2 + dy, zoom, rot, ay=0.5)
    return out


def shake(t, at, amp, decay=7.0, seed=0):
    e = hit(t, at, decay)
    return (amp * e * math.sin(t * 91 + seed), amp * e * math.cos(t * 77 + seed * 2), 0.6 * e * math.sin(t * 53 + seed))


# ------------------------------------------------------------ backgrounds
def solid(color):
    return Image.new("RGBA", (W, H), color + (255,))


def radial_bg(inner, outer, cx=0.5, cy=0.45, r=0.75, extra=None):
    xx, yy = STATIC["lowgrid"]
    d = np.sqrt(((xx - cx * W) / max(W, H)) ** 2 + ((yy - cy * H) / max(W, H)) ** 2) / r
    k = np.clip(d, 0, 1)[..., None] ** 1.3
    a = np.array(inner, np.float32) / 255
    b = np.array(outer, np.float32) / 255
    arr = a * (1 - k) + b * k
    if extra is not None:
        arr = extra(arr, xx, yy)
    return from_low(arr)


def sky_bg(sun_x, sun_y, glow=1.0, top=C.SKY_TOP, low=C.SKY_LOW, horizon=0.62):
    xx, yy = STATIC["lowgrid"]
    v = np.clip(yy / (H * horizon), 0, 1)[..., None]
    a = np.array(top, np.float32) / 255
    b = np.array(low, np.float32) / 255
    arr = a * (1 - v) + b * v
    d = np.sqrt((xx - sun_x) ** 2 + (yy - sun_y) ** 2) / S
    g = (np.exp(-(d / 0.18) ** 2) * 0.9 + np.exp(-(d / 0.5) ** 2) * 0.35) * glow
    arr = arr + g[..., None] * np.array([1.0, 0.85, 0.55], np.float32)
    return from_low(arr)


@lru_cache(maxsize=8)
def glow_sprite(radius, color, core=0.25):
    n = int(radius * 2)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / radius
    g = np.exp(-(d / 0.45) ** 2) * 0.8 + np.exp(-(d / core) ** 2)
    rgb = np.clip(g[..., None] * np.array(color, np.float32) / 255, 0, 1)
    return Image.fromarray((rgb * 255).astype(np.uint8))


@lru_cache(maxsize=4)
def sun_disk(radius):
    ss = 3
    n = int(radius * 2 * ss + 8)
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2
    for i in range(24, 0, -1):
        r = radius * ss * i / 24
        col = mix_rgb((255, 244, 200), (255, 196, 80), (i / 24) ** 3)
        d.ellipse([c - r, c - r, c + r, c + r], fill=col + (255,))
    img = img.resize((n // ss, n // ss), Image.LANCZOS)
    return img


@lru_cache(maxsize=2)
def ray_sprite(n_rays=18):
    n = 1024
    img = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(img)
    c = n / 2
    rng = np.random.default_rng(11)
    for i in range(n_rays):
        a0 = 2 * math.pi * i / n_rays + rng.uniform(-0.05, 0.05)
        w = rng.uniform(0.04, 0.09)
        pts = [(c, c)]
        for a in (a0 - w, a0 + w):
            pts.append((c + math.cos(a) * n, c + math.sin(a) * n))
        d.polygon(pts, fill=int(rng.uniform(60, 120)))
    img = img.filter(ImageFilter.GaussianBlur(10))
    yy, xx = np.mgrid[0:n, 0:n]
    fall = np.clip(1 - np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c, 0, 1) ** 1.2
    arr = np.asarray(img, np.float32) * fall
    rgba = np.zeros((n, n, 4), np.uint8)
    rgba[..., :3] = (255, 244, 214)
    rgba[..., 3] = arr.astype(np.uint8)
    return Image.fromarray(rgba)


@lru_cache(maxsize=16)
def dot(radius, color, softness=0.5, alpha=255):
    n = max(3, int(radius * 2 + 4))
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2) / max(radius, 0.5)
    edge = max(0.05, softness)
    a = np.clip((1 - d) / edge, 0, 1) ** 1.5
    rgba = np.zeros((n, n, 4), np.uint8)
    rgba[..., :3] = color
    rgba[..., 3] = (a * alpha).astype(np.uint8)
    return Image.fromarray(rgba)


def dust(canvas, t, n=60, color=(255, 236, 190), seed=1, speed=1.0, size=1.0,
         drift=(0.0, -0.035), alpha=200, cam=(0, 0), depth_range=(0.3, 1.0)):
    """Deterministic floating bokeh/flour dust, parallaxed by depth."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        z = rng.uniform(*depth_range)
        x0, y0 = rng.uniform(0, 1), rng.uniform(0, 1)
        ph = rng.uniform(0, 6.28)
        x = (x0 + drift[0] * t * speed * z + 0.01 * math.sin(t * 0.8 + ph)) % 1.0
        y = (y0 + drift[1] * t * speed * z + 0.008 * math.cos(t * 0.6 + ph)) % 1.0
        px = x * (W + 200) - 100 + cam[0] * z
        py = y * (H + 200) - 100 + cam[1] * z
        r = (2 + 10 * z ** 3) * size * S / 1080
        tw = 0.6 + 0.4 * math.sin(t * 2.0 + ph * 3)
        spr = dot(round(r * 2) / 2, color, 0.9 if z > 0.85 else 0.5, int(alpha * tw * (0.5 + 0.5 * z)))
        sw, sh = spr.size
        x0i, y0i = int(px - sw / 2), int(py - sh / 2)
        if -sw < x0i < W and -sh < y0i < H:
            if x0i >= 0 and y0i >= 0 and x0i + sw <= W and y0i + sh <= H:
                canvas.alpha_composite(spr, (x0i, y0i))


def flour_burst(canvas, t, t0, cx, cy, n=140, seed=5, power=1.0, color=(250, 244, 232)):
    """Explosion of flour particles with drag and gravity."""
    lt = t - t0
    if lt < 0 or lt > 2.5:
        return
    rng = np.random.default_rng(seed)
    k = 3.2
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        v = rng.uniform(0.15, 1.0) ** 1.5 * S * 1.6 * power
        rr = v / k * (1 - math.exp(-k * lt))
        g = 0.08 * S * lt * lt
        px = cx + math.cos(ang) * rr
        py = cy + math.sin(ang) * rr * 0.8 + g
        z = rng.uniform(0, 1)
        r = (1.5 + 9 * z ** 2) * S / 1080 * (1 + lt * 0.8)
        a = int(230 * math.exp(-lt * 1.6) * (0.4 + 0.6 * z))
        if a < 6:
            continue
        spr = dot(round(r * 2) / 2, color, 0.85, a)
        sw, sh = spr.size
        x0, y0 = int(px - sw / 2), int(py - sh / 2)
        if 0 <= x0 and 0 <= y0 and x0 + sw <= W and y0 + sh <= H:
            canvas.alpha_composite(spr, (x0, y0))
    # soft puff cloud
    puff = glow_sprite(int(S * 0.42), (200, 190, 170), 0.3)
    screen_add(canvas, puff, cx, cy, 0.3 * math.exp(-lt * 3.0))


# --------------------------------------------------------------- icons
def ss_canvas(size, ss=3):
    img = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), ss


def ss_done(img, ss):
    return img.resize((img.size[0] // ss, img.size[1] // ss), Image.LANCZOS)


@lru_cache(maxsize=8)
def icon_roti(size, toasted=True):
    img, d, ss = ss_canvas(size)
    n = size * ss
    c = n / 2
    r = n * 0.46
    d.ellipse([c - r, c - r * 0.96, c + r, c + r * 0.96], fill=(226, 180, 112, 255))
    r2 = r * 0.93
    d.ellipse([c - r2, c - r2 * 0.95, c + r2, c + r2 * 0.95], fill=(238, 200, 140, 255))
    rng = np.random.default_rng(4)
    if toasted:
        for _ in range(26):
            a, rr = rng.uniform(0, 6.28), r2 * math.sqrt(rng.uniform(0, 0.85))
            x, y = c + math.cos(a) * rr, c + math.sin(a) * rr
            s = rng.uniform(0.02, 0.07) * n
            d.ellipse([x - s, y - s * 0.7, x + s, y + s * 0.7], fill=(150, 88, 40, int(rng.uniform(120, 220))))
    img = ss_done(img, ss)
    # soft highlight
    hl = glow_sprite(int(size * 0.3), (255, 240, 210), 0.2)
    base = img.convert("RGB")
    lay = Image.new("RGB", img.size, 0)
    lay.paste(hl, (int(size * 0.18), int(size * 0.1)))
    out = ImageChops.screen(base, lay.point(lambda v: int(v * 0.35)))
    out = out.convert("RGBA")
    out.putalpha(img.getchannel("A"))
    return out


@lru_cache(maxsize=4)
def icon_millstone(size):
    img, d, ss = ss_canvas(size)
    n = size * ss
    c = n / 2
    r = n * 0.47
    d.ellipse([c - r, c - r, c + r, c + r], fill=(120, 96, 78, 255))
    d.ellipse([c - r * 0.94, c - r * 0.94, c + r * 0.94, c + r * 0.94], fill=(168, 142, 118, 255))
    for k in range(12):
        a = 2 * math.pi * k / 12
        for j in range(4):
            aa = a + j * 0.06
            d.line([(c + math.cos(aa) * r * 0.25, c + math.sin(aa) * r * 0.25),
                    (c + math.cos(aa + 0.35) * r * 0.92, c + math.sin(aa + 0.35) * r * 0.92)],
                   fill=(120, 96, 78, 255), width=int(ss * size / 160) + 1)
    d.ellipse([c - r * 0.16, c - r * 0.16, c + r * 0.16, c + r * 0.16], fill=(60, 44, 32, 255))
    return ss_done(img, ss)


@lru_cache(maxsize=8)
def icon_wheat(size, color=C.GOLD, stem=(150, 110, 50)):
    img, d, ss = ss_canvas(size)
    n = size * ss
    cx = n / 2
    lw = max(2, int(n * 0.018))
    d.line([(cx, n * 0.98), (cx, n * 0.12)], fill=stem + (255,), width=lw)
    for i in range(7):
        y = n * (0.2 + i * 0.075)
        for side in (-1, 1):
            gx = cx + side * n * 0.055
            box = [gx - n * 0.05, y - n * 0.07, gx + n * 0.05, y + n * 0.07]
            g = Image.new("RGBA", (int(n * 0.1) + 2, int(n * 0.14) + 2), (0, 0, 0, 0))
            ImageDraw.Draw(g).ellipse([1, 1, g.size[0] - 2, g.size[1] - 2], fill=color + (255,))
            g = g.rotate(-side * 28, expand=True, resample=Image.BICUBIC)
            img.alpha_composite(g, (int(gx - g.size[0] / 2), int(y - g.size[1] / 2)))
            d.line([(gx, y - n * 0.06), (gx + side * n * 0.12, y - n * 0.2)], fill=color + (200,), width=max(1, lw // 2))
    d.ellipse([cx - n * 0.04, n * 0.08, cx + n * 0.04, n * 0.2], fill=color + (255,))
    # leaf
    d.polygon([(cx, n * 0.8), (cx + n * 0.22, n * 0.62), (cx + n * 0.05, n * 0.78)], fill=stem + (255,))
    return ss_done(img, ss)


@lru_cache(maxsize=4)
def icon_tawa(size):
    img, d, ss = ss_canvas(size)
    n = size * ss
    c = n / 2
    r = n * 0.36
    d.rounded_rectangle([c + r * 0.8, c - n * 0.035, n * 0.99, c + n * 0.035], radius=n * 0.03, fill=(40, 26, 18, 255))
    d.ellipse([c - r - n * 0.08, c - r, c + r - n * 0.08, c + r], fill=(48, 34, 26, 255))
    d.ellipse([c - r * 0.92 - n * 0.08, c - r * 0.92, c + r * 0.92 - n * 0.08, c + r * 0.92], fill=(70, 52, 40, 255))
    img = ss_done(img, ss)
    roti = icon_roti(int(size * 0.56))
    img.alpha_composite(roti, (int(size / 2 - size * 0.08 - roti.size[0] / 2), int(size / 2 - roti.size[1] / 2)))
    return img


@lru_cache(maxsize=4)
def icon_paratha(size):
    img, d, ss = ss_canvas(size)
    n = size * ss
    pts = [(n * 0.5, n * 0.08), (n * 0.94, n * 0.86), (n * 0.06, n * 0.86)]
    d.polygon(pts, fill=(214, 160, 90, 255))
    for k in range(1, 4):
        f = 1 - k * 0.2
        cx, cy = n * 0.5, n * 0.6
        q = [(cx + (x - cx) * f, cy + (y - cy) * f) for x, y in pts]
        d.line(q + [q[0]], fill=(176, 116, 56, 255), width=int(n * 0.012))
    rng = np.random.default_rng(9)
    for _ in range(14):
        x, y = rng.uniform(0.3, 0.7) * n, rng.uniform(0.45, 0.8) * n
        s = rng.uniform(0.015, 0.04) * n
        d.ellipse([x - s, y - s * 0.7, x + s, y + s * 0.7], fill=(140, 80, 34, 170))
    return ss_done(img, ss)


@lru_cache(maxsize=4)
def icon_puri(size):
    img, d, ss = ss_canvas(size)
    n = size * ss
    c = n / 2
    r = n * 0.44
    for i in range(18, 0, -1):
        rr = r * i / 18
        col = mix_rgb((255, 222, 150), (214, 140, 50), (i / 18) ** 1.5)
        d.ellipse([c - rr, c - rr * 0.92 - (18 - i) * n * 0.002, c + rr, c + rr * 0.92], fill=col + (255,))
    d.ellipse([c - r * 0.5, c - r * 0.62, c - r * 0.05, c - r * 0.3], fill=(255, 246, 220, 140))
    return ss_done(img, ss)


@lru_cache(maxsize=4)
def icon_loaf(size):
    img, d, ss = ss_canvas(size)
    n = size * ss
    d.rounded_rectangle([n * 0.06, n * 0.3, n * 0.94, n * 0.8], radius=n * 0.22, fill=(186, 110, 48, 255))
    d.rounded_rectangle([n * 0.1, n * 0.33, n * 0.9, n * 0.66], radius=n * 0.18, fill=(214, 140, 64, 255))
    for k in range(4):
        x = n * (0.25 + k * 0.17)
        d.line([(x - n * 0.05, n * 0.4), (x + n * 0.06, n * 0.58)], fill=(250, 214, 150, 255), width=int(n * 0.03))
    return ss_done(img, ss)


@lru_cache(maxsize=4)
def icon_sun(size, color=C.DARK):
    img, d, ss = ss_canvas(size)
    n = size * ss
    c = n / 2
    r = n * 0.22
    d.ellipse([c - r, c - r, c + r, c + r], fill=color + (255,))
    for k in range(12):
        a = 2 * math.pi * k / 12
        d.line([(c + math.cos(a) * r * 1.35, c + math.sin(a) * r * 1.35),
                (c + math.cos(a) * r * 2.05, c + math.sin(a) * r * 2.05)], fill=color + (255,), width=int(n * 0.055))
    return ss_done(img, ss)


# ------------------------------------------------------- text animators
def draw_line(canvas, text, name, size, color, cx, cy, wght=None, tracking=0.0,
              alpha=1.0, scale=1.0, rot=0.0, ax=0.5):
    spr = text_img(text, name, int(size), color, tracking, wght)
    place(canvas, spr, cx, cy, scale, rot, alpha, ax=ax)


def letters_rise(canvas, text, name, size, color, cx, cy, t, t0, stagger=0.05,
                 dur=0.5, rise=0.6, wght=None, tracking=0.0, clip=True):
    """Each glyph slides up from behind a mask line, staggered."""
    tw = text_width(text, name, size, tracking, wght)
    f = font(name, int(size), wght)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = cx - tw / 2
    for i, ch in enumerate(text):
        w = f.getlength(ch)
        p = ease_out_expo(prog(t, t0 + i * stagger, t0 + i * stagger + dur))
        if p > 0 and ch != " ":
            spr = text_img(ch, name, int(size), color, 0.0, wght)
            pad = spr.info["pad"]
            place(layer, spr, x - pad, cy + (1 - p) * size * rise, 1.0, 0, 1.0, ax=0.0)
        x += w + tracking * size
    if clip:
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).rectangle([0, 0, W, int(cy + size * 0.42)], fill=255)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), m))
    canvas.alpha_composite(layer)


def words_from_sides(canvas, text, name, size, color, cx, cy, t, t0, stagger=0.07, dur=0.55, wght=None):
    words = text.split()
    sp = text_width(" ", name, size, wght=wght)
    widths = [text_width(w, name, size, wght=wght) for w in words]
    total = sum(widths) + sp * (len(words) - 1)
    x = cx - total / 2
    for i, (w, ww) in enumerate(zip(words, widths)):
        p = prog(t, t0 + i * stagger, t0 + i * stagger + dur)
        e = ease_out_back(p, 1.4) if p > 0 else 0
        side = -1 if i % 2 == 0 else 1
        off = (1 - e) * side * W * 0.6
        draw_line(canvas, w, name, size, color, x + ww / 2 + off, cy, wght, alpha=min(1, p * 3))
        x += ww + sp


def letters_pop(canvas, text, name, size, color, cx, cy, t, t0, stagger=0.035, wght=None):
    tw = text_width(text, name, size, wght=wght)
    f = font(name, int(size), wght)
    x = cx - tw / 2
    for i, ch in enumerate(text):
        w = f.getlength(ch)
        p = prog(t, t0 + i * stagger, t0 + i * stagger + 0.4)
        if p > 0 and ch != " ":
            e = ease_out_back(p, 2.6)
            spr = text_img(ch, name, int(size), color, 0.0, wght)
            place(canvas, spr, x + w / 2, cy - (1 - e) * size * 0.4, max(0.01, e), (1 - e) * -25, min(1, p * 4))
        x += w


# =================================================================== SCENES
# ---------------------------------------------------------------- 1 HOOK
@lru_cache(maxsize=2)
def hook_o_assets():
    """High-res FLOUR word mask + the O's counter as a window mask."""
    size = int(S * (0.36 if PORTRAIT else 0.42)) * 2
    f = font(SERIF, size, 900)
    word = "FLOUR"
    tw = int(f.getlength(word)) + size
    asc, desc = f.getmetrics()
    m = Image.new("L", (tw, asc + desc + size // 2), 0)
    ImageDraw.Draw(m).text((size // 2, size // 4), word, font=f, fill=255)
    x_o = size // 2 + f.getlength("FL")
    w_o = f.getlength("O")
    arr = np.asarray(m) > 128
    bbox = ImageDraw.Draw(m).textbbox((x_o, size // 4), "O", font=f)
    ocx, ocy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    lab, _ = ndimage.label(~arr)
    counter = lab == lab[int(ocy), int(ocx)]
    counter = ndimage.binary_dilation(counter, iterations=max(2, size // 60))
    win = Image.fromarray((counter * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
    ys, xs = np.nonzero(counter)
    half_w, half_h = (xs.max() - xs.min()) / 2, (ys.max() - ys.min()) / 2
    return m, win, (ocx, ocy), (half_w, half_h), size, w_o


def scene_hook(t):
    bg = radial_bg((44, 28, 18), C.COCOA, 0.5, 0.5, 0.8)
    cam_dx = cam_dy = cam_r = 0.0
    zoom = 1.0
    ca = 0.0
    big = int(S * (0.25 if PORTRAIT else 0.2))
    if t < 1.5:
        lines = C.HOOK_WORDS
        gap = big * 1.05
        ys = [H / 2 - gap, H / 2, H / 2 + gap]
        for i, word in enumerate(lines):
            t0 = i * C.BEAT
            if t < t0:
                continue
            p = prog(t, t0, t0 + 0.2)
            sc = lerp(1.6, 1.0, ease_out_expo(p))
            if i == 1:
                name, sz, tr, col = SANS_LIGHT, big * 0.62, 0.18, C.WHEAT
            else:
                name, sz, tr, col = SANS_BLACK, big, -0.02, C.CREAM
            sz = fit_size(word, name, sz, W * 0.86)
            draw_line(bg, word, name, sz, col, W / 2, ys[i], tracking=tr, alpha=min(1, p * 4), scale=sc)
            flour_burst(bg, t, t0, W / 2, ys[i], n=70, seed=10 + i, power=0.7)
            sx, sy, sr = shake(t, t0, S * 0.025, 9, i)
            cam_dx += sx
            cam_dy += sy
            cam_r += sr
            ca += 10 * hit(t, t0, 10)
        zoom = 1.0 + 0.04 * t
        return camera(bg, zoom, cam_r, cam_dx, cam_dy), ca, 0.0
    if t < 2.0:
        # glitch beat: the statement breaks apart, the twist lands
        sz = fit_size(C.HOOK_TWIST, SERIF, S * 0.2, W * 0.8, 300)
        jitter = math.sin(t * 140) * S * 0.01
        draw_line(bg, C.HOOK_TWIST, SERIF, sz, C.GOLD, W / 2 + jitter, H / 2, wght=300,
                  scale=lerp(0.92, 1.0, ease_out(prog(t, 1.5, 2.0))))
        return bg, 18 + 14 * math.sin(t * 60) ** 2, 1.0
    # 2.0-3.0: giant serif FLOUR, camera flies through the O into the sun
    m, win, (ocx, ocy), (hw, hh), msize, _ = hook_o_assets()
    base_scale = (W * 0.9) / m.size[0]
    need = 1.15 * math.sqrt((W / 2 / (hw * base_scale)) ** 2 + (H / 2 / (hh * base_scale)) ** 2)
    p = prog(t, 2.15, 3.0)
    z = math.exp(math.log(need) * ease_in(p, 2.6))
    pop = lerp(1.25, 1.0, ease_out_expo(prog(t, 2.0, 2.18)))
    sc = base_scale * z * pop
    # anchor: O centre drifts from its natural spot to frame centre
    nat_x = W / 2 + (ocx - m.size[0] / 2) * base_scale
    nat_y = H / 2 + (ocy - m.size[1] / 2) * base_scale
    k = ease_in_out(clamp(p * 1.6))
    ax_, ay_ = lerp(nat_x, W / 2, k), lerp(nat_y, H / 2, k)
    reveal = scene_reveal(min(0.0, t - 3.0), preroll=True)
    w_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wspr = Image.merge("RGBA", (win, win, win, win))
    place(w_layer, wspr, ax_, ay_, sc, 0, 1.0, ax=ocx / m.size[0], ay=ocy / m.size[1])
    bg.paste(reveal, (0, 0), w_layer.getchannel("A"))
    t_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tspr = Image.new("RGBA", m.size, C.CREAM + (0,))
    tspr.putalpha(m)
    place(t_layer, tspr, ax_, ay_, sc, 0, 1.0, ax=ocx / m.size[0], ay=ocy / m.size[1])
    bg.alpha_composite(t_layer)
    flour_burst(bg, t, 2.0, W / 2, H / 2, n=90, seed=33, power=1.0)
    sx, sy, sr = shake(t, 2.0, S * 0.03, 9, 4)
    out = camera(bg, 1.0, sr, sx, sy)
    zb = ease_in(prog(t, 2.55, 3.0), 2) * 0.12
    if zb > 0:
        out = zoom_blur(out, zb)
    return out, 6 * hit(t, 2.0, 8), 0.0


def zoom_blur(img, amount, steps=6):
    acc = np.asarray(img.convert("RGB"), np.float32)
    total = 1.0
    for i in range(1, steps):
        z = 1 + amount * i / steps
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        place(tmp, img, W / 2, H / 2, z, ay=0.5)
        wgt = 1 - i / steps * 0.5
        acc += np.asarray(tmp.convert("RGB"), np.float32) * wgt
        total += wgt
    return Image.fromarray((acc / total).astype(np.uint8)).convert("RGBA")


# --------------------------------------------------------------- 2 REVEAL
def scene_reveal(lt, preroll=False):
    """lt = seconds since 3.0 (may be negative during the fly-through)."""
    rise = ease_out(clamp((lt + 1.0) / 3.0), 3)
    sun_y = H * lerp(0.62, 0.36 if PORTRAIT else 0.34, rise)
    sun_x = W / 2
    canvas = sky_bg(sun_x, sun_y, glow=lerp(0.7, 1.0, rise), top=(255, 224, 160), low=(238, 140, 60), horizon=1.0)
    rays = ray_sprite()
    place(canvas, rays, sun_x, sun_y, max(W, H) * 1.6 / rays.size[0], lt * 6, 0.55, ay=0.5)
    sr = int(S * 0.15)
    place(canvas, sun_disk(sr), sun_x, sun_y, 1.0, ay=0.5)
    screen_add(canvas, glow_sprite(int(S * 0.5), (255, 200, 120), 0.18), sun_x, sun_y, 0.8)
    dust(canvas, lt + 3, 70, (255, 246, 220), seed=2, alpha=170)
    if preroll:
        return canvas.convert("RGB")
    logo_size = int(S * (0.2 if PORTRAIT else 0.17))
    ly = sun_y + S * (0.36 if PORTRAIT else 0.3)
    k = ease_out(prog(lt, 0.25, 0.8))
    draw_line(canvas, "INTRODUCING", SANS_SEMI, S * 0.032, C.DARK, W / 2, ly - logo_size * 0.95,
              tracking=lerp(0.6, 0.42, k), alpha=k)
    letters_rise(canvas, C.BRAND, SERIF, logo_size, C.DARK, W / 2, ly, lt, 0.45, 0.06, 0.6, 0.9, wght=650)
    # light sweep across the wordmark
    sp = prog(lt, 1.45, 2.05)
    if 0 < sp < 1:
        sweep_logo(canvas, C.BRAND, logo_size, W / 2, ly, sp)
    tag_y = ly + logo_size * 0.95
    words = C.TAGLINE.split()
    sz = fit_size(C.TAGLINE, SANS_MED, S * 0.048, W * 0.86)
    sp_w = text_width(" ", SANS_MED, sz)
    widths = [text_width(w, SANS_MED, sz) for w in words]
    x = W / 2 - (sum(widths) + sp_w * (len(words) - 1)) / 2
    for i, (w, ww) in enumerate(zip(words, widths)):
        p = ease_out(prog(lt, 2.0 + i * 0.08, 2.6 + i * 0.08))
        draw_line(canvas, w, SANS_MED, sz, (92, 50, 24), x + ww / 2, tag_y + (1 - p) * sz * 0.8, alpha=p)
        x += ww + sp_w
    zoom = 1.0 + 0.05 * ease_in_out(prog(lt, 0, 4))
    out_p = ease_in(prog(lt, 3.7, 4.0), 3)
    zoom += out_p * 0.5
    return camera(canvas, zoom, lerp(-0.6, 0.6, prog(lt, 0, 4)), 0, 0)


def sweep_logo(canvas, text, size, cx, cy, p):
    spr = text_img(text, SERIF, int(size), (255, 255, 255), 0.0, 650)
    mask = spr.getchannel("A")
    w, h = spr.size
    band = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(band)
    x = lerp(-w * 0.3, w * 1.3, p)
    d.polygon([(x - w * 0.08, 0), (x + w * 0.02, 0), (x - w * 0.12 + h * 0.3, h), (x - w * 0.22 + h * 0.3, h)], fill=255)
    band = band.filter(ImageFilter.GaussianBlur(size * 0.06))
    light = Image.new("RGBA", (w, h), (255, 236, 180, 0))
    light.putalpha(ImageChops.multiply(mask, band))
    place(canvas, light, cx, cy, 1.0)


# ------------------------------------------------------------ 3 FEATURES
CARD_STYLES = [
    # bg, text, accent
    (C.CREAM, C.DARK, C.MARIGOLD),
    (C.GOLD, C.DARK, (255, 246, 220)),
    (C.DARK, C.CREAM, C.GOLD),
    (C.TERRACOTTA, C.CREAM, C.WHEAT),
]


def brand_bug(canvas, color, alpha=0.9):
    sz = S * 0.034
    y = H * 0.06 if PORTRAIT else H * 0.08
    x = W * 0.08
    place(canvas, icon_sun(int(sz * 1.5), color), x, y, 1.0, alpha=alpha, ax=0.5, ay=0.5)
    draw_line(canvas, C.BRAND, SERIF, sz, color, x + sz * 1.0, y, wght=650, alpha=alpha, ax=0.0)


def progress_dots(canvas, i, color, accent, t_local):
    n = len(C.FEATURES)
    y = H * (0.93 if PORTRAIT else 0.9)
    seg = S * 0.08
    gap = S * 0.02
    x0 = W / 2 - (n * seg + (n - 1) * gap) / 2
    d = ImageDraw.Draw(canvas)
    hh = max(3, int(S * 0.005))
    for k in range(n):
        x = x0 + k * (seg + gap)
        d.rounded_rectangle([x, y - hh / 2, x + seg, y + hh / 2], radius=hh // 2, fill=color + (70,))
        fillp = 1.0 if k < i else (clamp(t_local / 2.0) if k == i else 0)
        if fillp > 0:
            d.rounded_rectangle([x, y - hh / 2, x + seg * fillp, y + hh / 2], radius=hh // 2, fill=accent + (255,))


def feature_card(i, lt):
    bg_c, fg, acc = CARD_STYLES[i]
    kicker, head = C.FEATURES[i]
    canvas = radial_bg(mix_rgb(bg_c, (255, 255, 255), 0.12), mix_rgb(bg_c, (0, 0, 0), 0.12), 0.5, 0.4, 0.9)
    # oversized background numeral with slow parallax
    num_sz = S * (0.9 if PORTRAIT else 0.75)
    draw_line(canvas, kicker, SANS_BLACK, num_sz, mix_rgb(bg_c, fg, 0.06),
              W * (0.62 if PORTRAIT else 0.72) - lt * S * 0.03, H * (0.3 if PORTRAIT else 0.45), tracking=-0.04)
    icon_y = H * (0.36 if PORTRAIT else 0.48)
    icon_x = W / 2 if PORTRAIT else W * 0.72
    head_x = W / 2 if PORTRAIT else W * 0.34
    head_y = H * (0.62 if PORTRAIT else 0.5)
    isz = int(S * (0.42 if PORTRAIT else 0.36))
    ip = ease_out_back(prog(lt, 0.05, 0.55), 1.6)
    if i == 0:
        place(canvas, icon_millstone(isz), icon_x, icon_y, max(0.01, ip), lt * 40, ay=0.5)
        for k in range(18):
            ph = k * 0.37
            yy = icon_y + isz * 0.42 + ((lt * 0.7 + ph) % 1) * S * 0.25
            xx = icon_x + math.sin(k * 2.1) * isz * 0.4
            place(canvas, dot(S * 0.006, (255, 255, 255), 0.6, 220), xx, yy, 1, ay=0.5,
                  alpha=(1 - ((lt * 0.7 + ph) % 1)) * ip)
    elif i == 1:
        puff = 1 + 0.06 * math.sin(lt * 7) * ease_out(prog(lt, 0.4, 0.8))
        place(canvas, icon_roti(isz), icon_x, icon_y, max(0.01, ip) * puff, 0, ay=0.5, sx=max(0.01, ip) * (2 - puff))
        d = ImageDraw.Draw(canvas)
        for k in range(3):
            pts = []
            base_x = icon_x + (k - 1) * isz * 0.25
            for j in range(20):
                yy = icon_y - isz * 0.45 - j * S * 0.012 - (lt * S * 0.05) % (S * 0.03)
                pts.append((base_x + math.sin(j * 0.5 + lt * 4 + k) * S * 0.015, yy))
            d.line(pts, fill=(255, 255, 255, int(110 * ip)), width=max(2, int(S * 0.005)), joint="curve")
    elif i == 2:
        for k, off in enumerate((-0.28, 0, 0.28)):
            sway = math.sin(lt * 2.4 + k) * 6
            place(canvas, icon_wheat(isz, C.GOLD if k != 1 else (255, 214, 120)), icon_x + off * isz,
                  icon_y + isz * 0.5, max(0.01, ip) * (0.8 if k != 1 else 1), sway + off * 30, ay=1.0)
    else:
        place(canvas, icon_tawa(isz), icon_x, icon_y, max(0.01, ip), math.sin(lt * 3) * 2, ay=0.5)
    # headline
    hs = S * (0.11 if PORTRAIT else 0.085)
    maxw = W * (0.86 if PORTRAIT else 0.5)
    lines = wrap(head, SERIF, hs, maxw, 600)
    lh = hs * 1.08
    y0 = head_y - (len(lines) - 1) * lh / 2
    draw_line(canvas, kicker + " —", SANS_SEMI, S * 0.03, acc, head_x, y0 - hs * 0.95,
              tracking=0.3, alpha=ease_out(prog(lt, 0.1, 0.4)))
    for li, line in enumerate(lines):
        y = y0 + li * lh
        if i == 0:
            letters_rise(canvas, line, SERIF, hs, fg, head_x, y, lt, 0.12 + li * 0.12, 0.022, 0.5, 1.0, wght=600)
        elif i == 1:
            p = prog(lt, 0.12 + li * 0.1, 0.5 + li * 0.1)
            draw_line(canvas, line, SERIF, hs, fg, head_x, y, wght=600,
                      tracking=lerp(0.25, 0.0, ease_out_expo(p)), scale=lerp(1.3, 1.0, ease_out_expo(p)),
                      alpha=min(1, p * 3))
        elif i == 2:
            words_from_sides(canvas, line, SERIF, hs, fg, head_x, y, lt, 0.1 + li * 0.15, wght=600)
        else:
            letters_pop(canvas, line, SERIF, hs, fg, head_x, y, lt, 0.1 + li * 0.2, 0.025, wght=600)
    brand_bug(canvas, fg, 0.85)
    progress_dots(canvas, i, fg, acc, lt)
    zoom = 1.0 + 0.04 * lt
    return camera(canvas, zoom, (lt - 1) * (0.4 if i % 2 else -0.4), (-1) ** i * S * 0.01 * lt, 0)


def scene_features(t):
    lt = t - C.FEATURES_T[0]
    i = min(3, int(lt // 2))
    li = lt - 2 * i
    hw = C.WHIP / 2
    # whip-pan around each internal boundary
    for b in (1, 2, 3):
        bt = 2 * b
        if bt - hw <= lt < bt + hw:
            p = (lt - (bt - hw)) / C.WHIP
            e = ease_in_out(p)
            out_f = feature_card(b - 1, min(lt - 2 * (b - 1), 2.0))
            in_f = feature_card(b, max(0.0, lt - bt))
            direction = -1 if b % 2 else 1
            off = e * W * direction
            frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            frame.paste(out_f, (int(off), 0))
            frame.paste(in_f, (int(off - W * direction), 0))
            vel = math.sin(math.pi * p)
            frame = motion_blur_h(frame, int(vel * S * 0.12))
            return frame, 12 * vel, 0.0
    frame = feature_card(i, li)
    flash = 0.85 * hit(t, C.FEATURES_T[0], 14)
    return frame, 6 * hit(t, C.FEATURES_T[0], 10), flash


def motion_blur_h(img, length, steps=9):
    if length < 2:
        return img
    a = np.asarray(img.convert("RGB"), np.float32)
    acc = np.zeros_like(a)
    for k in range(steps):
        s = int((k / (steps - 1) - 0.5) * length)
        acc += np.roll(a, s, axis=1)
    return Image.fromarray((acc / steps).astype(np.uint8)).convert("RGBA")


# --------------------------------------------------------------- 4 FIELD
def time_warp(lt):
    """Speed ramp: slow-mo through the field, then whip forward into the drop."""
    if lt < 4.5:
        return lt * 0.45
    x = lt - 4.5
    return 4.5 * 0.45 + x * 0.45 + x * x * 1.6


def wheat_layer(t, n, y_base, h_min, h_max, color, rim, seed, scale_x=1.0, ear=True, sway=1.0, x_off=0.0, thick=1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = np.random.default_rng(seed)
    for k in range(n):
        bx = (rng.uniform(-0.1, 1.1) * W - W / 2) * scale_x + W / 2 + x_off
        h = rng.uniform(h_min, h_max)
        ph = rng.uniform(0, 6.28)
        bend = (math.sin(t * 1.3 + ph + bx * 0.003) * 0.06 + 0.04) * sway
        by = y_base + rng.uniform(0, h_min * 0.15)
        pts = []
        for j in range(9):
            s = j / 8
            pts.append((bx + bend * h * s * s, by - h * s))
        lw = max(1, int(h * 0.012 * thick))
        d.line(pts, fill=color + (255,), width=lw)
        if ear:
            tipx, tipy = pts[-1]
            ang = math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0])
            el = h * 0.17
            gs = max(1.2, h * 0.011 * thick)
            awn = (rim or color) + (230,)
            for g in range(9):
                s = g / 8
                gx = tipx - math.cos(ang) * el * (1 - s)
                gy = tipy - math.sin(ang) * el * (1 - s)
                side = 1 if g % 2 else -1
                ox = math.cos(ang + side * math.pi / 2) * gs * 1.1
                oy = math.sin(ang + side * math.pi / 2) * gs * 1.1
                ex, ey = gx + ox, gy + oy
                aa = ang + side * 0.32
                d.line([(ex, ey), (ex + math.cos(aa) * gs * 7, ey + math.sin(aa) * gs * 7)],
                       fill=awn if rim else color + (200,), width=1)
                if rim:
                    d.ellipse([ex - gs - 1, ey - gs * 1.5 - 1, ex + gs - 1, ey + gs * 1.5 - 1], fill=rim + (255,))
                d.ellipse([ex - gs, ey - gs * 1.5, ex + gs, ey + gs * 1.5], fill=color + (255,))
    return layer


def scene_field(t):
    lt = t - C.FIELD[0]
    tw = time_warp(lt)
    dolly = ease_in_out(prog(lt, 0, 6))
    horizon = H * (0.62 if PORTRAIT else 0.6)
    sun_x, sun_y = W * 0.62, horizon - S * lerp(0.1, 0.16, dolly)
    canvas = sky_bg(sun_x, sun_y, 1.1, top=(255, 206, 128), low=(232, 108, 44), horizon=horizon / H)
    place(canvas, ray_sprite(), sun_x, sun_y, max(W, H) * 1.4 / 1024, tw * 4, 0.35, ay=0.5)
    place(canvas, sun_disk(int(S * 0.09)), sun_x, sun_y, 1.0, ay=0.5)
    d = ImageDraw.Draw(canvas)
    # distant hills (haze)
    for li, (col, amp, yo) in enumerate([((214, 120, 70), 0.035, -0.01), ((176, 88, 50), 0.05, 0.02)]):
        pts = [(0, H)]
        for x in range(0, W + 41, 40):
            y = horizon + S * yo - S * amp * (0.5 + 0.5 * math.sin(x / W * 5 + li * 2))
            pts.append((x, y))
        pts.append((W, H))
        d.polygon(pts, fill=col + (255,))
    d.rectangle([0, horizon + S * 0.04, W, H], fill=(150, 70, 32, 255))
    # parallax wheat layers: far, mid, near (near is out of focus)
    far = wheat_layer(tw, 160, horizon + S * 0.06, S * 0.05, S * 0.08, (128, 60, 28), None, 1,
                      1 + 0.05 * dolly, True, 0.6)
    canvas.alpha_composite(far.filter(ImageFilter.GaussianBlur(1.2)))
    mid = wheat_layer(tw, 70, H * 0.86, S * 0.22, S * 0.34, (92, 42, 20), (255, 196, 110), 2,
                      1 + 0.18 * dolly, True, 1.0, thick=1.1)
    canvas.alpha_composite(mid.filter(ImageFilter.GaussianBlur(0.8)))
    screen_add(canvas, glow_sprite(int(S * 0.6), (255, 170, 80), 0.2), sun_x, sun_y, 0.6)
    dust(canvas, tw * 2, 55, (255, 236, 190), seed=8, drift=(0.02, -0.02), alpha=200,
         cam=(-dolly * S * 0.2, 0))
    nh = S if PORTRAIT else H * 0.55
    near = wheat_layer(tw, 6, H * 1.02, nh * 0.7, nh * 0.95, (54, 24, 10), (255, 170, 80), 3,
                       1 + 0.6 * dolly, True, 1.2, x_off=-dolly * S * 0.25, thick=0.8)
    canvas.alpha_composite(near.filter(ImageFilter.GaussianBlur(S * 0.0035)))
    # copy
    sz = fit_size(C.FIELD_LINES[0], SERIF, S * 0.1, W * 0.86, 500)
    ty = H * (0.3 if PORTRAIT else 0.3)
    for k, (line, a, b) in enumerate([(C.FIELD_LINES[0], 0.4, 2.9), (C.FIELD_LINES[1], 3.1, 5.7)]):
        pin = ease_out(prog(lt, a, a + 0.8))
        pout = ease_in(prog(lt, b - 0.4, b), 2)
        al = pin * (1 - pout)
        if al > 0:
            draw_line(canvas, line, SERIF, sz, (255, 236, 200), W / 2, ty + 3, wght=500,
                      tracking=lerp(0.12, 0.0, pin) + pout * 0.1, alpha=al * 0.5)
            draw_line(canvas, line, SERIF, sz, C.DARK, W / 2, ty, wght=500,
                      tracking=lerp(0.12, 0.0, pin) + pout * 0.1, alpha=al)
    zoom = 1.0 + 0.12 * dolly + 0.25 * ease_in(prog(lt, 5.3, 6.0), 3)
    out = camera(canvas, zoom, lerp(-1.0, 0.5, dolly), 0, -S * 0.04 * dolly)
    zb = ease_in(prog(lt, 5.4, 6.0), 2) * 0.15
    if zb > 0:
        out = zoom_blur(out, zb)
    # cinematic letterbox
    bar = ease_out(prog(lt, 0, 0.6)) * (1 - ease_in(prog(lt, 5.6, 6.0))) * H * (0.07 if PORTRAIT else 0.1)
    if bar > 1:
        dd = ImageDraw.Draw(out)
        dd.rectangle([0, 0, W, bar], fill=(0, 0, 0, 255))
        dd.rectangle([0, H - bar, W, H], fill=(0, 0, 0, 255))
    flash = 0.3 * hit(t, C.FIELD[0], 6)
    return out, 3 * ease_in(prog(lt, 5.0, 6.0)), flash


# ------------------------------------------------------------- 5 MONTAGE
MONTAGE_STYLES = [(C.GOLD, C.DARK), (C.DARK, C.GOLD), (C.TERRACOTTA, C.CREAM), (C.CREAM, C.TERRACOTTA)]
MONTAGE_ICONS = [icon_roti, icon_paratha, icon_puri, icon_loaf]


def scene_montage(t):
    lt = t - C.MONTAGE[0]
    if lt < 2.0:
        i = min(3, int(lt / C.BEAT))
        li = lt - i * C.BEAT
        bg_c, fg = MONTAGE_STYLES[i]
        canvas = radial_bg(mix_rgb(bg_c, (255, 255, 255), 0.15), mix_rgb(bg_c, (0, 0, 0), 0.18), 0.5, 0.5, 0.8)
        isz = int(S * 0.62)
        place(canvas, MONTAGE_ICONS[i](isz), W / 2, H * 0.5, 1.0 + 0.15 * li, li * 20 * (-1) ** i, alpha=0.95, ay=0.5)
        word = C.MONTAGE_WORDS[i].upper()
        sz = fit_size(word, SANS_BLACK, S * 0.2, W * 0.9)
        p = ease_out_expo(prog(li, 0, 0.16))
        y = H * (0.5 if PORTRAIT else 0.5)
        if i == 0:
            draw_line(canvas, word, SANS_BLACK, sz, fg, W / 2, y, tracking=-0.03, scale=lerp(2.2, 1.0, p))
        elif i == 1:
            draw_line(canvas, word, SANS_BLACK, sz, fg, W / 2, lerp(-sz, y, p), tracking=-0.03)
        elif i == 2:
            draw_line(canvas, word, SANS_BLACK, sz, fg, W / 2, y, tracking=-0.03, rot=lerp(-14, 0, p), scale=lerp(0.6, 1, p))
        else:
            spr = text_img(word, SANS_BLACK, int(sz), fg, -0.03)
            place(canvas, spr, W / 2, y, 1.0, sx=lerp(1.8, 1.0, p))
        sx, sy, sr = shake(t, C.MONTAGE[0] + i * C.BEAT, S * 0.02, 12, i)
        out = camera(canvas, 1.03 + 0.05 * li, sr, sx, sy)
        return out, 14 * hit(li, 0, 14), 0.6 * hit(li, 0, 22)
    # 2x2 grid of favourites
    gl = lt - 2.0
    canvas = radial_bg((60, 38, 24), C.COCOA, 0.5, 0.45, 0.9)
    title_sz = fit_size(C.GRID_TITLE, SERIF, S * 0.075, W * 0.88, 600)
    tp = ease_out(prog(gl, 0.0, 0.5))
    if PORTRAIT:
        cell = W * 0.42
        gx0, gy0 = W / 2 - cell - W * 0.015, H * 0.5 - cell - W * 0.015 + S * 0.04
        title_y = gy0 - S * 0.12
    else:
        cell = H * 0.34
        gx0, gy0 = W / 2 - cell - H * 0.015, H * 0.52 - cell - H * 0.015
        title_y = gy0 - S * 0.08
    draw_line(canvas, C.GRID_TITLE, SERIF, title_sz, C.CREAM, W / 2, title_y + (1 - tp) * S * 0.05, wght=600, alpha=tp)
    gap = S * 0.03
    collapse = ease_in(prog(gl, 1.75, 2.0), 3)
    for k in range(4):
        r_, c_ = divmod(k, 2)
        cx = gx0 + c_ * (cell + gap) + cell / 2
        cy = gy0 + r_ * (cell + gap) + cell / 2
        cx, cy = lerp(cx, W / 2, collapse), lerp(cy, H / 2, collapse)
        p = prog(gl, 0.1 + k * 0.1, 0.6 + k * 0.1)
        e = ease_out_back(p, 1.8)
        if e <= 0:
            continue
        bg_c, fg = MONTAGE_STYLES[k]
        tile = tile_sprite(k, int(cell))
        place(canvas, tile, cx, cy, max(0.01, e) * (1 - collapse * 0.6), (1 - e) * 10, ay=0.5)
    zoom = lerp(1.08, 1.0, ease_out(prog(gl, 0, 1.8)))
    return camera(canvas, zoom, 0, 0, 0), 4 * hit(gl, 0, 10), 0.0


@lru_cache(maxsize=8)
def tile_sprite(k, cell):
    bg_c, fg = MONTAGE_STYLES[k]
    img, d, ss = ss_canvas(cell, 2)
    n = cell * ss
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=n * 0.08, fill=bg_c + (255,))
    img = ss_done(img, ss)
    ic = MONTAGE_ICONS[k](int(cell * 0.6))
    img.alpha_composite(ic, (int(cell / 2 - ic.size[0] / 2), int(cell * 0.42 - ic.size[1] / 2)))
    word = C.MONTAGE_WORDS[k]
    sz = fit_size(word, SANS_BOLD, cell * 0.13, cell * 0.85)
    spr = text_img(word, SANS_BOLD, int(sz), fg, 0.0)
    place(img, spr, cell / 2, cell * 0.85, 1.0)
    return img


# ----------------------------------------------------------------- 6 CTA
def scene_cta(t):
    lt = t - C.CTA[0]
    canvas = radial_bg((255, 214, 120), C.MARIGOLD, 0.5, 0.42, 0.9)
    k = 1.0 if PORTRAIT else 0.72
    cy_sun = H * (0.33 if PORTRAIT else 0.2)
    place(canvas, ray_sprite(), W / 2, cy_sun, max(W, H) * 1.5 / 1024, lt * 8, 0.5, ay=0.5)
    screen_add(canvas, glow_sprite(int(S * 0.45), (255, 230, 170), 0.2), W / 2, cy_sun, 0.7)
    dust(canvas, lt + 20, 50, (255, 248, 230), seed=12, alpha=160)
    p = ease_out_expo(prog(lt, 0, 0.5))
    bump = 1 + 0.06 * hit(t, 29.0, 6)
    isz = int(S * 0.24 * k)
    place(canvas, icon_sun(isz, C.DARK), W / 2, cy_sun, lerp(0.5, 1.0, p) * bump, lt * 12, alpha=p, ay=0.5)
    logo = int(S * 0.19 * k)
    ly = cy_sun + isz * 0.5 + logo * 0.75
    draw_line(canvas, C.BRAND, SERIF, logo, C.DARK, W / 2, ly, wght=650, scale=lerp(0.85, 1.0, p) * bump, alpha=p)
    if lt > 1.5 and lt < 2.2:
        sweep_logo(canvas, C.BRAND, logo, W / 2, ly, prog(lt, 1.5, 2.1))
    lp = ease_out(prog(lt, 0.6, 1.1))
    lsz = fit_size(C.CTA_LINE, SANS_MED, S * 0.05 * (1 if PORTRAIT else 0.85), W * 0.86)
    draw_line(canvas, C.CTA_LINE, SANS_MED, lsz, (92, 46, 18), W / 2, ly + logo * 0.75 + (1 - lp) * S * 0.03, alpha=lp)
    # button
    bp = prog(lt, 1.2, 1.7)
    if bp > 0:
        e = ease_out_back(bp, 2.2)
        beat_pulse = 1 + 0.035 * hit((lt - 1.7) % C.BEAT, 0, 9) if lt > 1.7 else 1
        btn = button_sprite(int(S * 0.6), int(S * 0.13))
        by = ly + logo * 0.75 + S * 0.18 * k
        place(canvas, btn, W / 2, by, e * beat_pulse, ay=0.5)
        sh = ((lt - 1.9) % 1.0) if lt > 1.9 else -1
        if 0 <= sh < 0.45:
            button_shine(canvas, W / 2, by, int(S * 0.6), int(S * 0.13), sh / 0.45, e * beat_pulse)
        up = ease_out(prog(lt, 1.6, 2.2))
        usz = S * 0.048
        uy = by + S * 0.15 * k
        draw_line(canvas, C.URL, SANS_SEMI, usz, C.DARK, W / 2, uy, tracking=0.04, alpha=up)
        uw = text_width(C.URL, SANS_SEMI, usz, 0.04)
        d = ImageDraw.Draw(canvas)
        lw_ = uw * ease_in_out(prog(lt, 1.8, 2.4))
        d.rectangle([W / 2 - uw / 2, uy + usz * 0.55, W / 2 - uw / 2 + lw_, uy + usz * 0.55 + max(2, S * 0.004)], fill=C.DARK + (255,))
    zoom = lerp(1.06, 1.0, ease_out(prog(lt, 0, 3))) + 0.02 * hit(t, 29.0, 4)
    sx, sy, sr = shake(t, 29.0, S * 0.012, 8, 7)
    out = camera(canvas, zoom, sr, sx, sy)
    flash = 0.9 * hit(t, C.CTA[0], 12) + 0.7 * hit(t, 29.0, 10)
    return out, 8 * hit(t, C.CTA[0], 10) + 6 * hit(t, 29.0, 10), flash


@lru_cache(maxsize=2)
def button_sprite(w, h):
    img, d, ss = ss_canvas(max(w, h), 3)
    img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=h * ss / 2, fill=C.DARK + (255,))
    img = img.resize((w, h), Image.LANCZOS)
    sz = h * 0.36
    tx = text_img(C.CTA_BUTTON + "  →", SANS_BOLD, int(sz), C.CREAM, 0.14)
    place(img, tx, w / 2, h / 2, 1.0)
    return img


def button_shine(canvas, cx, cy, w, h, p, scale):
    band = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    x = lerp(-w * 0.2, w * 1.2, p)
    d.polygon([(x, 0), (x + w * 0.08, 0), (x - w * 0.02, h), (x - w * 0.1, h)], fill=(255, 255, 255, 110))
    mask = button_sprite(w, h).getchannel("A")
    band.putalpha(ImageChops.multiply(band.getchannel("A"), mask))
    place(canvas, band.filter(ImageFilter.GaussianBlur(3)), cx, cy, scale, ay=0.5)


# ------------------------------------------------------------- post / main
def post(img, t, ca=0.0, flash=0.0, glitch=0.0, frame_idx=0):
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    if glitch > 0:
        rng = np.random.default_rng(frame_idx)
        for _ in range(9):
            y0 = rng.integers(0, H - 10)
            hgt = rng.integers(H // 60, H // 10)
            a[y0:y0 + hgt] = np.roll(a[y0:y0 + hgt], int(rng.normal(0, S * 0.05)), axis=1)
        if frame_idx % 5 == 0:
            a = 1 - a * 0.9
    if ca > 0.5:
        s = int(ca * S / 1080)
        a[..., 0] = np.roll(a[..., 0], s, axis=1)
        a[..., 2] = np.roll(a[..., 2], -s, axis=1)
    if flash > 0:
        a = a + (np.array([1.0, 0.97, 0.9], np.float32) - a) * min(1, flash)
    a *= STATIC["vignette"]
    g = STATIC["grain"][frame_idx % 4]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[:H, :W, None]
    a += g * 0.022
    # global fade-out on the last frames
    a *= 1 - ease_in(prog(t, C.DURATION - 0.35, C.DURATION), 2)
    return (np.clip(a, 0, 1) * 255).astype(np.uint8)


def render_frame(idx):
    t = idx / C.FPS
    glitch = 0.0
    if t < C.HOOK[1]:
        img, ca, glitch = scene_hook(t)
        flash = 0.0
    elif t < C.REVEAL[1]:
        lt = t - C.REVEAL[0]
        img = scene_reveal(lt)
        ca, flash = 12 * hit(lt, 0, 7), 0.9 * hit(lt, 0, 9)
    elif t < C.FEATURES_T[1]:
        img, ca, flash = scene_features(t)
    elif t < C.FIELD[1]:
        img, ca, flash = scene_field(t)
    elif t < C.MONTAGE[1]:
        img, ca, flash = scene_montage(t)
    else:
        img, ca, flash = scene_cta(t)
    return post(img, t, ca, flash, glitch, idx)


def _init(fmt):
    setup(fmt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", default="vertical", choices=list(C.FORMATS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--still", type=float, default=None)
    ap.add_argument("--sheet", default=None, help="contact sheet of one frame per 0.5 s")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=C.DURATION)
    args = ap.parse_args()
    setup(args.format)

    if args.still is not None:
        Image.fromarray(render_frame(int(round(args.still * C.FPS)))).save(args.out or "out/still.png")
        return
    if args.sheet:
        times = np.arange(0.25, C.DURATION, 0.75)
        with Pool(args.jobs, _init, (args.format,)) as pool:
            frames = pool.map(render_frame, [int(x * C.FPS) for x in times])
        cols = 8
        tw_ = 270 if PORTRAIT else 360
        th_ = int(tw_ * H / W)
        rows = math.ceil(len(frames) / cols)
        sheet = Image.new("RGB", (cols * tw_, rows * (th_ + 22)), (30, 30, 30))
        dd = ImageDraw.Draw(sheet)
        for k, (f, tm) in enumerate(zip(frames, times)):
            r, c = divmod(k, cols)
            sheet.paste(Image.fromarray(f).resize((tw_, th_), Image.LANCZOS), (c * tw_, r * (th_ + 22) + 22))
            dd.text((c * tw_ + 6, r * (th_ + 22) + 4), f"{tm:.2f}s", fill=(255, 255, 255))
        sheet.save(args.sheet)
        return

    out = args.out or f"out/{args.format}_video.mp4"
    n0, n1 = int(args.start * C.FPS), int(args.end * C.FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(C.FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-tune", "film",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(args.jobs, _init, (args.format,)) as pool:
        for k, fr in enumerate(pool.imap(render_frame, range(n0, n1), chunksize=2)):
            enc.stdin.write(fr.tobytes())
            if k % 60 == 0:
                print(f"  {args.format}: {k + n0}/{n1}", file=sys.stderr, flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
