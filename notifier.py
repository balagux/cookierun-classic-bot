"""Telegram notifications for the CookieRun bot.

Send periodic status summaries (coins/EXP, hearts, Cookie Relay stock, Mystery
Box totals) to a Telegram chat via the Bot API.  The bot token and chat id are
read from environment variables (falling back to values in ``config``) so they
are never hard-coded in source control.

Configure once, e.g. in ``gui_settings.json`` or the environment:

    TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
    TELEGRAM_CHAT_ID=-1001234567890

The module is deliberately dependency-light: it uses only the standard library
``urllib`` so it never blocks the worker thread on a package import.
"""

import json
import os
import time
import urllib.parse
import urllib.request

try:
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except Exception:  # pragma: no cover - config may not expose these yet
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_CHAT_ID = ""


# Optional local settings file so tokens/chats are not committed to git.
try:
    from runtime_paths import APP_DIR
except Exception:  # pragma: no cover
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

_SETTINGS_FILE = os.path.join(APP_DIR, "telegram_settings.json")


def _load_settings_file():
    """Read token/chat id from a local, git-ignored JSON file if present."""
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return str(data.get("bot_token", "")), str(data.get("chat_id", ""))
    except Exception:
        return "", ""


def _env_or(name, default):
    value = os.environ.get(name)
    if value and value.strip():
        return value.strip()
    return default


def _token():
    file_token, _ = _load_settings_file()
    if file_token:
        return file_token
    return _env_or("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)


def _chat_id():
    _, file_chat = _load_settings_file()
    if file_chat:
        return file_chat
    return _env_or("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)


def get_settings():
    """Return the currently configured (token, chat_id) pair."""
    return _token(), _chat_id()


def save_settings(bot_token, chat_id):
    """Persist the bot token and chat id to the git-ignored settings file.

    This keeps credentials out of source control while letting the GUI store
    them locally.  Returns True on success.
    """
    try:
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as handle:
            json.dump(
                {"bot_token": bot_token, "chat_id": chat_id},
                handle,
                ensure_ascii=False,
                indent=2,
            )
        return True
    except Exception as exc:
        print(f"[TELEGRAM] save settings failed: {exc}")
        return False


def is_enabled():
    """Return True when both a bot token and chat id are configured."""
    return bool(_token() and _chat_id())


def send_message(text):
    """Send a plain-text message to the configured Telegram chat.

    Returns True on success, False on any failure (network, bad token, or the
    feature being disabled).  Never raises, so the bot loop is unaffected.
    """
    if not is_enabled():
        return False
    token = _token()
    chat_id = _chat_id()
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = urllib.parse.urlencode(
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": "true",
            }
        ).encode("utf-8")
        request = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8", "replace"))
        return bool(body.get("ok"))
    except Exception as exc:
        # Never fail the automation because a notification could not send.
        try:
            print(f"[TELEGRAM] send failed: {exc}")
        except Exception:
            pass
        return False


def send_summary(
    *,
    attempts=None,
    completed=None,
    coins=None,
    exp=None,
    hearts_remaining=None,
    hearts_used=None,
    relay_stock=None,
    box_counts=None,
    relay_out_of_stock=False,
):
    """Compose and send a single status summary line; returns success bool."""
    if not is_enabled():
        return False

    lines = ["📊 CookieRun Bot Summary"]
    if attempts is not None and completed is not None:
        lines.append(f"▸ รอบ: {completed}/{attempts} สำเร็จ")
    if coins is not None:
        lines.append(f"▸ Coins: {coins:,}")
    if exp is not None:
        lines.append(f"▸ EXP: {exp:,}")
    if hearts_used is not None or hearts_remaining is not None:
        hearts_text = []
        if hearts_used is not None:
            hearts_text.append(f"ใช้ไป {hearts_used}")
        if hearts_remaining is not None:
            hearts_text.append(f"เหลือ {hearts_remaining}")
        if hearts_text:
            lines.append(f"▸ Mailbox หัวใจ: {' | '.join(hearts_text)}")
    if relay_stock is not None or relay_out_of_stock:
        if relay_out_of_stock:
            lines.append("▸ Cookie Relay: หมดแล้ว ⚠️")
        else:
            lines.append(f"▸ Cookie Relay: เหลือ {relay_stock}")
    if box_counts:
        box_text = " | ".join(
            f"{name} {count}" for name, count in box_counts.items()
        )
        lines.append(f"▸ กล่อง: {box_text}")

    text = "\n".join(lines)
    print(f"[TELEGRAM] {text}")
    return send_message(text)
