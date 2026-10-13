# Final films (v3): ElevenLabs voice + cinematic score

All 11 films are in the **Higgsfield media library**. They are voiced by **"Gia"** (ElevenLabs preset voice), scored with licensed cinematic tracks cut to the picture by `voiceover/music.py`, and mixed by `voiceover/mix.py`. This repo's cloud environment can't reach Higgsfield storage, so the mix runs in Higgsfield's sandbox from a clone of this branch.

| Film | Length | Loudness (integrated / peak) | Higgsfield media ID |
|---|---|---|---|
| Brand film (16:9) | 45 s | -13.9 LUFS / -1.8 dB | `07cb2616-1302-4651-9bd6-39fa55227080` |
| The Scroll Stopper (9:16) | 41 s | -14.2 LUFS / -1.9 dB | `e98b476c-a130-44da-9d70-b9ff66d26d45` |
| Healthcare (9:16) | 34 s | -14.2 LUFS / -2.0 dB | `9d551efb-035e-451b-86f9-226a9fb94e39` |
| Restaurants (9:16) | 34 s | -14.4 LUFS / -1.7 dB | `a2b01bc9-be98-46cb-93ca-a3e8b784bb61` |
| Real estate (9:16) | 34 s | -14.2 LUFS / -1.8 dB | `725af749-592b-45ca-b0df-1905652088ba` |
| Education (9:16) | 34 s | -14.4 LUFS / -1.9 dB | `cd1a1888-ba61-48d8-b09f-cfa27fa3e71a` |
| Fitness (9:16) | 34 s | -14.4 LUFS / -1.8 dB | `e3015636-f7b8-40de-a3f1-8d23d0aec3c7` |
| Retail (9:16) | 34 s | -14.4 LUFS / -1.9 dB | `d51332f3-c2e3-4cc1-8d1f-29526ace3c69` |
| Travel (9:16) | 34 s | -14.1 LUFS / -1.9 dB | `b4796762-4e51-4338-aced-35fe7473bfb3` |
| Finance (9:16) | 34 s | -14.5 LUFS / -1.8 dB | `a2d6ff82-bc03-4388-b762-03974786cc7d` |
| Manufacturing (9:16) | 34 s | -14.4 LUFS / -1.9 dB | `0d158ca5-70b1-4528-b841-4b8c6a7433bc` |
| Captions (.srt for all 11, zip) | | | `0e9df2e4-596c-4a43-8770-95c12356fbf3` |
| **Everything in one zip** (11 films + captions + this file, 113 MB) | | | `8c4892d1-abaa-4734-9138-9756d89418a2` |

## What changed from v2

- **Voice:** ElevenLabs "Gia", a warm Indian English read, replaces the cloned voice. All 100 unique lines are regenerated (`voiceover/jobs.json`).
- **Music:** a real cinematic score replaces the synthesized beds. Each track is tempo-conformed to the 120 BPM cut grid. Its big lift is slid onto the film's drop frame, with a breath before the hit. Its last full chord is backtimed onto the end-card hit, so the music resolves rather than fading.
- **Dialogue edit:** pauses inside a line are tightened before any time-stretch, and the Reels' sign-off now lands on the end-card hit.
- **Loudness:** -14 LUFS integrated (Instagram, YouTube and LinkedIn), true peak under -1.7 dB.

## Music credits

All tracks are under the [Mixkit Stock Music Free License](https://mixkit.co/license/#musicFree) (commercial use, no attribution required). They are credited here anyway. The audio files are not stored in this repo: `music.py` downloads them on demand.

| Film | Track | Artist | Source |
|---|---|---|---|
| brand-film | The Farewell | Eugenio Mininni | [mixkit.co #546](https://assets.mixkit.co/music/546/546.mp3) |
| scroll-stopper | Forest Walk | Eugenio Mininni | [mixkit.co #607](https://assets.mixkit.co/music/607/607.mp3) |
| healthcare | A New Life | Eugenio Mininni | [mixkit.co #543](https://assets.mixkit.co/music/543/543.mp3) |
| food | Kids on the Beach | Eugenio Mininni | [mixkit.co #544](https://assets.mixkit.co/music/544/544.mp3) |
| realestate | The Farewell | Eugenio Mininni | [mixkit.co #546](https://assets.mixkit.co/music/546/546.mp3) |
| education | A New Life | Eugenio Mininni | [mixkit.co #543](https://assets.mixkit.co/music/543/543.mp3) |
| fitness | Forest Walk | Eugenio Mininni | [mixkit.co #607](https://assets.mixkit.co/music/607/607.mp3) |
| retail | Other World | Lily J | [mixkit.co #723](https://assets.mixkit.co/music/723/723.mp3) |
| travel | Kids on the Beach | Eugenio Mininni | [mixkit.co #544](https://assets.mixkit.co/music/544/544.mp3) |
| finance | Other World | Lily J | [mixkit.co #723](https://assets.mixkit.co/music/723/723.mp3) |
| industry | Classical 8 | Jonny S. | [mixkit.co #715](https://assets.mixkit.co/music/715/715.mp3) |

Older versions: v2 (cloned voice, synthesized score) media IDs are in this file's git history.

Rebuild anywhere that can reach Higgsfield storage:

```bash
git clone -b claude/cool-allen-e9aonp https://github.com/sumitkumarmodi638-oss/sumit-modi.git
cd sumit-modi/voiceover && python3 jobs.py download && python3 mix.py   # -> ../final/
```

## Diwali Reel: "Pradhan Dukaan Digital Yojna 2026"

A 37.5 s, 9:16 parody of a public-service ad, in Hindi with Hinglish captions. It is clearly labelled as parody, with no emblems or real scheme names. **Branded version** (Varnik Labs purple and lime, logo opener, watermark and animated logo end card), Higgsfield media ID: `3399ea44-3d82-4488-93aa-aa4802e65dcf`. The first, unbranded cut is `6522ab14-50cb-4332-847b-546efb9487d8`. Loudness is -14.5 LUFS with peaks at -2.6 dB. Post it before 1 November (Diwali is 8 November).

- **Picture:** the uncle character comes from one Nano Banana 2.1 reference, so his face stays the same across 4 scenes. Each scene is animated with Kling 3.0 pro. The graphics (title card, approval-stamp checklist and application-form end card) are built by `diwali-yojna/film.py`.
- **Voice:** ElevenLabs "Gia", in Hindi.
- **Music:** "Meditation Sitar" and "India", both by Arulo, from Mixkit under the Mixkit Stock Music Free License.
- **Fonts:** Rozha One and Mukta, under the SIL Open Font License.
- **Cost:** about 42 credits.
- **To rebuild:** run `bash diwali-yojna/fetch.sh /tmp/dy && python3 diwali-yojna/film.py /tmp/dy out.mp4`.
