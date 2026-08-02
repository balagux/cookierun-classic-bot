import random
import threading
import time
from pathlib import Path

import actions as actions_module
from adb import device_capture_screen, device_connect, device_reset_app, device_tap
from actions import (
    accept_congratulations,
    accept_daily_checkin,
    accept_daily_checkin_boost_set,
    accept_daily_new,
    accept_daily_treasure,
    accept_enter_league,
    accept_league_results,
    accept_level_up,
    accept_mystery_box,
    accept_overtake_break_score,
    accept_previous_rank_results,
    accept_relic_claim,
    accept_too_many_treasures,
    close_announcement_dialog,
    close_party_run_mode,
    complete_finish,
    handle_anti_bot,
    handle_inactive,
    open_relic_complete,
    play_game,
    purchase_cookie_relay,
    purchase_desired_random_boost,
    purchase_fast_start,
    quick_exit_after_cookie_relay,
    start_game,
    using_cookie_relay,
    using_fast_start,
)
from config import (
    BOOST_17P_BASE_SPEED_TEMPLATE,
    BOOST_15P_SCORE_BONUS_TEMPLATE,
    BOOST_20P_HP_FROM_POTIONS_TEMPLATE,
    BOOST_2PIT_LIFTS_TEMPLATE,
    BOOST_70P_CRUSH_CHANCE_TEMPLATE,
    BOOST_DOUBLE_COINS_TEMPLATE,
    BOOST_GOLD_COIN_MAGIC_TEMPLATE,
    BOOST_M15P_HP_DRAIN_TEMPLATE,
    BOOST_M30P_COLLISION_DAMAGE_TEMPLATE,
    BOOST_MAGNETIC_AURA_TEMPLATE,
    BOOST_REVIVE_ONCE_WITH_80HP_TEMPLATE,
    DETECTION_ALWAYS_STAGES,
    DETECTION_GROUPS,
    DETECTION_RECOVERY_SCAN_INTERVAL,
    DEVICE_IP,
    DEVICE_PORT,
    GLOBAL_CONFIRM_TEMPLATE,
    NEXT_GAME_DELAY,
    RESULT_REWARD_MIN_WAIT,
    RESULT_REWARD_POLL_INTERVAL,
    RESULT_REWARD_STABLE_READS,
    RESULT_REWARD_TIMEOUT,
    SESSION_RESET_INTERVAL,
)
from detection import detect_all_template_matches, detect_stage, load_templates
from debug import save_debug_screen
from macro import TouchRecorder, profile_summary, replay_profile, update_profile_metadata
from result_ocr import read_result_rewards

# -------------------
# BOT OPTIONS
# -------------------
BOOST_CHOICES = [
    ("Double Coins",            BOOST_DOUBLE_COINS_TEMPLATE),
    ("+15% Score Bonus",        BOOST_15P_SCORE_BONUS_TEMPLATE),
    ("-15% HP Drain",           BOOST_M15P_HP_DRAIN_TEMPLATE),
    ("Revive Once with 80 HP",  BOOST_REVIVE_ONCE_WITH_80HP_TEMPLATE),
    ("70% Crush Chance",        BOOST_70P_CRUSH_CHANCE_TEMPLATE),
    ("+17% Base Speed",         BOOST_17P_BASE_SPEED_TEMPLATE),
    ("Gold Coin Magic",         BOOST_GOLD_COIN_MAGIC_TEMPLATE),
    ("-30% Collision Damage",   BOOST_M30P_COLLISION_DAMAGE_TEMPLATE),
    ("+20% HP from Potions",    BOOST_20P_HP_FROM_POTIONS_TEMPLATE),
    ("Magnetic Aura",           BOOST_MAGNETIC_AURA_TEMPLATE),
    ("2 Pit Lifts",             BOOST_2PIT_LIFTS_TEMPLATE),
]


