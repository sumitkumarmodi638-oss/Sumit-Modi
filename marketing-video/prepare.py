"""Extract source assets for the brand film.

Usage: python3 prepare.py <Brand_Identity.pdf>

- Pulls the full-page photography out of the brand identity PDF (pdfimages)
- Downloads Sora + DM Sans (the brand typefaces) from Google Fonts
- Cuts the logo out of the closing slide and splits it into the three mark
  "sparks" (Design, Tech, Growth) plus one image per wordmark letter, so the
  logo can be animated the way the brand's motion page describes.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")


def extract_photos(pdf):
    out = os.path.join(BUILD, "img")
    os.makedirs(out, exist_ok=True)
    subprocess.run(["pdfimages", "-j", pdf, os.path.join(out, "b")], check=True)


def fetch_fonts():
    out = os.path.join(BUILD, "fonts")
    os.makedirs(out, exist_ok=True)
    for family, weights in (("Sora", "600;700;800"), ("DM+Sans", "400;500;700")):
        req = urllib.request.Request(
            f"https://fonts.googleapis.com/css2?family={family}:wght@{weights}",
            headers={"User-Agent": "Mozilla/4.0"},  # old UA -> plain TTF urls
        )
        css = urllib.request.urlopen(req).read().decode()
        for weight, url in re.findall(r"font-weight: (\d+);.*?url\(([^)]+\.ttf)\)", css, re.S):
            name = family.replace("+", "")
            urllib.request.urlretrieve(url, os.path.join(out, f"{name}-{weight}.ttf"))


def cut_logo():
    """Lime logo on Royal Purple (closing slide) -> 3x supersampled alpha pieces."""
    im = cv2.imread(os.path.join(BUILD, "img", "b-050.jpg"))[:, :, ::-1].astype(np.float32)
    crop = im[530:820, 740:2140]
    lime = np.array([0xD4, 0xF5, 0x5A], np.float32)
    bg = np.array([70, 24, 149], np.float32)
    v = lime - bg
    t = np.clip(((crop - bg) @ v) / (v @ v), 0, 1)
    t = cv2.resize(t, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    t = cv2.GaussianBlur(t, (0, 0), 1.2)
    alpha = np.clip((t - 0.5) * 4 + 0.5, 0, 1)

    n, lab, st, _ = cv2.connectedComponentsWithStats((alpha > 0.5).astype(np.uint8))
    comps = sorted(
        [(int(st[i][0]), int(st[i][1]), int(st[i][2]), int(st[i][3]), i) for i in range(1, n) if st[i][4] > 500]
    )
    # Mark = the 3 leftmost blobs; everything right of it is the wordmark.
    mark = [c for c in comps if c[0] < 1000]
    letters = [c for c in comps if c[0] >= 1000]
    # Merge the dot of the "i" with its stem (overlapping x ranges).
    merged = []
    for c in letters:
        p = merged[-1][0] if merged else None
        if p and min(c[0] + c[2], p[0] + p[2]) - max(c[0], p[0]) > 0.6 * min(c[2], p[2]):
            merged[-1].append(c)
        else:
            merged.append([c])

    out = os.path.join(BUILD, "logo")
    os.makedirs(out, exist_ok=True)
    grow = cv2.dilate((lab > 0).astype(np.uint8), np.ones((5, 5), np.uint8))

    def save(group, name):
        x0 = min(c[0] for c in group) - 4
        y0 = min(c[1] for c in group) - 4
        x1 = max(c[0] + c[2] for c in group) + 4
        y1 = max(c[1] + c[3] for c in group) + 4
        m = np.zeros(lab.shape, bool)
        for c in group:
            m |= lab == c[4]
        m = cv2.dilate(m.astype(np.uint8), np.ones((7, 7), np.uint8)) & grow
        a = (alpha * m)[y0:y1, x0:x1]
        cv2.imwrite(os.path.join(out, name + ".png"), (a * 255).astype(np.uint8))
        return dict(name=name, x=x0, y=y0, w=x1 - x0, h=y1 - y0)

    # Mark blobs: base is the widest/lowest, left blade has smallest x of the top two.
    base = max(mark, key=lambda c: c[1] + c[3])
    blades = sorted([c for c in mark if c is not base])
    pieces = {
        "design": save([blades[0]], "design"),
        "tech": save([blades[1]], "tech"),
        "growth": save([base], "growth"),
        "letters": [save(g, f"letter{i}") for i, g in enumerate(merged)],
        "W": alpha.shape[1],
        "H": alpha.shape[0],
    }
    cv2.imwrite(os.path.join(out, "full.png"), (alpha * 255).astype(np.uint8))
    json.dump(pieces, open(os.path.join(out, "logo.json"), "w"), indent=1)


if __name__ == "__main__":
    extract_photos(sys.argv[1])
    fetch_fonts()
    cut_logo()
    print("assets ready in", BUILD)
