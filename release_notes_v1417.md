# CookieRun Classic Bot v1.4.17

This release focuses on the CookieBot desktop UI, game artwork, responsive controls, and application branding. Core bot behavior and the Anti-Bot solver remain based on v1.4.16.

## UI and branding

- Redesigned the interface as a CookieRun-inspired **game-themed modern** command center.
- Added real game artwork to navigation, action cards, status tiles, Mystery Box stats, Friends and Mailbox controls.
- Added sprite-based buttons with hover and disabled states.
- Fixed button overflow: sprite buttons now resize to the actual container width instead of keeping a fixed rendered width.
- Quick Actions, Run Control, and Telegram action buttons now stretch safely inside their cards.
- Replaced the main mascot with the headphone-wearing gingerbread cookie holding a heart envelope.
- The mascot is used for the window/taskbar icon, `CookieRunClassicBot.exe`, installer, and shortcuts.
- PyInstaller now bundles `ui_assets`, so source and packaged builds use the same visuals.

## Validation

- Python compile gate: passed
- Full automated suite: **168 passed + 12 subtests**
- Dashboard visual check: passed; action buttons stay inside their cards
- EXE rebuild: passed
- Inno Setup installer rebuild: passed
- Embedded EXE icon visually verified

## Build checksums

- EXE SHA-256: `3EFCE8A44833B5BA7F289BBE9E50435AD8BBDA86B4DDEEEEB3DCDB917CEB8F89`
- Installer SHA-256: `55C0C720C3456B90FFF3EFF969CC85412094C6C0CCD84EDE13D869421B1A4BA0`

> No gameplay automation behavior was intentionally changed in this release; it is primarily a UI, asset, branding, responsive-layout and packaging release.
