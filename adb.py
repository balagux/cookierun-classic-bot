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


def safe_device_scroll(ip: str, port: int, x: int, y: int, direction: str = "up", distance: int = 500, duration: int = 300):
    target = _resolve_device_target(ip, port)
    jx = x + random.randint(-15, 15)
    jy = y + random.randint(-15, 15)
    direction_map = {
        "up":    (jx, jy + distance, jx, jy - distance),
        "down":  (jx, jy - distance, jx, jy + distance),
        "left":  (jx + distance, jy, jx - distance, jy),
        "right": (jx - distance, jy, jx + distance, jy),
    }
    if direction not in direction_map:
        raise ValueError(f"Invalid direction '{direction}'. Use: up, down, left, right.")
    x1, y1, x2, y2 = direction_map[direction]
    adb_run(
        [ADB_EXECUTABLE, "-s", target, "shell", "input", "swipe",
         str(x1), str(y1), str(x2), str(y2), str(duration)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
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


def device_reset_app(ip: str, port: int, package: str = "com.devsisters.crg", max_retries: int = 5):
    target = _resolve_device_target(ip, port)
    print(f"🔄 Resetting app {package} on device at {ip}:{port}...")
    adb_run(
        [ADB_EXECUTABLE, "-s", target, "shell", "cmd", "activity", "force-stop", package],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"⏳ Waiting 15 seconds for app {package} to stop...")
    time.sleep(15)

    for attempt in range(1, max_retries + 1):
        print(f"📱 Restarting app {package} on device at {ip}:{port} (attempt {attempt}/{max_retries})...")
        adb_run(
            [ADB_EXECUTABLE, "-s", target, "shell", "monkey", "-p", package, "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"⏳ Waiting 15 seconds to check if app started...")
        time.sleep(15)

        if device_is_app_running(ip, port, package):
            print(f"📊 App {package} is running, verifying stability...")
            stable = True
            for check in range(1, 4):
                time.sleep(20)
                if not device_is_app_running(ip, port, package):
                    print(f"💥 App {package} crashed during stability check ({check}/3).")
                    stable = False
                    break
                print(f"✅ Stability check {check}/3 passed.")
            if stable:
                print(f"✅ App {package} is stable.")
                return

        print(f"💥 App {package} appears to have crashed after launch.")
        if attempt < max_retries:
            print(f"🔁 Retrying in 5 seconds...")
            time.sleep(5)

    raise Exception(f"❌ Failed to start {package} after {max_retries} attempts.")
