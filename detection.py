import os

import cv2
import numpy as np

from config import (
    ANTI_BOT_CARD_HEIGHT,
    ANTI_BOT_CARD_WIDTH,
    ANTI_BOT_CARD_POS_1,
    ANTI_BOT_CARD_POS_2,
    ANTI_BOT_CARD_POS_3,
    ANTI_BOT_CARD_POS_4,
    ANTI_BOT_CARD_POS_5,
    ANTI_BOT_CARD_POS_6,
    BOOST_TEMPLATES,
    GLOBAL_CONFIRM_TEMPLATE,
    MATCH_THRESHOLD,
    STAGE_REGIONS,
    STAGE_TEMPLATES,
    TEMPLATE_DIR,
)


_template_cache: dict = {}
_template_gray_cache: dict = {}


def _get_template(filename):
    """Return cached template image, loading from disk on first access."""
    if filename not in _template_cache:
        path = os.path.join(TEMPLATE_DIR, filename)
        _template_cache[filename] = _normalize(cv2.imread(path, cv2.IMREAD_UNCHANGED))
    return _template_cache[filename]


def _get_template_gray(filename):
    """Return cached grayscale template image, loading from disk on first access."""
    if filename not in _template_gray_cache:
        template = _get_template(filename)
        _template_gray_cache[filename] = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if template is not None else None
    return _template_gray_cache[filename]


def load_templates():
    """Pre-warm the template cache with all stage and boost templates at startup."""
    for template_files in STAGE_TEMPLATES.values():
        for filename in template_files:
            _get_template_gray(filename)
    for template_files in BOOST_TEMPLATES:
        for filename in template_files:
            _get_template_gray(filename)
    for filename in GLOBAL_CONFIRM_TEMPLATE:
        _get_template_gray(filename)
    # NEWS popup templates are only reachable via the detection groups, but
    # they are cheap to pre-warm so the first News screen never delays a tap.
    from config import STAGE_NEWS_CLOSE_TEMPLATE
    for filename in STAGE_NEWS_CLOSE_TEMPLATE:
        _get_template_gray(filename)


def _normalize(img):
    """Ensure image is BGR uint8 (3-channel). Returns None if conversion fails."""
    if img is None:
        return None
    if img.dtype != np.uint8:
        return None
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.ndim == 3 and img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    if img.ndim == 3 and img.shape[2] == 3:
        return img
    return None


def _normalize_gray(img):
    normalized = _normalize(img)
    if normalized is None:
        return None
    return cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)


def _crop_region(img, region):
    if region is None:
        return img
    x1, y1, x2, y2 = region
    return img[y1:y2, x1:x2]


def detect_templates(screen, template_files, region=None):
    screen_gray = _normalize_gray(screen)
    if screen_gray is None:
        return []
    screen_gray = _crop_region(screen_gray, region)
    offset_x, offset_y = (region[0], region[1]) if region is not None else (0, 0)
    matches = []
    for filename in template_files:
        template = _get_template_gray(filename)
        if template is None:
            continue
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= MATCH_THRESHOLD:
            th, tw = template.shape[:2]
            x = max_loc[0] + offset_x
            y = max_loc[1] + offset_y
            matches.append((x, y, tw, th))
    return matches


