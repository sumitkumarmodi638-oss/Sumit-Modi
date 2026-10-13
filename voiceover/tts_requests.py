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


def all_requests():
    out = []
    for fi, film in enumerate(ORDER):
        for li, (_s, _e, text) in enumerate(FILMS[film]["lines"]):
            out.append({"index": fi * 100 + li,
                        "params": {"model": MODEL, "prompt": text, "voice_type": "element", "voice_id": VOICE_ID}})
    return out


def take_path(index):
    return f"takes/{ORDER[index // 100]}/{index % 100:02d}"


if __name__ == "__main__":
    reqs = all_requests()
    if "--count" in sys.argv:
        print(f"{len(reqs)} lines, about {len(reqs) * 0.45:.0f} credits at ~0.4-0.5 per line")
    else:
        for k in range(0, len(reqs), 12):
            print(json.dumps(reqs[k:k + 12]))
