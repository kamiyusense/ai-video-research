# cat_sprites

Status cat for the top-right (full body) and bottom-right (face) of the app.

- Source: owner-supplied sprite atlas generated with ChatGPT (2026-10-27), pink angel cat with mandarins, 2048x768 RGBA, transparent background.
- Sliced by Claude (slicing logic: detect each frame by alpha, crop, bottom-align into a fixed cell). No redrawing.
- `idle/` 6, `walk/` 8 (faces left, so it walks right-to-left), `done/` 6, `error/` 6 frames, 256x192 each.
- `face/<state>/` are PROVISIONAL head crops (192x192) taken from the full-body frames. A dedicated interactive close-up set (`../cat_play/`) may replace them later.
- `manifest.json` follows the format in Issue #31 (frame_width, frame_height, states.<name>.frames/fps/loop/hold_last, and the same under `face`).
- The images are not pixel-exact dot art; scale them smoothly (no `image-rendering: pixelated` needed).
