"""Timeline for "The Scroll Stopper", a 41 s vertical Reel (1080x1920).

Shared by video.py and audio.py so every cut and hit lands on the same frame.
120 BPM: one beat = 0.5 s.
"""
BPM = 120
BEAT = 0.5
DURATION = 41.0

SCENES = [
    (0.0, 3.0, "hook_timer"),     # "This video has 2 seconds to stop your thumb."
    (3.0, 4.5, "so_does"),        # "So does your business."
    (4.5, 10.5, "feed"),          # doom-scroll through forgettable posts... STOP.
    (10.5, 12.5, "zoom_post"),    # dive into the one post that stopped us
    (12.5, 16.0, "brand"),        # STOP 01: brand identity
    (16.0, 19.5, "website"),      # STOP 02: website
    (19.5, 23.0, "chat"),         # STOP 03: 2 a.m. auto-reply
    (23.0, 26.5, "search"),       # STOP 04: found first on search
    (26.5, 30.0, "growth"),       # STOP 05: growth
    (30.0, 33.0, "recap"),        # Design. Tech. Growth. One team.
    (33.0, 38.0, "cta"),          # Your next customer is one thumb away.
    (38.0, 41.0, "endcard"),
]
VIGNETTES = ("brand", "website", "chat", "search", "growth")
DROP = 12.5

# (time, kind, gain); "riser@2.0" = a 2 s build that ENDS at that time.
CUES = [
    (0.05, "pop", 0.5),
    *[(0.5 + k * 0.25, "clock", 0.45 + 0.03 * k) for k in range(8)],
    (1.0, "pop", 0.4), (1.1, "pop", 0.4), (1.2, "pop", 0.4), (1.3, "pop", 0.4),
    (2.5, "riser@1.0", 0.5),
    (2.5, "buzzer", 0.8), (2.5, "impact", 0.9),
    (3.0, "hit", 0.9), (3.4, "hit", 0.9),
    (4.5, "whoosh_up", 0.7),
    *[(5.0 + k * 0.5, "swipe", 0.5) for k in range(9)],
    (5.5, "hit_soft", 0.6), (6.5, "hit_soft", 0.6), (7.5, "hit_soft", 0.6),
    (9.6, "tape_stop", 0.0),        # marker only: audio.py slows the phone-speaker music here
    (10.0, "stop_thud", 1.0),
    (10.5, "whoosh_in", 0.8),
    (12.5, "riser@2.0", 0.8), (12.5, "revcrash@0.6", 0.7),
    (12.5, "drop", 1.0),
    # brand
    (12.7, "whoosh", 0.5), (12.8, "pop", 0.5), (12.9, "pop", 0.5), (13.4, "snap", 0.8),
    (13.9, "shimmer", 0.5), (14.4, "pop", 0.4), (14.5, "pop", 0.4), (14.6, "pop", 0.4), (14.7, "pop", 0.4),
    # website
    (16.0, "whip", 0.7), *[(16.1 + k * 0.12, "tick", 0.35) for k in range(6)],
    (16.9, "fill", 0.5), (18.2, "tap", 0.8), (18.5, "notify", 0.7),
    # chat
    (19.5, "whip", 0.7), (19.8, "msg_in", 0.6), (20.3, "typing", 0.4), (20.8, "msg_out", 0.6),
    (21.5, "msg_in", 0.6), (21.9, "msg_out", 0.6), (22.1, "ding", 0.5),
    # search
    (23.0, "whip", 0.7), *[(23.2 + k * 0.055, "key", 0.4) for k in range(14)],
    (24.0, "whoosh", 0.4), (24.6, "slide_up", 0.6), (25.2, "ding", 0.7), (25.3, "pin", 0.6),
    # growth
    (26.5, "whip", 0.7), *[(26.8 + k * 0.1, "blip", 0.45 + 0.04 * k) for k in range(6)],
    (27.5, "levelup", 0.6), (28.2, "pop", 0.4), (28.35, "pop", 0.4), (28.5, "pop", 0.4),
    # recap / cta / end
    (30.0, "whip", 0.7), *[(30.05 + k * 0.12, "card", 0.4) for k in range(5)],
    (31.4, "hit", 0.9),
    (33.0, "impact", 0.9), (34.6, "pop", 0.6), (34.8, "tap", 0.9), (35.0, "notify", 0.6),
    (38.0, "final_hit", 1.0), (38.2, "sparkle", 0.6), (39.0, "shimmer", 0.6),
]
