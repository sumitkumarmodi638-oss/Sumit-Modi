"""Render the picture for "The Scroll Stopper" (1080x1920 vertical Reel).

Usage:
  python3 video.py                  # full render -> build/picture.mp4
  python3 video.py --stills 1 9.8   # preview frames -> build/stills/
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np

from lib import *  # noqa: F401,F403  (drawing toolkit + palette)
from lib import FPS, H, W
from timeline import BEAT, DURATION, SCENES, VIGNETTES

BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
CREAM = (245, 230, 200)
CRUST = (196, 132, 64)
DIM = (60, 56, 76)

# ================================================================ hook
def sc_hook_timer(t, lt):
    f = bg((34, 22, 70), MIDNIGHT, r=0.7)
    f = dot_grid(f, t, a=0.08)
    Text(["This video has"], "Sora-700", 84, CLOUD, align="center").draw(f, W / 2, 380, lt, 0.05, 0.08, 0.35, "pop")
    cx, cy, r = W // 2, 920, 270
    p_ring = ease_out_back(prog(lt, 0.2, 0.4))
    remain = 2.0 * (1 - prog(lt, 0.5, 2.0))
    if p_ring > 0:
        ov = np.zeros((H, W), np.float32)
        cv2.circle(ov, (cx, cy), int(r * p_ring), 1.0, 22, cv2.LINE_AA)
        f = f * (1 - ov[..., None] * 0.6) + C(DIM) * ov[..., None] * 0.6
        ov[:] = 0
        sweep = 360 * remain / 2.0
        if sweep > 0.5:
            cv2.ellipse(ov, (cx, cy), (int(r * p_ring), int(r * p_ring)), -90, 0, -sweep, 1.0, 22, cv2.LINE_AA)
        urgent = remain < 0.6 and int(lt * 8) % 2 == 0
        col = WHITE if urgent else LIME
        f = f * (1 - ov[..., None]) + C(col) * ov[..., None]
        f = add_glow(f, ov, col, 0.5, 30)
        num = text_rgba(f"{remain:.2f}", "Sora-800", 170, WHITE)[0]
        blit_c(f, num, cx, cy - 20, 0.6 + 0.4 * p_ring, min(1, p_ring * 2))
        label(f, "SECONDS", cx, cy + 90, 30, LAVENDER, "DMSans-700", min(1, p_ring), align="center")
    Text(["to stop your *thumb.*"], "Sora-800", 96, align="center").draw(f, W / 2, 1300, lt, 1.0, 0.1, 0.3, "pop")
    k = lt - 2.5
    if k >= 0:
        f = flash(f, LIME, 0.6 * (1 - prog(k, 0, 0.2)))
        f = glitch(f, t, 1 - prog(k, 0, 0.3), 1)
        f = shake(f, 26 * (1 - prog(k, 0, 0.4)), t, 2)
    return f


def sc_so_does(t, lt):
    f = bg(LIME, (190, 225, 70), r=0.9)
    Text(["So does your"], "Sora-800", 118, INK, PURPLE, align="center").draw(f, W / 2, 760, lt, 0.0, 0.08, 0.2, "slam")
    Text(["*business.*"], "Sora-800", 170, INK, PURPLE, align="center").draw(f, W / 2, 900, lt, 0.4, 0, 0.2, "slam")
    since = lt if lt < 0.4 else lt - 0.4
    f = flash(f, WHITE, 0.8 * (1 - prog(lt, 0, 0.2)))
    return shake(f, 18 * (1 - prog(since, 0, 0.25)), t, 3)


# ================================================================ feed
PHONE = (190, 430, 700, 1400)            # device x, y, w, h
SCREEN = (214, 454, 652, 1352)           # screen inside the device
POST_H = 760
POSTS = [
    ("SALE 50% OFF!!!", (196, 188, 176), "bestdeals_shop"),
    ("Happy Monday :)", (172, 180, 190), "cityfashion"),
    ("We are the best in town", (190, 184, 168), "royal.sweets"),
    ("New arrivals", (176, 174, 182), "trendz_store"),
    ("Call now!!", (188, 176, 176), "quick.repairs"),
    ("Good morning", (180, 186, 176), "fitzone_gym"),
    ("Best prices guaranteed", (190, 182, 172), "mega.mart"),
    ("Visit us today", (176, 180, 188), "dr.smile.clinic"),
]
STOP_INDEX = len(POSTS)
SCROLL_END = STOP_INDEX * POST_H + POST_H / 2 - SCREEN[3] / 2 + 40


def post_header(strip, y, handle, avatar):
    circle(strip, 52, y + 46, 28, avatar)
    label(strip, handle, 96, y + 26, 28, (60, 58, 66) if avatar != LIME else WHITE, "DMSans-700")
    label(strip, "Sponsored", 96, y + 58, 22, (130, 128, 136) if avatar != LIME else LAVENDER)


@lru_cache(None)
def feed_strip():
    sw = SCREEN[2]
    strip = np.ones(((len(POSTS) + 2) * POST_H, sw, 3), np.float32) * C((236, 234, 238))
    for i, (txt, col, handle) in enumerate(POSTS):
        y = i * POST_H
        post_header(strip, y, handle, (150, 146, 156))
        strip[y + 96:y + 96 + 540] = C(col)
        Text([txt], "DMSans-500", 46, (96, 94, 102), align="center").draw(strip, sw / 2, y + 96 + 240, 1, 0, 0, 0.01)
        for k in range(3):
            circle(strip, 44 + k * 64, y + 680, 18, (150, 146, 156), thickness=4)
        card(strip, 30, y + 716, 380, 18, 9, (200, 198, 206))
    # the one post worth stopping for
    y = STOP_INDEX * POST_H
    strip[y:y + POST_H] = C(MIDNIGHT)
    post_header(strip, y, "varniklabs", LIME)
    block = bg(PURPLE, (70, 20, 160), r=0.9, size=(sw, 540))
    strip[y + 96:y + 636] = block
    Text(["Stop", "scrolling."], "Sora-800", 92, WHITE, align="center").draw(strip, sw / 2, y + 160, 1, 0, 0, 0.01)
    Text(["*Start growing.*"], "Sora-800", 64, align="center").draw(strip, sw / 2, y + 400, 1, 0, 0, 0.01)
    card(strip, sw / 2 - 150, y + 520, 300, 70, 35, LIME)
    label(strip, "Learn more", sw / 2, y + 535, 30, INK, "DMSans-700", align="center")
    for k in range(3):
        circle(strip, 44 + k * 64, y + 680, 18, LIME if k == 0 else LAVENDER, thickness=-1 if k == 0 else 4)
    label(strip, "Liked by 2,418 people", 30, y + 706, 26, CLOUD, "DMSans-700")
    return strip


def scroll_pos(t):
    """Feed offset in px: flick-scroll that accelerates, then brakes onto the stopper post."""
    p = prog(t, 5.0, 5.0)
    off = SCROLL_END * (0.5 * ease_in_out(p) + 0.5 * ease_out_cubic(p) ** 1.0 * p)
    if t > 10.0:
        k = t - 10.0
        off = SCROLL_END + 36 * math.exp(-k * 9) * math.sin(k * 30)
    return off


def phone_frame(t, scale=1.0):
    """Full-frame layer with the phone and its scrolled screen."""
    x, y, w, h = PHONE
    sx, sy, sw, sh = SCREEN
    lay = np.zeros((H, W, 4), np.float32)
    blit(lay, rrect(w, h, 92, (16, 14, 26), (70, 64, 96), 4), x, y)
    off = scroll_pos(t)
    speed = abs(scroll_pos(t + 1 / FPS) - off) * FPS
    strip = feed_strip()
    o = int(clamp(off, 0, strip.shape[0] - sh))
    screen = strip[o:o + sh].copy()
    screen = vblur(screen, min(speed / FPS * 0.9, 220))
    # status bar
    screen[:54] = screen[:54] * 0.15 + C((250, 250, 252)) * 0.85
    label(screen, "9:41", 36, 12, 26, INK, "DMSans-700")
    card(screen, sw - 92, 18, 56, 22, 6, INK)
    m = round_mask(sw, sh, 64)
    blit(lay, np.dstack([screen * m, m]), sx, sy)
    card(lay, x + w / 2 - 80, y + 34, 160, 34, 17, (8, 8, 12))  # camera island
    return lay


def thumb(f, t):
    """Flick gesture: a translucent thumb-dot swiping up every beat."""
    if not 5.0 <= t < 9.8:
        return f
    k = ((t - 5.0) % BEAT) / BEAT
    y = lerp(1600, 1100, ease_out_cubic(k))
    circle(f, 640, y, 46, WHITE, 0.25 * (1 - k))
    return f


def sc_feed(t, lt):
    f = bg((30, 22, 56), MIDNIGHT, r=0.8)
    f = dot_grid(f, t, a=0.06)
    rise = ease_out_expo(prog(lt, 0, 0.5))
    lay = phone_frame(t)
    blit(f, lay, 0, (1 - rise) * 1300)
    f = thumb(f, t)
    # captions above the phone
    if lt < 3.75:
        n = 1 if lt < 2.0 else 2 if lt < 3.0 else 3
        txt = Text(["  ".join(["Scroll."] * n)], "Sora-800", 74 if n < 3 else 66, CLOUD, align="center")
        txt.draw(f, W / 2, 230, lt, 1.0 if n == 1 else 1.0 + (n - 1), 0.0, 0.2, "pop")
    elif lt < 5.5:
        Text(["Every post fights for", "the *same thumb.*"], "Sora-800", 68, align="center").draw(
            f, W / 2, 170, lt, 3.75, 0.05, 0.35)
    else:
        Text(["*STOP.*"], "Sora-800", 150, align="center").draw(f, W / 2, 175, lt, 5.5, 0, 0.18, "slam")
        f = flash(f, WHITE, 0.5 * (1 - prog(lt, 5.5, 0.2)))
        f = shake(f, 22 * (1 - prog(lt, 5.5, 0.3)), t, 4)
    return f


def sc_zoom_post(t, lt):
    base = sc_feed(10.49, 5.99)
    cy = SCREEN[1] + SCREEN[3] / 2 - 40
    p = ease_in_cubic(prog(lt, 0, 0.5))
    if lt < 0.5:
        f = zoom(base, 1 + 3.2 * p, W / 2, cy)
        return zoom_blur(f, 0.25 * p, W / 2, cy)
    f = bg(PURPLE, (70, 20, 160), r=0.9)
    f = dot_grid(f, t, a=0.1)
    Text(["That's what", "we build:"], "Sora-700", 92, CLOUD, align="center").draw(f, W / 2, 600, lt, 0.5, 0.07, 0.35)
    Text(["things people", "*stop* for."], "Sora-800", 128, align="center").draw(f, W / 2, 900, lt, 1.1, 0.08, 0.3, "pop")
    f = flash(f, WHITE, 0.7 * (1 - prog(lt, 0.5, 0.25)))
    return zoom_blur(f, 0.12 * (1 - ease_out_expo(prog(lt, 0.5, 0.3))))


# ================================================================ the five stops
def vignette_bg(t, tag, headline):
    def draw(lt):
        f = bg((32, 22, 64), MIDNIGHT, r=0.8)
        f = dot_grid(f, t, a=0.09)
        eyebrow(f, tag, W / 2, 190, lt, 0.05)
        Text(headline, "Sora-800", 88, align="center").draw(f, W / 2, 245, lt, 0.1, 0.05, 0.4)
        label(f, "Demo client: Golden Crust Bakery", W / 2, 1760, 28, LAVENDER, "DMSans-500",
              alpha=ease_out_cubic(prog(lt, 0.6, 0.5)), align="center")
        return f
    return draw


def sc_brand(t, lt):
    f = vignette_bg(t, "STOP 01  ·  BRAND", ["A face they", "*remember.*"])(lt)
    cx, cy = W / 2, 880
    merge = ease_in_out(prog(lt, 0.7, 0.25))
    shapes = [  # (from, color, kind)
        ((-400, -200), LIME, "circle"), ((420, 80), PURPLE, "square"), ((0, 600), LAVENDER, "tri")]
    if merge < 1:
        for i, ((ox, oy), col, kind) in enumerate(shapes):
            q = ease_out_expo(prog(lt, 0.2 + i * 0.1, 0.45))
            if q <= 0:
                continue
            home = [(-170, -40), (170, -40), (0, 150)][i]
            x = cx + lerp(ox, home[0], q) * (1 - merge)
            y = cy + lerp(oy, home[1], q) * (1 - merge)
            s = 110 * (1 - 0.6 * merge)
            rot = (1 - q) * 160 + lt * 40
            if kind == "circle":
                circle(f, x, y, s, col, min(1, q * 2))
            else:
                n = 4 if kind == "square" else 3
                pts = [(x + s * 1.1 * math.cos(math.radians(rot + 90 + k * 360 / n)),
                        y + s * 1.1 * math.sin(math.radians(rot + 90 + k * 360 / n))) for k in range(n)]
                poly(f, pts, col, min(1, q * 2))
    mask = np.zeros((H, W), np.float32)
    k = lt - 0.9
    if k >= 0:
        e = ease_out_back(prog(k, 0, 0.4), 2.4)
        r = 230 * e
        blit_c(f, rrect(int(2 * r) + 2, int(2 * r) + 2, int(r) + 1, PURPLE, LIME, 10), cx, cy, mask=mask)
        Text(["GC"], "Sora-800", 170, LIME, align="center").draw(f, cx, cy - 115, lt, 0.95, 0, 0.3, "pop", mask=mask)
        ring = prog(k, 0, 0.5)
        if ring < 1:
            circle(f, cx, cy, 240 + 260 * ease_out_expo(ring), LIME, 1 - ring, thickness=max(1, int(14 * (1 - ring))))
        f = add_glow(f, mask, LIME, 0.3, 30)
        Text(["Golden Crust"], "Sora-800", 92, WHITE, align="center").draw(f, W / 2, 1160, lt, 1.0, 0.08)
        eyebrow(f, "ARTISAN BAKERY  ·  SINCE TODAY", W / 2, 1290, lt, 1.2, color=LAVENDER, size=26)
        for i, col in enumerate((PURPLE, LIME, CREAM, INK)):
            q = prog(lt, 1.9 + i * 0.1, 0.35)
            if q > 0:
                x = W / 2 + (i - 1.5) * 150
                circle(f, x, 1470, 56 * ease_out_back(q), (90, 80, 120), min(1, q * 3))
                circle(f, x, 1470, 50 * ease_out_back(q), col, min(1, q * 3))
        f = light_sweep(f, mask, prog(lt, 1.4, 0.7))
    return f


def sc_website(t, lt):
    f = vignette_bg(t, "STOP 02  ·  WEBSITE", ["A site that makes", "the *phone ring.*"])(lt)
    x0, y0, w, h = 210, 540, 660, 1080
    card(f, x0, y0, w, h, 44, (250, 248, 252), ease_out_cubic(prog(lt, 0.0, 0.3)))
    blocks = [  # x, y, w, h (relative), fill
        (30, 30, 600, 70, (255, 255, 255)), (30, 120, 600, 430, CREAM), (30, 570, 290, 250, (240, 236, 244)),
        (340, 570, 290, 250, (240, 236, 244)), (30, 850, 600, 110, LIME), (30, 980, 600, 60, (240, 236, 244))]
    fill = ease_out_cubic(prog(lt, 0.9, 0.4))
    for i, (bx, by, bw, bh, col) in enumerate(blocks):
        q = prog(lt, 0.1 + i * 0.12, 0.25)
        if q <= 0:
            continue
        blit_c(f, rrect(bw, bh, 22, (0, 0, 0, 0), PURPLE, 3), x0 + bx + bw / 2, y0 + by + bh / 2,
               0.9 + 0.1 * ease_out_back(q), min(1, q * 3) * (1 - fill))
        if fill > 0:
            card(f, x0 + bx, y0 + by, bw, bh, 22, col, fill)
    if fill > 0:
        a = fill
        label(f, "Golden Crust", x0 + 56, y0 + 50, 30, INK, "Sora-700", a)
        for k in range(3):
            f[y0 + 52 + k * 12:y0 + 56 + k * 12, x0 + 570:x0 + 604] = C(INK) * a + f[y0 + 52 + k * 12:y0 + 56 + k * 12, x0 + 570:x0 + 604] * (1 - a)
        Text(["Fresh bread,", "every morning."], "Sora-800", 56, INK, PURPLE).draw(f, x0 + 60, y0 + 160, lt, 0.95, 0.04, 0.3, alpha=a)
        # loaf illustration
        ov = np.zeros((H, W), np.float32)
        cv2.ellipse(ov, (x0 + 330, y0 + 440), (190, 80), 0, 180, 360, 1.0, -1, cv2.LINE_AA)
        cv2.rectangle(ov, (x0 + 140, y0 + 440), (x0 + 520, y0 + 500), 1.0, -1)
        f = f * (1 - ov[..., None] * a) + C(CRUST) * ov[..., None] * a
        for k in range(3):
            poly(f, [(x0 + 250 + k * 80, y0 + 400), (x0 + 290 + k * 80, y0 + 450)], (240, 200, 140), a, False, 8)
        for k, name in enumerate(("Sourdough", "Croissant")):
            bx = x0 + 30 + k * 310
            circle(f, bx + 145, y0 + 670, 62, CRUST if k == 0 else (230, 170, 80), a)
            label(f, name, bx + 145, y0 + 755, 30, INK, "DMSans-700", a, align="center")
        label(f, "Order now", x0 + w / 2, y0 + 880, 44, INK, "Sora-700", a, align="center")
        label(f, "Open 7am - 9pm  ·  Free delivery", x0 + w / 2, y0 + 990, 26, (110, 104, 124), "DMSans-500", a, align="center")
    tap = prog(lt, 2.2, 0.5)
    f = ripple(f, x0 + w / 2, y0 + 905, tap, PURPLE, 200)
    if lt > 2.2:
        circle(f, x0 + w / 2 + 30, y0 + 930, 40, WHITE, 0.35 * (1 - tap))
    q = ease_out_back(prog(lt, 2.5, 0.4))
    if q > 0:
        ty = lerp(y0 - 140, y0 + 40, q)
        card(f, x0 + 40, ty, w - 80, 120, 30, INK, min(1, q * 2), border=LIME, bw=3)
        circle(f, x0 + 110, ty + 60, 34, LIME, min(1, q * 2))
        check(f, x0 + 110, ty + 62, 16, INK, prog(lt, 2.7, 0.3), 7)
        label(f, "New order received", x0 + 170, ty + 26, 34, WHITE, "Sora-700", min(1, q * 2))
        label(f, "1x Chocolate cake  ·  just now", x0 + 170, ty + 70, 24, LAVENDER, "DMSans-500", min(1, q * 2))
    return f


CHAT = [  # (time, side, lines)
    (0.3, "in", ["Hi! Can I order a birthday", "cake for tomorrow?"]),
    (1.3, "out", ["Yes! Chocolate or vanilla?", "I've held a 10 AM pickup", "slot for you."]),
    (2.0, "in", ["Chocolate please!"]),
    (2.4, "out", ["Done. See you at 10!"]),
]


def sc_chat(t, lt):
    f = vignette_bg(t, "STOP 03  ·  AUTOMATION", ["Answers at 2 a.m.", "*You sleep.*"])(lt)
    x0, y0, w, h = 110, 540, 860, 1100
    card(f, x0, y0, w, h, 44, (26, 22, 44), border=(60, 52, 96), bw=3)
    f[y0 + 2:y0 + 130, x0 + 40:x0 + w - 40] = f[y0 + 2:y0 + 130, x0 + 40:x0 + w - 40]
    circle(f, x0 + 80, y0 + 66, 40, LIME)
    label(f, "GC", x0 + 80, y0 + 46, 30, INK, "Sora-800", align="center")
    label(f, "Golden Crust Bakery", x0 + 140, y0 + 30, 34, WHITE, "Sora-700")
    label(f, "Auto-reply  ·  online", x0 + 140, y0 + 76, 24, LIME, "DMSans-500")
    # 2:07 AM with a moon
    circle(f, x0 + w - 200, y0 + 66, 20, LAVENDER)
    circle(f, x0 + w - 190, y0 + 58, 18, (26, 22, 44))
    label(f, "2:07 AM", x0 + w - 165, y0 + 48, 30, CLOUD, "DMSans-700")
    f[y0 + 130:y0 + 132, x0:x0 + w] = C((60, 52, 96))
    y = y0 + 170
    for i, (t0, side, lines) in enumerate(CHAT):
        if side == "out" and t0 - 0.5 <= lt < t0 and i == 1:  # typing dots
            card(f, x0 + w - 200, y, 160, 80, 40, PURPLE)
            for k in range(3):
                bob = math.sin((lt * 10) - k * 0.9) * 8
                circle(f, x0 + w - 160 + k * 40, y + 40 + bob, 10, CLOUD)
        q = prog(lt, t0, 0.35)
        if q <= 0:
            continue
        lh = 46
        bw = max(text_rgba(s, "DMSans-500", 34, WHITE)[2] for s in lines) + 60
        bh = len(lines) * lh + 40
        e = ease_out_back(q, 2.0)
        bx = x0 + 40 if side == "in" else x0 + w - 40 - bw
        bub = np.zeros((int(bh), int(bw), 4), np.float32)
        blit(bub, rrect(bw, bh, 30, (240, 238, 246) if side == "in" else PURPLE), 0, 0)
        for k, s in enumerate(lines):
            blit(bub, text_rgba(s, "DMSans-500", 34, INK if side == "in" else WHITE)[0], 22, 14 + k * lh)
        blit_c(f, bub, bx + bw / 2, y + bh / 2 + (1 - e) * 30, 0.6 + 0.4 * e, min(1, q * 3))
        if i == 3:
            circle(f, bx + bw + 0 - 0, y + bh + 26, 0, LIME)
            check(f, bx + bw - 40, y + bh + 30, 14, LIME, prog(lt, 2.6, 0.3), 6)
            label(f, "Order confirmed", bx + bw - 70, y + bh + 14, 24, LIME, "DMSans-700", min(1, prog(lt, 2.6, 0.3) * 2), align="right")
        y += bh + 34
    return f


RESULTS = ["Sunrise Bakes", "City Bread House", "The Muffin Corner", "Golden Crust Bakery", "Daily Loaf"]
RATINGS = ["4.1", "3.9", "4.0", "4.9", "3.8"]


def sc_search(t, lt):
    f = vignette_bg(t, "STOP 04  ·  SEARCH", ["Found", "*first.*"])(lt)
    x0, w = 110, 860
    card(f, x0, 560, w, 110, 55, WHITE)
    circle(f, x0 + 70, 605, 22, GREY, thickness=6)
    poly(f, [(x0 + 86, 621), (x0 + 104, 640)], GREY, closed=False, thickness=7)
    q = "bakery near me"
    n = int(clamp((lt - 0.2) / 0.055, 0, len(q)))
    if n:
        label(f, q[:n], x0 + 130, 592, 40, INK, "DMSans-500")
    if lt < 1.0 and int(lt * 4) % 2 == 0:
        tw = text_rgba(q[:n] or " ", "DMSans-500", 40, INK)[2] if n else 0
        f[590:648, x0 + 132 + int(tw):x0 + 135 + int(tw)] = C(PURPLE)
    climb = ease_in_out(prog(lt, 1.6, 0.6))
    order = {i: i for i in range(5)}
    for i, name in enumerate(RESULTS):
        if i == 3:
            pos = lerp(3, 0, climb)
        elif i < 3:
            pos = i + climb
        else:
            pos = i
        qa = prog(lt, 1.0 + i * 0.08, 0.3)
        if qa <= 0:
            continue
        y = 720 + pos * 172
        star_ours = i == 3
        hi = star_ours and lt > 2.2
        fillc = PURPLE if hi else (34, 28, 56)
        card(f, x0, y + (1 - ease_out_cubic(qa)) * 40, w, 150, 28, fillc, min(1, qa * 3),
             border=LIME if hi else (60, 52, 96), bw=4 if hi else 2)
        yy = y + (1 - ease_out_cubic(qa)) * 40
        label(f, name, x0 + 40, yy + 26, 38, WHITE, "Sora-700", min(1, qa * 3))
        rating = RATINGS[i]
        label(f, rating, x0 + 40, yy + 84, 28, LIME if hi else CLOUD, "DMSans-700", min(1, qa * 3))
        nstars = 5 if star_ours else 4
        for k in range(5):
            poly(f, star(x0 + 112 + k * 34, yy + 100, 14), LIME if (k < nstars and hi) else (230, 190, 60) if k < nstars else GREY,
                 min(1, qa * 3))
        label(f, f"{[1.2, 2.4, 0.8, 0.6, 3.1][i]} km", x0 + 300, yy + 84, 28, LAVENDER, "DMSans-500", min(1, qa * 3))
        if hi:
            bq = ease_out_back(prog(lt, 2.2, 0.35))
            blit_c(f, rrect(90, 56, 28, LIME), x0 + w - 90, yy + 75, bq)
            label(f, "#1", x0 + w - 90, yy + 58, 30, INK, "Sora-800", min(1, bq), align="center")
    # map pin drops onto the winner
    pq = prog(lt, 2.3, 0.45)
    if pq > 0:
        py = lerp(300, 690, ease_out_back(pq, 1.5) if pq < 1 else 1)
        px = x0 + w - 210
        poly(f, [(px - 30, py - 10), (px + 30, py - 10), (px, py + 45)], LIME)
        circle(f, px, py - 20, 38, LIME)
        circle(f, px, py - 20, 15, INK)
    return f


def sc_growth(t, lt):
    f = vignette_bg(t, "STOP 05  ·  GROWTH", ["Then it", "*grows.*"])(lt)
    x0, y0, w, h = 110, 540, 860, 1000
    card(f, x0, y0, w, h, 44, (26, 22, 44), border=(60, 52, 96), bw=3)
    label(f, "Orders per month", x0 + 50, y0 + 44, 36, WHITE, "Sora-700")
    label(f, "Golden Crust  ·  illustrative", x0 + 50, y0 + 96, 24, LAVENDER, "DMSans-500")
    vals = [0.22, 0.3, 0.42, 0.55, 0.74, 1.0]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    base, top = y0 + 680, y0 + 200
    tops = []
    for i, v in enumerate(vals):
        q = ease_out_back(prog(lt, 0.3 + i * 0.1, 0.4), 1.3)
        bx = x0 + 70 + i * 128
        hh = (base - top) * v * q
        if hh > 2:
            card(f, bx, base - hh, 88, hh, 16, LIME if i == 5 else PURPLE)
        label(f, months[i], bx + 44, base + 20, 26, LAVENDER, "DMSans-500", align="center")
        tops.append((bx + 44, base - (base - top) * v - 30))
    lp = prog(lt, 1.0, 0.6)
    if lp > 0:
        segs = lp * (len(tops) - 1)
        pts = tops[:int(segs) + 1]
        if int(segs) < len(tops) - 1:
            a, b = tops[int(segs)], tops[int(segs) + 1]
            fr = segs - int(segs)
            pts = pts + [(lerp(a[0], b[0], fr), lerp(a[1], b[1], fr))]
        poly(f, pts, WHITE, closed=False, thickness=6)
        for p in pts[:-1]:
            circle(f, p[0], p[1], 10, WHITE)
        tip = pts[-1]
        circle(f, tip[0], tip[1], 14, LIME)
    for i, name in enumerate(("Calls", "Orders", "Walk-ins")):
        q = ease_out_back(prog(lt, 1.7 + i * 0.15, 0.35))
        if q <= 0:
            continue
        cx = x0 + 150 + i * 280
        blit_c(f, rrect(240, 90, 45, (40, 34, 66), LIME, 3), cx, y0 + 870, q)
        label(f, name, cx - 20, y0 + 848, 32, WHITE, "DMSans-700", min(1, q), align="center")
        ax = cx + text_rgba(name, "DMSans-700", 32, WHITE)[2] / 2 + 10
        poly(f, [(ax - 14, y0 + 884), (ax + 14, y0 + 884), (ax, y0 + 858)], LIME, min(1, q))
    return f


# ================================================================ recap, CTA, end
@lru_cache(None)
def thumb_of(name):
    fn = SCENE_FN[name]
    start = [s for s, e, n in SCENES if n == name][0]
    full = fn(start + 3.4, 3.4)
    return cv2.resize(full, (288, 512), interpolation=cv2.INTER_AREA)


def sc_recap(t, lt):
    f = bg(PURPLE, (64, 18, 150), r=0.9)
    f = dot_grid(f, t, a=0.1)
    Text(["Design.  Tech.  Growth."], "Sora-800", 84, align="center").draw(f, W / 2, 230, lt, 0.4, 0.15, 0.3, "pop")
    slots = [(-330, 30, -10), (-165, -20, -5), (0, -50, 0), (165, -20, 5), (330, 30, 10)]
    for i, name in enumerate(VIGNETTES):
        q = prog(lt, 0.05 + i * 0.12, 0.45)
        if q <= 0:
            continue
        e = ease_out_back(q, 1.6)
        th = thumb_of(name)
        m = round_mask(288, 512, 28)
        img = np.dstack([th * m, m])
        border = rrect(300, 524, 32, LIME)
        dx, dy, rot = slots[i if i != 2 else 2]
        order_i = [0, 4, 1, 3, 2][i]
        dx, dy, rot = slots[[0, 1, 2, 3, 4][i]]
        cx, cy = W / 2 + dx * e, 900 + dy + (1 - e) * 500
        blit_c(f, border, cx, cy, 0.95, min(1, q * 3), rot * e)
        blit_c(f, img, cx, cy, 0.95, min(1, q * 3), rot * e)
    Text(["*One team.*"], "Sora-800", 150, align="center").draw(f, W / 2, 1300, lt, 1.4, 0, 0.2, "slam")
    since = lt - 1.4
    if since > 0:
        f = flash(f, WHITE, 0.5 * (1 - prog(since, 0, 0.2)))
        f = shake(f, 20 * (1 - prog(since, 0, 0.3)), t, 9)
    label(f, "One plan. One bill.", W / 2, 1520, 44, CLOUD, "DMSans-500", ease_out_cubic(prog(lt, 1.8, 0.4)), align="center")
    return f


def sc_cta(t, lt):
    f = bg(LIME, (186, 222, 66), r=0.9)
    Text(["Your next", "customer is"], "Sora-800", 108, INK, PURPLE, align="center").draw(f, W / 2, 330, lt, 0.0, 0.08, 0.25, "slam")
    Text(["*one thumb*", "away."], "Sora-800", 140, INK, PURPLE, align="center").draw(f, W / 2, 580, lt, 0.6, 0.1, 0.3, "pop")
    q = ease_out_back(prog(lt, 1.6, 0.4))
    if q > 0:
        pulse = 1 + 0.025 * math.sin(max(0, lt - 2.2) * 2 * math.pi / BEAT) * (lt > 2.2)
        btn = np.zeros((150, 900, 4), np.float32)
        blit(btn, rrect(900, 150, 75, PURPLE), 0, 0)
        r = text_rgba("Book a free 15-min audit", "Sora-700", 50, WHITE)[0]
        blit(btn, r, (900 - r.shape[1]) / 2, (150 - r.shape[0]) / 2 - 4)
        blit_c(f, btn, W / 2, 1050, q * pulse, min(1, q * 2))
        f = ripple(f, W / 2 + 120, 1070, prog(lt, 1.8, 0.5), WHITE, 260)
    tq = ease_out_back(prog(lt, 2.0, 0.4))
    if tq > 0:
        card(f, W / 2 - 300, 1180, 600, 92, 46, INK, min(1, tq * 2))
        circle(f, W / 2 - 240, 1226, 26, LIME, min(1, tq * 2))
        check(f, W / 2 - 240, 1228, 12, INK, prog(lt, 2.2, 0.3), 5)
        label(f, "Audit booked", W / 2 - 196, 1204, 36, WHITE, "Sora-700", min(1, tq * 2))
    for i, s in enumerate(("WhatsApp  +91 73659 77561", "varniklabs.com")):
        Text([s], "DMSans-700", 46, INK, align="center").draw(f, W / 2, 1380 + i * 72, lt, 2.4 + i * 0.12, 0.0, 0.4)
    draw_logo(f, W / 2, 1640, 420, PURPLE, INK, ease_out_cubic(prog(lt, 2.8, 0.5)))
    f = flash(f, WHITE, 0.6 * (1 - prog(lt, 0, 0.25)))
    return shake(f, 16 * (1 - prog(lt, 0, 0.3)), t, 11)


def sc_endcard(t, lt):
    f = bg(PURPLE, (52, 16, 128), r=0.9)
    f = dot_grid(f, t, a=0.08)
    mask = np.zeros((H, W), np.float32)
    draw_logo(f, W / 2, 860, 860, mask=mask, t=lt, t0=0.05)
    f = add_glow(f, mask, LIME, 0.35, 30)
    Text(["DESIGN.  TECH.  GROWTH."], "DMSans-700", 34, WHITE, tracking=9, align="center").draw(f, W / 2, 1000, lt, 0.7, 0, 0.5)
    Text(["Stop the scroll.", "*Start the growth.*"], "Sora-800", 72, align="center").draw(f, W / 2, 1180, lt, 1.0, 0.06, 0.4)
    f = light_sweep(f, mask, prog(lt, 1.0, 0.8))
    f = flash(f, WHITE, 0.8 * (1 - ease_out_cubic(prog(lt, 0, 0.3))))
    return f * (1 - ease_in_cubic(prog(lt, 2.4, 0.6)))


SCENE_FN = {
    "hook_timer": sc_hook_timer, "so_does": sc_so_does, "feed": sc_feed, "zoom_post": sc_zoom_post,
    "brand": sc_brand, "website": sc_website, "chat": sc_chat, "search": sc_search, "growth": sc_growth,
    "recap": sc_recap, "cta": sc_cta, "endcard": sc_endcard,
}


def whip_in(f, lt):
    """Cuts between the five stops are a fast scroll: the new screen flicks up into place."""
    p = prog(lt, 0, 0.28)
    if p >= 1:
        return f
    off = (1 - ease_out_expo(p)) * H * 0.4
    M = np.float32([[1, 0, 0], [0, 1, off]])
    f = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return vblur(f, off * 0.5)


def render(i):
    t = i / FPS
    for s, e, name in SCENES:
        if s <= t < e:
            f = SCENE_FN[name](t, t - s)
            if name in VIGNETTES or name == "recap":
                f = whip_in(f, t - s)
            break
    else:
        f = np.zeros((H, W, 3), np.float32)
    f = f * vignette() + grain_bank()[i % 6] * 0.016
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


def warm():
    vignette(), grain_bank(), feed_strip(), logo_meta()
    for n in VIGNETTES:
        thumb_of(n)


if __name__ == "__main__":
    warm()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
        for ts in sys.argv[2:]:
            img = render(int(round(float(ts) * FPS)))
            cv2.imwrite(os.path.join(BUILD, "stills", f"{float(ts):05.2f}.png"), img[:, :, ::-1])
        sys.exit()
    from multiprocessing import Pool
    os.makedirs(BUILD, exist_ok=True)
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
