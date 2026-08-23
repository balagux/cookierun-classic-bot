"""Colour-aware Mystery Box detection for the post-run opening screen.

The existing stage detector intentionally works in grayscale, which is useful
for finding the shared ``Mystery Box`` heading but cannot tell the four box
tiers apart.  This module keeps the tier artwork in colour and performs two
separate steps:

1. find square box candidates with fast, colour-preserving template matches;
2. classify each candidate with alpha-masked colour correlation.

Keeping candidate discovery separate from classification lets an ambiguous
box fail closed as ``unknown`` instead of silently being credited to the wrong
tier.  Coordinates are normalised to the game's 1280x720 design resolution,
then mapped back to the supplied screenshot for debug output.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

import cv2
import numpy as np

from runtime_paths import resource_path


BOX_TYPES = ("wood", "silver", "gold", "rainbow")
UNKNOWN_BOX_TYPE = "unknown"

REFERENCE_FILES = {
    "wood": "MYSTERY_BOX_WOOD.png",
    "silver": "MYSTERY_BOX_SILVER.png",
    "gold": "MYSTERY_BOX_GOLD.png",
    "rainbow": "MYSTERY_BOX_RAINBOW.png",
}

CANONICAL_WIDTH = 1280
CANONICAL_HEIGHT = 720

# Unopened boxes only occupy the middle panel.  Excluding the banner and the
# Open All button avoids turning bright text/buttons into weak candidates.
BOX_SEARCH_REGION = (70, 110, 1210, 570)

# The supplied artwork is about 170x152 px.  Old and current 1280x720 clients
# render it between roughly 0.85x and 1.25x, depending on row/layout.
PROPOSAL_SCALES = (0.85, 0.95, 1.05, 1.15, 1.25)
PROPOSAL_MIN_SCORE = 0.78

# Classification uses the transparent sprite mask, and is deliberately
# stricter than proposal discovery.  The runner-up margin is important for
# wood/gold and silver/rainbow, whose outlines are intentionally similar.
CLASSIFICATION_MIN_SCORE = 0.76
CLASSIFICATION_MIN_MARGIN = 0.10
CLASSIFICATION_SCALE_OFFSETS = (-0.05, 0.0, 0.05)

MIN_MASKED_CANDIDATE_SCORE = 0.58
NMS_IOU_THRESHOLD = 0.30
MAX_BOXES_PER_SCREEN = 5
LOCAL_MAX_KERNEL_SIZE = 25


@dataclass(frozen=True)
class MysteryBoxDetection:
    """One unopened Mystery Box, including diagnostics for uncertain cases."""

    box_type: str
    confidence: float
    score_margin: float
    bbox: tuple[int, int, int, int]
    best_guess: str


@dataclass(frozen=True)
class _Candidate:
    score: float
    proposed_type: str
    bbox: tuple[int, int, int, int]
    scale: float


def _normalise_bgr(image):
    if image is None or not isinstance(image, np.ndarray) or image.dtype != np.uint8:
        return None
    if image.ndim == 2:
        # Tier classification depends on colour.  Replicating a grayscale
        # frame into three channels can make silver/wood look deceptively
        # confident, so reject it instead of inventing a tier.
        return None
    if image.ndim != 3:
        return None
    if image.shape[2] == 3:
        return np.ascontiguousarray(image)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return None


@lru_cache(maxsize=1)
def _load_references():
    references = {}
    for box_type, filename in REFERENCE_FILES.items():
        image = cv2.imread(
            str(resource_path("templates", filename)),
            cv2.IMREAD_UNCHANGED,
        )
        if (
            image is None
            or image.dtype != np.uint8
            or image.ndim != 3
            or image.shape[2] != 4
        ):
            continue
        references[box_type] = image
    return references


@lru_cache(maxsize=None)
def _scaled_reference(box_type: str, scale: float):
    source = _load_references().get(box_type)
    if source is None:
        return None
    width = max(1, round(source.shape[1] * scale))
    height = max(1, round(source.shape[0] * scale))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    resized = cv2.resize(source, (width, height), interpolation=interpolation)
    return resized[:, :, :3], resized[:, :, 3]


def _canonical_screen(screen):
    screen_bgr = _normalise_bgr(screen)
    if screen_bgr is None or screen_bgr.shape[0] < 100 or screen_bgr.shape[1] < 100:
        return None, 1.0, 1.0

    height, width = screen_bgr.shape[:2]
    scale_x = width / CANONICAL_WIDTH
    scale_y = height / CANONICAL_HEIGHT
    if width == CANONICAL_WIDTH and height == CANONICAL_HEIGHT:
        return screen_bgr, scale_x, scale_y

    interpolation = (
        cv2.INTER_AREA
        if width > CANONICAL_WIDTH or height > CANONICAL_HEIGHT
        else cv2.INTER_CUBIC
    )
    canonical = cv2.resize(
        screen_bgr,
        (CANONICAL_WIDTH, CANONICAL_HEIGHT),
        interpolation=interpolation,
    )
    return canonical, scale_x, scale_y


def _proposal_template(box_type: str, scale: float):
    scaled = _scaled_reference(box_type, scale)
    if scaled is None:
        return None, 0, 0, 0, 0
    image, _alpha = scaled
    height, width = image.shape[:2]

    # This centre is fully opaque for every tier.  Cropping away transparent
    # corners makes the first pass fast without sacrificing its colour signal.
    margin_x = round(width * 0.265)
    margin_y = round(height * 0.165)
    inner = image[margin_y:height - margin_y, margin_x:width - margin_x]
    return inner, margin_x, margin_y, width, height


def _find_candidates(canonical_screen) -> list[_Candidate]:
    x1, y1, x2, y2 = BOX_SEARCH_REGION
    search = canonical_screen[y1:y2, x1:x2]
    candidates = []
    local_max_kernel = np.ones(
        (LOCAL_MAX_KERNEL_SIZE, LOCAL_MAX_KERNEL_SIZE),
        dtype=np.uint8,
    )

    for box_type in BOX_TYPES:
        for scale in PROPOSAL_SCALES:
            template, margin_x, margin_y, full_width, full_height = _proposal_template(
                box_type,
                scale,
            )
            if template is None:
                continue
            if search.shape[0] < template.shape[0] or search.shape[1] < template.shape[1]:
                continue

            response = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
            response = np.nan_to_num(
                response,
                copy=False,
                nan=-1.0,
                posinf=-1.0,
                neginf=-1.0,
            )
            local_max = cv2.dilate(response, local_max_kernel)
            match_y, match_x = np.where(
                (response >= PROPOSAL_MIN_SCORE)
                & (response >= local_max - 1e-7)
            )

            # A valid popup has at most five boxes.  Bounding the peaks per
            # response also keeps deliberately noisy input cheap and safe.
            if len(match_x) > 12:
                peak_scores = response[match_y, match_x]
                best_indices = np.argsort(peak_scores)[-12:]
                match_x = match_x[best_indices]
                match_y = match_y[best_indices]

            for response_y, response_x in zip(match_y, match_x):
                candidates.append(
                    _Candidate(
                        score=float(response[response_y, response_x]),
                        proposed_type=box_type,
                        bbox=(
                            int(response_x + x1 - margin_x),
                            int(response_y + y1 - margin_y),
                            full_width,
                            full_height,
                        ),
                        scale=scale,
                    )
                )
    return candidates


def _intersection_over_union(first, second):
    first_x, first_y, first_w, first_h = first
    second_x, second_y, second_w, second_h = second
    overlap_left = max(first_x, second_x)
    overlap_top = max(first_y, second_y)
    overlap_right = min(first_x + first_w, second_x + second_w)
    overlap_bottom = min(first_y + first_h, second_y + second_h)
    overlap = max(0, overlap_right - overlap_left) * max(
        0,
        overlap_bottom - overlap_top,
    )
    union = (first_w * first_h) + (second_w * second_h) - overlap
    return overlap / union if union > 0 else 0.0


def _cross_tier_nms(candidates: Iterable[_Candidate]):
    """Collapse scale and tier proposals before enforcing the five-box cap."""

    remaining = sorted(candidates, key=lambda candidate: candidate.score, reverse=True)
    selected = []
    while remaining:
        best = remaining.pop(0)
        selected.append(best)
        remaining = [
            candidate
            for candidate in remaining
            if _intersection_over_union(best.bbox, candidate.bbox) < NMS_IOU_THRESHOLD
        ]
    return selected


def _masked_class_scores(canonical_screen, candidate: _Candidate):
    references = _load_references()
    if not references:
        return {}

    x, y, width, height = candidate.bbox
    centre_x = x + (width / 2.0)
    centre_y = y + (height / 2.0)
    largest_width = 0
    largest_height = 0
    valid_scales = []
    for offset in CLASSIFICATION_SCALE_OFFSETS:
        scale = min(1.35, max(0.75, candidate.scale + offset))
        if scale not in valid_scales:
            valid_scales.append(scale)
        for source in references.values():
            largest_width = max(largest_width, round(source.shape[1] * scale))
            largest_height = max(largest_height, round(source.shape[0] * scale))

    padding = 16
    left = max(0, round(centre_x - largest_width / 2.0 - padding))
    top = max(0, round(centre_y - largest_height / 2.0 - padding))
    right = min(
        canonical_screen.shape[1],
        round(centre_x + largest_width / 2.0 + padding),
    )
    bottom = min(
        canonical_screen.shape[0],
        round(centre_y + largest_height / 2.0 + padding),
    )
    patch = canonical_screen[top:bottom, left:right]

    scores = {}
    for box_type in BOX_TYPES:
        best_score = -1.0
        for scale in valid_scales:
            scaled = _scaled_reference(box_type, scale)
            if scaled is None:
                continue
            template, alpha = scaled
            if patch.shape[0] < template.shape[0] or patch.shape[1] < template.shape[1]:
                continue

            # Ignore transparent and barely-antialiased pixels.  CCOEFF removes
            # global brightness shifts while still comparing all three colour
            # channels under the sprite's real silhouette.
            mask = np.where(alpha >= 32, 255, 0).astype(np.uint8)
            response = cv2.matchTemplate(
                patch,
                template,
                cv2.TM_CCOEFF_NORMED,
                mask=mask,
            )
            response = np.nan_to_num(
                response,
                copy=False,
                nan=-1.0,
                posinf=-1.0,
                neginf=-1.0,
            )
            if response.size:
                best_score = max(best_score, float(response.max()))
        scores[box_type] = best_score
    return scores


def _classify_candidate(canonical_screen, candidate: _Candidate):
    scores = _masked_class_scores(canonical_screen, candidate)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked:
        return None

    best_guess, confidence = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else -1.0
    margin = confidence - runner_up
    if confidence < MIN_MASKED_CANDIDATE_SCORE:
        return None

    box_type = best_guess
    if (
        confidence < CLASSIFICATION_MIN_SCORE
        or margin < CLASSIFICATION_MIN_MARGIN
    ):
        box_type = UNKNOWN_BOX_TYPE
    return box_type, confidence, margin, best_guess


def _map_bbox_to_input(bbox, scale_x, scale_y):
    x, y, width, height = bbox
    return (
        round(x * scale_x),
        round(y * scale_y),
        max(1, round(width * scale_x)),
        max(1, round(height * scale_y)),
    )


def _reading_order(detections: list[MysteryBoxDetection]):
    """Group slightly staggered boxes into visual rows, then sort left-to-right."""

    rows = []
    for detection in sorted(
        detections,
        key=lambda item: item.bbox[1] + item.bbox[3] / 2.0,
    ):
        centre_y = detection.bbox[1] + detection.bbox[3] / 2.0
        target_row = None
        for row in rows:
            row_centre = sum(item[0] for item in row) / len(row)
            typical_height = sum(item[1].bbox[3] for item in row) / len(row)
            if abs(centre_y - row_centre) <= typical_height * 0.35:
                target_row = row
                break
        if target_row is None:
            rows.append([(centre_y, detection)])
        else:
            target_row.append((centre_y, detection))

    ordered = []
    for row in rows:
        ordered.extend(
            item[1]
            for item in sorted(
                row,
                key=lambda item: item[1].bbox[0] + item[1].bbox[2] / 2.0,
            )
        )
    return ordered


def detect_mystery_boxes(screen) -> list[MysteryBoxDetection]:
    """Detect and classify every unopened box shown in one popup.

    Bad/non-image input and screens with no credible box candidate return an
    empty list.  A credible but low-confidence tier is retained as ``unknown``
    so callers can include it in the session total without mislabelling it.
    """

    canonical_screen, scale_x, scale_y = _canonical_screen(screen)
    if canonical_screen is None:
        return []

    proposals = _cross_tier_nms(_find_candidates(canonical_screen))
    detections = []
    for candidate in proposals:
        classified = _classify_candidate(canonical_screen, candidate)
        if classified is None:
            continue
        box_type, confidence, margin, best_guess = classified
        detections.append(
            MysteryBoxDetection(
                box_type=box_type,
                confidence=confidence,
                score_margin=margin,
                bbox=_map_bbox_to_input(candidate.bbox, scale_x, scale_y),
                best_guess=best_guess,
            )
        )

    # Cross-tier NMS is complete before the game rule's five-box cap is used.
    detections = sorted(detections, key=lambda item: item.confidence, reverse=True)[
        :MAX_BOXES_PER_SCREEN
    ]
    return _reading_order(detections)


def detect_mystery_box_types(screen) -> list[str]:
    """Return just the tier labels needed by the bot/session-stat protocol."""

    return [detection.box_type for detection in detect_mystery_boxes(screen)]


def classify_mystery_box(box_crop) -> str:
    """Classify one already-cropped box sprite, failing closed as ``unknown``."""

    crop = _normalise_bgr(box_crop)
    if crop is None or crop.shape[0] < 40 or crop.shape[1] < 40:
        return UNKNOWN_BOX_TYPE

    references = _load_references()
    if not references:
        return UNKNOWN_BOX_TYPE
    median_width = float(np.median([image.shape[1] for image in references.values()]))
    median_height = float(np.median([image.shape[0] for image in references.values()]))
    scale = min(
        1.35,
        max(
            0.75,
            ((crop.shape[1] / median_width) + (crop.shape[0] / median_height)) / 2.0,
        ),
    )

    padding = 20
    canvas = cv2.copyMakeBorder(
        crop,
        padding,
        padding,
        padding,
        padding,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )
    candidate = _Candidate(
        score=1.0,
        proposed_type=UNKNOWN_BOX_TYPE,
        bbox=(padding, padding, crop.shape[1], crop.shape[0]),
        scale=scale,
    )
    classified = _classify_candidate(canvas, candidate)
    return classified[0] if classified is not None else UNKNOWN_BOX_TYPE
