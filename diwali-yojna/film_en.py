"""'The Diwali Shop Upgrade': premium English cut of the Diwali Reel (9:16, ~38 s).

Same four AI shots of the shopkeeper as film.py, re-told in English in the Varnik Labs
brand: Royal Purple / Electric Lime, Sora + DM Sans, glass cards, the real logo, a cinematic
score, and Gia (ElevenLabs) reading the VO. No parody styling.

  bash fetch.sh $ASSETS && bash fetch_en.sh $ASSETS
  python3 film_en.py $ASSETS out.mp4
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "voiceover"))
sys.path.insert(0, os.path.join(HERE, "..", "scroll-stopper"))
import lib as L  # noqa: E402
from mix import VO_CHAIN, dialogue_edit, envelope, ffmpeg_audio, rms_db, room_ir  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
A = sys.argv[1] if len(sys.argv) > 1 else "/home/user/diwali"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(A, "diwali-upgrade.mp4")
BF = os.path.join(HERE, "..", "brand", "fonts")

PURPLE, LIME, MIDNIGHT, LAVENDER = (0x6D, 0x28, 0xD9), (0xD4, 0xF5, 0x5A), (0x12, 0x0B, 0x26), (0xA7, 0x8B, 0xFA)
DEEP, WHITE, RED = (52, 16, 128), (255, 255, 255), (235, 72, 72)

T_SHOT1, T_SHOT2 = 5.2, 7.9


def F(name, size):
    return ImageFont.truetype(os.path.join(BF, name + ".ttf"), size)


# ---------------------------------------------------------------------------- voice
def load_vo():
    out = []
    for i, name in enumerate([f"en{k}.mp3" for k in range(10)] + ["signoff.mp3"]):
        x = dialogue_edit(ffmpeg_audio(os.path.join(A, name), VO_CHAIN, os.path.join(A, f"_e{i}.wav")))
        out.append(x * 10 ** ((-17.0 - rms_db(x)) / 20))
    return out


VO = load_vo()
D = [len(x) / SR for x in VO]
# the cut points follow the read (an editor cuts picture to the VO, not the other way round);
# each shot is capped by its 5 s clip
S = {0: 0.75, 1: 5.4}
S[2] = max(7.95, S[1] + D[1] + 0.2)
T_CHECK = min(T_SHOT2 + 4.1, max(10.7, S[2] + D[2] + 0.15))
S[3] = T_CHECK + 0.25
S[4] = S[3] + D[3] + 0.4
S[5] = S[4] + D[4] + 0.45
S[6] = S[5] + D[5] + 0.45
CHECKS = [S[k] + D[k] + 0.05 for k in (4, 5, 6)]
T_SHOT3 = max(21.0, CHECKS[-1] + 0.6)
S[7] = T_SHOT3 + 0.4
T_SHOT4 = min(T_SHOT3 + 4.6, max(T_SHOT3 + 4.0, S[7] + D[7] + 0.05))
S[8] = T_SHOT4 + 0.25
T_CTA = min(T_SHOT4 + 4.7, max(T_SHOT4 + 3.8, S[8] + D[8] + 0.3))
S[9] = T_CTA + 0.35
T_BRAND = max(S[9] + 2.7, S[9] + D[9] + 0.5)
S[10] = T_BRAND + 0.3
DUR = round(S[10] + D[10] + 0.9, 2)
SHOTS = [(T_SHOT1, T_SHOT2, "c1.mp4", 0.0), (T_SHOT2, T_CHECK, "c2.mp4", 0.8),
         (T_SHOT3, T_SHOT4, "c3.mp4", 0.3), (T_SHOT4, T_CTA, "c4.mp4", 0.2)]
CAPTIONS = {1: "Every Diwali, the same story.", 2: "Customers are calling. Nobody's picking up.",
            7: "The result? 47 new orders. Before lunch.", 8: "Same shop. Same sweets. A very different Diwali."}


# ---------------------------------------------------------------------------- drawing helpers
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def pop(t, t0, dur=0.3):
    if t < t0:
        return 0.0
    x = (t - t0) / dur
    return 1.0 if x >= 1 else ease(x) * (1 + 0.14 * np.sin(np.pi * x))


def text_img(text, f, fill, pad=10, tracking=0):
    if tracking:
        widths = [f.getlength(c) for c in text]
        w = int(sum(widths) + tracking * (len(text) - 1)) + 2 * pad
        l, t, r, b = f.getbbox("Ag")
        im = Image.new("RGBA", (w, b - t + 2 * pad), (0, 0, 0, 0))
        d, x = ImageDraw.Draw(im), pad
        for c, cw in zip(text, widths):
            d.text((x, pad - t), c, font=f, fill=fill)
            x += cw + tracking
        return im
    l, t, r, b = f.getbbox(text)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=fill)
    return im


def pill(text, f, bg, fg, padx=46, pady=20, border=None):
    t = text_img(text, f, fg, pad=0)
    im = Image.new("RGBA", (t.width + 2 * padx, t.height + 2 * pady), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bg,
                                         outline=border, width=3 if border else 0)
    im.alpha_composite(t, (padx, pady))
    return im


def put(base, im, cx, cy, s=1.0, alpha=1.0):
    if s <= 0.01 or alpha <= 0.01:
        return
    if abs(s - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if alpha < 0.999:
        a = np.array(im)
        a[..., 3] = (a[..., 3] * alpha).astype(np.uint8)
        im = Image.fromarray(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def logo_rgba(width, color=LIME):
    f = np.zeros((H, W, 3), np.float32)
    m = np.zeros((H, W), np.float32)
    L.draw_logo(f, W / 2, H / 2, width, mark=color, word=color, mask=m)
    ys, xs = np.nonzero(m > 0.01)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgba = np.zeros(m.shape + (4,), np.uint8)
    rgba[..., :3] = color
    rgba[..., 3] = (m.clip(0, 1) * 255).astype(np.uint8)
    return Image.fromarray(rgba)


BG = L.bg(PURPLE, DEEP, r=0.9)


def brand_bg(t):
    f = L.dot_grid(BG.copy(), t, a=0.07)
    return f


def to_pil(f):
    return Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def notif(title, body, dot):
    im = Image.new("RGBA", (900, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 899, 149], radius=36, fill=(22, 16, 40, 225), outline=(167, 139, 250, 120), width=2)
    d.ellipse([34, 39, 106, 111], fill=dot)
    d.text((132, 26), title, font=F("DMSans-700", 38), fill=WHITE)
    d.text((132, 80), body, font=F("DMSans-500", 33), fill=(205, 196, 235))
    d.text((800, 30), "now", font=F("DMSans-500", 28), fill=(160, 150, 190))
    return im


def check_card(title, sub, done):
    im = Image.new("RGBA", (940, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 939, 209], radius=40, fill=(18, 11, 38, 165),
                        outline=LIME if done else (167, 139, 250, 150), width=4 if done else 2)
    if done:
        d.ellipse([40, 63, 124, 147], fill=LIME)
        d.line([(62, 106), (78, 123), (104, 88)], fill=MIDNIGHT, width=9, joint="curve")
    else:
        d.ellipse([40, 63, 124, 147], outline=(167, 139, 250, 200), width=4)
    d.text((158, 42), title, font=F("Sora-700", 54), fill=WHITE)
    d.text((158, 118), sub, font=F("DMSans-500", 38), fill=LAVENDER)
    return im


def caption(text):
    f = F("Sora-700", 48)
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if f.getlength(trial) > 860 and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    lines.append(cur)
    ims = [text_img(l_, f, WHITE, pad=4) for l_ in lines]
    im = Image.new("RGBA", (max(i.width for i in ims) + 64, sum(i.height for i in ims) + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=30, fill=PURPLE + (220,))
    y = 20
    for i in ims:
        im.alpha_composite(i, ((im.width - i.width) // 2, y))
        y += i.height
    return im


# static layers
LOGO_SM, WATERMARK = logo_rgba(470), logo_rgba(220)
EYEBROW = text_img("A DIWALI PUBLIC SERVICE ANNOUNCEMENT", F("DMSans-700", 30), LAVENDER, tracking=5)
T1 = text_img("The Diwali", F("Sora-800", 128), WHITE)
T2 = text_img("Shop Upgrade", F("Sora-800", 128), LIME)
T3 = text_img("2 0 2 6", F("DMSans-700", 44), LAVENDER)
UP_EYEBROW = text_img("THE UPGRADE", F("DMSans-700", 32), LIME, tracking=6)
UP_HEAD = text_img("Three fixes.", F("Sora-800", 100), WHITE)
UP_HEAD2 = text_img("One weekend.", F("Sora-800", 100), LIME)
ITEMS = [("WhatsApp replies", "in under 10 seconds"), ("Photos", "from this decade"),
         ("A website", "that loads before the chai gets cold")]
CARDS = [(check_card(a, b, False), check_card(a, b, True)) for a, b in ITEMS]
NOTIF2 = [notif("Missed call", "Customer  ·  9:12 pm", RED), notif("WhatsApp", "\"Is the shop open today?\"", (37, 211, 102)),
          notif("14 missed calls", "Sharma Sweets", RED)]
NOTIF3 = [notif("New order", "Kaju katli  ·  1 kg", LIME), notif("New order", "Diwali gift box  ·  x 12", LIME)]
ORDERS = pill("47 new orders today", F("Sora-800", 56), LIME + (255,), MIDNIGHT)
CTA1 = text_img("Want this Diwali", F("Sora-800", 92), WHITE)
CTA2 = text_img("for your shop?", F("Sora-800", 92), LIME)
CTA_PILL = pill("Comment  DIWALI", F("Sora-800", 78), LIME + (255,), MIDNIGHT, padx=56, pady=26)
CTA_SUB = text_img("Free 15-minute audit, on WhatsApp", F("DMSans-500", 40), LAVENDER)
TAG = text_img("DESIGN.   TECH.   GROWTH.", F("DMSans-700", 34), WHITE, tracking=7)
END_PILL = pill("Comment  DIWALI", F("Sora-800", 54), (0, 0, 0, 0), LIME, border=LIME)
CAPS = {k: caption(v) for k, v in CAPTIONS.items()}

yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.3 * (((xx - W / 2) / (W / 1.5)) ** 2 + ((yy - H / 2) / (H / 1.5)) ** 2)).clip(0.6, 1)[..., None].astype(np.float32)
SHADE = np.clip((yy - 1250) / 670, 0, 1)[..., None].astype(np.float32) * 0.45  # bottom shade under captions


# ---------------------------------------------------------------------------- clips
class Clip:
    def __init__(self, path, start, dur):
        vf = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(start), "-i", path, "-t", str(dur + 0.2),
                                   "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.last = None

    def next(self):
        b = self.p.stdout.read(W * H * 3)
        if len(b) == W * H * 3:
            self.last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        return self.last


clips = {}


def shot(t):
    for i, (a, b, f, off) in enumerate(SHOTS):
        if a <= t < b:
            if i not in clips:
                clips[i] = Clip(os.path.join(A, f), off, b - a)
            x = clips[i].next().astype(np.float32) / 255
            lt = t - a
            z = 1 + 0.04 * lt / (b - a)  # slow push-in, keeps the AI shots alive
            x = L.zoom(x, z, W / 2, H / 2) if z > 1.001 else x
            x = x * VIG * (1 - SHADE)
            return to_pil(x)
    return None


# ---------------------------------------------------------------------------- scenes
def title(t):
    im = to_pil(brand_bg(t) * min(1, t / 0.3))
    put(im, LOGO_SM, W / 2, 340, pop(t, 0.2, 0.4))
    put(im, EYEBROW, W / 2, 760, 1, ease((t - 0.6) / 0.4))
    put(im, T1, W / 2, 900, pop(t, 0.9))
    put(im, T2, W / 2, 1050, pop(t, 1.15))
    put(im, T3, W / 2, 1210, 1, ease((t - 1.6) / 0.4))
    ln = int(360 * ease((t - 1.7) / 0.6))
    if ln > 2:
        ImageDraw.Draw(im).rounded_rectangle([W / 2 - ln / 2, 1290, W / 2 + ln / 2, 1296], radius=3, fill=LIME)
    return im


def upgrade(t):
    im = to_pil(brand_bg(t))
    put(im, UP_EYEBROW, W / 2, 300, 1, ease((t - T_CHECK - 0.1) / 0.3))
    put(im, UP_HEAD, W / 2, 420, pop(t, S[3] - 0.05))
    put(im, UP_HEAD2, W / 2, 530, pop(t, S[3] + 0.35))
    for k in range(3):
        t_in = S[4 + k] - 0.15
        if t < t_in:
            continue
        a = ease((t - t_in) / 0.35)
        done = t >= CHECKS[k]
        card = CARDS[k][1 if done else 0]
        s = 1 + 0.04 * max(0.0, 1 - (t - CHECKS[k]) / 0.2) if done else 1
        put(im, card, W / 2 + 60 * (1 - a), 800 + 250 * k, s, a)
    return im


def cta(t):
    im = to_pil(brand_bg(t))
    put(im, LOGO_SM, W / 2, 340, 0.75, ease((t - T_CTA) / 0.4))
    put(im, CTA1, W / 2, 760, pop(t, T_CTA + 0.15))
    put(im, CTA2, W / 2, 880, pop(t, T_CTA + 0.4))
    pulse = 1 + 0.03 * np.sin(2 * np.pi * 2 * (t - S[9] - 1.5)) if t > S[9] + 1.5 else 1
    put(im, CTA_PILL, W / 2, 1150, pop(t, S[9] + 1.1, 0.32) * pulse)
    put(im, CTA_SUB, W / 2, 1310, 1, ease((t - S[9] - 1.5) / 0.4))
    return im


def brand(t):
    lt = t - T_BRAND
    f = brand_bg(t)
    mask = np.zeros((H, W), np.float32)
    L.draw_logo(f, W / 2, 820, 860, mask=mask, t=lt, t0=0.05)
    f = L.add_glow(f, mask, LIME, 0.35, 30)
    f = L.light_sweep(f, mask, L.prog(lt, 1.0, 0.8))
    f = L.flash(f, WHITE, 0.6 * (1 - L.ease_out_cubic(L.prog(lt, 0, 0.3))))
    im = to_pil(f)
    put(im, TAG, W / 2, 985, 1, ease((lt - 0.7) / 0.5))
    put(im, END_PILL, W / 2, 1200, 1, ease((lt - 1.2) / 0.5))
    return im


def overlays(im, t):
    if any(a <= t < b for a, b, _, _ in SHOTS):
        im.alpha_composite(WATERMARK, (W - WATERMARK.width - 56, 120))
    if T_SHOT2 <= t < T_CHECK:  # notifications pile up, unanswered
        for k, n in enumerate(NOTIF2):
            t0 = T_SHOT2 + 0.3 + 0.7 * k
            if t >= t0:
                a = ease((t - t0) / 0.3)
                put(im, n, W / 2, 330 + 175 * k - 40 * (1 - a), 1, a)
    if T_SHOT3 <= t < T_SHOT4:
        for k, n in enumerate(NOTIF3):
            t0 = T_SHOT3 + 0.5 + 0.6 * k
            if t >= t0:
                a = ease((t - t0) / 0.3)
                put(im, n, W / 2, 330 + 175 * k - 40 * (1 - a), 1, a)
        put(im, ORDERS, W / 2, 720, pop(t, T_SHOT3 + 1.9))
    for k, c in CAPS.items():
        if S[k] <= t < S[k] + D[k] + 0.3:
            put(im, c, W / 2, 1560, 1, min(1.0, (t - S[k]) / 0.12))
    return im


def frame(t):
    if t < T_SHOT1:
        im = title(t)
    elif T_CHECK <= t < T_SHOT3:
        im = upgrade(t)
    elif T_CTA <= t < T_BRAND:
        im = cta(t)
    elif t >= T_BRAND:
        im = brand(t)
    else:
        im = shot(t)
    im = overlays(im, t)
    a = np.array(im.convert("RGB")).astype(np.float32)
    for ts in (T_SHOT1, T_CHECK, T_SHOT3, T_CTA):  # quick light flash on the big cuts
        if 0 <= t - ts < 0.1:
            a = a + (1 - (t - ts) / 0.1) * (140 if ts == T_SHOT3 else 60)
    return a.clip(0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------- audio
def sfx_bank(rng):
    t = lambda d_: np.arange(int(d_ * SR)) / SR  # noqa: E731
    bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)  # noqa: E731
    out = {}
    tt = t(0.5)
    out["whoosh"] = bp(rng.normal(0, 1, len(tt)), 300, 5000) * np.sin(np.pi * tt / 0.5) ** 2 * 0.3
    tt = t(0.12)
    out["pop"] = np.sin(2 * np.pi * (500 + 1000 * tt / 0.12) * tt) * np.exp(-tt * 30) * 0.4
    tt = t(0.9)
    out["ding"] = (np.sin(2 * np.pi * 1568 * tt) * 0.5 + np.sin(2 * np.pi * 2349 * tt) * 0.3) * np.exp(-tt * 6) * 0.45
    tt = t(0.35)
    out["notify"] = (np.sin(2 * np.pi * 1318 * tt) * (tt < 0.12) + np.sin(2 * np.pi * 1760 * tt) * (tt >= 0.12)) * np.exp(-tt * 9) * 0.3
    tt = t(0.6)
    buzz = np.sign(np.sin(2 * np.pi * 160 * tt)) * 0.18 * ((tt % 0.3) < 0.2)
    out["buzz"] = sosfilt(butter(2, 800, "low", fs=SR, output="sos"), buzz)
    tt = t(1.4)
    out["riser"] = bp(rng.normal(0, 1, len(tt)), 800, 9000) * (tt / 1.4) ** 2.5 * 0.35
    tt = t(1.4)
    out["shimmer"] = sum(np.sin(2 * np.pi * f_ * tt) * a_ for f_, a_ in [(2637, .3), (3520, .25), (4186, .2)]) * np.exp(-tt * 3) * 0.35
    return out


def onset_near(x, t, win=0.3):
    m = x.mean(1)
    a, b = int((t - win) * SR), int((t + win) * SR)
    h = int(0.01 * SR)
    seg = m[a:b]
    n = len(seg) // h
    e = 10 * np.log10(np.mean(seg[: n * h].reshape(n, h) ** 2, 1) + 1e-10)
    return (a + (int(np.argmax(e[5:] - e[:-5])) + 5) * h) / SR


def build_audio(path):
    rng = np.random.default_rng(3)
    n = int(DUR * SR)
    vo = np.zeros(n, np.float32)
    for k, x in enumerate(VO):
        s = int(S[k] * SR)
        vo[s:s + len(x)] += x[: n - s]
    talk = envelope(vo)
    duck = 10 ** (-10 * talk / 20)
    mus = np.zeros((n, 2), np.float32)
    # first half: calm sitar ambience
    a = ffmpeg_audio(os.path.join(A, "m344.mp3"), f"atrim=0:{T_SHOT3 + 0.5},aformat=channel_layouts=stereo",
                     os.path.join(A, "_a.wav"))
    ramp = np.clip(np.arange(len(a)) / (0.6 * SR), 0, 1) * np.clip((T_SHOT3 * SR - np.arange(len(a))) / (0.4 * SR), 0, 1)
    mus[: len(a)] += a[:n] * ramp[: n, None] * 0.5
    # payoff: "A New Life" (Mixkit #543) with its lift placed on the cut to the busy shop
    full = ffmpeg_audio(os.path.join(A, "m543.mp3"), "aformat=channel_layouts=stereo", os.path.join(A, "_b.wav"))
    lift = onset_near(full, 24.65)
    pre = 1.2
    seg = full[int((lift - pre) * SR): int((lift - pre) * SR) + int((DUR - T_SHOT3 + pre) * SR)]
    s0 = int((T_SHOT3 - pre) * SR)
    seg = seg[: n - s0]
    env = np.clip(np.arange(len(seg)) / (pre * SR), 0, 1) ** 2 * np.clip((n - s0 - np.arange(len(seg))) / (1.8 * SR), 0, 1) ** 1.5
    mus[s0:s0 + len(seg)] += seg * env[:, None] * 0.85

    sfx = np.zeros(n, np.float32)
    bank = sfx_bank(rng)

    def at(name, t0, g=1.0):
        x = bank[name] * g
        s = int(t0 * SR)
        sfx[s:s + len(x)] += x[: n - s]

    at("pop", 0.2)
    at("pop", 0.9, 0.7)
    at("pop", 1.15, 0.7)
    for t0 in (T_SHOT1, T_CHECK, T_CTA, T_BRAND):
        at("whoosh", t0 - 0.25)
    for k in range(3):
        at("buzz" if k != 1 else "notify", T_SHOT2 + 0.3 + 0.7 * k)
    for t0 in CHECKS:
        at("ding", t0)
    at("riser", T_SHOT3 - 1.4)
    at("shimmer", T_SHOT3, 0.8)
    for k in range(2):
        at("notify", T_SHOT3 + 0.5 + 0.6 * k)
    at("pop", T_SHOT3 + 1.9)
    at("pop", S[9] + 1.1)
    at("shimmer", T_BRAND, 0.7)

    voice = vo + np.convolve(vo, room_ir()[:2000], mode="same") * 0.05
    on = talk > 0.5
    bed = mus.mean(1) * duck + sfx * 10 ** (-3 * talk / 20)
    bed_db = 20 * np.log10(np.sqrt(np.mean(bed[on] ** 2)) + 1e-9)
    vo_db = 20 * np.log10(np.sqrt(np.mean(voice[on] ** 2)) + 1e-9)
    voice *= 10 ** ((bed_db + 10 - vo_db) / 20)
    mix = mus * duck[:, None] + (sfx * 10 ** (-3 * talk / 20))[:, None] + voice[:, None]
    wavfile.write(path, SR, (mix / (np.max(np.abs(mix)) + 1e-9) * 0.9).astype(np.float32))
    return lift


def main():
    wav = os.path.join(A, "_mix_en.wav")
    lift = build_audio(wav)
    pic = os.path.join(A, "_pic_en.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                            "-pix_fmt", "yuv420p", pic], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        enc.stdin.write(frame(i / FPS).tobytes())
    enc.stdin.close()
    enc.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "alimiter=limit=0.7:attack=2:release=40:level=false,loudnorm=I=-14:TP=-2:LRA=9,aresample=48000,"
                    "aformat=sample_fmts=fltp:channel_layouts=stereo", "-c:a", "aac", "-b:a", "256k",
                    "-movflags", "+faststart", "-shortest", OUT], check=True)
    print("cuts:", [round(x, 2) for x in (T_CHECK, T_SHOT3, T_SHOT4, T_CTA, T_BRAND, DUR)])
    print("lines:", {k: (round(S[k], 2), round(D[k], 2)) for k in sorted(S)})
    print("checks:", [round(c, 2) for c in CHECKS], "music lift:", round(lift, 2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
