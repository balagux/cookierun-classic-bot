import random
import time

import cv2

from adb import device_capture_screen, device_scroll, device_tap, safe_device_tap
from config import (
    ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON,
    ACCEPT_CONGRATULATIONS_BUTTON,
    ACCEPT_DAILY_CHECKIN_BOOST_SET_BUTTON,
    ACCEPT_DAILY_CHECKIN_BUTTON,
    ACCEPT_DAILY_TREASURE_BUTTON,
    ACCEPT_DAILY_NEW_BUTTON,
    ACCEPT_ENTER_LEAGUE_BUTTON,
    ACCEPT_LEAGUE_RESULTS_BUTTON,
    ACCEPT_LEVEL_UP_BUTTON,
    ACCEPT_MYSTERY_BOX_BUTTON,
    ACCEPT_OVERTAKE_BREAK_SCORE_BUTTON,
    ACCEPT_PREVIOUS_RANK_RESULTS_BUTTON,
    ACCEPT_TOO_MANY_TREASURES_BUTTON,
    ALL_LIVES_RECEIVED_AND_SENT_REGION,
    ALL_LIVES_RECEIVED_AND_SENT_TEMPLATE,
    CLOSE_ANNOUNCEMENT_DIALOG_BUTTON,
    COMPLETE_FINISH_BUTTON,
    CONFIRM_SEND_LIFE_BUTTON,
    CONFIRM_SEND_LIFE_REGION,
    CONFIRM_SEND_LIFE_TEMPLATE,
    CONFIRM_QUIT_BUTTON,
    CONFIRM_QUIT_BUTTON_REGION,
    COOKIE_RELAY_ITEM,
    COOKIE_RELAY_STOCK_REGION,
    COOKIE_RELAY_USE_BUTTON,
    DEVICE_IP,
    DEVICE_PORT,
    EXIT_PARTY_RUN_MODE_BUTTON,
    FAST_START_ITEM,
    FAST_START_USE_BUTTON,
    FRIEND_ACKNOWLEDGEMENT_REGION,
    FRIEND_BOTTOM_LEADERBOARD_REGION,
    FRIEND_BOTTOM_LEADERBOARD_TEMPLATE,
    FRIEND_SEND_LIFE_REGION,
    FRIEND_SEND_LIFE_TEMPLATE,
    FRIEND_TOP_LEADERBOARD_REGION,
    FRIEND_TOP_LEADERBOARD_TEMPLATE,
    INACTIVE_RELOAD_BUTTON,
    LEADERBOARD_TOP_POSITION,
    MAIL_BOX_BUTTON,
    MAIL_BOX_LIVES_TAB_BUTTON,
    MAIL_BOX_CLOSE_BUTTON,
    MULTI_BUY_BUTTON,
    MULTI_PURCHASE_BUTTON,
    NO_LIVES_TO_RECEIVE_REGION,
    NO_LIVES_TO_RECEIVE_TEMPLATE,
    PLAY_BUTTON,
    PAUSE_GAME_BUTTON,
    PAUSE_QUIT_BUTTON_REGION,
    PURCHASE_BUTTON,
    QUIT_GAME_BUTTON,
    QUIT_BUTTON_COLOR_RATIO,
    QUIT_BUTTON_WAIT_TIMEOUT,
    QUICK_RECEIVE_AND_SEND_LIVES_BUTTON,
    RANDOM_BOOST_ITEM,
    RANDOM_BOOST_REGION,
    RANDOM_BOOST_DIALOG_CLOSE_BUTTON,
    RANDOM_BOOST_SELECTION_BUTTONS,
    RELIC_CLAIM_BUTTON,
    RELIC_CLOSE_BUTTON,
    RELIC_COMPLETE_BUTTON,
    RELAY_QUICK_EXIT_MIN_WAIT,
    RELAY_QUICK_EXIT_RUNOUT_BUFFER,
    RELAY_QUICK_EXIT_TIMEOUT,
    START_BUTTON,
    CONNECTION_LOST_RELOAD_BUTTON,
    STAGE_GAME_RELAY_REGION,
    STAGE_GAME_RELAY_TEMPLATE,
    STAGE_MAINMENU_REGION,
    STAGE_MAINMENU_TEMPLATE,
)
from detection import (
    detect_all_template_matches,
    detect_templates,
    detect_anti_bot_odd_cards,
    detect_stage,
)
from config import (
    ANTI_BOT_CARD_POS_1, ANTI_BOT_CARD_POS_2, ANTI_BOT_CARD_POS_3,
    ANTI_BOT_CARD_POS_4, ANTI_BOT_CARD_POS_5, ANTI_BOT_CARD_POS_6,
    ANTI_BOT_CARD_WIDTH, ANTI_BOT_CARD_HEIGHT,
)

