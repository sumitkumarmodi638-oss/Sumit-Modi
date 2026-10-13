"""Voiceover scripts for all 11 films, written to the edit.

Each line is (start, latest_end, text):
  start       when the voice comes in, usually a few frames AFTER a cut or hit so the
              picture lands first and the voice rides on it (an editor's J/L-cut timing)
  latest_end  the line must be finished by here (next important beat); mix.py
              time-fits a take that runs long, up to 12% faster, never more

Voice: Sumit's cloned voice (Higgsfield "sumit's-voice"), a confident, warm,
conversational read. The founder talking to a business owner, not an announcer.
Rules followed: short lines, one idea per line, the voice never fights on-screen
text (it says it the way you'd say it out loud), the logo moments are left silent
so they breathe, and every film ends on the same spoken sign-off.
"""

SIGN_OFF = "Varnik Labs. Design. Tech. Growth."
AUDIT = "Book a free fifteen-minute audit."

FILMS = {}

# ------------------------------------------------------------------ brand film (45 s, 16:9)
FILMS["brand-film"] = dict(
    project="marketing-video", video="output/varnik-labs-brand-film.mp4", stem="brand-film", duration=45.0,
    lines=[
        (0.62, 1.60, "Blink."),
        (2.05, 4.10, "That's all the time you get."),       # the screen finishes the thought: "...to be noticed."
        (4.15, 8.40, "Great product. Nobody knows. Five agencies... zero clarity."),  # one line rides the montage
        (10.72, 11.95, "Sound familiar?"),
        (13.65, 16.20, "One team. Design. Tech. Growth."),  # starts on the drop, tails into the first spark
        (16.25, 17.45, "People look twice."),
        (17.60, 19.25, "It works while you sleep."),
        (19.30, 20.55, "The phone rings."),
        (20.65, 22.55, "Three sparks. One shape."),  # lands just before the logo snap (22.6)
        # 22.3-26 s: logo reveal, left silent so it can breathe
        (26.20, 29.90, "Same shop. Now... impossible to ignore."),
        (30.15, 33.90, "Twenty-plus brands. Four countries. Sixteen services, one team."),
        (34.40, 36.95, "Now... imagine the whole city."),
        (37.15, 40.60, "Your turn. " + AUDIT),
        (41.40, 44.20, SIGN_OFF),
    ])

# ------------------------------------------------------------------ The Scroll Stopper (41 s, 9:16)
FILMS["scroll-stopper"] = dict(
    project="scroll-stopper", video="output/varnik-labs-scroll-stopper-reel.mp4", stem="scroll-stopper", duration=41.0,
    lines=[
        (0.15, 2.45, "Two seconds to stop a thumb."),       # finishes before the buzzer at 2.5
        (3.05, 4.45, "So does your business."),
        (5.40, 7.95, "Post after post after post."),
        (7.45, 9.95, "All fighting for one thumb."),  # must clear the STOP thud at 10.0
        # 10.0 s: STOP. The thud carries it, no voice
        (10.95, 12.45, "That's what we build."),
        (12.75, 15.80, "A brand they remember."),
        (16.20, 19.30, "A website that makes the phone ring."),
        (19.70, 22.80, "Replies at two a.m.... while you sleep."),
        (23.20, 26.30, "When they search, they find you first."),
        (26.70, 29.80, "And growth you can see, every month."),
        (30.15, 32.80, "Design. Tech. Growth. One team."),
        (33.15, 37.60, "Your next customer is one thumb away. " + AUDIT),
        (38.30, 40.60, "Stop the scroll. Start the growth."),
    ])

