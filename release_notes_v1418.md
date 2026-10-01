# CookieRun Classic Bot v1.4.18

This maintenance release fixes a News-popup detection failure that could leave the bot stalled on the in-game News / Episode Cookie Challenge screen.

## Fixed

- Replaced the corrupted `templates/NEWS_TITLE_1.png` file that OpenCV could not decode (`libpng: IDAT: incorrect data check`).
- Re-cropped the News title template from a real 1280×720 game screenshot.
- Verified `detect_stage(..., ("NEWS",))` now recognises the News popup correctly.
- Preserved the existing dedicated News X-button handler and generic popup fallback/recovery flow.

## Validation

- Python compile gate: passed.
- Full automated suite: **168 tests passed**.
- News template loads as a valid 240×58 image.
- Synthetic detector validation: `detected = NEWS`.
- PyInstaller archive check confirms `templates\\NEWS_TITLE_1.png` is bundled in the packaged EXE.
- EXE rebuild: passed.
- Inno Setup installer rebuild: passed.
- Silent installer smoke test: passed (`INSTALL_EXIT=0`).
- Installed packaged OCR runtime self-test: passed (`value=1198`, confidence `0.99994`).
- Silent uninstall/cleanup smoke test: passed.

## Build checksums

- EXE SHA-256: `36C8220B0BF6FFC33C5531DDC1406C8EA719961855FE7F9C3CD2E9F18312E53B`
- Installer SHA-256: `2D3FAF7D7D39B38A06AD5F23A2D867DBBD4228ECB1F97960BDE50689AEEDB972`

This release is intentionally narrow: it fixes the News detection asset and bumps the packaged application to v1.4.18 without changing gameplay automation logic.
