# CookieRun Classic Bot v1.4.20

This build fixes three real-game reliability issues found in the Friends/Mailbox flows and popup handling.

## Fixed

- Send Hearts now handles a delayed `Message sent!` acknowledgement that can appear one frame after the Friends leaderboard briefly returns. The bot closes the delayed Confirm before scanning the next row instead of aborting with `Friends leaderboard could not be recovered`.
- Mailbox receive/send now locates the final large green Confirm on `All Lives received and sent!`, verifies that the modal actually closes, and retries safely instead of tapping below the button and reporting completion while the modal remains open.
- The fallback final Mailbox Confirm coordinate was corrected from `(640, 520)` to `(640, 460)` for the current 1280x720 game layout.
- `NEWS` and `ANNOUNCEMENT` stages are checked before gameplay stages so a popup cannot be ignored just because the underlying game screen is still detectable.
- A dim overlay over Main Menu is dismissed before START is tapped, instead of waiting for several swallowed START attempts.

## Validation

- Targeted Friends / Mailbox / popup regression suite: **52 tests passed**.
- Full automated suite: **176 tests passed**.
- Python compile gate: passed.
- Real-game Send Hearts reproduction: the old build stopped after 59 confirmed hearts with a delayed `Message sent!` popup still open; the fixed build detected the same delayed-popup timing during the follow-up run and closed it automatically before continuing.

## Build artifacts

Pending final EXE/installer build and hashes.

This build is prepared locally only. It has not been committed, pushed, tagged, or published to GitHub.
