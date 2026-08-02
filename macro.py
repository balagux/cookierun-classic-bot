import ctypes
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

from adb import ADB_EXECUTABLE, ADB_SUBPROCESS_FLAGS, _resolve_device_target, adb_run
from config import LEGACY_REPLAY_START_DELAY, REPLAY_INPUT_LEAD_TIME
from runtime_paths import app_path


PROFILE_DIR = app_path("recordings")
INPUT_DEVICES = ("/dev/input/event4", "/dev/input/event2")
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CONTROL_COORDS = {
    "jump": (160, 625),
    "slide": (1110, 625),
}
WINDOWS_CONTROLS = {
    0x57: "jump",  # W
    0x53: "slide",  # S
}
SPECIAL_TOUCH_REGIONS = {
    "pause": (1120, 0, 1280, 160),
    "continue": (450, 220, 830, 380),
    "quit": (450, 360, 830, 560),
}

_EVENT_RE = re.compile(
    r"\[\s*[\d.]+\]\s+(?:/dev/input/event\d+:\s+)?"
    r"EV_ABS\s+(ABS_MT_SLOT|ABS_MT_TRACKING_ID|ABS_MT_POSITION_X|ABS_MT_POSITION_Y)\s+"
    r"([0-9a-fA-F]+)"
)
_KEY_EVENT_RE = re.compile(
    r"\[\s*[\d.]+\]\s+(?:/dev/input/event\d+:\s+)?"
    r"EV_KEY\s+(KEY_W|KEY_S)\s+(DOWN|UP|00000000|00000001|00000002)"
)


def list_profiles():
    PROFILE_DIR.mkdir(exist_ok=True)
    profiles = []
    for path in sorted(PROFILE_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data.get("actions"), list):
                profiles.append(path)
        except (OSError, json.JSONDecodeError):
            continue
    return profiles


