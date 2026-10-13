#!/usr/bin/env bash
# Render every industry Reel (or the ones named): ./render_all.sh [healthcare food ...]
# Fonts + logo come from ../marketing-video/build (run ../marketing-video/prepare.py once).
set -euo pipefail
cd "$(dirname "$0")"
KEYS=("$@")
[ ${#KEYS[@]} -eq 0 ] && KEYS=(healthcare food realestate education fitness retail travel finance industry)
mkdir -p output
for k in "${KEYS[@]}"; do
  python3 audio.py "$k"
  python3 film.py "$k"
  ffmpeg -y -loglevel error -i "build/$k.mp4" -i "build/$k.wav" -map 0:v -map 1:a \
    -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -af volume=-4dB -c:a aac -b:a 192k \
    -shortest -movflags +faststart "output/varnik-labs-$k.mp4"
  echo "done: output/varnik-labs-$k.mp4"
done
