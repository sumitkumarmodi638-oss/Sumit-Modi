# Varnik Labs brand kit (for the video pipeline)

- `logo/`: the logo, cut from the Brand Identity PDF by `marketing-video/prepare.py`. It contains alpha masks for the three marks (design, tech, growth) and the 10 wordmark letters, with their positions in `logo.json`. `scroll-stopper/lib.py` `draw_logo()` animates them piece by piece.
- `fonts/`: Sora (headlines) and DM Sans (body), both under the SIL Open Font License.
- **Palette:**

  | Name | Hex | Use |
  |---|---|---|
  | Royal Purple | `#6D28D9` | primary |
  | Electric Lime | `#D4F55A` | accent |
  | Midnight | `#120B26` | dark |
  | Ink | `#1C1830` | dark |
  | Lavender | `#A78BFA` | light accent |
  | Cloud | `#F7F5FC` | light background |

`lib.py` uses `marketing-video/build/` when it has been built, and falls back to this folder in a plain clone.
