# CookieRun Classic Bot v1.4.19

This bug-fix build hardens large Mailbox heart batches and prevents the in-game News/announcement popup from being misclassified as an Anti-Bot challenge.

## Fixed

- Mailbox receive/send no longer treats one transient dark animation frame as a successful end of the batch.
- Mailbox panel disappearance now requires repeated verification; an unexpected persistent disappearance raises a clear error instead of silently reporting a partial batch as complete.
- Per-heart Confirm handling now supports back-to-back dialogs where the next sender replaces the previous dialog immediately and the same Confirm template never disappears.
- Truly frozen Confirm dialogs get bounded retries, a debug screenshot, and an explicit error instead of a false success.
- News, Announcement, and Party Run templates now override the broad Anti-Bot layout heuristic, preventing the old "Anti-Bot challenge remains visible..." failure on normal event/news screens.
- News close recovery first locates the real X from `NEWS_CLOSE_1.png`, then falls back to the historical coordinate and generic popup recovery.

## Validation

- Targeted Mailbox / News / Anti-Bot / popup regression tests: passed.
- Full automated suite: **172 tests passed + 12 subtests passed**.
- Python compile gate: passed.
- PyInstaller EXE build: passed.
- Packaged EXE archive contains both `templates\\NEWS_CLOSE_1.png` and `templates\\NEWS_TITLE_1.png`.
- Inno Setup installer build: passed (v1.4.19).

## Build artifacts

- EXE: `dist/CookieRunClassicBot.exe`
  - Size: 120,369,378 bytes
  - SHA-256: `31C2E7D5B9CEF78927D3A914000011F4A7A35B9F2E420D1C49C80281C3D1D216`
- Installer: `installer/CookieRunClassicBot-Setup.exe`
  - Size: 122,019,472 bytes
  - SHA-256: `11CBE70B4E05B9434B0FB39C23D408DFB8D0EE17E49288E191B104AD5DDBDD89`

This build is prepared locally only. It has not been committed, pushed, tagged, or published to GitHub.
