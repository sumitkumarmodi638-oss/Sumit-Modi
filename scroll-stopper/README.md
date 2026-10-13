# Varnik Labs: "The Scroll Stopper" (41 s vertical Reel, 1080x1920)

`output/varnik-labs-scroll-stopper-reel.mp4`: a second, completely different film.
It's pure motion graphics (no photography) and built for Instagram Reels, YouTube
Shorts and WhatsApp Status. The story speaks directly to the viewer's thumb.

## Story

| Time | Beat | Picture | Sound |
|---|---|---|---|
| 0:00 | **Hook:** "This video has 2 seconds to stop your thumb." | A countdown ring drains 2.00 → 0.00, then glitches at zero | Clock ticks speeding up, buzzer, impact |
| 0:03 | "So does your **business.**" | Lime slam card | Two hits |
| 0:04.5 | **The doom-scroll** | A phone rises and flicks through bland posts ("SALE 50% OFF!!!", "Happy Monday :)"...), with motion blur and thumb swipes. Captions: Scroll. Scroll. Scroll. / Every post fights for the same thumb | Cheesy music through a tiny phone speaker, finger-flick swipes |
| 0:10 | **STOP.** | The feed brakes onto one great post: "Stop scrolling. Start growing." | Tape-stop, deep thud |
| 0:10.5 | "That's what we build: things people **stop** for." | Dive into the post | Whoosh, riser |
| 0:12.5 | **Drop.** Five "stops" for a demo client, Golden Crust Bakery | Each cut is a whip-scroll | Half-time trap beat in Ab, 808 glides |
| | STOP 01 · Brand | Shapes fly in and snap into a badge, wordmark, colour swatches | Pops, snap, shimmer |
| | STOP 02 · Website | A wireframe builds, then fills into a mobile site. Tap "Order now", "New order received" | Ticks, tap, notification |
| | STOP 03 · Automation | A 2:07 AM chat: a customer orders a cake and the bot handles it. "Order confirmed" | Message in/out blips, typing |
| | STOP 04 · Search | "bakery near me" types out; Golden Crust climbs from #4 to #1, a map pin drops | Keystrokes, slide, ding |
| | STOP 05 · Growth | Bars grow, a trend line draws, Calls / Orders / Walk-ins chips | Rising blips, level-up |
| 0:30 | Recap | The five stops fan out as cards. "Design. Tech. Growth. **One team.**" | Card whooshes, hit |
| 0:33 | **CTA** | "Your next customer is **one thumb** away." Book a free 15-min audit (tapped), "Audit booked", WhatsApp, web | Impact, tap, notification |
| 0:38 | End card | Logo pops in letter by letter. "Stop the scroll. Start the growth." | Final chord, sparkle |

Golden Crust Bakery is a fictional demo client and is labelled on screen as one.
The growth chart is labelled "illustrative". The video makes no invented
statistics or client claims.

## Rebuild

```bash
python3 ../marketing-video/prepare.py <Brand_Identity.pdf>   # once: fonts + logo
./render.sh
```

`timeline.py` holds the scenes and the SFX cue sheet, `video.py` the picture,
`lib.py` the drawing toolkit and `audio.py` the synthesized score and sound design.