# ------------------------------------------------------------------ industry Reels (32 s, 9:16), same beat map
INDUSTRY = {
    "healthcare": dict(
        hook="Your next patient is googling 'doctor near me'.",
        night="It's nine forty-seven at night. Calls missed. Messages unread.",
        problem="By morning, they've booked elsewhere.",
        fixes=["We put your clinic first on Google.", "Patients book in three taps.", "And reminders send themselves."],
        result="A fuller waiting room. A calmer front desk.",
        cta="Running a clinic? " + AUDIT),
    "food": dict(
        hook="People eat with their eyes first.",
        night="Seven thirty on a Friday. Three likes. Zero reservations.",
        problem="Great food. Empty tables.",
        fixes=["Posts that make people hungry.", "A name and a menu they crave.", "And orders, straight to your kitchen."],
        result="Fuller tables. A busier kitchen.",
        cta="Running a restaurant? " + AUDIT),
    "realestate": dict(
        hook="Buyers decide in one scroll.",
        night="Ten p.m. Fourteen leads. Not one called back.",
        problem="Hot leads. Cold by Monday.",
        fixes=["A launch page that books site visits.", "Every lead, tracked in one place.", "And brochures sent in thirty seconds."],
        result="Every lead, answered in minutes.",
        cta="Selling property? " + AUDIT),
    "education": dict(
        hook="Admissions season starts before you're ready.",
        night="Nine p.m. The same question about fees. Again.",
        problem="Every. Single. Night.",
        fixes=["Parents get answers while you teach.", "You're the first name they find.", "And admissions stay open, twenty-four seven."],
        result="More enquiries. Fewer repeat calls.",
        cta="Running an institute? " + AUDIT),
    "fitness": dict(
        hook="January joins. February... vanishes.",
        night="Six a.m. class. Two out of twenty booked.",
        problem="Members join. Then drift away.",
        fixes=["Classes that fill themselves.", "A feed people train along to.", "And members who keep coming back."],
        result="Members who stay.",
        cta="Running a gym? " + AUDIT),
    "retail": dict(
        hook="Your shop closes at nine. Your store shouldn't.",
        night="Eleven twenty. 'Do you have this in medium?' No reply.",
        problem="Ready to buy. Nobody replied.",
        fixes=["A store that never closes.", "Instant answers, right in the DMs.", "And sales while the shutters are down."],
        result="Selling... while you sleep.",
        cta="Running a store? " + AUDIT),
    "travel": dict(
        hook="Guests book the photo. Not the room.",
        night="Your listing just slipped to page three.",
        problem="Beautiful place. Invisible online.",
        fixes=["A stay people remember.", "Direct bookings, without the commission.", "And reels that sell the view."],
        result="More direct bookings. Fewer empty rooms.",
        cta="Running a stay? " + AUDIT),
    "finance": dict(
        hook="Trust... is designed.",
        night="One a.m. Demo day's close. Site's down again.",
        problem="Great product. Looks risky.",
        fixes=["Look like the company you're becoming.", "An app people actually trust.", "Then the numbers follow."],
        result="Look ready. Be ready.",
        cta="Building a startup? " + AUDIT),
    "industry": dict(
        hook="Your catalogue is a forty-page PDF.",
        night="A buyer in Dubai. Still waiting on a quote.",
        problem="Big buyers. Slow replies.",
        fixes=["A catalogue that answers itself.", "Every RFQ, tracked.", "And found by buyers worldwide."],
        result="Faster quotes. Bigger orders.",
        cta="Running a factory? " + AUDIT),
}

for key, v in INDUSTRY.items():
    FILMS[key] = dict(
        project="industry-series", video=f"output/varnik-labs-{key}.mp4", stem=key, duration=34.0,
        lines=[
            (0.20, 3.60, v["hook"]),              # over the icon + hook text
            (3.65, 7.25, v["night"]),             # as the notifications pile up
            (7.50, 9.45, v["problem"]),           # lands on the slam line (7.4 s)
            (9.60, 10.95, "Let's switch it on."),  # toggle flips, then the drop at 11.0
            (11.25, 14.85, v["fixes"][0]),
            (15.25, 18.85, v["fixes"][1]),
            (19.25, 22.85, v["fixes"][2]),
            (23.20, 26.35, v["result"]),
            (26.75, 30.60, v["cta"]),
            (31.30, 33.60, SIGN_OFF),
        ])


ORDER = ["brand-film", "scroll-stopper", "healthcare", "food", "realestate", "education", "fitness", "retail",
         "travel", "finance", "industry"]

WPS = 2.75  # a brisk, natural ad read (words per second)


def estimate(text):
    """Rough spoken length: words at WPS plus a beat for each pause."""
    words = len(text.replace("...", " ").split())
    pauses = text.count(".") + text.count("?") + text.count(",") * 0.5 - text.count("...") * 2
    return words / WPS + 0.12 * pauses


if __name__ == "__main__":
    total, worst = 0, []
    for k in ORDER:
        for s, e, txt in FILMS[k]["lines"]:
            total += 1
            need = estimate(txt)
            if need > (e - s) * 1.12:
                worst.append((k, s, round(need, 2), round(e - s, 2), txt))
        ls = FILMS[k]["lines"]
        for (s1, e1, t1), (s2, _e2, t2) in zip(ls, ls[1:]):
            if e1 > s2:
                print(f"OVERLAP: {k} {t1!r} may run to {e1} but {t2!r} starts {s2}")
    print(f"{total} lines across {len(ORDER)} films")
    for w in worst:
        print("TIGHT:", w)
