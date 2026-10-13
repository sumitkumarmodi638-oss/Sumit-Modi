# Varnik Labs: industry Reels (9 × 32 s, vertical 1080x1920)

One story per industry, each in the client's own world. They all follow the same
proven arc, so the series feels like a set, but every film has its own hook, problem,
fixes, music key and groove.

**Arc (32 s):** hook with an industry icon (0–3 s) → the 9 PM problem: unanswered
notifications pile up (3–8 s) → *"Let's switch it on"*: a toggle flips and the music drops
(8–9.5 s) → three fixes, each an animated product scene (9.5–21.5 s) → result checklist
(21.5–25 s) → CTA: free 15-min audit, WhatsApp, web (25–29 s) → logo end card (29–32 s).

| File | Industry | Hook | Problem | Fixes shown | Result | Demo business |
|---|---|---|---|---|---|---|
| `varnik-labs-healthcare.mp4` | Clinics & hospitals | Your next patient is googling **'doctor near me'** right now. | 9:47 PM: By morning, they've booked **somewhere else.** | Search → Online booking → Automation | A fuller waiting room. A **calmer** front desk. | CityCare Clinic |
| `varnik-labs-food.mp4` | Restaurants & cafés | People eat with their **eyes** first. | 7:30 PM: Great food. **Empty tables.** | Social & reels → Brand & menu → Online orders | Fuller tables. A **busier** kitchen. | Spice Route Kitchen |
| `varnik-labs-realestate.mp4` | Real estate | Buyers decide in **one scroll.** | 10:12 PM: Hot leads. **Cold by Monday.** | Project website → CRM & ads → Automation | Every lead answered **in minutes.** | Skyline Homes |
| `varnik-labs-education.mp4` | Schools & coaching | Admissions season starts **before** you're ready. | 9:05 PM: Same questions. **Every single night.** | Automation → Search → Website | More enquiries. **Fewer** repeat calls. | BrightPath Academy |
| `varnik-labs-fitness.mp4` | Gyms & wellness | January joins. February **vanishes.** | 6:00 AM: Members join. Then **drift away.** | Class booking → Reels → Retention | Members who **stay.** | IronPulse Gym |
| `varnik-labs-retail.mp4` | Retail & fashion | Your shop closes at 9. Your **store** shouldn't. | 11:20 PM: They wanted to buy. **Nobody** answered. | E-commerce → Automation → Ads & growth | Selling while **you sleep.** | Threadline Boutique |
| `varnik-labs-travel.mp4` | Travel & stays | Guests book the **photo,** not the room. | 8:40 PM: Beautiful place. **Invisible** online. | Brand → Direct booking → Reels | More direct bookings. **Fewer** empty rooms. | Lagoon Stays |
| `varnik-labs-finance.mp4` | Finance & startups | Trust is **designed.** | 1:15 AM: Great product. **Looks risky.** | Brand identity → Web & app → Growth | Look ready. **Be** ready. | Ledgerly |
| `varnik-labs-industry.mp4` | Manufacturing & B2B | Your catalogue is a **40-page** PDF. | 6:30 PM: Big buyers. **Slow replies.** | B2B website → CRM → Search | Faster quotes. **Bigger** orders. | Apex Fasteners |

All businesses are fictional demo clients and are labelled on screen. Charts are marked
"illustrative". No statistics are claimed.

## Where to post

- Instagram Reels / YouTube Shorts / WhatsApp Status as-is (1080x1920, −14 LUFS audio)
- Use them as industry-targeted Meta ads: each film speaks to one audience
- Send the matching film in sales follow-ups ("Here's what we'd do for your clinic")

## Make another industry

Add an entry to `stories.py` (hook, 5 notifications, problem, 3 fixes picked from
`search`, `booking`, `chat`, `site`, `brand`, `post`, `leads`, `growth`, `shop`, a result
and a CTA question). Add the key to `ORDER`, then run:

```bash
./render_all.sh <key>      # or no args to render all nine
```

`film.py` holds the scenes and widgets (it reuses the drawing toolkit in `../scroll-stopper/lib.py`),
and `audio.py` synthesizes each film's music and SFX from the same cue sheet.
