"""Fuzzy device name normalizer.

Matches retailer product titles to canonical device names from GSMArena
using RapidFuzz token_sort_ratio with a configurable confidence threshold.
"""
import re
from functools import lru_cache
from typing import Optional

from loguru import logger
from rapidfuzz import fuzz, process

MIN_CONFIDENCE = 70  # percent

_NOISE = re.compile(
    r"(\d+\s*gb|\d+\s*tb|\d+\s*mp|\bram\b|\brom\b|\bdual\s*sim\b|\b4g\b|\b5g\b"
    r"|\blte\b|official|egypt|warranty|sealed|brand\s*new|\bwith\b.*$)",
    re.IGNORECASE,
)


def clean_name(name: str) -> str:
    """Strip storage, colour, and noise tokens for better matching."""
    name = _NOISE.sub("", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def match_device(
    raw_name: str,
    canonical_names: list[str],
    threshold: int = MIN_CONFIDENCE,
) -> Optional[str]:
    """Return the best-matching canonical name or None if below threshold."""
    cleaned = clean_name(raw_name)
    if not cleaned or not canonical_names:
        return None

    result = process.extractOne(
        cleaned,
        canonical_names,
        scorer=fuzz.token_sort_ratio,
    )
    if result is None:
        return None

    matched_name, score, _ = result
    if score >= threshold:
        logger.debug(f"Matched '{raw_name}' -> '{matched_name}' (score={score})")
        return matched_name

    logger.debug(f"No match for '{raw_name}' (best={matched_name}, score={score})")
    return None
