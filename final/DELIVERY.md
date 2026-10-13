# Final films with voiceover

All 11 films, voiced in Sumit's cloned voice and mixed by `voiceover/mix.py`, are in the
**Higgsfield media library** (this repo's cloud environment can't reach Higgsfield
storage, so the mix runs in Higgsfield's sandbox from a clone of this branch).

| Film | Length | Loudness | Higgsfield media ID |
|---|---|---|---|
| Brand film (16:9) | 45 s | -15.2 LUFS / -1.9 dBTP | `6e380cf7-deb2-4e4b-ba77-558da9ec864f` |
| The Scroll Stopper (9:16) | 41 s | -14.9 LUFS / -1.8 dBTP | `2bf4c5a0-38b6-46e0-9b87-d8a5f479160b` |
| Healthcare (9:16) | 34 s | -15.1 LUFS / -1.9 dBTP | `b7213665-9c2a-40a6-88a5-1e7930b9036a` |
| Restaurants (9:16) | 34 s | -15.1 LUFS / -1.8 dBTP | `c31c2716-7eba-4cda-976e-3c247286daab` |
| Real estate (9:16) | 34 s | -15.1 LUFS / -1.8 dBTP | `44f4be37-a19b-443a-a408-51f7769183a1` |
| Education (9:16) | 34 s | -15.0 LUFS / -1.8 dBTP | `329739ce-65c7-41d0-b6b8-c8a13299aef0` |
| Fitness (9:16) | 34 s | -15.2 LUFS / -1.9 dBTP | `82dd9834-55e1-417d-b58b-1fe2c84c41ae` |
| Retail (9:16) | 34 s | -15.2 LUFS / -1.9 dBTP | `0d0e6803-fe3a-499e-bab4-12e98aa09b37` |
| Travel (9:16) | 34 s | -15.1 LUFS / -1.8 dBTP | `bc92a99f-330b-4d8a-9fd6-6ce0ddabfb22` |
| Finance (9:16) | 34 s | -15.2 LUFS / -1.8 dBTP | `d6bd6d22-c377-4c97-8717-6f4cb06d0681` |
| Manufacturing (9:16) | 34 s | -15.3 LUFS / -1.8 dBTP | `6f46d7c9-b4da-4fdd-860c-083fc62fa480` |
| Captions (.srt for all 11, zip) | | | `d1dcab52-398a-4f25-938f-20a8a4af7c5b` |

Rebuild anywhere that can reach Higgsfield storage:

```bash
git clone -b claude/cool-allen-e9aonp https://github.com/sumitkumarmodi638-oss/sumit-modi.git
cd sumit-modi/voiceover && python3 jobs.py download && python3 mix.py   # -> ../final/
```
