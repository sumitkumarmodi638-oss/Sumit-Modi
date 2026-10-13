#!/usr/bin/env bash
# Build the Varnik Labs brand film end to end.
# Usage: ./render.sh path/to/Varnik_Labs_Brand_Identity.pdf
# Needs: python3 (numpy, scipy, opencv-python-headless, pillow), ffmpeg, poppler-utils
set -euo pipefail
cd "$(dirname "$0")"

python3 prepare.py "$1"
python3 audio.py
python3 video.py

mkdir -p output
ffmpeg -y -loglevel error -i build/picture.mp4 -i build/soundtrack.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart \
  output/varnik-labs-brand-film.mp4
echo "done: output/varnik-labs-brand-film.mp4"
