"""Fuzzy match retailer product names to canonical GSMArena device names."""
from __future__ import annotations

import re
from rapidfuzz import fuzz, process

MIN_SCORE = 70  # minimum similarity threshold (0-100)

# Noise tokens to strip before matching
_NOISE = re.compile(
    r"\b("
    r"dual sim|single sim|lte|5g|4g|3g|wi-fi|wifi|"
    r"new|official|import|global|arabic|english|"
    r"sealed|open box|used|refurb|"
    r"with|and|or|the|"
    r"\d+gb|\d+tb|\d+mb|\d+mp"
    r")\b",
    re.IGNORECASE,
)


def _clean(name: str) -> str:
    name = name.lower()
    name = _NOISE.sub(" ", name)
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def match_device(
    raw_name: str,
    canonical_names: list[str],
    threshold: int = MIN_SCORE,
) -> tuple[str, int] | None:
    """
    Match a raw retailer product name to the closest canonical device name.

    Returns (canonical_name, score) or None if below threshold.
    """
    if not canonical_names:
        return None

    cleaned_raw = _clean(raw_name)
    cleaned_map = {_clean(c): c for c in canonical_names}

    result = process.extractOne(
        cleaned_raw,
        list(cleaned_map.keys()),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold,
    )

    if result is None:
        return None

    matched_clean, score, _ = result
    return cleaned_map[matched_clean], score


class DeviceNameIndex:
    """Pre-built index of canonical device names for fast batch matching."""

    def __init__(self, canonical_names: list[str]):
        self.canonical = canonical_names
        self._clean_map = {_clean(n): n for n in canonical_names}
        self._cleaned   = list(self._clean_map.keys())

    def match(self, raw: str, threshold: int = MIN_SCORE) -> tuple[str, int] | None:
        cleaned = _clean(raw)
        result  = process.extractOne(
            cleaned,
            self._cleaned,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
        )
        if result is None:
            return None
        matched_clean, score, _ = result
        return self._clean_map[matched_clean], score