def profile_summary(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    actions = data.get("actions", [])
    calculated_duration = max(
        (float(action.get("at", 0)) + float(action.get("duration", 0)) for action in actions),
        default=0.0,
    )
    jump_count = 0
    slide_count = 0
    pause_count = 0
    continue_count = 0
    quit_count = 0
    touch_count = 0
    keyboard_count = 0
    for action in actions:
        action_type = str(action.get("type", "touch"))
        if action_type == "touch":
            touch_count += 1
        else:
            keyboard_count += 1

        control = str(action.get("control", "")).lower()
        key = str(action.get("key", "")).upper()
        label = str(action.get("label", "")).lower()
        if control == "jump" or key == "W":
            jump_count += 1
        elif control == "slide" or key == "S":
            slide_count += 1
        elif action_type == "touch" and not label:
            x = int(action.get("x1", -1))
            y = int(action.get("y1", -1))
            if y >= 500 and x <= 420:
                jump_count += 1
            elif y >= 500 and x >= 860:
                slide_count += 1

        if label == "pause":
            pause_count += 1
        elif label == "continue":
            continue_count += 1
        elif label == "quit":
            quit_count += 1

    resolution = data.get("resolution", [SCREEN_WIDTH, SCREEN_HEIGHT])
    return {
        "name": str(data.get("name") or path.stem),
        "duration_seconds": float(data.get("duration_seconds", calculated_duration)),
        "coins": max(0, int(data.get("coins", 0))),
        "exp": max(0, int(data.get("exp", 0))),
        "action_count": len(actions),
        "created_at": str(data.get("created_at", "")),
        "jump_count": jump_count,
        "slide_count": slide_count,
        "pause_count": pause_count,
        "continue_count": continue_count,
        "quit_count": quit_count,
        "touch_count": touch_count,
        "keyboard_count": keyboard_count,
        "resolution": resolution,
    }


def update_profile_metadata(path, name, coins, exp):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["name"] = str(name).strip() or path.stem
    data["coins"] = max(0, int(coins))
    data["exp"] = max(0, int(exp))
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary_path.replace(path)


class TouchRecorder:
    """Record Android multitouch gestures from getevent as timed screen actions."""

    def __init__(
        self,
        ip,
        port,
        input_devices=INPUT_DEVICES,
        autosave_path=None,
        profile_name=None,
    ):
        self.ip = ip
        self.port = port
        self.input_devices = tuple(input_devices)
        self.autosave_path = Path(autosave_path) if autosave_path else None
        self.profile_name = str(profile_name).strip() if profile_name else None
        self.process = None
        self.thread = None
        self.keyboard_thread = None
        self.actions = []
        self._started_at = None
        self._created_at = None
        self._slots = {}
        self._current_slot = 0
        self._key_down_at = {}
        self._keyboard_stop = threading.Event()
        self._lock = threading.Lock()
        self._save_lock = threading.Lock()

    def start(self, timeline_started_at=None):
        target = _resolve_device_target(self.ip, self.port)
        self._started_at = (
            float(timeline_started_at)
            if timeline_started_at is not None
            else time.monotonic()
        )
        self._created_at = time.strftime("%Y-%m-%d %H:%M:%S")
        if self.autosave_path is not None:
            self.autosave_path.parent.mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen(
            [ADB_EXECUTABLE, "-s", target, "shell", "getevent", "-lt"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=ADB_SUBPROCESS_FLAGS,
        )
        self.thread = threading.Thread(target=self._read_events, daemon=True)
        self.thread.start()
        if os.name == "nt":
            self.keyboard_thread = threading.Thread(target=self._poll_windows_keyboard, daemon=True)
            self.keyboard_thread.start()

    def _slot(self):
        return self._slots.setdefault(
            self._current_slot,
            {"down_at": None, "start_x": None, "start_y": None, "x": None, "y": None},
        )

    def _read_events(self):
        if self.process is None or self.process.stdout is None:
            return
        for line in iter(self.process.stdout.readline, ""):
            key_match = _KEY_EVENT_RE.search(line)
            if key_match:
                self._handle_key_event(*key_match.groups())
                continue
            match = _EVENT_RE.search(line)
            if not match:
                continue
            event_name, raw_value = match.groups()
            value = int(raw_value, 16)
            now = time.monotonic()

            if event_name == "ABS_MT_SLOT":
                self._current_slot = value
                continue

            slot = self._slot()
            if event_name == "ABS_MT_TRACKING_ID":
                if value == 0xFFFFFFFF:
                    self._finish_touch(slot, now)
                else:
                    slot.update(
                        down_at=now,
                        start_x=None,
                        start_y=None,
                        x=None,
                        y=None,
                    )
            elif event_name == "ABS_MT_POSITION_X":
                slot["x"] = max(0, min(SCREEN_WIDTH - 1, value))
                if slot["start_x"] is None:
                    slot["start_x"] = slot["x"]
            elif event_name == "ABS_MT_POSITION_Y":
                slot["y"] = max(0, min(SCREEN_HEIGHT - 1, value))
                if slot["start_y"] is None:
                    slot["start_y"] = slot["y"]

    def _handle_key_event(self, key_name, state):
        now = time.monotonic()
        is_down = state in ("DOWN", "00000001")
        is_up = state in ("UP", "00000000")
        if is_down and key_name not in self._key_down_at:
            self._key_down_at[key_name] = now
        elif is_up and key_name in self._key_down_at and self._started_at is not None:
            down_at = self._key_down_at.pop(key_name)
            self._append_action(
                {
                    "type": "key",
                    "key": key_name.removeprefix("KEY_"),
                    "at": round(down_at - self._started_at, 4),
                    "duration": round(max(0.02, now - down_at), 4),
                }
            )

    def _poll_windows_keyboard(self):
        user32 = ctypes.windll.user32
        pressed_at = {}
        while not self._keyboard_stop.wait(0.005):
            now = time.monotonic()
            for virtual_key, control in WINDOWS_CONTROLS.items():
                is_pressed = bool(user32.GetAsyncKeyState(virtual_key) & 0x8000)
                if is_pressed and virtual_key not in pressed_at:
                    pressed_at[virtual_key] = now
                elif not is_pressed and virtual_key in pressed_at:
                    down_at = pressed_at.pop(virtual_key)
                    self._append_control(control, down_at, now)
        now = time.monotonic()
        for virtual_key, down_at in pressed_at.items():
            self._append_control(WINDOWS_CONTROLS[virtual_key], down_at, now)

    def _append_control(self, control, down_at, up_at):
        if self._started_at is None:
            return
        self._append_action(
            {
                "type": "control",
                "control": control,
                "at": round(down_at - self._started_at, 4),
                "duration": round(max(0.02, up_at - down_at), 4),
            }
        )

    def _finish_touch(self, slot, now):
        if self._started_at is None or slot["down_at"] is None:
            return
        if slot["x"] is None or slot["y"] is None:
            slot["down_at"] = None
            return

        start_x = slot["start_x"] if slot["start_x"] is not None else slot["x"]
        start_y = slot["start_y"] if slot["start_y"] is not None else slot["y"]
        action = {
            "type": "touch",
            "at": round(slot["down_at"] - self._started_at, 4),
            "duration": round(max(0.02, now - slot["down_at"]), 4),
            "x1": int(start_x),
            "y1": int(start_y),
            "x2": int(slot["x"]),
            "y2": int(slot["y"]),
        }
        for label, (x1, y1, x2, y2) in SPECIAL_TOUCH_REGIONS.items():
            if x1 <= action["x1"] <= x2 and y1 <= action["y1"] <= y2:
                action["label"] = label
                break
        self._append_action(action)
        slot["down_at"] = None

    def _append_action(self, action):
        with self._lock:
            self.actions.append(action)
            action_count = len(self.actions)
        if action_count == 1:
            print(f"[OK] Input capture is working ({action.get('type', 'touch')}).")
        if action.get("label") in SPECIAL_TOUCH_REGIONS:
            print(f"[REC] Captured {action['label']} action.")
        if self.autosave_path is not None:
            self._write_profile(self.autosave_path)

    def _filtered_actions(self):
        with self._lock:
            actions = sorted(self.actions, key=lambda action: action["at"])
        touch_times = [action["at"] for action in actions if action.get("type", "touch") == "touch"]
        control_times = [action["at"] for action in actions if action.get("type") == "control"]
        filtered = []
        for action in actions:
            action_type = action.get("type", "touch")
            if action_type == "control" and any(
                abs(action["at"] - touch_time) <= 0.15 for touch_time in touch_times
            ):
                continue
            if action_type == "key" and (
                any(abs(action["at"] - touch_time) <= 0.15 for touch_time in touch_times)
                or any(abs(action["at"] - control_time) <= 0.15 for control_time in control_times)
            ):
                continue
            filtered.append(action)
        return filtered

    def _write_profile(self, path):
        with self._save_lock:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            actions = self._filtered_actions()
            duration_seconds = max(
                (
                    float(action.get("at", 0)) + float(action.get("duration", 0))
                    for action in actions
                ),
                default=0.0,
            )
            data = {
                "version": 4,
                "timeline_origin": "play_tap",
                "name": self.profile_name or path.stem,
                "created_at": self._created_at or time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": round(duration_seconds, 3),
                "coins": 0,
                "exp": 0,
                "resolution": [SCREEN_WIDTH, SCREEN_HEIGHT],
                "input_devices": list(self.input_devices),
                "controls": {"W": "jump", "S": "slide"},
                "actions": actions,
            }
            temporary_path = path.with_suffix(path.suffix + ".tmp")
            temporary_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary_path.replace(path)
            return len(actions)

    def stop_and_save(self, path):
        self.stop()
        return self._write_profile(path)

    def stop(self):
        self._keyboard_stop.set()
        if self.keyboard_thread is not None:
            self.keyboard_thread.join(timeout=2)
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.thread is not None:
            self.thread.join(timeout=2)


def _action_command(target, action):
    if action.get("type") == "control":
        x, y = CONTROL_COORDS[action["control"]]
        duration_ms = max(20, int(float(action.get("duration", 0.05)) * 1000))
        return [
            ADB_EXECUTABLE, "-s", target, "shell", "input", "swipe",
            str(x), str(y), str(x), str(y), str(duration_ms),
        ]

    if action.get("type") == "key":
        key_code = f"KEYCODE_{action['key']}"
        command = [ADB_EXECUTABLE, "-s", target, "shell", "input", "keyevent"]
        if float(action.get("duration", 0.0)) >= 0.35:
            command.append("--longpress")
        command.append(key_code)
        return command

    # Reuse the exact recorded coordinates. Variation should come from selecting
    # different profiles, not from shifting a carefully recorded jump/slide.
    x1 = int(action["x1"])
    y1 = int(action["y1"])
    x2 = int(action.get("x2", x1))
    y2 = int(action.get("y2", y1))
    duration_ms = max(20, int(float(action.get("duration", 0.05)) * 1000))

    x1 = max(0, min(SCREEN_WIDTH - 1, x1))
    y1 = max(0, min(SCREEN_HEIGHT - 1, y1))
    x2 = max(0, min(SCREEN_WIDTH - 1, x2))
    y2 = max(0, min(SCREEN_HEIGHT - 1, y2))

    if duration_ms <= 80 and abs(x2 - x1) < 8 and abs(y2 - y1) < 8:
        return [ADB_EXECUTABLE, "-s", target, "shell", "input", "tap", str(x1), str(y1)]
    return [
        ADB_EXECUTABLE, "-s", target, "shell", "input", "swipe",
        str(x1), str(y1), str(x2), str(y2), str(duration_ms),
    ]


def _play_action(target, action):
    """Compatibility helper for callers that need to execute one action synchronously."""
    return adb_run(
        _action_command(target, action),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _launch_action(target, action):
    """Dispatch an input immediately without adding a scheduler thread per action."""
    return subprocess.Popen(
        _action_command(target, action),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=ADB_SUBPROCESS_FLAGS,
    )


def _wait_until(deadline, stop_event=None):
    """Wait accurately for an absolute monotonic deadline and allow cancellation."""
    while True:
        if stop_event is not None and stop_event.is_set():
            return False
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return True
        if remaining > 0.006:
            sleep_for = remaining - 0.003
            if stop_event is not None:
                if stop_event.wait(sleep_for):
                    return False
            else:
                time.sleep(sleep_for)
        else:
            # Yield without adding the usual Windows multi-millisecond sleep drift.
            time.sleep(0)


def _resolve_replay_start(data, timeline_started_at):
    if timeline_started_at is None:
        return time.monotonic(), False
    if data.get("timeline_origin") == "play_tap":
        return float(timeline_started_at), False
    return float(timeline_started_at) + LEGACY_REPLAY_START_DELAY, True


def replay_profile(ip, port, path, stop_event=None, timeline_started_at=None):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    actions = data.get("actions", [])
    if not actions:
        raise ValueError(f"Recording has no touch actions: {path.name}")

    target = _resolve_device_target(ip, port)
    started_at, legacy_timing = _resolve_replay_start(data, timeline_started_at)
    if legacy_timing:
        print(
            "[REPLAY_TIMING] Legacy profile: using the old 1.1s start offset. "
            "Record this profile again for exact Play-tap timing."
        )
    processes = []
    dispatch_lateness = []
    replayed_count = 0
    timer_resolution_enabled = False
    if os.name == "nt":
        try:
            timer_resolution_enabled = ctypes.windll.winmm.timeBeginPeriod(1) == 0
        except (AttributeError, OSError):
            timer_resolution_enabled = False
    try:
        for action in actions:
            deadline = started_at + max(
                0.0,
                float(action["at"]) - REPLAY_INPUT_LEAD_TIME,
            )
            if not _wait_until(deadline, stop_event):
                break
            dispatched_at = time.monotonic()
            processes.append(_launch_action(target, action))
            dispatch_lateness.append(max(0.0, dispatched_at - deadline))
            replayed_count += 1
        for process in processes:
            process.wait()
    finally:
        if timer_resolution_enabled:
            ctypes.windll.winmm.timeEndPeriod(1)
    if dispatch_lateness:
        average_late_ms = sum(dispatch_lateness) * 1000 / len(dispatch_lateness)
        maximum_late_ms = max(dispatch_lateness) * 1000
        print(
            f"[REPLAY_TIMING] lead={REPLAY_INPUT_LEAD_TIME * 1000:.0f}ms "
            f"dispatch_avg_late={average_late_ms:.1f}ms "
            f"dispatch_max_late={maximum_late_ms:.1f}ms"
        )
    return replayed_count
