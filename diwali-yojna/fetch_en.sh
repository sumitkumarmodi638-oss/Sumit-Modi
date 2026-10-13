#!/usr/bin/env bash
# Extra assets for the English cut (film_en.py). Run after fetch.sh.
set -euo pipefail
A=${1:-/home/user/diwali}
B=https://d8j0ntlcm91z4.cloudfront.net/user_36uz3wkI1VJGctsM7WMOjC31Fpr
get() { [ -s "$A/$1" ] || curl -sSfL -o "$A/$1" "$2"; }
# English VO, ElevenLabs "Gia" (en0..en9, in script order)
i=0
for u in 214627_494b261d-dd66-4ce4-a7a0-f9233d799df8 214626_17955df5-8cad-4d4a-8801-ee5fa65bdd24 \
         214626_539b95c2-56f0-4e00-a585-16658f0f4ab0 214635_15bbe9ae-fa61-4c90-a10f-67f141a8fa0b \
         214626_d0797325-3bd2-49c9-b9dc-a96904440b99 214635_b6056fc0-482a-433b-bffa-33fbfbca5242 \
         214635_e92f0acc-7c06-4a51-88c2-63e69ddabcc3 214643_2afa88d1-03cd-43d9-b6c5-9cf4735443ee \
         214643_86d0bb85-1900-4ae3-9f06-261f5bc3ebe4 214643_8ef40c8c-106b-4f29-80e4-a088cec65878; do
  get en$i.mp3 $B/hf_20261013_$u.mp3; i=$((i+1))
done
# payoff score: "A New Life" by Eugenio Mininni (Mixkit Stock Music Free License)
get m543.mp3 https://assets.mixkit.co/music/543/543.mp3
echo "english assets ready in $A"