def get_detection_stage_names(group_name):
    stage_names = []
    # For non-in-game groups, always stages have higher priority
    if group_name != "IN_GAME":
        for stage_name in DETECTION_ALWAYS_STAGES:
            if stage_name not in stage_names:
                stage_names.append(stage_name)
    # Add stages from the specified detection group
    for stage_name in DETECTION_GROUPS[group_name]:
        if stage_name not in stage_names:
            stage_names.append(stage_name)
    # For in-game, always stages are appended last (original behavior)
    if group_name == "IN_GAME":
        for stage_name in DETECTION_ALWAYS_STAGES:
            if stage_name not in stage_names:
                stage_names.append(stage_name)
    return stage_names


def should_quick_exit_after_relay(options):
    """Quick-exit only during automated replay, never while recording a profile."""
    return bool(options.get("use_cookie_relay") and not options.get("record_profile"))


def prompt_user_options():
    desired_boost_template = None

    print("⚙️ --- Bot Options ---")
    use_fast_start = input("⚡ Use Fast Start (buy + use)? [y/n]: ").strip().lower() == "y"
    use_cookie_relay = input("🍪 Use Cookie Relay (buy + use)? [y/n]: ").strip().lower() == "y"
    use_desired_random_boost = input("🎲 Use Desired Random Boost (buy + use)? [y/n]: ").strip().lower() == "y"
    if use_desired_random_boost:
        print("  Select desired boost (must match the boost option configured in-game):")
        for i, (name, _) in enumerate(BOOST_CHOICES, 1):
            print(f"  {i:2}. {name}")
        while True:
            choice = input("  Enter number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(BOOST_CHOICES):
                desired_boost_template = BOOST_CHOICES[int(choice) - 1][1]
                desired_boost_name = BOOST_CHOICES[int(choice) - 1][0]
                print(f"  ✅ Selected: {desired_boost_name}")
                break
            print(f"  ⚠️ Please enter a number between 1 and {len(BOOST_CHOICES)}.")
    print("---------------------")

    return {
        "use_fast_start": use_fast_start,
        "use_cookie_relay": use_cookie_relay,
        "use_desired_random_boost": use_desired_random_boost,
        "desired_boost_template": desired_boost_template,
        "desired_boost_name": desired_boost_name if use_desired_random_boost else None,
    }


# -------------------
# MAIN LOOP
# -------------------
def configure_device(device_ip, device_port):
    """Apply GUI/CLI device settings to modules that perform ADB actions."""
    global DEVICE_IP, DEVICE_PORT

    DEVICE_IP = str(device_ip).strip()
    DEVICE_PORT = int(device_port)
    actions_module.DEVICE_IP = DEVICE_IP
    actions_module.DEVICE_PORT = DEVICE_PORT


def _replay_profile_safely(profile_path, stop_event=None, timeline_started_at=None):
    try:
        print(f"🎬 Replaying recorded run: {Path(profile_path).name}")
        action_count = replay_profile(
            DEVICE_IP,
            DEVICE_PORT,
            profile_path,
            stop_event=stop_event,
            timeline_started_at=timeline_started_at,
        )
        if stop_event is not None and stop_event.is_set():
            print(f"⏹️ Replay cancelled cleanly after {action_count} touch actions.")
        else:
            print(f"✅ Replay completed ({action_count} touch actions).")
    except Exception as exc:
        print(f"❌ Replay failed: {exc}")


def _dismiss_visible_confirm_buttons(screen, max_clicks=8, action_lock=None):
    """Click visible Confirm buttons and recapture until none remain."""
    click_count = 0
    current_screen = screen
    initial_matches = detect_all_template_matches(current_screen, GLOBAL_CONFIRM_TEMPLATE)
    if not initial_matches:
        return click_count, current_screen

    acquired = action_lock is None or action_lock.acquire(timeout=0.5)
    if not acquired:
        return click_count, current_screen
    try:
        # Another detector may have cleared the dialog before this lock was acquired.
        if action_lock is not None:
            current_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        while click_count < max_clicks:
            matches = detect_all_template_matches(current_screen, GLOBAL_CONFIRM_TEMPLATE)
            if not matches:
                break
            x, y, width, height = matches[0]
            click_count += 1
            print(f"✅ Confirm button detected — clicking ({click_count}/{max_clicks}).")
            device_tap(DEVICE_IP, DEVICE_PORT, x + width // 2, y + height // 2)
            time.sleep(0.12)
            current_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
    finally:
        if action_lock is not None:
            action_lock.release()
    if click_count:
        print(f"✅ Cleared {click_count} Confirm button(s).")
    return click_count, current_screen


def _read_stable_result_rewards(
    initial_screen,
    capture_func=None,
    ocr_func=None,
    min_wait=RESULT_REWARD_MIN_WAIT,
    poll_interval=RESULT_REWARD_POLL_INTERVAL,
    stable_reads=RESULT_REWARD_STABLE_READS,
    timeout=RESULT_REWARD_TIMEOUT,
):
    """Wait for Result Coins/XP count-up animations to settle before returning."""
    capture_func = capture_func or (
        lambda: device_capture_screen(DEVICE_IP, DEVICE_PORT)
    )
    ocr_func = ocr_func or read_result_rewards
    started_at = time.monotonic()
    screen = initial_screen
    previous_complete = None
    consecutive_reads = 0
    latest_coins = None
    latest_exp = None
    latest_details = {"coins": None, "exp": None}
    last_logged_values = None

    while True:
        coins, exp, details = ocr_func(screen)
        if coins is not None:
            latest_coins = coins
        if exp is not None:
            latest_exp = exp
        if coins is not None or exp is not None:
            latest_details = details

        complete_values = (coins, exp) if coins is not None and exp is not None else None
        if complete_values is not None and complete_values == previous_complete:
            consecutive_reads += 1
        elif complete_values is not None:
            previous_complete = complete_values
            consecutive_reads = 1
        else:
            consecutive_reads = 0

        elapsed = time.monotonic() - started_at
        display_values = (latest_coins, latest_exp)
        if display_values != last_logged_values and any(value is not None for value in display_values):
            print(
                f"[OCR] Reward count-up: coins={latest_coins} exp={latest_exp} "
                f"({elapsed:.1f}s)"
            )
            last_logged_values = display_values

        if (
            complete_values is not None
            and elapsed >= min_wait
            and consecutive_reads >= stable_reads
        ):
            print(
                f"[OCR] Final rewards stable: coins={coins} exp={exp} "
                f"after {elapsed:.1f}s."
            )
            return coins, exp, details, screen, True

        if elapsed >= timeout:
            print(
                f"[OCR] Reward count-up timeout after {elapsed:.1f}s; "
                f"using latest values coins={latest_coins} exp={latest_exp}."
            )
            return latest_coins, latest_exp, latest_details, screen, False

        time.sleep(max(0.0, poll_interval))
        screen = capture_func()


def _save_profile_rewards(profile_path, coins, exp):
    """Update fields OCR managed to read while preserving any missing value."""
    if profile_path is None or (coins is None and exp is None):
        return None
    try:
        summary = profile_summary(profile_path)
        saved_coins = summary["coins"] if coins is None else coins
        saved_exp = summary["exp"] if exp is None else exp
        update_profile_metadata(
            profile_path,
            summary["name"],
            saved_coins,
            saved_exp,
        )
        print(
            f"[PROFILE_REWARDS_UPDATED] {Path(profile_path).name} "
            f"coins={saved_coins} exp={saved_exp}"
        )
        return {**summary, "coins": saved_coins, "exp": saved_exp}
    except (OSError, ValueError, KeyError) as exc:
        print(f"[OCR] Could not update profile rewards: {exc}")
        return None


def main(options=None, device_ip=None, device_port=None):
    if device_ip is not None or device_port is not None:
        configure_device(
            DEVICE_IP if device_ip is None else device_ip,
            DEVICE_PORT if device_port is None else device_port,
        )

    recorder = None
    try:
        print("🚀 CookieRun Classic Bot Started")
        print("⚠️ Screen must be 1280x720 resolution for the bot to work properly.")
        print(f"📱 Connecting to device at {DEVICE_IP}:{DEVICE_PORT}...")

        device_connect(DEVICE_IP, DEVICE_PORT)
        initial_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        if initial_screen is None:
            raise RuntimeError("Connected, but the device screenshot could not be decoded.")
        screen_height, screen_width = initial_screen.shape[:2]
        if (screen_width, screen_height) != (1280, 720):
            raise RuntimeError(
                f"Unsupported screen resolution {screen_width}x{screen_height}; "
                "this version requires LDPlayer 1280x720."
            )
        load_templates()

        # * for debugging *
        # device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
        # save_debug_screen(device_screen)

        if options is None:
            options = prompt_user_options()

        last_stage = None
        is_first_game = True
        detection_group = "PRE_GAME"
        last_detected_time = time.time()
        session_start_time = time.time()
        session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
        recording_completed = False
        game_macro_started = False
        macro_thread = None
        macro_stop_event = None
        retry_interrupted_run = False
        relay_quick_exit_pending = False
        relay_quick_exit_rewards = {"coins": 0, "exp": 0}
        session_run_count = 0
        completed_run_count = 0
        session_coins = 0
        session_exp = 0
        current_profile_stats = {"coins": 0, "exp": 0}
        current_profile_path = None

        while True:
            device_screen = device_capture_screen(DEVICE_IP, DEVICE_PORT)
            # The watcher owns the click. The main loop pauses so it cannot also
            # trigger a stage action against the same dialog or the screen below it.
            if detect_all_template_matches(device_screen, GLOBAL_CONFIRM_TEMPLATE):
                _dismiss_visible_confirm_buttons(device_screen)
                last_stage = None
                last_detected_time = time.time()
                continue
            stage = detect_stage(device_screen, get_detection_stage_names(detection_group))
            if stage is None:
                if time.time() - last_detected_time >= DETECTION_RECOVERY_SCAN_INTERVAL[detection_group]:
                    stage = detect_stage(device_screen)
                    last_detected_time = time.time()
            else:
                last_detected_time = time.time()

            if stage == last_stage:
                time.sleep(0.1)
                continue

            last_stage = stage

            if stage == "MAINMENU":
                print("🎮 Detected Stage: MAINMENU")
                quick_exit_return = relay_quick_exit_pending
                if quick_exit_return:
                    relay_quick_exit_pending = False
                    completed_run_count += 1
                    session_coins += int(relay_quick_exit_rewards.get("coins", 0))
                    session_exp += int(relay_quick_exit_rewards.get("exp", 0))
                    relay_quick_exit_rewards = {"coins": 0, "exp": 0}
                    current_profile_path = None
                    current_profile_stats = {"coins": 0, "exp": 0}
                    print("✅ Relay quick-exit round confirmed at Main Menu.")
                    print(
                        f"[STATS] attempts={session_run_count} completed={completed_run_count} "
                        f"coins={session_coins} exp={session_exp}"
                    )
                premature_return = (
                    not quick_exit_return
                    and not options.get("record_profile")
                    and detection_group == "IN_GAME"
                    and game_macro_started
                )
                if premature_return:
                    print(
                        "⚠️ Returned to Main Menu before GAME_COMPLETE — "
                        "cancelling the remaining replay and retrying this run."
                    )
                    if macro_stop_event is not None:
                        macro_stop_event.set()
                    if macro_thread is not None:
                        macro_thread.join(timeout=5)
                    macro_thread = None
                    macro_stop_event = None
                    game_macro_started = False
                    current_profile_path = None
                    current_profile_stats = {"coins": 0, "exp": 0}
                    session_run_count = max(completed_run_count, session_run_count - 1)
                    retry_interrupted_run = True
                    detection_group = "PRE_GAME"
                    print(
                        f"[STATS] attempts={session_run_count} completed={completed_run_count} "
                        f"coins={session_coins} exp={session_exp}"
                    )
                # Wait screen refresh
                refresh_wait = 0.5 if quick_exit_return else 1.0
                print(f"⏳ Waiting {refresh_wait:.0f} seconds for screen refresh...")
                time.sleep(refresh_wait)
                if recorder is not None and options.get("record_profile"):
                    record_path = Path(options["record_profile"])
                    action_count = recorder.stop_and_save(record_path)
                    recorder = None
                    recording_completed = True
                    if action_count:
                        print(
                            f"💾 Saved partial recording {record_path.name} "
                            f"after Pause/Quit ({action_count} actions)."
                        )
                    else:
                        record_path.unlink(missing_ok=True)
                        print("⚠️ No input was captured; partial recording was not saved.")
                if recording_completed:
                    print("✅ Recording run finished. Returning control to the GUI.")
                    return
                max_runs = int(options.get("max_runs", 0) or 0)
                if (
                    not options.get("record_profile")
                    and max_runs > 0
                    and session_run_count >= max_runs
                ):
                    print(
                        f"🏁 Run limit reached ({session_run_count}/{max_runs}). "
                        f"Estimated total: {session_coins:,} coins, {session_exp:,} EXP."
                    )
                    return
                elapsed = time.time() - session_start_time
                if elapsed >= session_reset_interval:
                    print(f"🔄 Session reset triggered after {elapsed / 3600:.2f}h — restarting app...")
                    device_reset_app(DEVICE_IP, DEVICE_PORT)
                    close_announcement_dialog()
                    session_start_time = time.time()
                    session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
                    detection_group = "PRE_GAME"
                    last_stage = None
                    is_first_game = True
                    continue
                if detection_group == "POST_GAME":
                    detection_group = "PRE_GAME"
                    last_stage = None
                    continue
                if not is_first_game:
                    if quick_exit_return:
                        print("⚡ Relay quick-exit complete — starting the next run immediately...")
                    elif retry_interrupted_run:
                        print("🔄 Retrying the interrupted run immediately...")
                    else:
                        delay = random.uniform(*NEXT_GAME_DELAY)
                        print(f"⏳ Waiting for {delay:.2f} seconds before starting the next game...")
                        time.sleep(delay)
                retry_interrupted_run = False
                is_first_game = False
                start_game()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "PURCHASE_ITEM":
                print("🛒 Detected Stage: PURCHASE_ITEM")
                if macro_stop_event is not None:
                    macro_stop_event.set()
                if macro_thread is not None:
                    macro_thread.join(timeout=5)
                macro_thread = None
                macro_stop_event = None
                game_macro_started = False
                if options["use_fast_start"]:
                    purchase_fast_start()
                if options["use_cookie_relay"]:
                    purchase_cookie_relay()
                if options["use_desired_random_boost"]:
                    purchase_desired_random_boost(options["desired_boost_template"], options["desired_boost_name"])
                run_timeline_started_at = play_game()
                current_profile_stats = {"coins": 0, "exp": 0}
                current_profile_path = None
                if not options.get("record_profile"):
                    session_run_count += 1
                    print(
                        f"[STATS] attempts={session_run_count} completed={completed_run_count} "
                        f"coins={session_coins} exp={session_exp}"
                    )
                if not game_macro_started:
                    game_macro_started = True
                    record_path = options.get("record_profile")
                    replay_profiles = options.get("replay_profiles") or []
                    if record_path:
                        recorder = TouchRecorder(
                            DEVICE_IP,
                            DEVICE_PORT,
                            autosave_path=record_path,
                            profile_name=options.get("profile_name"),
                        )
                        recorder.start(timeline_started_at=run_timeline_started_at)
                        print("🔴 Recording started after Play — play this run yourself now.")
                    elif replay_profiles:
                        selected_profile = random.choice(replay_profiles)
                        current_profile_path = selected_profile
                        try:
                            current_profile_stats = profile_summary(selected_profile)
                        except (OSError, ValueError, KeyError):
                            current_profile_stats = {"coins": 0, "exp": 0}
                        macro_stop_event = threading.Event()
                        macro_thread = threading.Thread(
                            target=_replay_profile_safely,
                            args=(selected_profile, macro_stop_event, run_timeline_started_at),
                            daemon=True,
                        )
                        macro_thread.start()
                detection_group = "IN_GAME"
                time.sleep(0.2)
                last_stage = None
            elif stage == "GAME_START":
                print("🏁 Detected Stage: GAME_START")
                if options["use_fast_start"]:
                    using_fast_start()
                detection_group = "IN_GAME"
                last_stage = None
            elif stage == "GAME_RELAY":
                print("🔄 Detected Stage: GAME_RELAY")
                if options["use_cookie_relay"]:
                    quick_exit_enabled = should_quick_exit_after_relay(options)
                    if quick_exit_enabled:
                        if macro_stop_event is not None:
                            macro_stop_event.set()
                        if macro_thread is not None:
                            macro_thread.join(timeout=5)
                        macro_thread = None
                        macro_stop_event = None
                        game_macro_started = False
                        using_cookie_relay(wait_after=False)
                        relay_quick_exit_pending = quick_exit_after_cookie_relay()
                        last_stage = None
                    else:
                        using_cookie_relay()
                detection_group = "POST_GAME" if relay_quick_exit_pending else "IN_GAME"
                last_stage = None
            elif stage == "GAME_COMPLETE":
                if relay_quick_exit_pending:
                    if macro_stop_event is not None:
                        macro_stop_event.set()
                    if macro_thread is not None:
                        macro_thread.join(timeout=5)
                    macro_thread = None
                    macro_stop_event = None
                    try:
                        (
                            result_coins,
                            result_exp,
                            ocr_details,
                            device_screen,
                            rewards_stable,
                        ) = _read_stable_result_rewards(device_screen)
                        result_coins = int(result_coins or 0)
                        result_exp = int(result_exp or 0)
                        print(
                            f"[OCR] Relay quick result: coins={result_coins} exp={result_exp} "
                            f"stable={rewards_stable} details={ocr_details}"
                        )
                    except Exception as exc:
                        result_coins = result_exp = 0
                        print(f"[OCR] Relay quick result could not be read: {exc}")
                    relay_quick_exit_rewards = {
                        "coins": result_coins,
                        "exp": result_exp,
                    }
                    _save_profile_rewards(
                        current_profile_path,
                        result_coins if result_coins > 0 else None,
                        result_exp if result_exp > 0 else None,
                    )
                    complete_finish(wait_after=False)
                    game_macro_started = False
                    detection_group = "POST_GAME"
                    last_stage = None
                    continue
                if macro_stop_event is not None:
                    macro_stop_event.set()
                if macro_thread is not None:
                    macro_thread.join(timeout=5)
                macro_thread = None
                macro_stop_event = None
                finished_record_path = None
                finished_record_action_count = None
                if recorder is not None:
                    # Stop timing immediately when Result appears. OCR may wait for
                    # count-up animations and must not extend the recorded profile.
                    finished_record_path = Path(options["record_profile"])
                    finished_record_action_count = recorder.stop_and_save(
                        finished_record_path
                    )
                    recorder = None
                    recording_completed = True
                result_coins = None
                result_exp = None
                try:
                    (
                        result_coins,
                        result_exp,
                        ocr_details,
                        device_screen,
                        rewards_stable,
                    ) = _read_stable_result_rewards(device_screen)
                    coin_detail = ocr_details.get("coins")
                    exp_detail = ocr_details.get("exp")
                    if result_coins is not None or result_exp is not None:
                        print(
                            f"[OCR] Result rewards: coins={result_coins} exp={result_exp} "
                            f"(raw coins={coin_detail}, raw exp={exp_detail})"
                        )
                        if result_coins is None or result_exp is None:
                            print("[OCR] One reward value was unreadable; its existing value was kept.")
                            save_debug_screen(device_screen)
                    else:
                        print("[OCR] Could not read Coins or XP; existing profile values were kept.")
                        save_debug_screen(device_screen)
                except Exception as exc:
                    print(f"[OCR] Reward reading failed; existing values were kept: {exc}")
                    save_debug_screen(device_screen)
                print("✅ Detected Stage: GAME_COMPLETE")
                if finished_record_path is not None:
                    if finished_record_action_count:
                        _save_profile_rewards(
                            finished_record_path,
                            result_coins,
                            result_exp,
                        )
                        print(
                            f"💾 Saved recording {finished_record_path.name} "
                            f"({finished_record_action_count} touch actions)."
                        )
                    else:
                        finished_record_path.unlink(missing_ok=True)
                        print("⚠️ No touch actions were captured; recording was not saved.")
                elif not options.get("record_profile"):
                    completed_run_count += 1
                    updated_stats = _save_profile_rewards(
                        current_profile_path,
                        result_coins,
                        result_exp,
                    )
                    if updated_stats is not None:
                        current_profile_stats = updated_stats
                    run_coins = (
                        result_coins
                        if result_coins is not None
                        else int(current_profile_stats.get("coins", 0))
                    )
                    run_exp = (
                        result_exp
                        if result_exp is not None
                        else int(current_profile_stats.get("exp", 0))
                    )
                    session_coins += int(run_coins)
                    session_exp += int(run_exp)
                    print(
                        f"[STATS] attempts={session_run_count} completed={completed_run_count} "
                        f"coins={session_coins} exp={session_exp}"
                    )
                complete_finish()
                game_macro_started = False
                detection_group = "POST_GAME"
                last_stage = None
            elif stage == "MYSTERY_BOX":
                print("🎁 Detected Stage: MYSTERY_BOX")
                accept_mystery_box()
                time.sleep(0.5)
                detection_group = "POST_GAME"
                last_stage = None
            elif stage == "CONGRATULATIONS":
                print("🎉 Detected Stage: CONGRATULATIONS")
                accept_congratulations()
                detection_group = "POST_GAME"
                last_stage = None
            elif stage == "LEVEL_UP":
                print("⬆️ Detected Stage: LEVEL_UP")
                accept_level_up()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "DAILY_CHECKIN":
                print("📅 Detected Stage: DAILY_CHECKIN")
                accept_daily_checkin()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "DAILY_CHECKIN_BOOST_SET":
                print("📅 Detected Stage: DAILY_CHECKIN_BOOST_SET")
                accept_daily_checkin_boost_set()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "DAILY_TREASURE":
                print("💎 Detected Stage: DAILY_TREASURE")
                accept_daily_treasure()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "DAILY_NEW":
                print("📰 Detected Stage: DAILY_NEW")
                accept_daily_new()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "ENTER_LEAGUE":
                print("🏆 Detected Stage: ENTER_LEAGUE")
                accept_enter_league()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "LEAGUE_RESULTS":
                print("🏆 Detected Stage: LEAGUE_RESULTS")
                accept_league_results()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "PREVIOUS_RANK_RESULTS":
                print("🏆 Detected Stage: PREVIOUS_RANK_RESULTS")
                accept_previous_rank_results()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "OVERTAKE_BREAK_SCORE":
                print("🏆 Detected Stage: OVERTAKE_BREAK_SCORE")
                accept_overtake_break_score()
                detection_group = "POST_GAME"
                last_stage = None
            elif stage == "TOO_MANY_TREASURES":
                print("💎 Detected Stage: TOO_MANY_TREASURES")
                accept_too_many_treasures()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "RELIC_COMPLETE":
                print("🏺 Detected Stage: RELIC_COMPLETE")
                open_relic_complete()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "RELIC_CLAIM":
                print("🏺 Detected Stage: RELIC_CLAIM")
                accept_relic_claim()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "PARTY_RUN":
                print("🎉 Detected Stage: PARTY_RUN")
                close_party_run_mode()
                detection_group = "PRE_GAME"
                last_stage = None
            elif stage == "ANTI_BOT":
                print("⚠️ Detected Stage: ANTI_BOT")
                handle_anti_bot(device_screen)
                last_stage = None
            elif stage == "CONNECTION_LOST":
                print("🔌 Detected Stage: CONNECTION_LOST")
                device_reset_app(DEVICE_IP, DEVICE_PORT)
                close_announcement_dialog()
                session_start_time = time.time()
                session_reset_interval = random.uniform(*SESSION_RESET_INTERVAL)
                detection_group = "PRE_GAME"
                last_stage = None
                is_first_game = True
            elif stage == "INACTIVE":
                print("💤 Detected Stage: INACTIVE")
                handle_inactive()
                last_stage = None
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise
    finally:
        if "macro_stop_event" in locals() and macro_stop_event is not None:
            macro_stop_event.set()
        if "macro_thread" in locals() and macro_thread is not None:
            macro_thread.join(timeout=5)
        if recorder is not None:
            recorder.stop()
