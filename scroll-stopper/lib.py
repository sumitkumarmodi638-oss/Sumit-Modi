"""Drawing toolkit for the vertical (1080x1920) Reel: easing, compositing,
type, UI primitives and camera effects. Frames are float32 RGB in [0, 1]."""
import math
import os
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "marketing-video", "build")  # fonts + logo cut by prepare.py

PURPLE = (0x6D, 0x28, 0xD9)
LIME = (0xD4, 0xF5, 0x5A)
MIDNIGHT = (0x12, 0x0B, 0x26)
INK = (0x1C, 0x18, 0x30)
LAVENDER = (0xA7, 0x8B, 0xFA)
CLOUD = (0xF7, 0xF5, 0xFC)
WHITE = (255, 255, 255)
GREY = (120, 116, 132)


def C(c):
    return np.array(c[:3], np.float32) / 255.0


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, t0, dur):
    return clamp((t - t0) / dur)


def lerp(a, b, p):
    return a + (b - a) * p


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


# ---------------------------------------------------------------- canvases
@lru_cache(None)
def _radial(c_in, c_out, cx, cy, r, w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx / w - cx) * w / h) ** 2 + (yy / h - cy) ** 2) / r
    k = np.clip(d, 0, 1)[..., None] ** 1.3
    return C(c_in) * (1 - k) + C(c_out) * k


def bg(c_in, c_out=None, cx=0.5, cy=0.42, r=0.75, size=(W, H)):
    return _radial(c_in, c_out or c_in, cx, cy, r, size[0], size[1]).copy()


@lru_cache(None)
def _dots():
    m = np.zeros((H + 60, W), np.float32)
    for y in range(0, H + 60, 60):
        for x in range(30, W, 60):
            cv2.circle(m, (x, y), 2, 1.0, -1, cv2.LINE_AA)
    return m


def dot_grid(f, t, color=LAVENDER, a=0.12, speed=20):
    oy = int(t * speed) % 60
    m = _dots()[oy:oy + H][..., None] * a
    return f * (1 - m) + C(color) * m


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return (1 - 0.3 * np.clip(d - 0.5, 0, 1) ** 1.4)[..., None]


@lru_cache(None)
def grain_bank():
    rng = np.random.default_rng(3)
    return [cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.7)[..., None]
            for _ in range(6)]


# ---------------------------------------------------------------- compositing
def blit(dst, src, x, y, alpha=1.0, mask=None):
    """Composite premultiplied RGBA `src` with its top-left at (x, y)."""
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
    if d.shape[2] == 4:
        d[..., 3:] += a
    if mask is not None:
        np.maximum(mask[y0:y1, x0:x1], a[..., 0], out=mask[y0:y1, x0:x1])


def blit_c(dst, src, cx, cy, scale=1.0, alpha=1.0, rot=0.0, mask=None):
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


def opaque(f):
    return np.dstack([f, np.ones(f.shape[:2] + (1,), np.float32)])


def flash(f, color, a):
    if a > 0:
        f += (C(color) - f) * a
    return f


