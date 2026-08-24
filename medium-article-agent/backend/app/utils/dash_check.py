"""Deterministic em/en dash checker."""

from __future__ import annotations

import re

EM_DASH = "\u2014"
EN_DASH = "\u2013"

_VIOLATION_RE = re.compile(f"[{EM_DASH}{EN_DASH}]")


def find_em_en_dash_violations(text: str) -> list[dict]:
    violations = []
    for match in _VIOLATION_RE.finditer(text):
        char = match.group()
        violations.append(
            {
                "index": match.start(),
                "char": "em dash" if char == EM_DASH else "en dash",
                "context": text[max(0, match.start() - 20) : match.start() + 20],
            }
        )
    return violations


def assert_no_em_en_dash(text: str) -> list[dict]:
    """Return violations list (empty = clean)."""
    return find_em_en_dash_violations(text)


def strip_em_en_dashes(text: str) -> str:
    return text.replace(EM_DASH, ", ").replace(EN_DASH, "-")
