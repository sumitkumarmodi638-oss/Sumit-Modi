# Voiceover and final mix (all 11 films)

The edit is built around the voiceover, the way a finishing editor would do it.
The finished films land in `../final/`.

## What's here

| File | Purpose |
|---|---|
| `SCRIPTS.md` | Every line of every film, with in/out timing. **Read and approve this first.** |
| `scripts.py` | The same scripts as data, plus a lint: `python3 scripts.py` flags lines too long for their slot or overlapping the next |
| `tts_requests.py` | Builds the text-to-speech requests: ElevenLabs "Gia" preset voice via Higgsfield `text2speech_v2`, 100 unique lines |
| `jobs.py` / `jobs.json` | Tracks every generated take (job ID and result URL); `python3 jobs.py download` fetches them into `takes/` |
| `music.py` | The music edit: picks each film's licensed cinematic track, conforms tempo, syncs the lift to the drop and backtimes the ending |
| `takes/<film>/<NN>.wav` | The recorded/generated takes go here (NN = line number in `SCRIPTS.md`) |
| `mix.py` | Places, cleans, fits and mixes the voice over music + SFX stems and encodes the final films |

## Editing decisions

- **Voice leads, picture follows.** The 9 industry Reels were re-cut from 32 s to 34 s so the
  9 PM problem and the "switch it on" moment have room for the read. Every cut still sits on the
  120 BPM beat grid.
- **J-cut timing.** Each line comes in a few frames after its cut or hit, so the picture lands
  and the voice rides on it.
- **Don't narrate the screen.** In fast montages one line carries several shots. Where the
  on-screen type finishes a thought ("...to be noticed."), the voice doesn't repeat it.
- **Silence is a choice.** The brand film's logo reveal and the Scroll Stopper's "STOP." thud
  have no voice.
- **One sign-off everywhere:** "Varnik Labs. Design. Tech. Growth."

## Music edit (`music.py`)

1. Tempo-conform the track to the films' 120 BPM cut grid (Rubber Band, pitch kept, only within 8%).
2. Slide it so its big lift lands on the drop frame. The measured lift is snapped to the sharpest onset within 150 ms. There's a 4 dB breath in the 300 ms before the hit.
3. Backtime the ending: the track's last full chord lands on the end-card hit and rings out under the sign-off.
4. Level-match to the old synthesized score, so the SFX stem keeps its balance.

Credits and license: see `../final/DELIVERY.md`.

## Mix chain (`mix.py`)

1. Voice: trim silence → high-pass 85 Hz → −2.5 dB at 200 Hz (mud) → +2.5 dB at 3.2 kHz
   (presence) → +1.5 dB at 10 kHz (air) → de-esser → 3:1 compressor → every line level-matched.
2. If a take runs past its slot, first tighten the pauses inside the line, then Rubber Band time-stretch (pitch kept) up to 12% faster. Anything
   still long is flagged `OVERRUN` in the report.
3. Music ducks −10 dB under the voice with 80 ms look-ahead (it dips just before each word) and
   a 250 ms hold between words so it never pumps. SFX duck only −3 dB, so hits still land.
4. A short room reverb glues the voice into the track.
5. Look-ahead limiter → EBU R128 −14 LUFS / −2 dBTP (Instagram, YouTube and LinkedIn targets).
6. An `.srt` subtitle file is written next to each film for closed captions on YouTube and LinkedIn.

## Finishing the voice

All 100 takes are already generated (`jobs.json`). From a machine that can reach Higgsfield
storage (`d8j0ntlcm91z4.cloudfront.net`) and `assets.mixkit.co`:

1. `python3 jobs.py download` puts every take into `takes/<film>/<NN>.mp3`
2. `python3 mix.py` writes all 11 films to `../final/`

Or drop your own studio recordings into `takes/` with the same names. The mixer doesn't care
where a take came from.

`python3 mix.py --scratch` runs the whole pipeline with placeholder noise "voices" to test
timing and ducking. Those files are marked `-SCRATCH` and are never committed.
