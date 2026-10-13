#!/usr/bin/env bash
# Fetch the generated assets for the Diwali Yojna Reel into $1 (default /home/user/diwali).
# Needs network access to Higgsfield storage, mixkit.co and GitHub (fonts).
set -euo pipefail
A=${1:-/home/user/diwali}
mkdir -p "$A/fonts"
B=https://d8j0ntlcm91z4.cloudfront.net/user_36uz3wkI1VJGctsM7WMOjC31Fpr
get() { [ -s "$A/$1" ] || curl -sSfL -o "$A/$1" "$2"; }

# shots: Kling 3.0 pro, animated from Nano Banana 2.1 stills of one character reference
get c1.mp4 $B/hf_20261013_212346_118cb5ea-9525-4528-9550-7d04db0b6b1c.mp4   # yawning uncle
get c2.mp4 $B/hf_20261013_212354_a6e4a8f4-1396-4686-a1ce-8726bb4f1a68.mp4   # phone buzzing, uncle dozing
get c3.mp4 $B/hf_20261013_212345_72116e21-4601-4b91-b3b2-1ef84cad69b4.mp4   # beaming with phone, Diwali rush
get c4.mp4 $B/hf_20261013_212346_be0026fc-0be9-4056-883f-62447395aee4.mp4   # family packing gift boxes

# Hindi VO, ElevenLabs "Gia"
i=0
for u in 211617_b8066518-0515-4d89-94d8-108da8ba988a 211736_505b4899-08a6-4619-8281-d2e38b2eb316 \
         211736_c44a722c-71ca-4c75-8ca8-97a24080c7b6 211737_8e7625cc-1fa4-4f5a-85b1-2e6f1e7c6f16 \
         211736_c27b8b9d-48bf-4086-8e3d-e9fd48ac97de 211758_26bb114a-3aaf-4981-9a30-d34cfdae1333 \
         211758_fede9a4b-64f5-48e4-bce1-eb43b7fadcca 211757_4bfb36fb-78f8-4abe-acf0-0a8c3e7aa973 \
         211758_510ce681-6f7d-4297-a388-edee70ecf610; do
  get vo$i.mp3 $B/hf_20261013_$u.mp3; i=$((i+1))
done
# sign-off: the shared "Varnik Labs. Design. Tech. Growth." take
get signoff.mp3 "$(python3 -c "import json,sys; sys.path.insert(0,'$(dirname "$0")/../voiceover'); print(json.load(open('$(dirname "$0")/../voiceover/jobs.json'))['13']['url'])")"

# music (Mixkit Stock Music Free License): "Meditation Sitar" and "India", both by Arulo
get m344.mp3 https://assets.mixkit.co/music/344/344.mp3
get m205.mp3 https://assets.mixkit.co/music/205/205.mp3

# fonts (SIL Open Font License, Google Fonts)
for p in rozhaone/RozhaOne-Regular.ttf mukta/Mukta-Bold.ttf mukta/Mukta-Regular.ttf mukta/Mukta-ExtraBold.ttf; do
  get "fonts/$(basename $p)" https://github.com/google/fonts/raw/main/ofl/$p
done
echo "assets ready in $A"
