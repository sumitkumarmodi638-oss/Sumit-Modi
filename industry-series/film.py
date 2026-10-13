"""Industry Reels: one 32 s vertical film per industry, built from stories.py.

Usage:
  python3 film.py healthcare                 # render build/healthcare.mp4 (picture only)
  python3 film.py healthcare --stills 1 5    # preview frames
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scroll-stopper"))
from lib import *  # noqa: E402,F401,F403  (shared drawing toolkit)
from lib import FPS, H, W  # noqa: E402

from stories import STORIES  # noqa: E402

BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
DURATION = 32.0
BEAT = 0.5
SCENES = [(0.0, 3.0, "hook"), (3.0, 8.0, "problem"), (8.0, 9.5, "switch"), (9.5, 13.5, "fix0"),
          (13.5, 17.5, "fix1"), (17.5, 21.5, "fix2"), (21.5, 25.0, "result"), (25.0, 29.0, "cta"),
          (29.0, 32.0, "endcard")]
DROP = 9.5
CARDBG = (30, 26, 48)
CREAM = (245, 230, 200)
EDGE = (64, 56, 100)


def FText(lines, fname, size, *a, maxw=960, **kw):
    """Text that shrinks until every line fits inside `maxw` px."""
    txt = Text(lines, fname, size, *a, **kw)
    while txt.width > maxw and size > 30:
        size -= 4
        txt = Text(lines, fname, size, *a, **kw)
    return txt


ACRONYMS = {"crm", "b2b", "ui", "ux"}


def tagcase(s, first_upper=True):
    """'CRM & ADS' -> 'CRM & ads'; keeps acronyms upper-case."""
    words = [w.upper() if w.lower() in ACRONYMS else w.lower() for w in s.split(" ")]
    out = " ".join(words)
    return out[0].upper() + out[1:] if first_upper else out


# ================================================================ hook icons
def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _gear():
    parts = []
    for k in range(8):
        a = k * math.pi / 4
        c, s = math.cos(a), math.sin(a)
        pts = [(-0.17, 0.62), (0.17, 0.62), (0.17, 1.05), (-0.17, 1.05)]
        parts.append(("poly", [(x * c - y * s, x * s + y * c) for x, y in pts], LIME))
    return parts + [("circle", (0, 0), 0.78, PURPLE), ("circle", (0, 0), 0.3, MIDNIGHT)]


ICONS = {
    "cross": [("circle", (0, 0), 1.0, PURPLE), ("poly", _rect(-0.22, -0.62, 0.44, 1.24), LIME),
              ("poly", _rect(-0.62, -0.22, 1.24, 0.44), LIME)],
    "plate": [("circle", (0, 0), 1.0, PURPLE), ("circle", (0, 0), 0.7, LAVENDER), ("circle", (0, 0), 0.5, CLOUD),
              ("poly", _rect(-1.35, -0.85, 0.14, 1.7), LIME), ("poly", _rect(1.21, -0.85, 0.14, 1.7), LIME)],
    "house": [("poly", _rect(-0.75, -0.1, 1.5, 1.0), PURPLE), ("poly", [(-1.05, 0.0), (0, -0.95), (1.05, 0.0)], LIME),
              ("poly", _rect(-0.18, 0.35, 0.36, 0.55), LIME)],
    "cap": [("poly", _rect(-0.6, 0.0, 1.2, 0.6), PURPLE), ("poly", [(-1.15, -0.2), (0, -0.72), (1.15, -0.2), (0, 0.3)], LIME),
            ("poly", _rect(0.86, -0.22, 0.06, 0.82), LAVENDER), ("circle", (0.89, 0.66), 0.11, LAVENDER)],
    "dumbbell": [("poly", _rect(-0.9, -0.12, 1.8, 0.24), LAVENDER), ("poly", _rect(-1.15, -0.62, 0.3, 1.24), LIME),
                 ("poly", _rect(0.85, -0.62, 0.3, 1.24), LIME), ("poly", _rect(-0.82, -0.45, 0.2, 0.9), PURPLE),
                 ("poly", _rect(0.62, -0.45, 0.2, 0.9), PURPLE)],
    "bag": [("ring", (0, -0.45), 0.42, LIME), ("poly", _rect(-0.85, -0.45, 1.7, 1.35), PURPLE),
            ("circle", (0, 0.2), 0.2, LIME)],
    "suitcase": [("ring", (0, -0.62), 0.3, LAVENDER), ("poly", _rect(-1.0, -0.55, 2.0, 1.35), PURPLE),
                 ("poly", _rect(-1.0, -0.02, 2.0, 0.14), LIME), ("poly", _rect(-0.65, -0.55, 0.12, 1.35), LIME),
                 ("poly", _rect(0.53, -0.55, 0.12, 1.35), LIME)],
    "chart": [("poly", _rect(-0.95, 0.2, 0.45, 0.7), LAVENDER), ("poly", _rect(-0.22, -0.25, 0.45, 1.15), PURPLE),
              ("poly", _rect(0.5, -0.8, 0.45, 1.7), LIME), ("circle", (-0.72, -0.35), 0.16, LIME)],
    "gear": _gear(),
}


def draw_icon(f, kind, cx, cy, s, lt, t0=0.0):
    mask = np.zeros((H, W), np.float32)
    for i, part in enumerate(ICONS[kind]):
        q = prog(lt, t0 + i * 0.1, 0.4)
        if q <= 0:
            continue
        e = ease_out_back(q, 2.0)
        a = min(1, q * 3)
        typ = part[0]
        if typ == "poly":
            pts = [(cx + x * s * e, cy + y * s * e) for x, y in part[1]]
            poly(f, pts, part[2], a)
            ov = np.zeros((H, W), np.float32)
            cv2.fillPoly(ov, [np.int32(pts)], 1.0, cv2.LINE_AA)
            np.maximum(mask, ov * a, out=mask)
        else:
            (x, y), r, col = part[1], part[2], part[3]
            circle(f, cx + x * s * e, cy + y * s * e, r * s * e, col, a, -1 if typ == "circle" else max(2, int(s * 0.12)))
    return mask


# ================================================================ common scene chrome
def dark_bg(t):
    f = bg((32, 22, 64), MIDNIGHT, r=0.8)
    return dot_grid(f, t, a=0.09)


def chrome(f, t, lt, tag, head, demo):
    eyebrow(f, tag, W / 2, 190, lt, 0.05)
    FText(head, "Sora-800", 84, align="center").draw(f, W / 2, 245, lt, 0.1, 0.05, 0.4)
    label(f, f"Demo business: {demo}", W / 2, 1760, 28, LAVENDER, "DMSans-500",
          alpha=ease_out_cubic(prog(lt, 0.6, 0.5)), align="center")


def whip_in(f, lt):
    p = prog(lt, 0, 0.28)
    if p >= 1:
        return f
    off = (1 - ease_out_expo(p)) * H * 0.4
    f = cv2.warpAffine(f, np.float32([[1, 0, 0], [0, 1, off]]), (W, H), flags=cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_REFLECT)
    return vblur(f, off * 0.5)


def toast(f, x, y, w, text, sub, q, lt_check):
    if q <= 0:
        return
    a = min(1, q * 2)
    card(f, x, y, w, 120, 30, INK, a, border=LIME, bw=3)
    circle(f, x + 70, y + 60, 34, LIME, a)
    check(f, x + 70, y + 62, 16, INK, lt_check, 7)
    label(f, text, x + 130, y + 24, 34, WHITE, "Sora-700", a)
    if sub:
        label(f, sub, x + 130, y + 70, 24, LAVENDER, "DMSans-500", a)


# ================================================================ widgets (4 s each)
def w_search(f, lt, sp, st):
    x0, w = 110, 860
    card(f, x0, 560, w, 110, 55, WHITE)
    circle(f, x0 + 70, 605, 22, GREY, thickness=6)
    poly(f, [(x0 + 86, 621), (x0 + 104, 640)], GREY, closed=False, thickness=7)
    q = sp["query"]
    step = min(0.055, 0.85 / len(q))
    n = int(clamp((lt - 0.2) / step, 0, len(q)))
    if n:
        label(f, q[:n], x0 + 130, 592, 38, INK, "DMSans-500")
    climb = ease_in_out(prog(lt, 1.7, 0.6))
    ours = 2
    for i, name in enumerate(sp["results"]):
        pos = lerp(ours, 0, climb) if i == ours else (i + climb if i < ours else i)
        qa = prog(lt, 1.1 + i * 0.08, 0.3)
        if qa <= 0:
            continue
        y = 720 + pos * 190 + (1 - ease_out_cubic(qa)) * 40
        hi = i == ours and lt > 2.3
        a = min(1, qa * 3)
        card(f, x0, y, w, 165, 28, PURPLE if hi else (34, 28, 56), a, border=LIME if hi else EDGE, bw=4 if hi else 2)
        label(f, name, x0 + 40, y + 28, 38, WHITE, "Sora-700", a)
        rating = "4.9" if i == ours else ["4.1", "3.9", "4.0", "3.8"][i]
        label(f, rating, x0 + 40, y + 92, 28, LIME if hi else CLOUD, "DMSans-700", a)
        for k in range(5):
            full = k < (5 if i == ours else 4)
            poly(f, star(x0 + 112 + k * 34, y + 108, 14), (LIME if hi else (230, 190, 60)) if full else GREY, a)
        label(f, f"{[1.2, 2.4, 0.6, 3.1][i]} km  ·  Open now", x0 + 300, y + 92, 28, LAVENDER, "DMSans-500", a)
        if hi:
            bq = ease_out_back(prog(lt, 2.3, 0.35))
            blit_c(f, rrect(90, 56, 28, LIME), x0 + w - 90, y + 82, bq)
            label(f, "#1", x0 + w - 90, y + 64, 30, INK, "Sora-800", min(1, bq), align="center")
    pq = prog(lt, 2.4, 0.45)
    if pq > 0:
        py = lerp(330, 700, ease_out_back(pq, 1.5) if pq < 1 else 1)
        px = x0 + w - 210
        poly(f, [(px - 30, py - 10), (px + 30, py - 10), (px, py + 45)], LIME)
        circle(f, px, py - 20, 38, LIME)
        circle(f, px, py - 20, 15, INK)
    return f


def cues_search(sp):
    step = min(0.055, 0.85 / len(sp["query"]))
    return [(0.2 + k * step, "key", 0.35) for k in range(len(sp["query"]))] + [
        (1.1, "whoosh", 0.4), (1.7, "slide_up", 0.6), (2.3, "ding", 0.7), (2.4, "pin", 0.6)]


SLOTS = ["9:00", "10:30", "12:00", "4:00", "5:30", "7:00"]


def w_booking(f, lt, sp, st):
    x0, y0, w, h = 110, 540, 860, 1080
    card(f, x0, y0, w, h, 44, CARDBG, border=EDGE, bw=3)
    circle(f, x0 + 80, y0 + 75, 40, LIME)
    label(f, st["initials"], x0 + 80, y0 + 55, 30, INK, "Sora-800", align="center")
    label(f, sp["title"], x0 + 140, y0 + 40, 34, WHITE, "Sora-700")
    label(f, "Pick a day", x0 + 50, y0 + 170, 28, LAVENDER, "DMSans-700")
    days = ["M", "T", "W", "T", "F", "S", "S"]
    pick_day = 5
    for i, d in enumerate(days):
        q = ease_out_back(prog(lt, 0.15 + i * 0.04, 0.3))
        cx = x0 + 95 + i * 112
        sel = i == pick_day and lt > 0.6
        blit_c(f, rrect(92, 120, 26, LIME if sel else (44, 38, 70)), cx, y0 + 290, q)
        label(f, d, cx, y0 + 248, 26, INK if sel else LAVENDER, "DMSans-700", min(1, q), align="center")
        label(f, str(14 + i), cx, y0 + 285, 36, INK if sel else WHITE, "Sora-700", min(1, q), align="center")
    f = ripple(f, x0 + 95 + pick_day * 112, y0 + 290, prog(lt, 0.6, 0.4), WHITE, 90)
    label(f, "Pick a time", x0 + 50, y0 + 400, 28, LAVENDER, "DMSans-700", alpha=ease_out_cubic(prog(lt, 0.85, 0.3)))
    pick = 1
    for i, s in enumerate(SLOTS):
        q = ease_out_back(prog(lt, 0.9 + i * 0.06, 0.3))
        cx = x0 + 165 + (i % 3) * 265
        cy = y0 + 500 + (i // 3) * 120
        sel = i == pick and lt > 1.6
        blit_c(f, rrect(230, 90, 45, LIME if sel else (44, 38, 70), None if sel else EDGE, 2), cx, cy, q)
        label(f, s, cx, cy - 22, 34, INK if sel else WHITE, "Sora-700", min(1, q), align="center")
    f = ripple(f, x0 + 165 + 265, y0 + 500, prog(lt, 1.6, 0.4), WHITE, 120)
    bq = ease_out_back(prog(lt, 1.8, 0.3))
    if bq > 0:
        blit_c(f, rrect(760, 110, 55, PURPLE), x0 + w / 2, y0 + 820, bq)
        label(f, "Confirm  ·  " + sp["slot"], x0 + w / 2, y0 + 795, 38, WHITE, "Sora-700", min(1, bq), align="center")
    f = ripple(f, x0 + w / 2, y0 + 820, prog(lt, 2.2, 0.4), LIME, 260)
    toast(f, x0 + 40, lerp(y0 - 140, y0 + 920, ease_out_back(prog(lt, 2.5, 0.4))) if lt > 2.5 else 0,
          w - 80, sp["toast"], sp["slot"], ease_out_back(prog(lt, 2.5, 0.4)), prog(lt, 2.7, 0.3))
    return f


def cues_booking(sp):
    return [(0.15 + i * 0.04, "tick", 0.25) for i in range(7)] + [(0.6, "tap", 0.7)] + \
        [(0.9 + i * 0.06, "tick", 0.25) for i in range(6)] + [(1.6, "tap", 0.7), (2.2, "tap", 0.8), (2.5, "notify", 0.7)]


def chat_times(msgs):
    return [0.3 + k * 0.85 for k in range(len(msgs))]


def w_chat(f, lt, sp, st):
    x0, y0, w, h = 110, 540, 860, 1100
    card(f, x0, y0, w, h, 44, (26, 22, 44), border=EDGE, bw=3)
    circle(f, x0 + 80, y0 + 66, 40, LIME)
    label(f, st["initials"], x0 + 80, y0 + 46, 30, INK, "Sora-800", align="center")
    label(f, st["demo"], x0 + 140, y0 + 30, 34, WHITE, "Sora-700")
    label(f, "Auto-reply  ·  online", x0 + 140, y0 + 76, 24, LIME, "DMSans-500")
    label(f, sp["time"], x0 + w - 40, y0 + 48, 30, CLOUD, "DMSans-700", align="right")
    f[y0 + 130:y0 + 132, x0:x0 + w] = C(EDGE)
    y = y0 + 170
    for i, (side, lines) in enumerate(sp["msgs"]):
        t0 = chat_times(sp["msgs"])[i]
        if side == "out" and t0 - 0.45 <= lt < t0:
            card(f, x0 + w - 200, y, 160, 80, 40, PURPLE)
            for k in range(3):
                circle(f, x0 + w - 160 + k * 40, y + 40 + math.sin(lt * 10 - k * 0.9) * 8, 10, CLOUD)
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
        y += bh + 34
    cq = prog(lt, 0.3 + len(sp["msgs"]) * 0.85, 0.3)
    if cq > 0:
        check(f, x0 + w - 70, y + 10, 14, LIME, cq, 6)
        label(f, "Handled automatically", x0 + w - 100, y - 6, 26, LIME, "DMSans-700", min(1, cq * 2), align="right")
    return f


def cues_chat(sp):
    out = []
    for (side, _), t0 in zip(sp["msgs"], chat_times(sp["msgs"])):
        if side == "out":
            out.append((t0 - 0.45, "typing", 0.35))
        out.append((t0, "msg_out" if side == "out" else "msg_in", 0.6))
    return out + [(0.3 + len(sp["msgs"]) * 0.85, "ding", 0.5)]


def w_site(f, lt, sp, st):
    x0, y0, w, h = 210, 540, 660, 1080
    card(f, x0, y0, w, h, 44, (250, 248, 252), ease_out_cubic(prog(lt, 0.0, 0.3)))
    blocks = [(30, 30, 600, 70, (255, 255, 255)), (30, 120, 600, 430, CREAM), (30, 570, 290, 250, (240, 236, 244)),
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
        label(f, sp["name"], x0 + 56, y0 + 50, 30, INK, "Sora-700", a)
        for k in range(3):
            sl = f[y0 + 52 + k * 12:y0 + 56 + k * 12, x0 + 570:x0 + 604]
            sl[:] = C(INK) * a + sl * (1 - a)
        FText(sp["hero"], "Sora-800", 58, INK, PURPLE, maxw=540).draw(f, x0 + 60, y0 + 160, lt, 0.95, 0.04, 0.3, alpha=a)
        # abstract hero art in brand colours
        circle(f, x0 + 480, y0 + 440, 110, PURPLE, a)
        circle(f, x0 + 380, y0 + 470, 70, LIME, a)
        card(f, x0 + 90, y0 + 400, 220, 110, 30, (230, 214, 186), a)
        for k, name in enumerate(sp["items"]):
            bx = x0 + 30 + k * 310
            circle(f, bx + 145, y0 + 670, 62, PURPLE if k == 0 else LAVENDER, a)
            label(f, name, bx + 145, y0 + 755, 30, INK, "DMSans-700", a, align="center")
        label(f, sp["button"], x0 + w / 2, y0 + 878, 44, INK, "Sora-700", a, align="center")
        label(f, "Fast  ·  Mobile-first  ·  Secure", x0 + w / 2, y0 + 990, 26, (110, 104, 124), "DMSans-500", a, align="center")
    tap = prog(lt, 2.2, 0.5)
    f = ripple(f, x0 + w / 2, y0 + 905, tap, PURPLE, 200)
    q = ease_out_back(prog(lt, 2.5, 0.4))
    if q > 0:
        toast(f, x0 + 30, lerp(y0 - 140, y0 + 40, q), w - 60, sp["toast"].split(" · ")[0],
              " · ".join(sp["toast"].split(" · ")[1:]) or "just now", q, prog(lt, 2.7, 0.3))
    return f


def cues_site(sp):
    return [(0.1 + k * 0.12, "tick", 0.3) for k in range(6)] + [(0.9, "fill", 0.5), (2.2, "tap", 0.8), (2.5, "notify", 0.7)]


def w_brand(f, lt, sp, st):
    cx, cy = W / 2, 860
    merge = ease_in_out(prog(lt, 0.7, 0.25))
    shapes = [((-400, -200), LIME, "circle"), ((420, 80), PURPLE, "square"), ((0, 600), LAVENDER, "tri")]
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
        Text([st["initials"]], "Sora-800", 160, LIME, align="center").draw(f, cx, cy - 108, lt, 0.95, 0, 0.3, "pop", mask=mask)
        ring = prog(k, 0, 0.5)
        if ring < 1:
            circle(f, cx, cy, 240 + 260 * ease_out_expo(ring), LIME, 1 - ring, thickness=max(1, int(14 * (1 - ring))))
        f = add_glow(f, mask, LIME, 0.3, 30)
        FText([sp["name"]], "Sora-800", 88, WHITE, align="center").draw(f, W / 2, 1140, lt, 1.0, 0.08)
        eyebrow(f, sp["tagline"], W / 2, 1270, lt, 1.2, color=LAVENDER, size=26)
        for i, col in enumerate((PURPLE, LIME, CREAM, INK)):
            q = prog(lt, 1.9 + i * 0.1, 0.35)
            if q > 0:
                x = W / 2 + (i - 1.5) * 150
                circle(f, x, 1450, 56 * ease_out_back(q), (90, 80, 120), min(1, q * 3))
                circle(f, x, 1450, 50 * ease_out_back(q), col, min(1, q * 3))
        f = light_sweep(f, mask, prog(lt, 1.4, 0.7))
    return f


def cues_brand(sp):
    return [(0.2, "whoosh", 0.5), (0.3, "pop", 0.5), (0.4, "pop", 0.5), (0.9, "snap", 0.8), (1.4, "shimmer", 0.5)] + \
        [(1.9 + i * 0.1, "pop", 0.4) for i in range(4)]


def heart(f, cx, cy, s, color, a=1.0):
    circle(f, cx - s * 0.5, cy - s * 0.2, s * 0.55, color, a)
    circle(f, cx + s * 0.5, cy - s * 0.2, s * 0.55, color, a)
    poly(f, [(cx - s * 1.02, cy - s * 0.02), (cx + s * 1.02, cy - s * 0.02), (cx, cy + s * 1.05)], color, a)


def w_post(f, lt, sp, st):
    x0, y0, w = 160, 540, 760
    q0 = ease_out_cubic(prog(lt, 0, 0.3))
    card(f, x0, y0, w, 1100, 36, (24, 20, 40), q0, border=EDGE, bw=2)
    circle(f, x0 + 60, y0 + 56, 32, LIME, q0)
    label(f, st["initials"], x0 + 60, y0 + 40, 24, INK, "Sora-800", q0, align="center")
    label(f, sp["handle"], x0 + 110, y0 + 36, 30, WHITE, "DMSans-700", q0)
    img = bg(PURPLE, (60, 18, 140), r=0.8, size=(w, 700))
    lines = [f"*{s}*" if i == len(sp["art"]) - 1 else s for i, s in enumerate(sp["art"])]
    FText(lines, "Sora-800", 104, WHITE, align="center", maxw=680).draw(img, w / 2, 160, 1, 0, 0, 0.01)
    m = round_mask(w, 700, 8)
    blit(f, np.dstack([img * m, m]), x0, y0 + 112, q0)
    # double-tap like
    hq = prog(lt, 0.6, 0.6)
    if 0 < hq < 1:
        e = ease_out_back(min(1, hq * 2), 2.5)
        heart(f, x0 + w / 2, y0 + 440, 120 * e, WHITE, 1 - max(0, hq - 0.5) * 2)
    liked = lt > 0.6
    heart(f, x0 + 60, y0 + 870, 26, LIME if liked else GREY)
    n = int(sp["likes"] * ease_out_expo(prog(lt, 0.7, 1.6)))
    label(f, f"{n:,} likes", x0 + 110, y0 + 850, 34, WHITE, "Sora-700", q0)
    for k, c in enumerate(sp["comments"]):
        cq = ease_out_back(prog(lt, 2.0 + k * 0.45, 0.35))
        if cq > 0:
            tw = text_rgba(c, "DMSans-500", 32, WHITE)[2]
            blit_c(f, rrect(int(tw + 60), 70, 35, (44, 38, 70)), x0 + 40 + (tw + 60) / 2, y0 + 940 + k * 84, cq)
            label(f, c, x0 + 70, y0 + 918 + k * 84, 32, WHITE, "DMSans-500", min(1, cq))
    return f


def cues_post(sp):
    return [(0.6, "tap", 0.6), (0.68, "tap", 0.6), (0.75, "pop", 0.6)] + \
        [(0.8 + k * 0.12, "tick", 0.2 + 0.03 * k) for k in range(10)] + [(2.0, "msg_in", 0.5), (2.45, "msg_in", 0.5)]


def w_leads(f, lt, sp, st):
    x0, y0, w, h = 60, 560, 960, 1040
    card(f, x0, y0, w, h, 40, CARDBG, border=EDGE, bw=3)
    cols = ["New", "Contacted", "Booked"]
    cw = (w - 80) / 3
    for i, c in enumerate(cols):
        cx = x0 + 40 + cw * i
        label(f, c.upper(), cx + cw / 2, y0 + 40, 26, LIME if i == 2 else LAVENDER, "DMSans-700", align="center")
        if i:
            f[y0 + 30:y0 + h - 30, int(cx):int(cx) + 2] = C(EDGE)
    for k, lead in enumerate(sp["leads"]):
        q = ease_out_back(prog(lt, 0.2 + k * 0.15, 0.3))
        if q <= 0:
            continue
        col = 0
        m1 = ease_in_out(prog(lt, 1.0 + k * 0.25, 0.35))
        m2 = ease_in_out(prog(lt, 2.0 + k * 0.3, 0.35)) if k < 2 else 0
        colpos = m1 + m2
        cx = x0 + 40 + cw * colpos + cw / 2
        cy = y0 + 160 + k * 230
        fill = PURPLE if colpos >= 2 else (44, 38, 70)
        c = np.zeros((200, int(cw - 24), 4), np.float32)
        blit(c, rrect(int(cw - 24), 200, 24, fill, LIME if colpos >= 2 else EDGE, 2), 0, 0)
        name, need = lead.split(" · ")
        blit(c, text_rgba(name, "Sora-700", 32, WHITE)[0], 14, 14)
        blit(c, text_rgba(need, "DMSans-500", 26, LAVENDER if colpos < 2 else CLOUD)[0], 14, 62)
        if m1 > 0.9:
            tag = "Booked" if colpos >= 2 else "Replied in 2 min"
            tw = text_rgba(tag, "DMSans-700", 22, INK)[2]
            blit(c, rrect(int(tw + 30), 40, 20, LIME), 14, 130)
            blit(c, text_rgba(tag, "DMSans-700", 22, INK)[0], 22, 132)
        blit_c(f, c, cx, cy + 50, q)
    return f


def cues_leads(sp):
    return [(0.2 + k * 0.15, "pop", 0.5) for k in range(3)] + [(1.0 + k * 0.25, "card", 0.5) for k in range(3)] + \
        [(2.0 + k * 0.3, "card", 0.5) for k in range(2)] + [(2.35, "ding", 0.6)]


def w_growth(f, lt, sp, st):
    x0, y0, w, h = 110, 540, 860, 1000
    card(f, x0, y0, w, h, 44, CARDBG, border=EDGE, bw=3)
    label(f, sp["title"], x0 + 50, y0 + 44, 36, WHITE, "Sora-700")
    label(f, f"{st['demo']}  ·  illustrative", x0 + 50, y0 + 96, 24, LAVENDER, "DMSans-500")
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
    lp_ = prog(lt, 1.0, 0.6)
    if lp_ > 0:
        segs = lp_ * (len(tops) - 1)
        pts = tops[:int(segs) + 1]
        if int(segs) < len(tops) - 1:
            a, b = tops[int(segs)], tops[int(segs) + 1]
            fr = segs - int(segs)
            pts = pts + [(lerp(a[0], b[0], fr), lerp(a[1], b[1], fr))]
        poly(f, pts, WHITE, closed=False, thickness=6)
        for p in pts[:-1]:
            circle(f, p[0], p[1], 10, WHITE)
        circle(f, pts[-1][0], pts[-1][1], 14, LIME)
    for i, name in enumerate(sp["chips"]):
        q = ease_out_back(prog(lt, 1.7 + i * 0.15, 0.35))
        if q <= 0:
            continue
        cx = x0 + 150 + i * 280
        tw = text_rgba(name, "DMSans-700", 30, WHITE)[2]
        blit_c(f, rrect(int(max(240, tw + 80)), 90, 45, (40, 34, 66), LIME, 3), cx, y0 + 870, q)
        label(f, name, cx - 18, y0 + 850, 30, WHITE, "DMSans-700", min(1, q), align="center")
        ax = cx + tw / 2 + 8
        poly(f, [(ax - 13, y0 + 884), (ax + 13, y0 + 884), (ax, y0 + 860)], LIME, min(1, q))
    return f


def cues_growth(sp):
    return [(0.3 + k * 0.1, "blip", 0.45 + 0.04 * k) for k in range(6)] + [(1.0, "levelup", 0.6)] + \
        [(1.7 + k * 0.15, "pop", 0.4) for k in range(3)]


def w_shop(f, lt, sp, st):
    x0, y0, w = 160, 540, 760
    q0 = ease_out_cubic(prog(lt, 0, 0.3))
    card(f, x0, y0, w, 1100, 40, (250, 248, 252), q0)
    label(f, st["demo"], x0 + 40, y0 + 34, 30, INK, "Sora-700", q0)
    # cart with badge
    cx, cy = x0 + w - 70, y0 + 54
    card(f, cx - 26, cy - 14, 52, 38, 8, INK, q0)
    circle(f, cx - 14, cy + 34, 7, INK, q0)
    circle(f, cx + 14, cy + 34, 7, INK, q0)
    bq = ease_out_back(prog(lt, 1.6, 0.3), 3)
    if bq > 0:
        circle(f, cx + 26, cy - 22, 22 * bq, PURPLE)
        label(f, "1", cx + 26, cy - 40, 26, WHITE, "Sora-800", min(1, bq), align="center")
    # product image: hanger + garment
    img = bg((236, 228, 250), (214, 200, 240), r=0.9, size=(w - 80, 560))
    poly(img, [(340, 70), (340, 40)], INK, closed=False, thickness=6)
    poly(img, [(160, 150), (340, 70), (520, 150)], INK, closed=False, thickness=6)
    poly(img, [(170, 150), (510, 150), (560, 260), (470, 290), (470, 520), (210, 520), (210, 290), (120, 260)], (64, 72, 170))
    poly(img, [(300, 150), (340, 220), (380, 150)], (236, 228, 250))
    m = round_mask(w - 80, 560, 28)
    blit(f, np.dstack([img * m, m]), x0 + 40, y0 + 100, q0)
    label(f, sp["name"], x0 + 40, y0 + 690, 44, INK, "Sora-800", q0)
    label(f, sp["price"], x0 + 40, y0 + 750, 36, PURPLE, "Sora-700", q0)
    for i, s in enumerate(("S", "M", "L", "XL")):
        sel = i == 1 and lt > 0.8
        sq = ease_out_back(prog(lt, 0.3 + i * 0.06, 0.3))
        blit_c(f, rrect(110, 80, 20, LIME if sel else (240, 236, 244), INK if sel else (210, 204, 220), 2),
               x0 + 95 + i * 130, y0 + 860, sq)
        label(f, s, x0 + 95 + i * 130, y0 + 840, 32, INK, "Sora-700", min(1, sq), align="center")
    f = ripple(f, x0 + 225, y0 + 860, prog(lt, 0.8, 0.4), PURPLE, 90)
    added = lt > 1.4
    card(f, x0 + 40, y0 + 960, w - 80, 100, 50, PURPLE if not added else INK, q0)
    label(f, "Add to cart" if not added else "Checkout", x0 + w / 2, y0 + 985, 38, WHITE if not added else LIME,
          "Sora-700", q0, align="center")
    f = ripple(f, x0 + w / 2, y0 + 1010, prog(lt, 1.4, 0.4), LIME, 200)
    f = ripple(f, x0 + w / 2, y0 + 1010, prog(lt, 2.0, 0.4), LIME, 200)
    q = ease_out_back(prog(lt, 2.4, 0.4))
    if q > 0:
        toast(f, x0 + 20, lerp(y0 - 140, y0 + 120, q), w - 40, sp["toast"].split(" · ")[0],
              " · ".join(sp["toast"].split(" · ")[1:]), q, prog(lt, 2.6, 0.3))
    return f


def cues_shop(sp):
    return [(0.3 + i * 0.06, "tick", 0.25) for i in range(4)] + [(0.8, "tap", 0.7), (1.4, "tap", 0.7), (1.6, "pop", 0.6),
                                                                 (2.0, "tap", 0.8), (2.4, "notify", 0.7)]


WIDGETS = {"search": (w_search, cues_search), "booking": (w_booking, cues_booking), "chat": (w_chat, cues_chat),
           "site": (w_site, cues_site), "brand": (w_brand, cues_brand), "post": (w_post, cues_post),
           "leads": (w_leads, cues_leads), "growth": (w_growth, cues_growth), "shop": (w_shop, cues_shop)}


# ================================================================ scenes
def sc_hook(t, lt, st):
    f = dark_bg(t)
    eyebrow(f, "FOR " + st["industry"].upper(), W / 2, 300, lt, 0.05)
    mask = draw_icon(f, st["icon"], W / 2, 640, 170, lt, 0.05)
    f = add_glow(f, mask, LIME, 0.35, 40)
    n = len(st["hook"])
    size = 104 if n <= 2 else 92
    FText(st["hook"], "Sora-800", size, align="center").draw(f, W / 2, 940, lt, 0.6, 0.12, 0.35, "pop")
    return zoom(f, 1 + 0.03 * lt, W / 2, H / 2)


def note_times(st):
    return [0.3 + k * 0.55 for k in range(len(st["notes"]))]


def sc_problem(t, lt, st):
    f = bg((40, 34, 58), (12, 10, 20), r=0.9)
    label(f, st["clock"], W / 2, 170, 170, WHITE, "Sora-700", align="center")
    hour, ampm = int(st["clock"].split(":")[0]), st["clock"][-2:]
    when = "This morning" if ampm == "AM" and 5 <= hour < 12 else "Tonight"
    label(f, when, W / 2, 390, 34, LAVENDER, "DMSans-500", align="center")
    times = note_times(st)
    shown = [k for k, t0 in enumerate(times) if lt >= t0]
    for k in shown:
        # newest sits on top; older ones get pushed down
        newer = [j for j in shown if j > k]
        push = sum(ease_out_expo(prog(lt, times[j], 0.35)) for j in newer)
        q = ease_out_back(prog(lt, times[k], 0.35))
        y = 520 + push * 170 + (1 - q) * -60
        title, body = st["notes"][k]
        c = np.zeros((150, 920, 4), np.float32)
        blit(c, rrect(920, 150, 34, (52, 46, 74, 235)), 0, 0)
        col = (235, 90, 100) if "call" in title.lower() else LIME if title in ("WhatsApp", "Instagram DM") else LAVENDER
        circle(c[..., :3], 60, 75, 30, col)
        c[..., 3] = np.maximum(c[..., 3], 0)
        blit(c, text_rgba(title, "DMSans-700", 28, WHITE)[0], 110, 24)
        blit(c, text_rgba(body, "DMSans-500", 32, CLOUD)[0], 110, 70)
        blit(c, text_rgba("now", "DMSans-500", 24, GREY)[0], 840, 26)
        blit_c(f, c, W / 2, y + 75, 0.9 + 0.1 * q, min(1, q * 3) * (1 - 0.5 * prog(lt, 3.4, 0.4)))
    badge_q = ease_out_back(prog(lt, 3.0, 0.3))
    if badge_q > 0:
        n = len(st["notes"])
        blit_c(f, rrect(300, 70, 35, (235, 90, 100)), W / 2, 465, badge_q)
        label(f, f"{n} unanswered", W / 2, 445, 30, WHITE, "DMSans-700", min(1, badge_q), align="center")
    sl = lt - 3.4
    if sl >= 0:
        g = prog(sl, 0, 0.4)
        lum = f @ np.float32([0.299, 0.587, 0.114])
        f = f * (1 - 0.7 * g) + lum[..., None] * 0.7 * g * 0.6
        card(f, 0, 1330, W, 400, 0, (12, 10, 20), 0.85 * g)
        FText(st["problem"], "Sora-800", 84, align="center").draw(f, W / 2, 1400, lt, 3.4, 0.08, 0.22, "slam")
        f = shake(f, 20 * (1 - prog(sl, 0, 0.3)), t, 5)
    return zoom(f, 1 + 0.02 * lt, W / 2, H / 2)


def sc_switch(t, lt, st):
    f = bg((24, 18, 44), (6, 4, 12), r=0.8)
    q = ease_out_back(prog(lt, 0.0, 0.4))
    on = ease_in_out(prog(lt, 0.55, 0.2))
    cx, cy = W / 2, 980
    mask = np.zeros((H, W), np.float32)
    if q > 0:
        tw, th = 400, 210
        blit_c(f, rrect(tw, th, th // 2, (60, 56, 76)), cx, cy, q)
        blit_c(f, rrect(tw, th, th // 2, LIME), cx, cy, q, on, mask=mask)
        kx = cx + lerp(-95, 95, on) * q
        circle(f, kx, cy, 82 * q, WHITE)
        f = add_glow(f, mask, LIME, 0.8 * on, 60)
    Text(["Let's switch", "it *on.*"], "Sora-800", 110, align="center").draw(f, W / 2, 420, lt, 0.65, 0.08, 0.3, "pop")
    r = prog(lt, 1.0, 0.5)
    if r > 0:
        circle(f, cx, cy, 120 + 2300 * ease_in_cubic(r), PURPLE)
    f = flash(f, WHITE, 0.4 * (1 - prog(lt, 0.6, 0.2)) * (lt > 0.6))
    return shake(f, 10 * (1 - prog(lt, 0.6, 0.2)) * (lt > 0.6), t, 6)


def sc_fix(i):
    def scene(t, lt, st):
        sp = st["fixes"][i]
        f = dark_bg(t)
        chrome(f, t, lt, f"FIX 0{i + 1}  ·  {sp['tag']}", sp["head"], st["demo"])
        f = WIDGETS[sp["kind"]][0](f, lt, sp, st)
        if i == 0:
            f = flash(f, WHITE, 0.5 * (1 - prog(lt, 0, 0.2)))
        return whip_in(f, lt)
    return scene


def sc_result(t, lt, st):
    f = bg(PURPLE, (64, 18, 150), r=0.9)
    f = dot_grid(f, t, a=0.1)
    eyebrow(f, "THE RESULT", W / 2, 330, lt, 0.0)
    FText(st["result"], "Sora-800", 92, align="center").draw(f, W / 2, 400, lt, 0.0, 0.08, 0.25, "slam")
    for k, fx in enumerate(st["fixes"]):
        q = ease_out_back(prog(lt, 0.8 + k * 0.3, 0.35))
        if q <= 0:
            continue
        y = 820 + k * 170
        blit_c(f, rrect(820, 130, 65, (90, 40, 200), LIME, 3), W / 2, y, q)
        circle(f, W / 2 - 330, y, 38 * min(1, q), LIME)
        check(f, W / 2 - 330, y + 2, 17, INK, prog(lt, 0.9 + k * 0.3, 0.3), 7)
        label(f, tagcase(fx["tag"]), W / 2 - 260, y - 24, 42, WHITE, "Sora-700", min(1, q))
    label(f, f"Demo business: {st['demo']}  ·  illustrative", W / 2, 1760, 28, LAVENDER, "DMSans-500",
          alpha=ease_out_cubic(prog(lt, 1.5, 0.5)), align="center")
    f = flash(f, WHITE, 0.4 * (1 - prog(lt, 0, 0.2)))
    return shake(f, 14 * (1 - prog(lt, 0, 0.25)), t, 7)


def sc_cta(t, lt, st):
    f = bg(LIME, (186, 222, 66), r=0.9)
    FText(st["cta_q"], "Sora-800", 124, INK, PURPLE, align="center").draw(f, W / 2, 300, lt, 0.0, 0.08, 0.25, "slam")
    Text(["Let's switch", "*yours* on."], "Sora-800", 88, INK, PURPLE, align="center").draw(f, W / 2, 620, lt, 0.6, 0.06, 0.3, "pop")
    q = ease_out_back(prog(lt, 1.4, 0.4))
    if q > 0:
        pulse = 1 + 0.025 * math.sin(max(0, lt - 2.0) * 2 * math.pi / BEAT) * (lt > 2.0)
        btn = np.zeros((150, 900, 4), np.float32)
        blit(btn, rrect(900, 150, 75, PURPLE), 0, 0)
        r = text_rgba("Book a free 15-min audit", "Sora-700", 50, WHITE)[0]
        blit(btn, r, (900 - r.shape[1]) / 2, (150 - r.shape[0]) / 2 - 4)
        blit_c(f, btn, W / 2, 1000, q * pulse, min(1, q * 2))
        f = ripple(f, W / 2 + 120, 1020, prog(lt, 1.7, 0.5), WHITE, 260)
    tq = ease_out_back(prog(lt, 1.9, 0.4))
    if tq > 0:
        card(f, W / 2 - 300, 1130, 600, 92, 46, INK, min(1, tq * 2))
        circle(f, W / 2 - 240, 1176, 26, LIME, min(1, tq * 2))
        check(f, W / 2 - 240, 1178, 12, INK, prog(lt, 2.1, 0.3), 5)
        label(f, "Audit booked", W / 2 - 196, 1154, 36, WHITE, "Sora-700", min(1, tq * 2))
    for i, s in enumerate(("WhatsApp  +91 73659 77561", "varniklabs.com")):
        Text([s], "DMSans-700", 46, INK, align="center").draw(f, W / 2, 1330 + i * 72, lt, 2.2 + i * 0.12, 0.0, 0.4)
    draw_logo(f, W / 2, 1620, 420, PURPLE, INK, ease_out_cubic(prog(lt, 2.6, 0.5)))
    f = flash(f, WHITE, 0.6 * (1 - prog(lt, 0, 0.25)))
    return shake(f, 16 * (1 - prog(lt, 0, 0.3)), t, 11)


def sc_end(t, lt, st):
    f = bg(PURPLE, (52, 16, 128), r=0.9)
    f = dot_grid(f, t, a=0.08)
    mask = np.zeros((H, W), np.float32)
    draw_logo(f, W / 2, 820, 860, mask=mask, t=lt, t0=0.05)
    f = add_glow(f, mask, LIME, 0.35, 30)
    Text(["DESIGN.  TECH.  GROWTH."], "DMSans-700", 34, WHITE, tracking=9, align="center").draw(f, W / 2, 960, lt, 0.7, 0, 0.5)
    FText([f"Varnik Labs for", f"*{tagcase(st['industry'], False)}.*"], "Sora-800", 68, align="center").draw(f, W / 2, 1140, lt, 1.0, 0.06, 0.4)
    f = light_sweep(f, mask, prog(lt, 1.0, 0.8))
    f = flash(f, WHITE, 0.8 * (1 - ease_out_cubic(prog(lt, 0, 0.3))))
    return f * (1 - ease_in_cubic(prog(lt, 2.4, 0.6)))


SCENE_FN = {"hook": sc_hook, "problem": sc_problem, "switch": sc_switch, "fix0": sc_fix(0), "fix1": sc_fix(1),
            "fix2": sc_fix(2), "result": sc_result, "cta": sc_cta, "endcard": sc_end}


# ================================================================ sound cue sheet (read by audio.py)
def cues_for(st):
    c = [(0.0, "hit", 0.8)] + [(0.05 + i * 0.1, "pop", 0.5) for i in range(len(ICONS[st["icon"]]))]
    words = sum(len(line.split()) for line in st["hook"])
    c += [(0.6 + k * 0.12, "pop", 0.35) for k in range(words)]
    c += [(3.0, "whoosh", 0.5)]
    for k, t0 in enumerate(note_times(st)):
        c.append((3.0 + t0, "buzz" if "call" in st["notes"][k][0].lower() else "ping", 0.6))
    c += [(6.0, "pop", 0.5), (6.4, "hit", 0.9), (8.0, "whoosh", 0.4), (8.55, "toggle", 1.0), (8.6, "glow_swell", 0.7),
          (9.5, "riser@1.3", 0.7), (9.5, "revcrash@0.5", 0.6), (9.5, "drop", 1.0)]
    for i, (s, _e, _n) in enumerate(SCENES[3:6]):
        sp = st["fixes"][i]
        if i:
            c.append((s, "whip", 0.7))
        c += [(s + rt, k, g) for rt, k, g in WIDGETS[sp["kind"]][1](sp)]
    c += [(21.5, "hit", 0.9)] + [(22.3 + k * 0.3, "ding", 0.55) for k in range(3)]
    c += [(25.0, "impact", 0.9), (25.6, "pop", 0.5), (26.4, "pop", 0.6), (26.7, "tap", 0.9), (26.9, "notify", 0.6)]
    c += [(29.0, "final_hit", 1.0), (29.1, "sparkle", 0.6), (30.0, "shimmer", 0.6)]
    return c


# ================================================================ render
STORY = None


def render(i):
    t = i / FPS
    for s, e, name in SCENES:
        if s <= t < e:
            f = SCENE_FN[name](t, t - s, STORY)
            break
    else:
        f = np.zeros((H, W, 3), np.float32)
    f = f * vignette() + grain_bank()[i % 6] * 0.016
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    key = sys.argv[1]
    STORY = STORIES[key]
    vignette(), grain_bank(), logo_meta()
    os.makedirs(BUILD, exist_ok=True)
    if "--stills" in sys.argv:
        d = os.path.join(BUILD, "stills", key)
        os.makedirs(d, exist_ok=True)
        for ts in sys.argv[sys.argv.index("--stills") + 1:]:
            cv2.imwrite(os.path.join(d, f"{float(ts):05.2f}.png"), render(int(round(float(ts) * FPS)))[:, :, ::-1])
        sys.exit()
    from multiprocessing import Pool
    n = int(DURATION * FPS)
    out = os.path.join(BUILD, f"{key}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, frame in enumerate(pool.imap(render, range(n), chunksize=4)):
            ff.stdin.write(frame.tobytes())
            if k % 240 == 0:
                print(f"{key}: frame {k}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)