def zoom(f, z, cx, cy):
    if abs(z - 1) < 1e-4:
        return f
    M = np.float32([[z, 0, cx - cx * z], [0, z, cy - cy * z]])
    return cv2.warpAffine(f, M, (f.shape[1], f.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def zoom_blur(f, amount, cx=W / 2, cy=H / 2, n=6):
    if amount < 0.004:
        return f
    acc = f.copy()
    for k in range(1, n):
        acc += zoom(f, 1 + amount * k / (n - 1), cx, cy)
    return acc / n


def vblur(f, px):
    """Vertical motion blur of `px` pixels (fast scrolling)."""
    px = int(px)
    if px < 2:
        return f
    return cv2.blur(f, (1, px))


def shake(f, amp, t, seed=0):
    if amp < 0.5:
        return f
    rng = np.random.default_rng(int(t * FPS) * 31 + seed)
    dx, dy = rng.uniform(-amp, amp, 2)
    z = 1 + 2.4 * amp / W
    M = np.float32([[z, 0, W / 2 - W / 2 * z + dx], [0, z, H / 2 - H / 2 * z + dy]])
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def glitch(f, t, strength, seed=0):
    if strength <= 0:
        return f
    rng = np.random.default_rng(int(t * FPS) * 7 + seed)
    out = f.copy()
    for _ in range(int(6 + 12 * strength)):
        y0 = rng.integers(0, H - 10)
        hh = int(rng.integers(6, 120))
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(rng.integers(-140, 140) * strength), axis=1)
    sh = int(16 * strength)
    out[..., 0] = np.roll(out[..., 0], sh, axis=1)
    out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    return out


def add_glow(f, mask, color, strength, sigma=28):
    small = cv2.resize(mask, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / 4)
    g = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return f + g * C(color) * strength


def light_sweep(f, mask, p, width=80, strength=0.85):
    if not 0 < p < 1:
        return f
    pos = lerp(-600, W + 600, ease_in_out(p))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    band = np.exp(-(((xx + (yy - H / 2) * 0.45) - pos) / width) ** 2)
    return f + (band * mask)[..., None] * strength


def ripple(f, cx, cy, p, color=WHITE, rmax=160):
    """Tap ripple: expanding ring + filled dot."""
    if not 0 < p < 1:
        return f
    ov = np.zeros(f.shape[:2], np.float32)
    cv2.circle(ov, (int(cx), int(cy)), int(20 + rmax * ease_out_expo(p)), 1.0, max(1, int(10 * (1 - p))), cv2.LINE_AA)
    cv2.circle(ov, (int(cx), int(cy)), int(34 * (1 - p)), 0.6, -1, cv2.LINE_AA)
    a = ov[..., None] * (1 - p)
    return f * (1 - a) + C(color) * a


# ---------------------------------------------------------------- type
@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(os.path.join(ASSETS, "fonts", name + ".ttf"), size)


@lru_cache(None)
def text_rgba(text, fname, size, color, tracking=0):
    f = font(fname, size)
    asc, desc = f.getmetrics()
    width = (sum(f.getlength(ch) for ch in text) + tracking * (len(text) - 1)) if tracking else f.getlength(text)
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
    return rgba_from_alpha(np.asarray(img, np.float32) / 255.0, color), pad, width


class Text:
    """Laid-out text; *starred* segments take the accent colour."""

    def __init__(self, lines, fname="Sora-800", size=100, color=WHITE, accent=LIME,
                 lh=1.08, align="left", tracking=0):
        self.size, self.words, self.width = size, [], 0
        space = font(fname, size).getlength(" ") + tracking
        y = 0
        for li, line in enumerate(lines):
            row, x = [], 0
            # "*...*" spans (may cover several words) take the accent colour
            tokens, acc = [], False
            for k, part in enumerate(line.split("*")):
                acc = k % 2 == 1
                for j, word in enumerate(part.split(" ")):
                    if j:
                        tokens.append(None)  # a space
                    if word:
                        tokens.append((word, acc))
            for tok in tokens:
                if tok is None:
                    x += space
                    continue
                word, acc = tok
                rgba, pad, ww = text_rgba(word, fname, size, accent if acc else color, tracking)
                row.append([x, y, rgba, pad, li, ww])
                x += ww
            x += space
            lw = x - space
            self.width = max(self.width, lw)
            if align != "left":
                for r in row:
                    r[0] -= lw / 2 if align == "center" else lw
            self.words += row
            y += size * lh
        self.height = y

    def draw(self, dst, ox, oy, t, t0=0.0, stagger=0.06, dur=0.4, style="rise", alpha=1.0, mask=None):
        for i, (x, y, rgba, pad, li, ww) in enumerate(self.words):
            p = prog(t, t0 + i * stagger, dur)
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


def eyebrow(dst, text, x, y, t, t0, color=LIME, size=30, align="center", alpha=1.0):
    Text([text], "DMSans-700", size, color, color, tracking=6, align=align).draw(
        dst, x, y, t, t0, stagger=0, dur=0.5, style="fade", alpha=alpha)


def label(dst, text, x, y, size=34, color=WHITE, fname="DMSans-500", alpha=1.0, align="left"):
    rgba, pad, ww = text_rgba(text, fname, size, color)
    if align == "center":
        x -= ww / 2
    elif align == "right":
        x -= ww
    blit(dst, rgba, x - pad, y - pad, alpha)
    return ww


# ---------------------------------------------------------------- UI shapes
@lru_cache(maxsize=1024)
def rrect(w, h, r, fill, border=None, bw=3):
    """Rounded rectangle as premultiplied RGBA (fill/border are RGB or RGBA tuples)."""
    s = 3
    w, h = max(int(w), 2), max(int(h), 2)
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fill = tuple(fill) + ((255,) if len(fill) == 3 else ())
    if border is not None:
        border = tuple(border) + ((255,) if len(border) == 3 else ())
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=min(r, h / 2, w / 2) * s, fill=fill,
                        outline=border, width=bw * s if border else 0)
    a = np.asarray(img.resize((w, h), Image.LANCZOS), np.float32) / 255.0
    return np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]])


