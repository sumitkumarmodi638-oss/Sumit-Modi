"""Build the Higgsfield text-to-speech requests for every voiceover line.

  python3 tts_requests.py            # prints JSON batches (12 lines each) for generate_audio_batch
  python3 tts_requests.py --count    # how many lines / estimated credits

Each request's `index` encodes film and line: film_number * 100 + line_number, so a
finished job maps straight to voiceover/takes/<film>/<NN>.<ext>.
"""
import json
import sys

from scripts import FILMS, ORDER

VOICE_ID = "f23263ce-3220-4c99-a488-8b6a8aab2a66"  # "sumit's-voice" (cloned, Higgsfield element)
MODEL = "seed_audio"
SPEECH_RATE = 35       # the cloned voice reads slowly at 0; +35 gives a brisk, natural ad read
SAMPLE_RATE = 48000    # match the mix (the default is 24 kHz)
RATE_OVERRIDE = {}     # per-line speech_rate for a retake, e.g. {8: 55}


def all_lines():
    for fi, film in enumerate(ORDER):
        for li, (_s, _e, text) in enumerate(FILMS[film]["lines"]):
            yield fi * 100 + li, text


def all_requests():
    """One request per UNIQUE line: repeated lines (the sign-off, "Let's switch it on.")
    are recorded once and the same take is reused, as an editor would."""
    out, seen = [], set()
    for index, text in all_lines():
        if text not in seen:
            seen.add(text)
            out.append({"index": index,
                        "params": {"model": MODEL, "prompt": text, "voice_type": "element", "voice_id": VOICE_ID,
                                   "speech_rate": RATE_OVERRIDE.get(index, SPEECH_RATE), "sample_rate": SAMPLE_RATE}})
    return out


def take_path(index):
    return f"takes/{ORDER[index // 100]}/{index % 100:02d}"


def paths_for(index):
    """Every take path that uses the same text as request `index`."""
    text = dict(all_lines())[index]
    return [take_path(i) for i, t in all_lines() if t == text]


if __name__ == "__main__":
    reqs = all_requests()
    if "--count" in sys.argv:
        print(f"{len(list(all_lines()))} lines, {len(reqs)} unique, about {len(reqs) * 0.45:.0f} credits")
    else:
        for k in range(0, len(reqs), 12):
            print(json.dumps(reqs[k:k + 12]))
