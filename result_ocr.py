"""Read Coins and XP from CookieRun's Result screen."""

import logging
import re

import cv2
import numpy as np

from config import RESULT_COINS_REGIONS, RESULT_EXP_REGIONS


_OCR_ENGINE = None
_MIN_CONFIDENCE = 0.65


def _get_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        logging.getLogger("RapidOCR").setLevel(logging.ERROR)
        from rapidocr import RapidOCR

        _OCR_ENGINE = RapidOCR(params={"Global.log_level": "error"})
    return _OCR_ENGINE


def _normalise_number(text):
    replacements = str.maketrans(
        {"O": "0", "o": "0", "I": "1", "l": "1", "|": "1", "S": "5"}
    )
    digits = re.sub(r"\D", "", str(text).translate(replacements))
    return int(digits) if digits else None


def _recognise_crop(crop):
    if crop is None or crop.size == 0:
        return None

    enlarged = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    best = None
    for candidate in (enlarged, thresholded):
        output = _get_engine()(
            candidate,
            use_det=False,
            use_cls=False,
            use_rec=True,
        )
        texts = tuple(getattr(output, "txts", ()) or ())
        scores = tuple(getattr(output, "scores", ()) or ())
        for text, score in zip(texts, scores):
            value = _normalise_number(text)
            confidence = float(score)
            if value is None:
                continue
            result = {"value": value, "text": str(text), "confidence": confidence}
            if best is None or confidence > best["confidence"]:
                best = result
        if best is not None and best["confidence"] >= 0.85:
            break
    return best


def read_number_region(screen, regions):
    """Return the best numeric OCR result from one or more screen regions."""
    if screen is None or not hasattr(screen, "shape") or len(screen.shape) < 2:
        return None

    height, width = screen.shape[:2]
    best = None
    for x1, y1, x2, y2 in regions:
        left = max(0, min(width, int(x1)))
        top = max(0, min(height, int(y1)))
        right = max(left, min(width, int(x2)))
        bottom = max(top, min(height, int(y2)))
        result = _recognise_crop(screen[top:bottom, left:right])
        if result is not None and (best is None or result["confidence"] > best["confidence"]):
            best = result
        if best is not None and best["confidence"] >= 0.85:
            break

    if best is None or best["confidence"] < _MIN_CONFIDENCE:
        return None
    return best


def read_result_rewards(screen):
    """Return (coins, exp, details) read from a 1280x720 Result screen."""
    coin_result = read_number_region(screen, RESULT_COINS_REGIONS)
    exp_result = read_number_region(screen, RESULT_EXP_REGIONS)
    return (
        coin_result["value"] if coin_result else None,
        exp_result["value"] if exp_result else None,
        {"coins": coin_result, "exp": exp_result},
    )


def runtime_self_test():
    """Load the bundled OCR runtime and recognise a deterministic test number."""
    canvas = np.full((100, 300, 3), 255, dtype=np.uint8)
    cv2.putText(
        canvas,
        "1,198",
        (15, 70),
        cv2.FONT_HERSHEY_DUPLEX,
        2,
        (40, 20, 20),
        4,
        cv2.LINE_AA,
    )
    result = read_number_region(canvas, ((0, 0, 300, 100),))
    if result is None or result["value"] != 1198:
        raise RuntimeError(f"OCR self-test returned {result!r}")
    return result
