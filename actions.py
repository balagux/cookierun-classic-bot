import random
import time

import cv2

from adb import device_capture_screen, device_tap, safe_device_scroll, safe_device_tap
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
    CLOSE_SEND_LIFE_DIALOG_BUTTON,
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
    FRIEND_BOTTOM_LEADERBOARD_REGION,
    FRIEND_BOTTOM_LEADERBOARD_TEMPLATE,
    FRIEND_SEND_LIFE_REGION,
    FRIEND_SEND_LIFE_TEMPLATE,
    FRIEND_TOP_LEADERBOARD_REGION,
    FRIEND_TOP_LEADERBOARD_TEMPLATE,
    INACTIVE_RELOAD_BUTTON,
    LEADERBOARD_BOTTOM_POSITION,
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
)
from detection import detect_templates, detect_anti_bot_odd_cards, detect_stage
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


def purchase_desired_random_boost(desired_template, desired_name):
    print("🛒 Purchasing Desired Random Boost...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, RANDOM_BOOST_ITEM[0], RANDOM_BOOST_ITEM[1])
    time.sleep(random.uniform(0.8, 1.4))
    safe_device_tap(DEVICE_IP, DEVICE_PORT, MULTI_PURCHASE_BUTTON[0], MULTI_PURCHASE_BUTTON[1])
    time.sleep(random.uniform(1, 2))
    selection_button = RANDOM_BOOST_SELECTION_BUTTONS.get(desired_name)
    if selection_button is None:
        print(f"❌ No selection coordinate configured for boost: {desired_name}")
        return
    print(f"🎯 Selecting desired boost: {desired_name}...")
    selection_confirmed = False
    for attempt in range(1, 4):
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if is_boost_selection_checked(screen, selection_button):
            selection_confirmed = True
            break
        print(f"🎯 Tapping boost option ({attempt}/3)...")
        device_tap(DEVICE_IP, DEVICE_PORT, selection_button[0], selection_button[1])
        time.sleep(0.9)
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if is_boost_selection_checked(screen, selection_button):
            selection_confirmed = True
            break
    if not selection_confirmed:
        print(f"❌ Could not confirm the check mark for boost: {desired_name}")
        print("⚠️ Multi-Buy was not pressed, so no Coins were spent accidentally.")
        safe_device_tap(
            DEVICE_IP,
            DEVICE_PORT,
            RANDOM_BOOST_DIALOG_CLOSE_BUTTON[0],
            RANDOM_BOOST_DIALOG_CLOSE_BUTTON[1],
        )
        time.sleep(0.8)
        return
    print(f"✅ Boost option checked: {desired_name}")
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
    """Wait for cookie two to run out, then leave through Pause -> Quit."""
    print("🏃 Waiting for the second cookie to run out...")
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


def handle_send_friend_life():
    print("💌 Handling Send Friend Life...")
    screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
    # Scroll leaderboard to top stop when find the "FRIEND LEADERBOARD" template
    while True:
        if detect_templates(screen, FRIEND_TOP_LEADERBOARD_TEMPLATE, FRIEND_TOP_LEADERBOARD_REGION):
            print("✅ Top of Friend Leaderboard reached.")
            break
        print("🔄 Scrolling up to find Send Friend Life...")
        safe_device_scroll(DEVICE_IP, DEVICE_PORT, LEADERBOARD_BOTTOM_POSITION[0], LEADERBOARD_BOTTOM_POSITION[1], direction="down", distance=300, duration=150)
        time.sleep(random.uniform(0.8, 1.4))
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
    # Scroll down, tap all send life buttons, stop when bottom leaderboard detected
    no_button_scroll_count = 0
    while True:
        screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if detect_templates(screen, FRIEND_BOTTOM_LEADERBOARD_TEMPLATE, FRIEND_BOTTOM_LEADERBOARD_REGION):
            print("✅ Bottom of Friend Leaderboard reached. Done sending lives.")
            break
        send_life_button_coords = detect_templates(screen, FRIEND_SEND_LIFE_TEMPLATE, FRIEND_SEND_LIFE_REGION)
        if send_life_button_coords:
            no_button_scroll_count = 0
            for x, y, w, h in send_life_button_coords:
                print("💌 Sending life to friend...")
                safe_device_tap(DEVICE_IP, DEVICE_PORT, x + w // 2, y + h // 2)
                time.sleep(random.uniform(0.8, 1.4))
                print("💌 Confirming send life...")
                safe_device_tap(DEVICE_IP, DEVICE_PORT, CONFIRM_SEND_LIFE_BUTTON[0], CONFIRM_SEND_LIFE_BUTTON[1])
                time.sleep(random.uniform(0.8, 1.4))
                print("💌 Closing send life dialog...")
                safe_device_tap(DEVICE_IP, DEVICE_PORT, CLOSE_SEND_LIFE_DIALOG_BUTTON[0], CLOSE_SEND_LIFE_DIALOG_BUTTON[1])
                time.sleep(random.uniform(0.8, 1.4))
        else:
            no_button_scroll_count += 1
            if no_button_scroll_count >= 30:
                print("⚠️ No send life buttons found for 30 consecutive scrolls. Giving up.")
                break
            print(f"🔄 No send life buttons found, scrolling down... ({no_button_scroll_count}/30)")
            safe_device_scroll(DEVICE_IP, DEVICE_PORT, LEADERBOARD_TOP_POSITION[0], LEADERBOARD_TOP_POSITION[1], direction="up", distance=70, duration=150)
            time.sleep(random.uniform(0.8, 1.4))


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
    time.sleep(random.uniform(0.8, 1.4))
    device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
    if detect_stage(device_screen, ["PARTY_RUN"]) == "PARTY_RUN":
        close_party_run_mode()


def close_party_run_mode():
    print("🖱️ Closing Party Run mode...")
    safe_device_tap(DEVICE_IP, DEVICE_PORT, EXIT_PARTY_RUN_MODE_BUTTON[0], EXIT_PARTY_RUN_MODE_BUTTON[1])
    time.sleep(random.uniform(0.8, 1.4))
