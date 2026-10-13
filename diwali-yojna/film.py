"""'Pradhan Dukaan Digital Yojna 2026': a Diwali parody Reel for Varnik Labs (9:16, 37.5 s).

A deadpan spoof of an old public-service ad. Clearly marked as a parody: no emblems, no real
ministry or scheme names. Picture: four AI shots of one shopkeeper (same face throughout), plus
our own title card, approval-stamp checklist, application form and Varnik Labs logo end card, all
in the brand palette (brand/README.md). Hindi VO by
ElevenLabs "Gia", Hinglish captions burned in for sound-off viewing.

Usage (assets fetched by fetch.sh into $ASSETS):
  python3 film.py $ASSETS out.mp4
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "voiceover"))
sys.path.insert(0, os.path.join(HERE, "..", "scroll-stopper"))
import lib as L  # noqa: E402  (brand logo, gradients, glow; falls back to ../brand in a plain clone)
from mix import VO_CHAIN, dialogue_edit, envelope, ffmpeg_audio, rms_db, room_ir  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
DUR = 37.5
A = sys.argv[1] if len(sys.argv) > 1 else "/home/user/diwali"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(A, "diwali-yojna.mp4")
F = os.path.join(A, "fonts")

# Varnik Labs palette (brand/README.md): the parody 'government' look is drawn in our colours
PURPLE, LIME, MIDNIGHT, LAVENDER = (0x6D, 0x28, 0xD9), (0xD4, 0xF5, 0x5A), (0x12, 0x0B, 0x26), (0xA7, 0x8B, 0xFA)
DEEP = (52, 16, 128)
NAVY, SAFFRON, GREEN = PURPLE, LIME, PURPLE  # header bars / accents / ticks
PAPER, INK, RED, GREY = (246, 243, 252), (28, 24, 48), (198, 40, 40), (110, 104, 128)
BRAND_F = os.path.join(HERE, "..", "brand", "fonts")

# ---------------------------------------------------------------------------- timeline
T_SHOT1, T_SHOT2, T_CHECK, T_SHOT3, T_SHOT4, T_END, T_BRAND = 5.2, 7.9, 10.7, 21.0, 25.2, 29.6, 33.2
SHOTS = [(T_SHOT1, T_SHOT2, "c1.mp4", 0.0), (T_SHOT2, T_CHECK, "c2.mp4", 0.8),
         (T_SHOT3, T_SHOT4, "c3.mp4", 0.3), (T_SHOT4, T_END, "c4.mp4", 0.2)]


def font(name, size):
    return ImageFont.truetype(os.path.join(F, name), size, layout_engine=ImageFont.Layout.RAQM)


ROZHA = lambda s: font("RozhaOne-Regular.ttf", s)  # noqa: E731
MUKTA_XB = lambda s: font("Mukta-ExtraBold.ttf", s)  # noqa: E731
MUKTA_B = lambda s: font("Mukta-Bold.ttf", s)  # noqa: E731
MUKTA = lambda s: font("Mukta-Regular.ttf", s)  # noqa: E731
SORA = lambda s: ImageFont.truetype(os.path.join(BRAND_F, "Sora-800.ttf"), s)  # noqa: E731
SORA7 = lambda s: ImageFont.truetype(os.path.join(BRAND_F, "Sora-700.ttf"), s)  # noqa: E731
DMS = lambda s: ImageFont.truetype(os.path.join(BRAND_F, "DMSans-700.ttf"), s)  # noqa: E731


# ---------------------------------------------------------------------------- voice
def load_vo():
    """Clean + trim each line; returns list of (array, seconds)."""
    takes = [os.path.join(A, f"vo{i}.mp3") for i in range(9)] + [os.path.join(A, "signoff.mp3")]
    out = []
    for i, p in enumerate(takes):
        x = dialogue_edit(ffmpeg_audio(p, VO_CHAIN, os.path.join(A, f"_v{i}.wav")))
        x = x * 10 ** ((-17.0 - rms_db(x)) / 20)
        out.append(x)
    return out


VO = load_vo()
D = [len(x) / SR for x in VO]
S = {}  # line index -> start time
S[0] = 0.35
S[1] = 5.35
S[2] = max(7.95, S[1] + D[1] + 0.15)
S[3] = 11.0
S[4] = S[3] + D[3] + 0.85
S[5] = S[4] + D[4] + 0.85
S[6] = 21.35
S[7] = S[6] + D[6] + 0.35
S[8] = 29.95
S[9] = max(33.45, S[8] + D[8] + 0.4)
STAMPS = [S[k] + D[k] + 0.12 for k in (3, 4, 5)]
assert STAMPS[-1] < T_SHOT3 - 0.3, STAMPS
assert S[7] + D[7] < T_END + 0.2, (S[7], D[7])
assert S[8] + D[8] < T_BRAND + 0.1, (S[8], D[8])
CAPTIONS = [(1, "Is Diwali, har dukaan ko milega…"), (2, "Ek Google profile… jo sach mein khulta hai."),
            (6, "Laabh: zyada grahak. Nuksaan: kuch nahi."), (7, "Bas thodi si sharm… ki padosi pehle kar gaya.")]

# ---------------------------------------------------------------------------- static layers
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.35 * (((xx - W / 2) / (W / 1.6)) ** 2 + ((yy - H / 2) / (H / 1.6)) ** 2)).clip(0.55, 1)[..., None]
SCAN = np.where(yy % 4 == 0, 0.92, 1.0)[..., None]
TV = (VIG * SCAN).astype(np.float32)
# a few fixed grain plates cycled at 12 fps: reads as film grain but stays compressible
GRAIN = [rng.normal(0, 3, (H, W, 1)).astype(np.float32) for _ in range(4)]


def paper():
    base = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32)
    n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    n = np.array(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)) - 128.0
    return Image.fromarray((base + n[..., None] * 0.35).clip(0, 255).astype(np.uint8))


def centered(d, y, text, f, fill, stroke=0, sfill=(0, 0, 0)):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)


def text_img(text, f, fill, stroke=0, sfill=(0, 0, 0), pad=20):
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im


def pill(text, f, bg, fg=(255, 255, 255), padx=34, pady=14):
    t = text_img(text, f, fg, pad=0)
    im = Image.new("RGBA", (t.width + 2 * padx, t.height + 2 * pady), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bg)
    im.alpha_composite(t, (padx, pady))
    return im


def stamp(text, sub=None, color=RED, size=110, angle=-11):
    f = MUKTA_XB(size)
    t = text_img(text, f, color + (255,), pad=0)
    sw = t.width + 70
    sh = t.height + (90 if sub else 50)
    im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, sw - 5, sh - 5], radius=18, outline=color + (255,), width=9)
    d.rounded_rectangle([18, 18, sw - 19, sh - 19], radius=12, outline=color + (255,), width=3)
    im.alpha_composite(t, ((sw - t.width) // 2, 22))
    if sub:
        fs = MUKTA_B(36)
        w = d.textlength(sub, font=fs)
        d.text(((sw - w) / 2, sh - 70), sub, font=fs, fill=color + (255,))
    a = np.array(im).astype(np.float32)
    ink = rng.uniform(0.55, 1.0, a.shape[:2])  # rough rubber-stamp ink
    ink[rng.random(a.shape[:2]) < 0.06] = 0.15
    a[..., 3] *= ink
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)


def paste_scaled(base, im, cx, cy, s=1.0, alpha=1.0):
    if s <= 0.01 or alpha <= 0.01:
        return
    if abs(s - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if alpha < 0.999:
        a = np.array(im)
        a[..., 3] = (a[..., 3] * alpha).astype(np.uint8)
        im = Image.fromarray(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def pop(t, t0, dur=0.28):
    """Scale for a pop-in with a small overshoot."""
    if t < t0:
        return 0.0
    x = (t - t0) / dur
    if x >= 1:
        return 1.0
    return ease(x) * (1 + 0.18 * np.sin(np.pi * x))


# title layers
def logo_rgba(width, color=LIME):
    """The real Varnik Labs lockup as an RGBA image."""
    f = np.zeros((H, W, 3), np.float32)
    m = np.zeros((H, W), np.float32)
    L.draw_logo(f, W / 2, H / 2, width, mark=color, word=color, mask=m)
    ys, xs = np.nonzero(m > 0.01)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgba = np.zeros(m.shape + (4,), np.uint8)
    rgba[..., :3] = color
    rgba[..., 3] = (m.clip(0, 1) * 255).astype(np.uint8)
    return Image.fromarray(rgba)


TITLE_LOGO = logo_rgba(560)
TITLE_TOP = text_img("प्रस्तुत करते हैं", MUKTA_B(46), LAVENDER + (255,))
TITLE_L1 = text_img("प्रधान दुकान", ROZHA(150), (255, 255, 255, 255))
TITLE_L2 = text_img("डिजिटल योजना", ROZHA(150), (255, 255, 255, 255))
TITLE_YR = text_img("2026", SORA(140), LIME + (255,))
TITLE_PARODY = text_img("एक व्यंग्य  ·  A PARODY", MUKTA_B(46), LAVENDER + (255,))
TITLE_BG = None  # purple gradient, built on first use

BADGE = pill("जनहित में जारी", MUKTA_B(46), PURPLE + (235,), fg=LIME)
WATERMARK = logo_rgba(230)

# checklist card
CHECK_BG = paper()
d = ImageDraw.Draw(CHECK_BG)
d.rectangle([0, 200, W, 430], fill=NAVY)
centered(d, 205, "योजना के लाभ", ROZHA(118), (255, 255, 255))
centered(d, 352, "प्रधान दुकान डिजिटल योजना 2026", MUKTA_B(46), SAFFRON)
d.text((90, 470), "प्रपत्र सं. : दिवाली / 2026 / 001", font=MUKTA(42), fill=GREY)
d.line([90, 1690, 560, 1690], fill=INK, width=3)
d.text((90, 1700), "हस्ताक्षर (अधिकारी)", font=MUKTA(40), fill=GREY)
ITEM_Y = [640, 960, 1280]
ITEMS = [("WhatsApp पर जवाब", "10 सेकंड में"), ("फ़ोटो", "इसी दशक की"), ("वेबसाइट", "चाय ठंडी होने से पहले खुले")]
ITEM_IMG = []
for main, sub in ITEMS:
    im = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rectangle([90, 40, 180, 130], outline=INK, width=6)
    dd.text((215, 14), main, font=MUKTA_XB(72), fill=INK)
    dd.text((215, 122), sub, font=MUKTA_B(48), fill=GREY)
    dd.line([90, 230, 990, 230], fill=(190, 178, 150), width=2)
    ITEM_IMG.append(im)
TICK = Image.new("RGBA", (130, 130), (0, 0, 0, 0))
ImageDraw.Draw(TICK).line([(18, 70), (52, 108), (122, 10)], fill=GREEN + (255,), width=16, joint="curve")
APPROVED = stamp("स्वीकृत", color=PURPLE, size=68, angle=-9)

# end card
END_BG = paper()
d = ImageDraw.Draw(END_BG)
d.rectangle([0, 180, W, 420], fill=NAVY)
centered(d, 190, "आवेदन पत्र", ROZHA(130), (255, 255, 255))
centered(d, 352, "दिवाली डिजिटल योजना 2026", MUKTA_B(44), SAFFRON)
d.text((80, 500), "दुकान का नाम :", font=MUKTA_B(56), fill=INK)
d.line([480, 575, 1000, 575], fill=INK, width=3)
d.text((80, 630), "समय सीमा :", font=MUKTA_B(56), fill=INK)
d.line([400, 705, 1000, 705], fill=INK, width=3)
d.rounded_rectangle([70, 790, 1010, 1300], radius=28, outline=NAVY, width=8)
centered(d, 815, "आवेदन कैसे करें ?", MUKTA_B(62), NAVY)
centered(d, 1700, "* यह कोई सरकारी योजना नहीं है। यह Varnik Labs है।", MUKTA(38), GREY)
centered(d, 1755, "Parody. Not affiliated with any government body or scheme.", MUKTA(32), GREY)
HAND_NAME = text_img("आपकी दुकान", MUKTA_B(60), (90, 40, 200, 255))
HAND_DATE = text_img("दिवाली से पहले!", MUKTA_B(60), (90, 40, 200, 255))
COMMENT = text_img("कमेंट करें", MUKTA_XB(96), INK + (255,))
DIWALI = text_img("DIWALI", SORA(190), PURPLE + (255,), stroke=6, sfill=DEEP)
BRAND_PILL = pill("Comment  DIWALI", SORA(70), LIME + (255,), fg=MIDNIGHT, padx=48, pady=22)
BRAND_TAG = text_img("D E S I G N .    T E C H .    G R O W T H .", DMS(34), (255, 255, 255, 255))
BRAND_FINE = text_img("Parody. Not a government scheme.", DMS(28), LAVENDER + (255,))

CAP_F = SORA7(54)


def caption_img(text):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if CAP_F.getlength(trial) > 900 and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    lines.append(cur)
    ims = [text_img(l_, CAP_F, (255, 255, 255, 255), pad=6) for l_ in lines]
    im = Image.new("RGBA", (max(i.width for i in ims) + 60, sum(i.height for i in ims) + 36), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=28, fill=PURPLE + (225,))
    y = 18
    for i in ims:
        im.alpha_composite(i, ((im.width - i.width) // 2, y))
        y += i.height
    return im


CAP_IMG = {k: caption_img(t) for k, t in CAPTIONS}


# ---------------------------------------------------------------------------- clip readers
class Clip:
    def __init__(self, path, start, dur):
        vf = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-t", str(dur + 0.2),
                                   "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None

    def next(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self.last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        return self.last


clips = {}


def shot_frame(t):
    for i, (a, b, f, off) in enumerate(SHOTS):
        if a <= t < b:
            if i not in clips:
                clips[i] = Clip(os.path.join(A, f), off, b - a)
            return Image.fromarray(clips[i].next()).convert("RGBA")
    return None


# ---------------------------------------------------------------------------- frame renderer
def brand_bg(t):
    f = L.bg(PURPLE, DEEP, r=0.9)
    return L.dot_grid(f, t, a=0.08)


def to_pil(f):
    return Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def title_frame(t):
    if t < 0.25:  # tune-in static
        n = rng.integers(0, 255, (H // 3, W // 3), dtype=np.uint8)
        return Image.fromarray(n).resize((W, H), Image.NEAREST).convert("RGBA")
    im = to_pil(brand_bg(t))
    paste_scaled(im, TITLE_LOGO, W / 2, 330, pop(t, 0.3, 0.35))
    paste_scaled(im, TITLE_TOP, W / 2, 470, 1, ease((t - 0.6) / 0.35))
    paste_scaled(im, TITLE_L1, W / 2, 830, pop(t, 1.0))
    paste_scaled(im, TITLE_L2, W / 2, 1010, pop(t, 1.25))
    paste_scaled(im, TITLE_YR, W / 2, 1230, pop(t, 1.6))
    paste_scaled(im, TITLE_PARODY, W / 2, 1720, 1, ease((t - 2.0) / 0.4))
    return im


def check_frame(t):
    im = CHECK_BG.copy().convert("RGBA")
    for k in range(3):
        t_in = S[3 + k] - 0.05
        if t < t_in:
            continue
        a = ease((t - t_in) / 0.3)
        layer = ITEM_IMG[k]
        im.alpha_composite(layer, (int(40 * (1 - a)), ITEM_Y[k]))
        if t >= STAMPS[k]:
            paste_scaled(im, TICK, 135, ITEM_Y[k] + 80, 1)
            s = 1 + 1.3 * max(0.0, 1 - (t - STAMPS[k]) / 0.11)
            paste_scaled(im, APPROVED, 912, ITEM_Y[k] + 150, s, min(1.0, (t - STAMPS[k]) / 0.05 + 0.4))
    # card shake on each stamp
    dx = sum(12 * np.exp(-(t - ts) * 16) * np.sin((t - ts) * 70) for ts in STAMPS if t >= ts)
    if abs(dx) > 0.5:
        im = Image.fromarray(np.roll(np.array(im), int(dx), axis=1))
    return im


def end_frame(t):
    im = END_BG.copy().convert("RGBA")
    paste_scaled(im, HAND_NAME, 740, 535, 1, ease((t - (T_END + 0.3)) / 0.35))
    paste_scaled(im, HAND_DATE, 700, 665, 1, ease((t - (T_END + 0.8)) / 0.35))
    paste_scaled(im, COMMENT, W / 2, 985, pop(t, S[8] + 0.3))
    pulse = 1 + 0.035 * np.sin(2 * np.pi * 2 * (t - S[8])) if t > S[8] + 1.2 else 1
    paste_scaled(im, DIWALI, W / 2, 1150, pop(t, S[8] + 0.9, 0.32) * pulse)
    return im


def brand_frame(t):
    lt = t - T_BRAND
    f = brand_bg(t)
    mask = np.zeros((H, W), np.float32)
    L.draw_logo(f, W / 2, 800, 860, mask=mask, t=lt, t0=0.05)
    f = L.add_glow(f, mask, LIME, 0.35, 30)
    f = L.light_sweep(f, mask, L.prog(lt, 1.0, 0.8))
    f = L.flash(f, (255, 255, 255), 0.8 * (1 - L.ease_out_cubic(L.prog(lt, 0, 0.3))))
    im = to_pil(f)
    paste_scaled(im, BRAND_TAG, W / 2, 965, 1, ease((lt - 0.7) / 0.5))
    pulse = 1 + 0.03 * np.sin(2 * np.pi * 2 * (lt - 1.6)) if lt > 1.6 else 1
    paste_scaled(im, BRAND_PILL, W / 2, 1200, pop(t, T_BRAND + 0.9, 0.3) * pulse)
    paste_scaled(im, BRAND_FINE, W / 2, 1800, 1, ease((lt - 1.2) / 0.5))
    return im


def overlays(im, t):
    if any(a <= t < b for a, b, _, _ in SHOTS):
        im.alpha_composite(BADGE, (60, 120))
        im.alpha_composite(WATERMARK, (W - WATERMARK.width - 56, 132))
    if T_SHOT2 + 0.6 <= t < T_CHECK:  # missed calls counter
        n = int(min(14, 14 * ease((t - T_SHOT2 - 0.6) / 0.9)))
        paste_scaled(im, pill(f"{n} मिस्ड कॉल", MUKTA_XB(70), RED + (240,)), W / 2, 420, pop(t, T_SHOT2 + 0.6))
    if T_SHOT3 + 0.5 <= t < T_SHOT4:  # orders counter
        n = int(min(47, 47 * ease((t - T_SHOT3 - 0.5) / 1.3)))
        paste_scaled(im, pill(f"{n} नए ऑर्डर", MUKTA_XB(70), LIME + (245,), fg=MIDNIGHT), W / 2, 420, pop(t, T_SHOT3 + 0.5))
    for k, _ in CAPTIONS:
        if S[k] <= t < S[k] + D[k] + 0.25:
            c = CAP_IMG[k]
            im.alpha_composite(c, ((W - c.width) // 2, 1500))
    return im


def frame(t):
    if t < T_SHOT1:
        im, tv = title_frame(t), True
    elif T_CHECK <= t < T_SHOT3:
        im, tv = check_frame(t), True
    elif t >= T_BRAND:
        im, tv = brand_frame(t), False
    elif t >= T_END:
        im, tv = end_frame(t), True
    else:
        im, tv = shot_frame(t), False
    im = overlays(im, t)
    a = np.array(im.convert("RGB")).astype(np.float32)
    if tv:
        a = a * TV + GRAIN[int(t * 12) % 4]
    elif t < T_BRAND:
        a = a * (0.75 + 0.25 * VIG)
    for ts in (T_SHOT3,):  # payoff flash
        if 0 <= t - ts < 0.12:
            a = a + (1 - (t - ts) / 0.12) * 200
    return a.clip(0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------- audio
def music(path, start, dur):
    return ffmpeg_audio(path, f"atrim=start={start}:duration={dur},asetpts=PTS-STARTPTS,aformat=channel_layouts=stereo",
                        os.path.join(A, "_m.wav"))


def best_entry(x, lo=4.0, hi=60.0):
    """Strongest energy rise in [lo, hi] s, for starting the payoff track on a hit."""
    m = x.mean(1)
    h = int(0.05 * SR)
    n = len(m) // h
    e = 10 * np.log10(np.mean(m[: n * h].reshape(n, h) ** 2, 1) + 1e-10)
    best, bt = -1e9, lo
    for i in range(int(lo / 0.05), min(n - 20, int(hi / 0.05))):
        d_ = e[i:i + 20].mean() - e[i - 20:i].mean()
        if d_ > best:
            best, bt = d_, i * 0.05
    return bt


def sfx_bank():
    t = lambda d_: np.arange(int(d_ * SR)) / SR  # noqa: E731
    out = {}
    tt = t(0.45)
    thump = np.sin(2 * np.pi * (55 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    slap = rng.normal(0, 1, len(tt)) * np.exp(-tt * 45)
    slap = sosfilt(butter(2, [300, 3500], "band", fs=SR, output="sos"), slap)
    out["stamp"] = 0.9 * thump + 0.5 * slap
    tt = t(0.25)
    out["static"] = sosfilt(butter(2, 1500, "high", fs=SR, output="sos"), rng.normal(0, 0.35, len(tt))) * np.minimum(1, (0.25 - tt) * 12)
    tt = t(0.12)
    out["pop"] = np.sin(2 * np.pi * (600 + 900 * tt / 0.12) * tt) * np.exp(-tt * 30) * 0.5
    tt = t(1.6)
    bell = sum(a_ * np.sin(2 * np.pi * f_ * tt) for f_, a_ in [(2093, 0.5), (3136, 0.35), (4186, 0.25), (5274, 0.15)])
    out["ching"] = bell * np.exp(-tt * 3.2) * 0.6
    tt = t(2.7)
    buzz = np.sign(np.sin(2 * np.pi * 165 * tt)) * 0.25
    gate = ((tt % 0.9) < 0.55).astype(float)
    out["buzz"] = sosfilt(butter(2, 900, "low", fs=SR, output="sos"), buzz * gate)
    tt = t(0.5)
    out["whoosh"] = sosfilt(butter(2, [400, 4000], "band", fs=SR, output="sos"), rng.normal(0, 1, len(tt))) * np.sin(np.pi * tt / 0.5) ** 2 * 0.35
    return out


def build_audio(path):
    n = int(DUR * SR)
    vo = np.zeros(n, np.float32)
    for k, x in enumerate(VO):
        s = int(S[k] * SR)
        seg = x[: n - s]
        vo[s:s + len(seg)] += seg
    talk = envelope(vo)
    duck = 10 ** (-10 * talk / 20)

    mus = np.zeros((n, 2), np.float32)
    a = music(os.path.join(A, "m344.mp3"), 0.0, T_SHOT3 + 0.3)  # solemn sitar for the 'official' half
    fade = np.clip((T_SHOT3 * SR - np.arange(len(a))) / (0.25 * SR), 0, 1)[:, None]
    mus[: len(a)] += a[: n] * fade[: n] * 0.55
    full = ffmpeg_audio(os.path.join(A, "m205.mp3"), "aformat=channel_layouts=stereo", os.path.join(A, "_m205.wav"))
    entry = best_entry(full)
    b = full[int(entry * SR): int(entry * SR) + int((DUR - T_SHOT3) * SR)]
    s0 = int(T_SHOT3 * SR)
    tail = np.clip((n - s0 - np.arange(len(b))) / (1.5 * SR), 0, 1)[:, None] ** 1.5
    mus[s0:s0 + len(b)] += b * tail * 0.8

    sfx = np.zeros(n, np.float32)
    bank = sfx_bank()

    def put(name, at, g=1.0):
        x = bank[name] * g
        s = int(at * SR)
        sfx[s:s + len(x)] += x[: n - s]

    put("static", 0.0, 0.8)
    for at in (0.3, 1.0, 1.25, 1.6):
        put("pop", at)
    put("whoosh", T_SHOT1 - 0.2)
    put("buzz", T_SHOT2, 0.8)
    put("whoosh", T_CHECK - 0.2)
    for at in STAMPS:
        put("stamp", at, 1.1)
    put("ching", T_SHOT3, 0.9)
    put("whoosh", T_END - 0.2)
    put("pop", S[8] + 0.3)
    put("stamp", S[8] + 0.9, 0.8)
    put("whoosh", T_BRAND - 0.2)
    put("ching", T_BRAND, 0.7)
    put("pop", T_BRAND + 0.9)

    voice = vo + np.convolve(vo, room_ir()[:2000], mode="same") * 0.05
    on = talk > 0.5
    bed = mus.mean(1) * duck + sfx * 10 ** (-3 * talk / 20)
    bed_db = 20 * np.log10(np.sqrt(np.mean(bed[on] ** 2)) + 1e-9)
    vo_db = 20 * np.log10(np.sqrt(np.mean(voice[on] ** 2)) + 1e-9)
    voice *= 10 ** ((bed_db + 10 - vo_db) / 20)
    mix = mus * duck[:, None] + (sfx * 10 ** (-3 * talk / 20))[:, None] + voice[:, None]
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.9
    wavfile.write(path, SR, mix.astype(np.float32))
    return entry


def main():
    wav = os.path.join(A, "_mix.wav")
    entry = build_audio(wav)
    silent = os.path.join(A, "_pic.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                            "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        enc.stdin.write(frame(i / FPS).tobytes())
    enc.stdin.close()
    enc.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "alimiter=limit=0.7:attack=2:release=40:level=false,loudnorm=I=-14:TP=-2:LRA=9,aresample=48000,"
                    "aformat=sample_fmts=fltp:channel_layouts=stereo", "-c:a", "aac", "-b:a", "256k",
                    "-movflags", "+faststart", "-shortest", OUT], check=True)
    print("lines:", {k: (round(S[k], 2), round(D[k], 2)) for k in S})
    print("stamps:", [round(x, 2) for x in STAMPS], "payoff music entry:", round(entry, 2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
