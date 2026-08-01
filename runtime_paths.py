"""Paths that work both from source and from a PyInstaller executable."""

import sys
from pathlib import Path


FROZEN = bool(getattr(sys, "frozen", False))
RESOURCE_DIR = Path(__file__).resolve().parent
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else RESOURCE_DIR


def app_path(*parts):
    return APP_DIR.joinpath(*parts)


def resource_path(*parts):
    return RESOURCE_DIR.joinpath(*parts)
