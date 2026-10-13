#!/usr/bin/env bash
# Builds the finished promo(s): soundtrack -> frames -> mastered MP4.
#   ./build.sh                 # vertical, landscape, square
#   ./build.sh vertical        # just one
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
formats=("${@:-vertical landscape square}")
formats=(${formats[@]})

python3 audio.py out/soundtrack.wav
for f in "${formats[@]}"; do
  python3 render.py --format "$f" --out "out/${f}_video.mp4"
  # master audio to -14 LUFS / -1 dBTP (social platform target) and mux
  ffmpeg -y -loglevel error -i "out/${f}_video.mp4" -i out/soundtrack.wav \
    -map 0:v -map 1:a -c:v copy \
    -af "loudnorm=I=-14:TP=-1.0:LRA=9" -ar 48000 -c:a aac -b:a 320k \
    -shortest -movflags +faststart "out/sunflour_${f}.mp4"
  rm "out/${f}_video.mp4"
  echo "done: out/sunflour_${f}.mp4"
done