def card(dst, x, y, w, h, r, fill, alpha=1.0, border=None, bw=3):
    blit(dst, rrect(int(w), int(h), int(r), tuple(fill), border, bw), x, y, alpha)


@lru_cache(None)
def round_mask(w, h, r):
    return rrect(w, h, r, (255, 255, 255))[..., 3:4]


def circle(dst, cx, cy, r, color, alpha=1.0, thickness=-1):
    ov = np.zeros(dst.shape[:2], np.float32)
    cv2.circle(ov, (int(cx), int(cy)), int(r), 1.0, thickness, cv2.LINE_AA)
    a = ov[..., None] * alpha
    dst *= 1 - a
    dst += C(color) * a


def poly(dst, pts, color, alpha=1.0, closed=True, thickness=-1):
    ov = np.zeros(dst.shape[:2], np.float32)
    pts = np.int32(np.round(pts))
    if thickness < 0:
        cv2.fillPoly(ov, [pts], 1.0, cv2.LINE_AA)
    else:
        cv2.polylines(ov, [pts], closed, 1.0, thickness, cv2.LINE_AA)
    a = ov[..., None] * alpha
    dst *= 1 - a
    dst += C(color) * a


def star(cx, cy, r):
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    return pts


def check(dst, cx, cy, s, color, p=1.0, thickness=8):
    """Tick mark drawn on with progress p."""
    a, b, c = (cx - s, cy), (cx - s * 0.3, cy + s * 0.7), (cx + s, cy - s * 0.8)
    if p <= 0:
        return
    if p < 0.4:
        q = p / 0.4
        poly(dst, [a, (lerp(a[0], b[0], q), lerp(a[1], b[1], q))], color, closed=False, thickness=thickness)
    else:
        q = (p - 0.4) / 0.6
        poly(dst, [a, b, (lerp(b[0], c[0], q), lerp(b[1], c[1], q))], color, closed=False, thickness=thickness)


# ---------------------------------------------------------------- logo
@lru_cache(None)
def logo_meta():
    import json
    m = json.load(open(os.path.join(ASSETS, "logo", "logo.json")))
    pieces = [m["design"], m["tech"], m["growth"]] + m["letters"]
    xs = [p["x"] for p in pieces] + [p["x"] + p["w"] for p in pieces]
    ys = [p["y"] for p in pieces] + [p["y"] + p["h"] for p in pieces]
    m["center"] = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    m["width"] = max(xs) - min(xs)
    m["pieces"] = pieces
    return m


@lru_cache(maxsize=256)
def piece_rgba(name, scale, color):
    a = cv2.imread(os.path.join(ASSETS, "logo", name + ".png"), 0).astype(np.float32) / 255.0
    a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return rgba_from_alpha(a, color)


def draw_logo(dst, cx, cy, width, mark=LIME, word=LIME, alpha=1.0, mask=None, t=None, t0=0.0):
    """Full lockup; with t given, pieces pop in one after another from t0."""
    m = logo_meta()
    s = round(width / m["width"], 3)
    for i, p in enumerate(m["pieces"]):
        sc, a, dy = 1.0, alpha, 0.0
        if t is not None:
            q = prog(t, t0 + i * 0.04, 0.35)
            if q <= 0:
                continue
            e = ease_out_back(q, 2.2)
            sc, a, dy = 0.5 + 0.5 * e, alpha * min(1, q * 3), (1 - e) * 50
        rgba = piece_rgba(p["name"], s, mark if i < 3 else word)
        blit_c(dst, rgba, cx + (p["x"] + p["w"] / 2 - m["center"][0]) * s,
               cy + (p["y"] + p["h"] / 2 - m["center"][1]) * s + dy, sc, a, mask=mask)
