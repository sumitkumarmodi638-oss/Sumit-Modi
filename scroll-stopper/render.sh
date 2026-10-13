#!/usr/bin/env bash
# Build "The Scroll Stopper" Reel (1080x1920). Fonts + logo come from ../marketing-video/build
# (run ../marketing-video/prepare.py once first).
set -euo pipefail
cd "$(dirname "$0")"
python3 audio.py
python3 video.py
mkdir -p output
ffmpeg -y -loglevel error -i build/picture.mp4 -i build/soundtrack.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -c:a aac -b:a 256k \
  -shortest -movflags +faststart output/varnik-labs-scroll-stopper-reel.mp4
echo "done: output/varnik-labs-scroll-stopper-reel.mp4"
