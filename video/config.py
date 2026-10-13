"""Single source of truth for the Sunflour promo: copy, palette, timing.

Edit the copy here and re-run `./build.sh`; video and soundtrack both read
their cue times from this file, so cuts stay locked to the music.
"""

# ---------------------------------------------------------------- brand copy
BRAND = "Sunflour"
URL = "sunflour.in"

HOOK_WORDS = ["FLOUR", "IS JUST", "FLOUR."]   # punched in on beats 1-3
HOOK_TWIST = "...right?"                       # glitch beat
TAGLINE = "Sunshine in every grain."

FEATURES = [  # (kicker, headline) - one per whip-pan card
    ("01", "Milled fresh."),
    ("02", "Soft, fluffy rotis."),
    ("03", "Wholesome by nature."),
    ("04", "Made for Indian kitchens."),
]

FIELD_LINES = ["Grown under the sun.", "Ground with care."]
MONTAGE_WORDS = ["Rotis.", "Parathas.", "Puris.", "Bakes."]
GRID_TITLE = "One flour. Every favourite."

CTA_LINE = "Bring the sunshine home."
CTA_BUTTON = "ORDER NOW"

# ------------------------------------------------------------------- palette
COCOA = (20, 12, 7)
DARK = (43, 26, 16)
CREAM = (246, 238, 223)
WHEAT = (233, 201, 138)
GOLD = (245, 184, 46)
MARIGOLD = (232, 137, 43)
TERRACOTTA = (198, 93, 46)
SKY_TOP = (255, 214, 140)
SKY_LOW = (240, 122, 52)

# -------------------------------------------------------------------- timing
FPS = 30
BPM = 120
BEAT = 60.0 / BPM          # 0.5 s
DURATION = 30.0

# scene boundaries (seconds) - every one lands on a beat
HOOK = (0.0, 3.0)          # pattern-interrupt + zoom through the "O"
REVEAL = (3.0, 7.0)        # drop: sun rise + logo
FEATURES_T = (7.0, 15.0)   # 4 cards x 2 s, whip-pans between
FIELD = (15.0, 21.0)       # cinematic golden-hour wheat field
MONTAGE = (21.0, 25.0)     # rapid beat cuts + grid
CTA = (25.0, 30.0)         # logo lockup + call to action

WHIP = 0.24                # whip-pan transition length (s)

FORMATS = {
    "vertical": (1080, 1920),   # Reels / Shorts / TikTok
    "landscape": (1920, 1080),  # YouTube / web hero
    "square": (1080, 1080),     # feed
}
