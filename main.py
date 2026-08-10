import argparse
import builtins
import os
import sys
from datetime import datetime


_worker_log_stream = None
_worker_log_path = os.environ.get("COOKIEBOT_LOG_FILE")
if _worker_log_path:
    try:
        _worker_log_stream = open(
            _worker_log_path,
            "w",
            encoding="utf-8",
            errors="replace",
            buffering=1,
        )
        sys.stdout = _worker_log_stream
        sys.stderr = _worker_log_stream
    except OSError:
        _worker_log_stream = None

from bot import BOOST_CHOICES, main as run_bot
from config import DEVICE_IP, DEVICE_PORT


for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


_original_print = builtins.print


def _print_with_datetime(*args, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _original_print(f"[{timestamp}]", *args, **kwargs)


builtins.print = _print_with_datetime


def build_parser():
    parser = argparse.ArgumentParser(description="CookieRun Classic Bot")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--console", action="store_true", help="run with the original terminal prompts")
    mode.add_argument("--run-bot", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument("--check-connection", action="store_true", help=argparse.SUPPRESS)
    mode.add_argument("--check-ocr-runtime", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--device-ip", default=DEVICE_IP)
    parser.add_argument("--device-port", type=int, default=DEVICE_PORT)
    parser.add_argument("--fast-start", action="store_true")
    parser.add_argument("--cookie-relay", action="store_true")
    parser.add_argument("--boost-index", type=int, choices=range(0, len(BOOST_CHOICES) + 1), default=0)
    parser.add_argument("--keep-relic-parts", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--max-runs", type=int, default=0, help=argparse.SUPPRESS)
    return parser


def _options_from_args(args):
    boost = BOOST_CHOICES[args.boost_index - 1] if args.boost_index else None
    return {
        "use_fast_start": args.fast_start,
        "use_cookie_relay": args.cookie_relay,
        "use_desired_random_boost": boost is not None,
        "desired_boost_template": boost[1] if boost else None,
        "desired_boost_name": boost[0] if boost else None,
        "claim_relic_rewards": not args.keep_relic_parts,
        "max_runs": max(0, args.max_runs),
    }


def _check_connection(ip, port):
    from adb import device_capture_screen, device_connect

    device_connect(ip, port)
    screen = device_capture_screen(ip, port)
    if screen is None:
        raise RuntimeError("Connected, but could not decode the device screenshot.")
    height, width = screen.shape[:2]
    print(f"✅ Connected successfully — screen resolution {width}x{height}")
    if (width, height) != (1280, 720):
        raise RuntimeError(
            f"Unsupported screen resolution {width}x{height}. "
            "Please change LDPlayer to 1280x720 before starting the bot."
        )


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.check_connection:
        try:
            _check_connection(args.device_ip, args.device_port)
            return 0
        except Exception as exc:
            print(f"❌ Connection test failed: {exc}")
            return 1

    if args.check_ocr_runtime:
        try:
            from result_ocr import runtime_self_test

            result = runtime_self_test()
            print(f"✅ OCR runtime self-test passed: {result}")
            return 0
        except Exception as exc:
            print(f"❌ OCR runtime self-test failed: {exc}")
            return 1

    if args.console:
        try:
            run_bot(device_ip=args.device_ip, device_port=args.device_port)
            return 0
        except Exception as exc:
            print(f"❌ Bot stopped safely: {exc}")
            return 1

    if args.run_bot:
        try:
            run_bot(
                options=_options_from_args(args),
                device_ip=args.device_ip,
                device_port=args.device_port,
            )
            return 0
        except Exception as exc:
            # A frozen/windowed worker must never leak an unhandled exception;
            # PyInstaller would otherwise show a disruptive crash dialog over
            # the emulator.  The GUI receives this line and the non-zero exit.
            print(f"❌ Bot stopped safely: {exc}")
            return 1

    from modern_gui import launch_gui

    launch_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
