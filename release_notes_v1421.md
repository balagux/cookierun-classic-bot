# CookieRun Classic Bot v1.4.21

This build focuses on the remaining real-game reliability issues in Friends hearts, Mailbox hearts, and event/announcement popup recovery.

## Fixed

- Send Hearts now tolerates a longer post-confirm transition and keeps checking for a late `Message sent!` acknowledgement during recovery instead of aborting the batch too early.
- Mailbox receive/send now tolerates longer dark/animation transitions before deciding that the Lives panel disappeared.
- Unknown Event/Announcement overlays that do not match an existing template are no longer treated as closed after the first wrong X tap when the Main Menu is still visibly dimmed underneath.
- Popup recovery now verifies that the Main Menu START area is actually clear before accepting an unknown overlay as dismissed.

## Validation

- Added regression coverage for delayed heart acknowledgement recovery.
- Added regression coverage for slow Mailbox transitions lasting more than four dark frames.
- Added regression coverage for unknown event overlays without a popup template.
- Full automated suite: **179 tests passed**.
- Python compile gate: passed.

## Build artifacts

- `dist\CookieRunClassicBot.exe`
- `installer\CookieRunClassicBot-Setup.exe`

SHA-256:
- `dist\CookieRunClassicBot.exe`: `603507358383C4E84C290B863DB3F9C51C65FCCE6C82BBF532EDA9DAC5624926`
- `installer\CookieRunClassicBot-Setup.exe`: `B75D7FEA6EC7ACB7C00E2ADB9B39B77315DEB0F24022C3850357B812C4F34285`

Installer ProductVersion: **1.4.21**.
Packaged EXE smoke test: process remained alive after 8 seconds and was terminated intentionally after verification.
