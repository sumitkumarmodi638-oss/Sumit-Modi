# Voiceover and final mix (all 11 films)

The edit is built around the voiceover, the way a finishing editor would do it.
The finished films land in `../final/`.

## What's here

| File | Purpose |
|---|---|
| `SCRIPTS.md` | Every line of every film, with in/out timing. **Read and approve this first.** |
| `scripts.py` | The same scripts as data, plus a lint: `python3 scripts.py` flags lines too long for their slot or overlapping the next |
| `tts_requests.py` | Builds the Higgsfield text-to-speech requests (Sumit's cloned voice, `seed_audio`): 117 lines, about 50 credits |
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

## Mix chain (`mix.py`)

1. Voice: trim silence → high-pass 85 Hz → −2.5 dB at 200 Hz (mud) → +2.5 dB at 3.2 kHz
   (presence) → +1.5 dB at 10 kHz (air) → de-esser → 3:1 compressor → every line level-matched.
2. If a take runs past its slot, Rubber Band time-stretch (pitch kept) up to 12% faster. Anything
   still long is flagged `OVERRUN` in the report.
3. Music ducks −10 dB under the voice with 80 ms look-ahead (it dips just before each word) and
   a 250 ms hold between words so it never pumps. SFX duck only −3 dB, so hits still land.
4. A short room reverb glues the voice into the track.
5. Look-ahead limiter → EBU R128 −14 LUFS / −2 dBTP (Instagram, YouTube and LinkedIn targets).
6. An `.srt` subtitle file is written next to each film for closed captions on YouTube and LinkedIn.

## Finishing the voice

1. Allow these hosts in the cloud environment's network settings (Network access → Allowed
   domains): `upload.higgsfield.ai`, `cdn.higgsfield.ai`, `d2ol7oe51mr4n9.cloudfront.net`,
   `d1xarpci4ikg0w.cloudfront.net`
2. Generate the 117 lines with Sumit's cloned voice (batches from `python3 tts_requests.py`),
   download each into `takes/<film>/<NN>.wav`
3. `python3 mix.py`, which writes all 11 films to `../final/`

Or drop your own studio recordings into `takes/` with the same names. The mixer doesn't care
where a take came from.

`python3 mix.py --scratch` runs the whole pipeline with placeholder noise "voices" to test
timing and ducking. Those files are marked `-SCRATCH` and are never committed.
