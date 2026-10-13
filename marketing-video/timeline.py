"""Shared timeline for the Varnik Labs brand film.

Picture (video.py) and sound (audio.py) both read from here, so every cut,
zoom punch and SFX hit lands on the same frame. Music runs at 120 BPM, so one
beat = 0.5 s and every major cut sits on a beat.
"""

W, H = 1920, 1080
FPS = 30
BPM = 120
BEAT = 60 / BPM
DURATION = 45.0

# Brand palette (Varnik Labs Brand Identity 2026)
PURPLE = (0x6D, 0x28, 0xD9)    # Royal Purple
LIME = (0xD4, 0xF5, 0x5A)      # Electric Lime
MIDNIGHT = (0x12, 0x0B, 0x26)
INK = (0x1C, 0x18, 0x30)
LAVENDER = (0xA7, 0x8B, 0xFA)
CLOUD = (0xF7, 0xF5, 0xFC)

# (start, end, name). Story arc follows the sales deck:
# Hook -> Lights off (problems) -> Switch on -> 3 sparks -> logo -> proof -> CTA
SCENES = [
    (0.0, 2.0, "hook_blink"),
    (2.0, 4.0, "noticed"),
    (4.0, 5.5, "great_product"),
    (5.5, 7.0, "sign_1998"),
    (7.0, 8.5, "five_agencies"),
    (8.5, 10.5, "strobe_problems"),
    (10.5, 12.0, "sound_familiar"),
    (12.0, 13.5, "switch"),
    (13.5, 16.0, "one_team"),
    (16.0, 17.5, "spark_design"),
    (17.5, 19.0, "spark_tech"),
    (19.0, 20.5, "spark_growth"),
    (20.5, 22.0, "three_sparks"),
    (22.0, 26.0, "logo_reveal"),
    (26.0, 30.0, "lights_everywhere"),
    (30.0, 34.0, "proof"),
    (34.0, 37.0, "whole_city"),
    (37.0, 41.0, "cta"),
    (41.0, 45.0, "endcard"),
]

# Montage in "lights_everywhere": one photo per beat
MONTAGE = [15, 17, 30, 31, 16, 32, 33, 34]

# Sound-design cue sheet: (time, kind, gain). audio.py renders these.
# "riser@1.3" = a 1.3 s build that *ends* on that time (lands on the hit).
CUES = [
    (0.00, "heartbeat", 0.9),
    (0.50, "riser@0.45", 0.6),
    (0.50, "impact", 1.0),
    (1.55, "shutter", 0.9),
    (2.00, "whoosh", 0.7),
    (2.00, "tick", 0.35), (2.25, "tick", 0.35), (2.50, "tick", 0.35),
    (2.75, "tick", 0.35), (3.00, "tick", 0.35), (3.25, "tick", 0.35),
    (3.30, "swipe", 0.6),
    (4.00, "hit", 0.8), (4.75, "hit_low", 0.7),
    (5.50, "glitch", 0.7), (6.25, "hit_low", 0.7),
    (7.00, "glitch", 0.7), (7.75, "hit_low", 0.7),
    (8.50, "stab", 0.8), (9.00, "stab", 0.8), (9.50, "stab", 0.8), (10.00, "stab", 0.8),
    (10.50, "power_down", 0.9),
    (13.50, "riser@2.9", 0.8),
    (12.00, "switch_click", 1.0),
    (12.75, "glow_swell", 0.7),
    (13.50, "revcrash@0.7", 0.8),
    (13.50, "drop", 1.0),
    (14.50, "hit", 0.8), (15.00, "hit", 0.8), (15.50, "hit", 0.9),
    (16.00, "whoosh", 0.8), (16.05, "sparkle", 0.5),
    (17.50, "whoosh", 0.8), (17.55, "digital", 0.5),
    (19.00, "whoosh", 0.8), (19.05, "sparkle", 0.4),
    (20.50, "whoosh", 0.7),
    (22.60, "riser@1.3", 0.7),
    (22.00, "fly_in", 0.9),
    (22.60, "impact", 1.0), (22.60, "sparkle", 0.8),
    (23.00, "pop", 0.45), (23.05, "pop", 0.4), (23.10, "pop", 0.4), (23.15, "pop", 0.4),
    (23.20, "pop", 0.4), (23.25, "pop", 0.4), (23.30, "pop", 0.4), (23.35, "pop", 0.4),
    (23.40, "pop", 0.4), (23.45, "pop", 0.4),
    (24.00, "shimmer", 0.7),
    (26.00, "hit", 0.6), (26.50, "camera", 0.5), (27.00, "camera", 0.5), (27.50, "camera", 0.5),
    (28.00, "hit", 0.6), (28.50, "camera", 0.5), (29.00, "camera", 0.5), (29.50, "camera", 0.5),
    (30.00, "whoosh", 0.7),
    (30.00, "count", 0.5), (30.50, "count", 0.5), (31.00, "count", 0.5), (31.50, "count", 0.5),
    (34.00, "whoosh", 0.6), (34.00, "pad_swell", 0.6),
    (37.00, "riser@1.2", 0.6), (37.00, "impact", 0.9),
    (38.00, "pop", 0.7), (38.50, "notify", 0.6),
    (41.00, "final_hit", 1.0), (41.05, "sparkle", 0.6),
    (42.00, "shimmer", 0.6),
]
