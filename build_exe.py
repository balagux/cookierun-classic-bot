"""Build the Windows GUI executable with PyInstaller."""

import os
from pathlib import Path

import PyInstaller.__main__
from PIL import Image, ImageDraw


BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "build_assets"
ICON_FILE = ASSET_DIR / "cookiebot.ico"


def create_icon():
    ASSET_DIR.mkdir(exist_ok=True)
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 248, 248), radius=58, fill="#6C5CE7")
    draw.ellipse((52, 52, 204, 204), fill="#F7B94C", outline="#E49331", width=12)
    for x, y, radius in ((96, 92, 15), (155, 82, 12), (135, 145, 16), (84, 161, 12), (174, 137, 11)):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#754334")
    image.save(
        ICON_FILE,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def main():
    create_icon()
    PyInstaller.__main__.run(
        [
            str(BASE_DIR / "main.py"),
            "--name=CookieRunClassicBot",
            "--onefile",
            "--windowed",
            "--noconfirm",
            "--clean",
            "--noupx",
            "--log-level=WARN",
            f"--icon={ICON_FILE}",
            f"--add-data={BASE_DIR / 'templates'}{os.pathsep}templates",
            "--collect-all=customtkinter",
            "--collect-all=rapidocr",
            "--collect-all=onnxruntime",
            "--hidden-import=PIL._tkinter_finder",
            f"--distpath={BASE_DIR / 'dist'}",
            f"--workpath={BASE_DIR / 'build'}",
            f"--specpath={BASE_DIR}",
        ]
    )


if __name__ == "__main__":
    main()
