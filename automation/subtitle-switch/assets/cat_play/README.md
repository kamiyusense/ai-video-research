# cat_play

Interactive close-up cat for the bottom-right corner (Issue #31 item 8).

- Source: owner-supplied sheets generated with ChatGPT (2026-10-27): a 8x2 sheet (look + punches) and a cat-teaser image. Sliced by Claude, no redrawing.
- `look/look_00.png`..`look_07.png`: face direction, 00 = right, then clockwise every 45 degrees (01 down-right, 02 down/front, 03 down-left, 04 left, 05 up-left, 06 up, 07 up-right).
- `punch_left/` and `punch_right/`: 4 frames each (raise, extend, hit, return).
- **Frame size is 256x192, not 192x192** as first planned in Issue #31: the extended paw reaches outside a square cell, so the frame is wider. Read `frame_width` / `frame_height` from `manifest.json`; do not hard-code the size. The cat body sits at the same place in every frame (bottom-centred), so switching frames does not make it jump.
- `cursor/teaser_32.png`, `cursor/teaser_64.png`: cat-teaser cursor, feather tip at top-left. `cursor.hotspot` in the manifest is for the 32px file (double it for 64px).