def start_game():
    print("🏁 Starting the game...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, START_BUTTON[0], START_BUTTON[1])
    time.sleep(random.uniform(0.45, 0.65))


def play_game():
    print("🎮 Playing the game...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, PLAY_BUTTON[0], PLAY_BUTTON[1])
    time.sleep(0.15)


def purchase_fast_start():
    print("🛒 Purchasing Fast Start...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, FAST_START_ITEM[0], FAST_START_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(DEVICE_IP, DEVICE_PORT, PURCHASE_BUTTON[0], PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1, 2))


def purchase_cookie_relay():
    print("🔎 Checking Cookie Relay stock...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, COOKIE_RELAY_ITEM[0], COOKIE_RELAY_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
    if not cookie_relay_has_stock(screen):
        print("🛒 Cookie Relay stock is 0 — purchasing one...")
        safe_device_tap(DEVICE_IP, DEVICE_PORT, PURCHASE_BUTTON[0], PURCHASE_BUTTON[1])
        time.sleep(random.uniform(1, 2))
    else:
        print("✅ Cookie Relay is already in stock — skipping purchase.")


def cookie_relay_has_stock(screen):
    """Return True when the shop tile shows a white stock quantity digit."""
    if screen is None or not hasattr(screen, "shape"):
        return False
    x1, y1, x2, y2 = COOKIE_RELAY_STOCK_REGION
    roi = screen[y1:y2, x1:x2]
    if roi.size == 0:
        return False
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # Stock digits are bright white with a dark outline.  The zero-stock badge
    # is grey, so its value stays below this threshold.
    white = cv2.inRange(hsv, (0, 0, 180), (179, 105, 255))
    component_count, _, stats, _ = cv2.connectedComponentsWithStats(white)
    for index in range(1, component_count):
        _, _, width, height, area = (int(value) for value in stats[index])
        if 5 <= width <= 24 and 12 <= height <= 30 and 35 <= area <= 400:
            return True
    return False


def purchase_random_boost():
    print("🛒 Purchasing Random Boost...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, RANDOM_BOOST_ITEM[0], RANDOM_BOOST_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(DEVICE_IP, DEVICE_PORT, PURCHASE_BUTTON[0], PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1, 2))


def is_boost_selection_checked(screen, selection_button):
    """Detect the green check mark shown beside a selected Multi-Buy boost."""
    if screen is None or not hasattr(screen, "shape"):
        return False
    x, y = selection_button
    height, width = screen.shape[:2]
    x1, x2 = max(0, x - 28), min(width, x + 29)
    y1, y2 = max(0, y - 28), min(height, y + 29)
    roi = screen[y1:y2, x1:x2]
    if roi.size == 0:
        return False
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, (35, 80, 80), (95, 255, 255))
    return cv2.countNonZero(green_mask) >= 80


def checked_boost_selection_names(screen):
    """Return every boost currently carrying a green check mark."""
    return {
        name
        for name, button in RANDOM_BOOST_SELECTION_BUTTONS.items()
        if is_boost_selection_checked(screen, button)
    }


def _set_boost_selection_state(
    boost_name,
    checked,
    *,
    capture_func=None,
    tap_func=None,
    sleep_func=None,
    max_attempts=3,
):
    """Toggle one Multi-Buy row until its visual check state matches."""
    selection_button = RANDOM_BOOST_SELECTION_BUTTONS.get(boost_name)
    if selection_button is None:
        return False
    capture_func = capture_func or (
        lambda: device_capture_screen(DEVICE_IP, DEVICE_PORT)
    )
    tap_func = tap_func or (
        lambda x, y: device_tap(DEVICE_IP, DEVICE_PORT, x, y)
    )
    sleep_func = sleep_func or time.sleep

    for attempt in range(1, max(1, int(max_attempts)) + 1):
        screen = capture_func()
        if is_boost_selection_checked(screen, selection_button) is checked:
            return True
        action = "check" if checked else "uncheck"
        print(f"🎯 Tapping {boost_name} to {action} it ({attempt}/{max_attempts})...")
        tap_func(selection_button[0], selection_button[1])
        # Wait for the visual state to settle before another tap. Retapping too
        # early can undo the first toggle on a laggy LDPlayer instance.
        for _ in range(4):
            sleep_func(0.2)
            screen = capture_func()
            if is_boost_selection_checked(screen, selection_button) is checked:
                return True

    screen = capture_func()
    return is_boost_selection_checked(screen, selection_button) is checked


def sync_desired_boost_selection(
    desired_name,
    *,
    capture_func=None,
    tap_func=None,
    sleep_func=None,
):
    """Leave exactly the GUI-selected boost checked in the Multi-Buy dialog."""
    if desired_name not in RANDOM_BOOST_SELECTION_BUTTONS:
        print(f"❌ No selection coordinate configured for boost: {desired_name}")
        return False
    capture_func = capture_func or (
        lambda: device_capture_screen(DEVICE_IP, DEVICE_PORT)
    )
    tap_func = tap_func or (
        lambda x, y: device_tap(DEVICE_IP, DEVICE_PORT, x, y)
    )
    sleep_func = sleep_func or time.sleep

    checked_names = checked_boost_selection_names(capture_func())
    stale_names = [
        name
        for name in RANDOM_BOOST_SELECTION_BUTTONS
        if name != desired_name and name in checked_names
    ]
    for stale_name in stale_names:
        print(f"🔄 Unchecking previous boost: {stale_name}...")
        if not _set_boost_selection_state(
            stale_name,
            False,
            capture_func=capture_func,
            tap_func=tap_func,
            sleep_func=sleep_func,
        ):
            print(f"❌ Could not remove the old check mark: {stale_name}")
            return False

    if not _set_boost_selection_state(
        desired_name,
        True,
        capture_func=capture_func,
        tap_func=tap_func,
        sleep_func=sleep_func,
    ):
        print(f"❌ Could not confirm the check mark for boost: {desired_name}")
        return False

    final_checked_names = checked_boost_selection_names(capture_func())
    if final_checked_names != {desired_name}:
        print(
            "❌ Boost selection did not settle to exactly one option: "
            f"{sorted(final_checked_names)}"
        )
        return False
    return True


def purchase_desired_random_boost(desired_template, desired_name):
    print("🛒 Purchasing Desired Random Boost...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, RANDOM_BOOST_ITEM[0], RANDOM_BOOST_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(DEVICE_IP, DEVICE_PORT, MULTI_PURCHASE_BUTTON[0], MULTI_PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1, 2))
    print(f"🎯 Syncing desired boost: {desired_name}...")
    if not sync_desired_boost_selection(desired_name):
        print("⚠️ Multi-Buy was not pressed, so no Coins were spent accidentally.")
        safe_device_tap(
            DEVICE_IP,
            DEVICE_PORT,
            RANDOM_BOOST_DIALOG_CLOSE_BUTTON[0],
            RANDOM_BOOST_DIALOG_CLOSE_BUTTON[1],
        )
        time.sleep(0.8)
        return
    print(f"✅ Only the selected boost is checked: {desired_name}")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, MULTI_BUY_BUTTON[0], MULTI_BUY_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
    print(f"🔍 Waiting for desired boost to be detected: {desired_name}...")
    timeout = 30
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            print(f"⏰ Timeout: Could not detect desired boost '{desired_name}' within {timeout} seconds.")
            print("⚠️ Skipping Desired Random Boost. Please verify your in-game boost config is correct.")
            return
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if detect_templates(screen, desired_template, RANDOM_BOOST_REGION):
            print(f"✅ Desired Boost detected: {desired_name}!")
            break
        time.sleep(0.5)


def using_fast_start():
    print("⚡ Using Fast Start...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, FAST_START_USE_BUTTON[0], FAST_START_USE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.2))


def using_cookie_relay(wait_after=True):
    print("🍪 Using Cookie Relay...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, COOKIE_RELAY_USE_BUTTON[0], COOKIE_RELAY_USE_BUTTON[1])
    if wait_after:
        time.sleep(random.uniform(0.8, 1.2))


def _is_cyan_quit_button_visible(screen, region):
    if screen is None or not hasattr(screen, "shape"):
        return False
    x1, y1, x2, y2 = region
    roi = screen[y1:y2, x1:x2]
    if roi.size == 0:
        return False
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    cyan_mask = cv2.inRange(hsv, (80, 100, 70), (105, 255, 255))
    cyan_ratio = cv2.countNonZero(cyan_mask) / cyan_mask.size
    return cyan_ratio >= QUIT_BUTTON_COLOR_RATIO


def _wait_for_quit_button(region, timeout=QUIT_BUTTON_WAIT_TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if _is_cyan_quit_button_visible(screen, region):
            return True
        time.sleep(0.08)
    return False


def quick_exit_after_cookie_relay():
    """Wait for cookie two to start running, then leave through Pause -> Quit."""
    print("🏃 Waiting for the second cookie to start running...")
    started_at = time.monotonic()
    time.sleep(RELAY_QUICK_EXIT_MIN_WAIT)
    while time.monotonic() - started_at < RELAY_QUICK_EXIT_TIMEOUT:
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if not detect_templates(screen, STAGE_GAME_RELAY_TEMPLATE, STAGE_GAME_RELAY_REGION):
            break
        time.sleep(0.12)
    time.sleep(RELAY_QUICK_EXIT_RUNOUT_BUFFER)
    print("⏸️ Second cookie is running — opening Pause and quitting to Main Menu...")
    device_tap(DEVICE_IP, DEVICE_PORT, PAUSE_GAME_BUTTON[0], PAUSE_GAME_BUTTON[1])
    if not _wait_for_quit_button(PAUSE_QUIT_BUTTON_REGION):
        print("⚠️ Pause menu was not ready — retrying Pause once.")
        device_tap(DEVICE_IP, DEVICE_PORT, PAUSE_GAME_BUTTON[0], PAUSE_GAME_BUTTON[1])
        if not _wait_for_quit_button(PAUSE_QUIT_BUTTON_REGION):
            print("❌ Pause menu did not appear; quick-exit was cancelled safely.")
            return False
    device_tap(DEVICE_IP, DEVICE_PORT, QUIT_GAME_BUTTON[0], QUIT_GAME_BUTTON[1])
    if not _wait_for_quit_button(CONFIRM_QUIT_BUTTON_REGION):
        print("⚠️ Quit confirmation was not ready — retrying Quit once.")
        device_tap(DEVICE_IP, DEVICE_PORT, QUIT_GAME_BUTTON[0], QUIT_GAME_BUTTON[1])
        if not _wait_for_quit_button(CONFIRM_QUIT_BUTTON_REGION):
            print("❌ Quit confirmation did not appear; quick-exit was cancelled safely.")
            return False
    device_tap(DEVICE_IP, DEVICE_PORT, CONFIRM_QUIT_BUTTON[0], CONFIRM_QUIT_BUTTON[1])
    time.sleep(0.5)
    return True


def complete_finish(wait_after=True):
    print("🏆 Completing the game...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, COMPLETE_FINISH_BUTTON[0], COMPLETE_FINISH_BUTTON[1])
    if wait_after:
        time.sleep(random.uniform(0.8, 1.4))


def accept_mystery_box():
    print("🎁 Accepting Mystery Box...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_MYSTERY_BOX_BUTTON[0], ACCEPT_MYSTERY_BOX_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_congratulations():
    print("🎉 Accepting Congratulations...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_CONGRATULATIONS_BUTTON[0], ACCEPT_CONGRATULATIONS_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_level_up():
    print("⬆️ Accepting Level Up...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_LEVEL_UP_BUTTON[0], ACCEPT_LEVEL_UP_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_daily_checkin():
    print("📅 Accepting Daily Check-in...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_DAILY_CHECKIN_BUTTON[0], ACCEPT_DAILY_CHECKIN_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_daily_checkin_boost_set():
    print("📅 Accepting Daily Check-in Boost Set...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_DAILY_CHECKIN_BOOST_SET_BUTTON[0], ACCEPT_DAILY_CHECKIN_BOOST_SET_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_daily_treasure():
    print("💎 Accepting Daily Treasure...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_DAILY_TREASURE_BUTTON[0], ACCEPT_DAILY_TREASURE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_daily_new():
    print("📰 Accepting Daily New...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_DAILY_NEW_BUTTON[0], ACCEPT_DAILY_NEW_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_enter_league():
    print("🏆 Accepting Enter League...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_ENTER_LEAGUE_BUTTON[0], ACCEPT_ENTER_LEAGUE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_league_results():
    print("🏆 Accepting League Results...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_LEAGUE_RESULTS_BUTTON[0], ACCEPT_LEAGUE_RESULTS_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_previous_rank_results():
    print("🏆 Accepting Previous Rank Results...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_PREVIOUS_RANK_RESULTS_BUTTON[0], ACCEPT_PREVIOUS_RANK_RESULTS_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))

def accept_too_many_treasures():
    print("💎 Accepting Too Many Treasures...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_TOO_MANY_TREASURES_BUTTON[0], ACCEPT_TOO_MANY_TREASURES_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))

def accept_overtake_break_score():
    print("🏆 Accepting Overtake Break Score...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_OVERTAKE_BREAK_SCORE_BUTTON[0], ACCEPT_OVERTAKE_BREAK_SCORE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))

def open_relic_complete():
    print("🏺 Opening Relic Complete...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, RELIC_COMPLETE_BUTTON[0], RELIC_COMPLETE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))


def accept_relic_claim():
    print("🏺 Accepting Relic Claim...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, RELIC_CLAIM_BUTTON[0], RELIC_CLAIM_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(DEVICE_IP, DEVICE_PORT, RELIC_CLOSE_BUTTON[0], RELIC_CLOSE_BUTTON[1])
    time.sleep(1.0)


def close_relic_claim_without_reward():
    """Close an already-open Relic dialog without consuming completed parts."""
    print("🏺 Keeping completed Relic parts — closing without claiming...")
    safe_device_tap(
        DEVICE_IP,
        DEVICE_PORT,
        RELIC_CLOSE_BUTTON[0],
        RELIC_CLOSE_BUTTON[1],
    )
    time.sleep(0.8)


def handle_anti_bot(screen):
    print("🤖 Solving Anti-Bot captcha...")
    card_coords = [
        ANTI_BOT_CARD_POS_1, ANTI_BOT_CARD_POS_2, ANTI_BOT_CARD_POS_3,
        ANTI_BOT_CARD_POS_4, ANTI_BOT_CARD_POS_5, ANTI_BOT_CARD_POS_6,
    ]

    current_screen = screen
    for attempt in range(1, 4):
        odd_indices = detect_anti_bot_odd_cards(current_screen)
        if not odd_indices:
            print("❌ Could not identify an Anti-Bot card.")
            return False
        idx = odd_indices[0]
        cx, cy = card_coords[idx]
        tx = cx + ANTI_BOT_CARD_WIDTH // 2
        ty = cy + ANTI_BOT_CARD_HEIGHT // 2
        print(f"  👆 Attempt {attempt}/3: tapping Card {idx + 1} at ({tx}, {ty})")
        device_tap(DEVICE_IP, DEVICE_PORT, tx, ty)
        time.sleep(0.35)
        current_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if detect_stage(current_screen, ("ANTI_BOT",)) != "ANTI_BOT":
            print("✅ Anti-Bot captcha solved!")
            return True
        print("🔄 Anti-Bot is still visible — recapturing and recalculating.")

    print("❌ Anti-Bot was not solved after 3 attempts.")
    return False


def handle_connection_lost():
    print("🔌 Handling Connection Lost...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, CONNECTION_LOST_RELOAD_BUTTON[0], CONNECTION_LOST_RELOAD_BUTTON[1])
    time.sleep(3.0)


def handle_inactive():
    print("💤 Handling Inactive state...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, INACTIVE_RELOAD_BUTTON[0], INACTIVE_RELOAD_BUTTON[1])
    time.sleep(3.0)


def _is_active_friend_life_button(screen, match):
    """Reject grey/disabled envelopes that still resemble the active template."""
    if screen is None or not hasattr(screen, "shape") or len(match) != 4:
        return False
    x, y, width, height = (int(value) for value in match)
    screen_height, screen_width = screen.shape[:2]
    x1, x2 = max(0, x), min(screen_width, x + width)
    y1, y2 = max(0, y), min(screen_height, y + height)
    roi = screen[y1:y2, x1:x2]
    if roi.size == 0:
        return False
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    active_green = cv2.inRange(hsv, (34, 90, 70), (50, 255, 255))
    return cv2.countNonZero(active_green) / active_green.size >= 0.25


def _same_friend_button(match, target_match, tolerance=28):
    x, y, width, height = match
    target_x, target_y, target_width, target_height = target_match
    center = (x + width // 2, y + height // 2)
    target_center = (
        target_x + target_width // 2,
        target_y + target_height // 2,
    )
    return (
        abs(center[0] - target_center[0]) <= tolerance
        and abs(center[1] - target_center[1]) <= tolerance
    )


def _friend_match_mean_brightness(screen, match):
    if screen is None or not hasattr(screen, "shape") or len(match) != 4:
        return 0.0
    x, y, width, height = (int(value) for value in match)
    screen_height, screen_width = screen.shape[:2]
    roi = screen[
        max(0, y):min(screen_height, y + height),
        max(0, x):min(screen_width, x + width),
    ]
    if roi.size == 0:
        return 0.0
    return float(cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)[:, :, 2].mean())


def _friend_list_change_ratio(before_screen, after_screen):
    """Measure visual change in static rank/name/score bands.

    The two narrow bands deliberately exclude the animated cookie/pet artwork
    and the green send buttons. That keeps idle character animation from
    looking like list motion while preserving enough text to detect a swipe.
    """
    if (
        before_screen is None
        or after_screen is None
        or not hasattr(before_screen, "shape")
        or not hasattr(after_screen, "shape")
        or before_screen.shape != after_screen.shape
    ):
        return 1.0

    screen_height, screen_width = before_screen.shape[:2]
    y1 = max(0, FRIEND_SEND_LIFE_REGION[1] + 30)
    y2 = min(screen_height, FRIEND_SEND_LIFE_REGION[3] - 35)
    rank_x1 = max(0, FRIEND_TOP_LEADERBOARD_REGION[0] + 20)
    rank_x2 = min(screen_width, FRIEND_TOP_LEADERBOARD_REGION[0] + 85)
    text_x1 = max(0, FRIEND_TOP_LEADERBOARD_REGION[0] + 270)
    text_x2 = min(screen_width, FRIEND_SEND_LIFE_REGION[0] - 10)
    if (
        rank_x2 <= rank_x1
        or text_x2 <= text_x1
        or y2 <= y1
    ):
        return 1.0

    before_roi = cv2.hconcat(
        [
            before_screen[y1:y2, rank_x1:rank_x2],
            before_screen[y1:y2, text_x1:text_x2],
        ]
    )
    after_roi = cv2.hconcat(
        [
            after_screen[y1:y2, rank_x1:rank_x2],
            after_screen[y1:y2, text_x1:text_x2],
        ]
    )
    if before_roi.size == 0 or after_roi.size == 0:
        return 1.0

    before_gray = cv2.cvtColor(before_roi, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after_roi, cv2.COLOR_BGR2GRAY)
    before_gray = cv2.GaussianBlur(before_gray, (5, 5), 0)
    after_gray = cv2.GaussianBlur(after_gray, (5, 5), 0)
    changed = cv2.absdiff(before_gray, after_gray) >= 18
    return float(changed.mean())


def _friend_list_has_moved(before_screen, after_screen):
    """Return whether friend names/scores visibly moved after a swipe."""
    return _friend_list_change_ratio(before_screen, after_screen) >= 0.06


def _friend_list_is_stable(before_screen, after_screen):
    """Return whether consecutive friend-list captures have stopped moving."""
    return _friend_list_change_ratio(before_screen, after_screen) <= 0.015


def _is_undimmed_friend_leaderboard(
    screen,
    header_matches,
    top_matches,
    heart_matches,
    bottom_matches,
):
    """Distinguish the live list from grayscale matches behind a dark modal."""
    # The Friends tab header is fixed outside the scrolling rows and remains
    # visible at ranks 1 through 202. Requiring that specific area to be bright
    # prevents a green modal button from brightening a row crop underneath it.
    return bool(header_matches) and any(
        _friend_match_mean_brightness(screen, match) >= 175.0
        for match in header_matches
    )


def _detect_friend_acknowledgement_button(screen):
    """Return a large green post-send acknowledgement button, if visible.

    The leaderboard's normal green row buttons are only about 111px wide and
    must never qualify. The post-send button uses the game's large dialog
    shape (roughly 290x101px).
    """
    if screen is None or not hasattr(screen, "shape"):
        return None
    x1, y1, x2, y2 = FRIEND_ACKNOWLEDGEMENT_REGION
    roi = screen[y1:y2, x1:x2]
    if roi.size == 0:
        return None
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, (32, 80, 75), (52, 255, 255))
    green = cv2.morphologyEx(
        green,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
    )
    contours, _ = cv2.findContours(
        green,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    candidates = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        contour_area = float(cv2.contourArea(contour))
        bounding_area = width * height
        fill_ratio = contour_area / bounding_area if bounding_area else 0.0
        if (
            180 <= width <= 430
            and 55 <= height <= 140
            and contour_area >= 6000
            and fill_ratio >= 0.30
        ):
            candidates.append(
                (contour_area, (x + x1, y + y1, width, height))
            )
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate[0])[1]


def handle_send_friend_life(
    *,
    capture_func=None,
    detect_func=None,
    tap_func=None,
    scroll_func=None,
    sleep_func=None,
    active_button_func=None,
    acknowledgement_detector_func=None,
    movement_detector_func=None,
    stability_detector_func=None,
    max_top_scrolls=96,
    max_list_scrolls=160,
    max_heart_sends=250,
    max_total_iterations=600,
    heart_tap_attempts=2,
    confirm_poll_attempts=8,
    confirm_tap_attempts=2,
    list_return_poll_attempts=4,
    acknowledgement_poll_attempts=8,
    settle_poll_attempts=8,
    scroll_attempts=2,
    scroll_settle_poll_attempts=6,
):
    """Send each visible active friend heart once, recapturing after every tap.

    The caller must already have the Friends leaderboard open.  Every loop is
    deliberately bounded so pressing the GUI action on another screen cannot
    leave an endless scroll or click worker running.
    """
    capture_func = capture_func or (
        lambda: device_capture_screen(DEVICE_IP, DEVICE_PORT)
    )
    detect_func = detect_func or detect_all_template_matches
    tap_func = tap_func or (
        lambda x, y: device_tap(DEVICE_IP, DEVICE_PORT, x, y)
    )
    scroll_func = scroll_func or (
        lambda x, y, direction, distance, duration: device_scroll(
            DEVICE_IP,
            DEVICE_PORT,
            x,
            y,
            direction=direction,
            distance=distance,
            duration=duration,
        )
    )
    sleep_func = sleep_func or time.sleep
    active_button_func = active_button_func or _is_active_friend_life_button
    acknowledgement_detector_func = (
        acknowledgement_detector_func
        or _detect_friend_acknowledgement_button
    )
    movement_detector_func = movement_detector_func or _friend_list_has_moved
    stability_detector_func = stability_detector_func or _friend_list_is_stable

    def capture_or_raise():
        current_screen = capture_func()
        if current_screen is None:
            raise RuntimeError("Could not capture the LDPlayer screen.")
        return current_screen

    def matches(current_screen, template_files, region):
        return list(detect_func(current_screen, template_files, region) or [])

    def active_hearts(current_screen):
        candidates = matches(
            current_screen,
            FRIEND_SEND_LIFE_TEMPLATE,
            FRIEND_SEND_LIFE_REGION,
        )
        return sorted(
            (
                match
                for match in candidates
                if active_button_func(current_screen, match)
            ),
            key=lambda match: (match[1], match[0]),
        )

    def leaderboard_evidence(current_screen):
        """Return list matches without relying on one specific scroll offset."""
        return (
            matches(
                current_screen,
                STAGE_MAINMENU_TEMPLATE,
                STAGE_MAINMENU_REGION,
            ),
            matches(
                current_screen,
                FRIEND_TOP_LEADERBOARD_TEMPLATE,
                FRIEND_TOP_LEADERBOARD_REGION,
            ),
            matches(
                current_screen,
                FRIEND_SEND_LIFE_TEMPLATE,
                FRIEND_SEND_LIFE_REGION,
            ),
            matches(
                current_screen,
                FRIEND_BOTTOM_LEADERBOARD_TEMPLATE,
                FRIEND_BOTTOM_LEADERBOARD_REGION,
            ),
        )

    def has_ready_leaderboard(current_screen):
        evidence = leaderboard_evidence(current_screen)
        return any(evidence) and _is_undimmed_friend_leaderboard(
            current_screen,
            *evidence,
        )

    print("💌 Sending hearts from the current Friends leaderboard position...")
    screen = capture_or_raise()
    if not has_ready_leaderboard(screen):
        raise RuntimeError(
            "Friends leaderboard not detected. Open the leaderboard screen "
            "with the green heart envelopes, then press Send Hearts again."
        )

    # Start exactly where the user opened the list. Rewinding to rank 1 first
    # caused many visually confusing swipes (especially when the list resumed
    # near rank 100). From here onward the only gesture is upward, toward lower
    # ranks. ``max_top_scrolls`` remains accepted for launcher compatibility.
    del max_top_scrolls

    sent_count = 0
    list_scroll_count = 0
    total_iteration_count = 0
    sent_centers_since_scroll = []
    while True:
        total_iteration_count += 1
        if total_iteration_count > max(1, int(max_total_iterations)):
            raise RuntimeError(
                "The Friends leaderboard safety limit was reached after "
                f"{sent_count} confirmed heart(s)."
            )
        if not has_ready_leaderboard(screen):
            raise RuntimeError(
                "The Friends leaderboard is covered or no longer ready. "
                f"Stopped safely after {sent_count} confirmed heart(s)."
            )
        heart_matches = active_hearts(screen)
        if heart_matches:
            if sent_count >= max(0, int(max_heart_sends)):
                raise RuntimeError(
                    "The maximum heart-send safety limit was reached "
                    f"({max(0, int(max_heart_sends))})."
                )
            # Only use one coordinate from this screenshot. The UI is captured
            # again before selecting the next friend so stale rows are never used.
            target = heart_matches[0]
            target_x, target_y, target_width, target_height = target
            target_center = (
                target_x + target_width // 2,
                target_y + target_height // 2,
            )
            if any(
                abs(target_center[0] - old_center[0]) <= 28
                and abs(target_center[1] - old_center[1]) <= 28
                for old_center in sent_centers_since_scroll
            ):
                raise RuntimeError(
                    "A previously sent heart button reappeared before the "
                    f"list moved. Stopped safely after {sent_count} heart(s)."
                )
            confirm_matches = []
            for heart_attempt in range(1, max(1, int(heart_tap_attempts)) + 1):
                print(
                    f"💌 Opening heart #{sent_count + 1} "
                    f"(attempt {heart_attempt}/{max(1, int(heart_tap_attempts))})..."
                )
                tap_func(*target_center)
                for _ in range(max(1, int(confirm_poll_attempts))):
                    sleep_func(0.15)
                    screen = capture_or_raise()
                    confirm_matches = matches(
                        screen,
                        CONFIRM_SEND_LIFE_TEMPLATE,
                        CONFIRM_SEND_LIFE_REGION,
                    )
                    if confirm_matches:
                        break
                if confirm_matches:
                    break

            if not confirm_matches:
                raise RuntimeError(
                    "The Send Heart confirmation did not appear. Stopped "
                    f"safely after {sent_count} confirmed heart(s)."
                )

            confirmation_cleared = False
            for confirm_attempt in range(
                1,
                max(1, int(confirm_tap_attempts)) + 1,
            ):
                # Tap the center of the button that was actually detected, not
                # the old fixed coordinate. Re-detection is required per retry.
                confirm_x, confirm_y, confirm_width, confirm_height = sorted(
                    confirm_matches,
                    key=lambda match: (match[1], match[0]),
                )[0]
                print(
                    f"💌 Confirming heart "
                    f"({confirm_attempt}/{max(1, int(confirm_tap_attempts))})..."
                )
                tap_func(
                    confirm_x + confirm_width // 2,
                    confirm_y + confirm_height // 2,
                )
                for _ in range(max(1, int(confirm_poll_attempts))):
                    sleep_func(0.15)
                    screen = capture_or_raise()
                    confirm_matches = matches(
                        screen,
                        CONFIRM_SEND_LIFE_TEMPLATE,
                        CONFIRM_SEND_LIFE_REGION,
                    )
                    if not confirm_matches:
                        confirmation_cleared = True
                        break
                if confirmation_cleared:
                    break

            if not confirmation_cleared:
                raise RuntimeError(
                    "The Send Heart confirmation did not close. Stopped "
                    f"after {sent_count} confirmed heart(s)."
                )

            # Some game versions show a large success acknowledgement after
            # confirmation. Never tap a guessed coordinate: wait until either
            # the bright list returns or a large dialog button is detected.
            leaderboard_returned = False
            for list_return_attempt in range(
                max(1, int(list_return_poll_attempts))
            ):
                if has_ready_leaderboard(screen):
                    leaderboard_returned = True
                    break
                if list_return_attempt + 1 < max(1, int(list_return_poll_attempts)):
                    sleep_func(0.15)
                    screen = capture_or_raise()

            if not leaderboard_returned:
                acknowledgement_match = None
                for acknowledgement_attempt in range(
                    max(1, int(acknowledgement_poll_attempts))
                ):
                    acknowledgement_match = acknowledgement_detector_func(screen)
                    if acknowledgement_match is not None:
                        break
                    if acknowledgement_attempt + 1 < max(
                        1,
                        int(acknowledgement_poll_attempts),
                    ):
                        sleep_func(0.15)
                        screen = capture_or_raise()
                if acknowledgement_match is None:
                    raise RuntimeError(
                        "The Friends leaderboard stayed dim and no large "
                        "heart-sent acknowledgement button was detected. "
                        f"Stopped safely after {sent_count} completed heart(s)."
                    )

                ack_x, ack_y, ack_width, ack_height = acknowledgement_match
                print("💌 Closing the detected heart-sent acknowledgement...")
                tap_func(
                    ack_x + ack_width // 2,
                    ack_y + ack_height // 2,
                )
                for _ in range(max(1, int(list_return_poll_attempts))):
                    sleep_func(0.15)
                    screen = capture_or_raise()
                    if has_ready_leaderboard(screen):
                        leaderboard_returned = True
                        break

            if not leaderboard_returned:
                raise RuntimeError(
                    "The Friends leaderboard did not return after confirming "
                    f"a heart. Stopped safely after {sent_count} completed "
                    "heart(s)."
                )

            # A successful send changes/disables that exact envelope. Wait for
            # the list to settle before counting it or touching another row.
            target_still_active = True
            for settle_attempt in range(max(1, int(settle_poll_attempts))):
                current_hearts = active_hearts(screen)
                target_still_active = any(
                    _same_friend_button(match, target) for match in current_hearts
                )
                if not target_still_active:
                    break
                if settle_attempt + 1 < max(1, int(settle_poll_attempts)):
                    sleep_func(0.15)
                    screen = capture_or_raise()
            if target_still_active:
                raise RuntimeError(
                    "The heart button did not change after confirmation. "
                    f"Stopped safely after {sent_count} confirmed heart(s)."
                )

            sent_count += 1
            sent_centers_since_scroll.append(target_center)
            print(f"✅ Heart sent ({sent_count}).")
            screen = capture_or_raise()
            continue

        # Process an active heart on the last row before honoring the bottom
        # marker. This fixes the previous flow that skipped the final friend.
        if matches(
            screen,
            FRIEND_BOTTOM_LEADERBOARD_TEMPLATE,
            FRIEND_BOTTOM_LEADERBOARD_REGION,
        ):
            print(f"✅ Finished sending hearts. Total sent: {sent_count}")
            return sent_count

        if list_scroll_count >= max(0, int(max_list_scrolls)):
            raise RuntimeError(
                "The bottom of the Friends leaderboard was not found after "
                f"{list_scroll_count} scrolls. Stopped safely after "
                f"{sent_count} confirmed heart(s)."
            )
        before_scroll_screen = screen
        list_moved = False
        for scroll_attempt in range(max(1, min(2, int(scroll_attempts)))):
            if list_scroll_count >= max(0, int(max_list_scrolls)):
                raise RuntimeError(
                    "The bottom of the Friends leaderboard was not found after "
                    f"{list_scroll_count} scrolls. Stopped safely after "
                    f"{sent_count} confirmed heart(s)."
                )
            list_scroll_count += 1
            print(
                "🔄 Scanning the next Friends leaderboard rows "
                f"({list_scroll_count}/{max(0, int(max_list_scrolls))})..."
            )
            # ``device_scroll`` measures distance from the center to each end,
            # so 90px here is an exact 180px gesture. The slower 400ms swipe
            # avoids inertia that previously caused stacked, erratic scrolling.
            scroll_func(
                LEADERBOARD_TOP_POSITION[0],
                LEADERBOARD_TOP_POSITION[1],
                "up",
                90,
                400,
            )
            sleep_func(0.15)
            previous_settle_screen = capture_or_raise()
            if not has_ready_leaderboard(previous_settle_screen):
                raise RuntimeError(
                    "The screen left the Friends leaderboard after scrolling. "
                    f"Stopped safely after {sent_count} confirmed heart(s)."
                )

            candidate_screen = previous_settle_screen
            list_settled = False
            for _ in range(max(1, int(scroll_settle_poll_attempts))):
                sleep_func(0.12)
                candidate_screen = capture_or_raise()
                if not has_ready_leaderboard(candidate_screen):
                    raise RuntimeError(
                        "The screen left the Friends leaderboard while the "
                        "list was settling. Stopped safely after "
                        f"{sent_count} confirmed heart(s)."
                    )
                if stability_detector_func(
                    previous_settle_screen,
                    candidate_screen,
                ):
                    list_settled = True
                    break
                previous_settle_screen = candidate_screen

            if not list_settled:
                raise RuntimeError(
                    "The Friends list did not settle after scrolling. Stopped "
                    "before tapping a moving row, after "
                    f"{sent_count} confirmed heart(s)."
                )
            semantic_progress = bool(active_hearts(candidate_screen)) or bool(
                matches(
                    candidate_screen,
                    FRIEND_BOTTOM_LEADERBOARD_TEMPLATE,
                    FRIEND_BOTTOM_LEADERBOARD_REGION,
                )
            )
            if semantic_progress or movement_detector_func(
                before_scroll_screen,
                candidate_screen,
            ):
                screen = candidate_screen
                list_moved = True
                break
            screen = candidate_screen
            if scroll_attempt == 0 and max(1, min(2, int(scroll_attempts))) > 1:
                print("⚠️ Friends list did not move; retrying once...")

        if not list_moved:
            raise RuntimeError(
                "The Friends list did not move after one controlled retry, "
                "and the bottom marker was not detected. Stopped safely after "
                f"{sent_count} confirmed heart(s)."
            )
        sent_centers_since_scroll.clear()


def handle_quick_receive_and_send_lives():
    print("✉️ Handling Quick Receive and Send Lives...")
    time.sleep(random.uniform(0.8, 1.4))
    # Tap the "Mail" button
    safe_device_tap(DEVICE_IP, DEVICE_PORT, MAIL_BOX_BUTTON[0], MAIL_BOX_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
    # Tap the "Lives" tab
    safe_device_tap(DEVICE_IP, DEVICE_PORT, MAIL_BOX_LIVES_TAB_BUTTON[0], MAIL_BOX_LIVES_TAB_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
    screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
    # No lives to receive
    if detect_templates(screen, NO_LIVES_TO_RECEIVE_TEMPLATE, NO_LIVES_TO_RECEIVE_REGION):
        print("✉️ No lives to receive. Proceeding to send lives...")
        # Close the mail dialog
        safe_device_tap(DEVICE_IP, DEVICE_PORT, MAIL_BOX_CLOSE_BUTTON[0], MAIL_BOX_CLOSE_BUTTON[1])
        return
    # Receive all lives
    print("✉️ Receiving all lives...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, QUICK_RECEIVE_AND_SEND_LIVES_BUTTON[0], QUICK_RECEIVE_AND_SEND_LIVES_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
    # Tap all send life buttons
    while True:
        # Check if all lifes received and sent!, so break the loop
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        all_lives_received_and_sent = detect_templates(screen, ALL_LIVES_RECEIVED_AND_SENT_TEMPLATE, ALL_LIVES_RECEIVED_AND_SENT_REGION)
        if all_lives_received_and_sent:
            print("✉️ All lives received and sent. Done!")
            # Tap the "Confirm" button
            safe_device_tap(DEVICE_IP, DEVICE_PORT, ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON[0], ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON[1])
            time.sleep(random.uniform(0.8, 1.4))
            # Close the mail dialog
            safe_device_tap(DEVICE_IP, DEVICE_PORT, MAIL_BOX_CLOSE_BUTTON[0], MAIL_BOX_CLOSE_BUTTON[1])
            time.sleep(random.uniform(0.8, 1.4))
            break
        # Send lifes to friends
        confirm_send_life_button_coords = detect_templates(screen, CONFIRM_SEND_LIFE_TEMPLATE, CONFIRM_SEND_LIFE_REGION)
        if confirm_send_life_button_coords:
            print("✉️ Sending lives to friends...")
            safe_device_tap(DEVICE_IP, DEVICE_PORT, CONFIRM_SEND_LIFE_BUTTON[0], CONFIRM_SEND_LIFE_BUTTON[1])
            time.sleep(random.uniform(0.8, 1.4))
    print("✉️ Quick Receive and Send Lives completed.")


def close_announcement_dialog():
    print("🖱️ Closing announcement dialog...")
    for i in range(5):
        print(f"🖱️ Tapping close announcement dialog button {i+1}/5")
        safe_device_tap(DEVICE_IP, DEVICE_PORT, CLOSE_ANNOUNCEMENT_DIALOG_BUTTON[0], CLOSE_ANNOUNCEMENT_DIALOG_BUTTON[1])
        time.sleep(random.uniform(0.8, 1.4))
        # Verify whether the announcement popup is still visible
        device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if device_screen is not None:
            still_visible = detect_stage(device_screen, ["ANNOUNCEMENT", "DAILY_NEW"])
            if still_visible is None:
                print("✅ Announcement dialog closed successfully.")
                if detect_stage(device_screen, ["PARTY_RUN"]) == "PARTY_RUN":
                    close_party_run_mode()
                return
    # Fallback: check party run even if we exhausted all taps
    time.sleep(random.uniform(0.8, 1.4))
    device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
    if device_screen is not None and detect_stage(device_screen, ["PARTY_RUN"]) == "PARTY_RUN":
        close_party_run_mode()


def close_party_run_mode():
    print("🖱️ Closing Party Run mode...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, EXIT_PARTY_RUN_MODE_BUTTON[0], EXIT_PARTY_RUN_MODE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