def detect_all_template_matches(screen, template_files, region=None, threshold=None, max_matches=20):
    """Find every spatially distinct occurrence, suppressing overlapping match peaks."""
    screen_gray = _normalize_gray(screen)
    if screen_gray is None:
        return []
    search_area = _crop_region(screen_gray, region)
    offset_x, offset_y = (region[0], region[1]) if region is not None else (0, 0)
    required_score = MATCH_THRESHOLD if threshold is None else float(threshold)
    matches = []

    for filename in template_files:
        template = _get_template_gray(filename)
        if template is None:
            continue
        template_height, template_width = template.shape[:2]
        if search_area.shape[0] < template_height or search_area.shape[1] < template_width:
            continue
        result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
        while len(matches) < max_matches:
            _, max_value, _, max_location = cv2.minMaxLoc(result)
            if max_value < required_score:
                break
            match_x, match_y = max_location
            matches.append(
                (match_x + offset_x, match_y + offset_y, template_width, template_height)
            )
            left = max(0, match_x - template_width // 2)
            top = max(0, match_y - template_height // 2)
            right = min(result.shape[1], match_x + template_width // 2 + 1)
            bottom = min(result.shape[0], match_y + template_height // 2 + 1)
            result[top:bottom, left:right] = -1.0

    return matches


def detect_stage(screen, stage_names=None):
    screen_bgr = _normalize(screen)
    if screen_bgr is None:
        return None
    screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    if stage_names is None:
        stage_names = STAGE_TEMPLATES.keys()
    for stage_name in stage_names:
        # The game alternates between "jumping card" and "sliding card" text.
        # A full-header template only recognised the older wording, so use the
        # stable six-card layout and cyan header before falling back to it.
        if stage_name == "ANTI_BOT" and _is_anti_bot_screen(screen_bgr):
            return stage_name
        template_files = STAGE_TEMPLATES.get(stage_name)
        if not template_files:
            continue
        search_area = _crop_region(screen_gray, STAGE_REGIONS.get(stage_name))
        for filename in template_files:
            template = _get_template_gray(filename)
            if template is None:
                continue
            if (
                search_area.shape[0] < template.shape[0]
                or search_area.shape[1] < template.shape[1]
            ):
                continue
            result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val >= MATCH_THRESHOLD:
                return stage_name
    return None


def _is_anti_bot_screen(screen):
    """Recognise either Anti-Bot wording from its stable header/card layout."""
    screen_bgr = _normalize(screen)
    if screen_bgr is None or screen_bgr.shape[0] < 700 or screen_bgr.shape[1] < 1172:
        return False

    # Several normal reward/event dialogs use the same cyan header and pale
    # geometry as the Anti-Bot screen. Prefer their specific templates over
    # the broad Anti-Bot layout heuristic so News/announcement panes cannot be
    # mistaken for six captcha cards and clicked until the safety stop fires.
    for normal_stage in (
        "DAILY_CHECKIN",
        "DAILY_CHECKIN_BOOST_SET",
        "DAILY_TREASURE",
        "ANNOUNCEMENT",
        "NEWS",
        "PARTY_RUN",
    ):
        if detect_templates(
            screen_bgr,
            STAGE_TEMPLATES.get(normal_stage, ()),
            STAGE_REGIONS.get(normal_stage),
        ):
            return False

    hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
    header = hsv[10:112, 108:1172]
    cyan = cv2.inRange(header, (80, 80, 80), (105, 255, 255))
    cyan_ratio = cv2.countNonZero(cyan) / cyan.size
    if cyan_ratio < 0.50:
        return False

    card_coords = (
        ANTI_BOT_CARD_POS_1,
        ANTI_BOT_CARD_POS_2,
        ANTI_BOT_CARD_POS_3,
        ANTI_BOT_CARD_POS_4,
        ANTI_BOT_CARD_POS_5,
        ANTI_BOT_CARD_POS_6,
    )
    beige_cards = 0
    for cx, cy in card_coords:
        card = hsv[
            cy + 10:cy + ANTI_BOT_CARD_HEIGHT - 10,
            cx + 10:cx + ANTI_BOT_CARD_WIDTH - 10,
        ]
        if card.size == 0:
            continue
        beige = cv2.inRange(card, (0, 0, 150), (179, 90, 255))
        if cv2.countNonZero(beige) / beige.size >= 0.70:
            beige_cards += 1
    return beige_cards >= 5


def _anti_bot_jumping_word_score(screen):
    """Return correlation for the word ``jumping`` in the Anti-Bot header.

    The full jumping/sliding headers share almost all pixels, so matching the
    entire banner can confuse the two instructions. We first align the known
    jumping banner, then compare only the word that differs.
    """
    screen_gray = _normalize_gray(screen)
    if screen_gray is None:
        return 0.0
    region = STAGE_REGIONS.get("ANTI_BOT")
    template_files = STAGE_TEMPLATES.get("ANTI_BOT", ())
    if region is None or not template_files:
        return 0.0
    header_template = _get_template_gray(template_files[0])
    if header_template is None:
        return 0.0
    search_area = _crop_region(screen_gray, region)
    if (
        search_area.shape[0] < header_template.shape[0]
        or search_area.shape[1] < header_template.shape[1]
    ):
        return 0.0

    alignment = cv2.matchTemplate(search_area, header_template, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(alignment)
    offset_x, offset_y = max_loc

    # Tight crop around the word "jumping" in ANTI_BOT_1.png. Keeping only
    # the differing word prevents common text such as "Surprise! Find the"
    # and "card!" from dominating the score.
    word_x1, word_y1, word_x2, word_y2 = (410, 15, 545, 75)
    word_template = header_template[word_y1:word_y2, word_x1:word_x2]
    word_screen = search_area[
        offset_y + word_y1:offset_y + word_y2,
        offset_x + word_x1:offset_x + word_x2,
    ]
    if word_screen.shape != word_template.shape or word_template.size == 0:
        return 0.0
    score = cv2.matchTemplate(word_screen, word_template, cv2.TM_CCOEFF_NORMED)
    return float(score[0, 0])


def detect_anti_bot_instruction(screen):
    """Return the requested Anti-Bot pose: ``jumping`` or ``sliding``."""
    screen_bgr = _normalize(screen)
    if screen_bgr is None:
        return None
    if not _is_anti_bot_screen(screen_bgr):
        return None

    jumping_score = _anti_bot_jumping_word_score(screen_bgr)
    print(f"  Anti-Bot jumping-word score: {jumping_score:.3f}")
    # Self-match is ~1.0. A deliberately changed instruction word drops well
    # below this threshold while small antialiasing/compression differences do
    # not, so the fallback can safely represent the alternate sliding wording.
    return "jumping" if jumping_score >= 0.72 else "sliding"


def _anti_bot_pose_scores(screen):
    """Return one sliding-likelihood score for each Anti-Bot card."""
    card_coords = [
        ANTI_BOT_CARD_POS_1,
        ANTI_BOT_CARD_POS_2,
        ANTI_BOT_CARD_POS_3,
        ANTI_BOT_CARD_POS_4,
        ANTI_BOT_CARD_POS_5,
        ANTI_BOT_CARD_POS_6,
    ]
    screen_bgr = _normalize(screen)
    if screen_bgr is None:
        return []

    scores = []
    for cx, cy in card_coords:
        inner = screen_bgr[
            cy + 20:cy + ANTI_BOT_CARD_HEIGHT - 20,
            cx + 20:cx + ANTI_BOT_CARD_WIDTH - 20,
        ]
        if inner.size == 0:
            scores.append(float("-inf"))
            continue
        hsv = cv2.cvtColor(inner, cv2.COLOR_BGR2HSV)
        foreground = cv2.inRange(hsv, (0, 80, 30), (179, 255, 255))
        ys, xs = np.where(foreground > 0)
        if len(xs) < 50:
            scores.append(float("-inf"))
            continue
        width = float(xs.max() - xs.min() + 1)
        height = float(ys.max() - ys.min() + 1)
        aspect = width / max(1.0, height)
        centroid_y = float(ys.mean()) / inner.shape[0]
        lower_ratio = float((ys > inner.shape[0] * 0.5).mean())
        scores.append((aspect * 2.0) + centroid_y + lower_ratio)
    return scores


def detect_anti_bot_card_candidates(screen, target="sliding"):
    """Rank all six cards for the requested pose, best candidate first."""
    if target not in ("jumping", "sliding"):
        return []
    scores = _anti_bot_pose_scores(screen)
    if not scores:
        return []

    # High score = wide/low (sliding). Low score = narrow/upright or little
    # lower-half foreground (jumping). ``-inf`` therefore belongs first for a
    # jumping challenge instead of being silently discarded.
    reverse = target == "sliding"
    ranked = sorted(range(len(scores)), key=lambda index: scores[index], reverse=reverse)
    print(f"?? Analyzing Anti-Bot card poses for: {target}...")
    for idx, score in enumerate(scores):
        print(f"  Card {idx + 1}: slide score {score:.2f}")
    print("  Candidate order: " + ", ".join(str(index + 1) for index in ranked))
    return [int(index) for index in ranked]


def detect_anti_bot_odd_cards(screen):
    """Backward-compatible helper returning the two most sliding-like cards."""
    return detect_anti_bot_card_candidates(screen, "sliding")[:2]
