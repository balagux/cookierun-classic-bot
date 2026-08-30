import random
import shutil
import subprocess
import threading
import time
from pathlib import Path

import cv2
import numpy as np

from runtime_paths import APP_DIR


ADB_SUBPROCESS_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_DEVICE_TARGET_CACHE = {}
_DEVICE_TARGET_CACHE_LOCK = threading.Lock()
_DEVICE_TARGET_CACHE_TTL = 5.0


def adb_run(command, **kwargs):
    """Run ADB without opening a console window on Windows."""
    kwargs.setdefault("creationflags", ADB_SUBPROCESS_FLAGS)
    return subprocess.run(command, **kwargs)


def _find_adb_executable():
    candidates = (
        APP_DIR / "platform-tools" / "adb.exe",
        Path(r"D:\platform-tools-latest-windows\platform-tools\adb.exe"),
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("adb") or "adb"


ADB_EXECUTABLE = _find_adb_executable()


def _resolve_device_target(ip: str, port: int):
    if port is None:
        return str(ip)

    cache_key = (str(ip), int(port))
    now = time.monotonic()
    with _DEVICE_TARGET_CACHE_LOCK:
        cached = _DEVICE_TARGET_CACHE.get(cache_key)
        if cached is not None and now - cached[0] < _DEVICE_TARGET_CACHE_TTL:
            return cached[1]

    devices_result = adb_run(
        [ADB_EXECUTABLE, "devices"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if devices_result.returncode == 0:
        for line in devices_result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() == "device":
                serial = parts[0]
                if serial.startswith("emulator-") and serial.endswith(str(port)):
                    with _DEVICE_TARGET_CACHE_LOCK:
                        _DEVICE_TARGET_CACHE[cache_key] = (time.monotonic(), serial)
                    return serial

    target = f"{ip}:{port}"
    with _DEVICE_TARGET_CACHE_LOCK:
        _DEVICE_TARGET_CACHE[cache_key] = (time.monotonic(), target)
    return target


def device_connect(ip: str, port: int):
    target = _resolve_device_target(ip, port)
    if target.startswith("emulator-"):
        result = adb_run(
            [ADB_EXECUTABLE, "-s", target, "get-state"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output = result.stdout.strip().lower()
        print(f"🔌 {output.capitalize()}")
        if "device" not in output:
            raise Exception(f"❌ Failed to connect to {target}\n{result.stderr.strip()}")
        return

    result = adb_run(
        [ADB_EXECUTABLE, "connect", target],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"🔌 {result.stdout.strip().capitalize()}")
    if "connected" not in result.stdout and "already connected" not in result.stdout:
        raise Exception(f"❌ Failed to connect to {ip}:{port}\n{result.stderr.strip()}")


def device_capture_screen(ip: str, port: int):
    target = _resolve_device_target(ip, port)
    result = adb_run(
        [ADB_EXECUTABLE, "-s", target, "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        check=True,
    )
    img = np.frombuffer(result.stdout, dtype=np.uint8)
    return cv2.imdecode(img, cv2.IMREAD_COLOR)


def device_tap(ip: str, port: int, x: int, y: int):
    target = _resolve_device_target(ip, port)
    adb_run(
        [ADB_EXECUTABLE, "-s", target, "shell", "input", "tap", str(x), str(y)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def safe_device_tap(ip: str, port: int, x: int, y: int):
    target = _resolve_device_target(ip, port)
    jitter_x = x + random.randint(-15, 15)
    jitter_y = y + random.randint(-15, 15)
    adb_run(
        [ADB_EXECUTABLE, "-s", target, "shell", "input", "tap", str(jitter_x), str(jitter_y)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def device_back(ip: str, port: int):
    """Press the Android BACK key to close overlays/dialogs and return home."""
    target = _resolve_device_target(ip, port)
    adb_run(
        [ADB_EXECUTABLE, "-s", target, "shell", "input", "keyevent", "4"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def device_scroll(ip: str, port: int, x: int, y: int, direction: str = "up", distance: int = 500, duration: int = 300):
    """Perform a deterministic swipe centered on ``(x, y)``.

    This is intended for UI lists where a small random coordinate change can
    land on another control or make the scroll look erratic.  Callers that
    deliberately want human-like jitter can continue using
    :func:`safe_device_scroll`.
    """
    target = _resolve_device_target(ip, port)
    direction_map = {
        "up":    (x, y + distance, x, y - distance),
        "down":  (x, y - distance, x, y + distance),
        "left":  (x + distance, y, x - distance, y),
        "right": (x - distance, y, x + distance, y),
    }
    if direction not in direction_map:
        raise ValueError(f"Invalid direction '{direction}'. Use: up, down, left, right.")
    x1, y1, x2, y2 = direction_map[direction]
    result = adb_run(
        [ADB_EXECUTABLE, "-s", target, "shell", "input", "swipe",
         str(x1), str(y1), str(x2), str(y2), str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        error = (result.stderr or result.stdout or "unknown ADB error").strip()
        raise RuntimeError(f"ADB swipe failed: {error}")


def safe_device_scroll(ip: str, port: int, x: int, y: int, direction: str = "up", distance: int = 500, duration: int = 300):
    jx = x + random.randint(-15, 15)
    jy = y + random.randint(-15, 15)
    device_scroll(
        ip,
        port,
        jx,
        jy,
        direction=direction,
        distance=distance,
        duration=duration,
    )


def device_is_app_running(ip: str, port: int, package: str) -> bool:
    target = _resolve_device_target(ip, port)
    result = adb_run(
        [ADB_EXECUTABLE, "-s", target, "shell", "pidof", package],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return bool(result.stdout.strip())


class DeviceAppStartError(RuntimeError):
    """Raised only when a caller explicitly requests a fatal app-start failure."""


def _result_message(result):
    """Return a compact ADB diagnostic without assuming a CompletedProcess object."""
    for name in ("stderr", "stdout"):
        value = getattr(result, name, "")
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return ""


def _find_launcher_activity(target: str, package: str):
    """Resolve the package launcher component for an explicit `am start` fallback."""
    result = adb_run(
        [
            ADB_EXECUTABLE,
            "-s",
            target,
            "shell",
            "cmd",
            "package",
            "resolve-activity",
            "--brief",
            "-a",
            "android.intent.action.MAIN",
            "-c",
            "android.intent.category.LAUNCHER",
            "-p",
            package,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    output = getattr(result, "stdout", "")
    if not isinstance(output, str):
        return None
    for line in reversed(output.splitlines()):
        component = line.strip()
        if "/" in component and " " not in component:
            return component
    return None


def _launch_app(target: str, package: str):
    """Ask Android's Monkey launcher to start the package."""
    monkey_result = adb_run(
        [
            ADB_EXECUTABLE,
            "-s",
            target,
            "shell",
            "monkey",
            "-p",
            package,
            "-c",
            "android.intent.category.LAUNCHER",
            "1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    message = _result_message(monkey_result)
    combined_output = " ".join(
        value
        for value in (
            getattr(monkey_result, "stdout", ""),
            getattr(monkey_result, "stderr", ""),
        )
        if isinstance(value, str)
    ).lower()
    failed = (
        getattr(monkey_result, "returncode", 0) != 0
        or "monkey aborted" in combined_output
        or "no activities found" in combined_output
    )
    return not failed, message if failed else ""


def _launch_app_via_activity(target: str, package: str):
    """Try an explicit launcher activity after Monkey did not produce a process."""
    launcher_activity = _find_launcher_activity(target, package)
    if not launcher_activity:
        return False, "launcher activity could not be resolved"
    activity_result = adb_run(
        [
            ADB_EXECUTABLE,
            "-s",
            target,
            "shell",
            "am",
            "start",
            "-n",
            launcher_activity,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if getattr(activity_result, "returncode", 0) != 0:
        return False, _result_message(activity_result)
    return True, ""


def _wait_for_app_process(
    ip: str,
    port: int,
    package: str,
    timeout: float,
    poll_interval: float,
    stability_wait: float,
):
    deadline = time.monotonic() + max(0.0, float(timeout))
    while True:
        if device_is_app_running(ip, port, package):
            print(f"[APP_START_CHECK] {package} is running; checking stability...")
            if stability_wait > 0:
                time.sleep(stability_wait)
            return device_is_app_running(ip, port, package)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(max(0.05, float(poll_interval)), remaining))


def device_reset_app(
    ip: str,
    port: int,
    package: str = "com.devsisters.crg",
    max_retries: int = 3,
    *,
    launch_timeout: float = 6.0,
    poll_interval: float = 0.5,
    stability_wait: float = 1.0,
    retry_delay: float = 1.0,
    raise_on_failure: bool = False,
) -> bool:
    """Restart an Android app and report failure without crashing the GUI by default.

    A failed launch used to raise unconditionally after five long attempts. In a
    packaged GUI that exception escaped the worker and produced an "Unhandled
    exception in script" dialog. Returning ``False`` lets the bot remain open
    and report the failure in its activity log. CLI callers that require the
    former fatal behavior can opt in with ``raise_on_failure=True``.
    """
    target = _resolve_device_target(ip, port)
    attempts = max(1, int(max_retries))
    print(f"[APP_RESET] Stopping {package} on {target}...")
    last_error = ""
    try:
        stop_result = adb_run(
            [ADB_EXECUTABLE, "-s", target, "shell", "am", "force-stop", package],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if getattr(stop_result, "returncode", 0) != 0:
            last_error = _result_message(stop_result)
    except Exception as exc:
        # A transient offline device should not take the desktop GUI down.
        last_error = str(exc)
    time.sleep(1.0)

    for attempt in range(1, attempts + 1):
        print(f"[APP_START] Starting {package} (attempt {attempt}/{attempts})...")
        try:
            total_timeout = max(0.0, float(launch_timeout))
            monkey_timeout = total_timeout * 0.6
            fallback_timeout = total_timeout - monkey_timeout
            monkey_started, launch_error = _launch_app(target, package)
            if launch_error:
                last_error = launch_error
            if monkey_started and _wait_for_app_process(
                ip,
                port,
                package,
                monkey_timeout,
                poll_interval,
                stability_wait,
            ):
                print(f"[APP_START_OK] {package} is running and stable.")
                return True

            print(f"[APP_START_FALLBACK] Trying the explicit launcher for {package}...")
            fallback_started, fallback_error = _launch_app_via_activity(target, package)
            if fallback_error:
                last_error = fallback_error
            if (fallback_started or monkey_started) and _wait_for_app_process(
                ip,
                port,
                package,
                fallback_timeout,
                poll_interval,
                stability_wait,
            ):
                print(f"[APP_START_OK] {package} is running and stable.")
                return True
            last_error = last_error or "process did not remain running"
        except Exception as exc:
            last_error = str(exc)

        if attempt < attempts:
            print(
                f"[APP_START_RETRY] {package} is not ready; "
                f"retrying in {retry_delay:.1f}s..."
            )
            if retry_delay > 0:
                time.sleep(retry_delay)

    message = (
        f"[APP_START_FAILED] Could not start {package} after {attempts} attempts. "
        "The bot window will remain open so you can start the game in LDPlayer "
        "and press Start again."
    )
    if last_error:
        message = f"{message} ADB: {last_error}"
    print(message)
    if raise_on_failure:
        raise DeviceAppStartError(message)
    return False
