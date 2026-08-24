"""Load and enforce backend/skills/medium.md.

The full markdown is injected into plan/draft prompts. This module extracts a
compact checklist for every later node, and runs deterministic lint so the
house skill is actually a gate, not flavor text the model can ignore.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.utils.dash_check import find_em_en_dash_violations, strip_em_en_dashes

DISCLOSURE_NEEDLE = "ai assistance"
DISCLOSURE_TEXT = (
    "This article was written with AI assistance. All ideas, personal experiences, "
    "and expert opinions are my own."
)

DEFAULT_BANNED = (
    "in today's fast-paced world",
    "in today's world",
    "game-changer",
    "paradigm shift",
    "delve",
    "delve deeper",
    "unlock your potential",
    "navigate the complexities",
    "leverage",
    "it's worth noting that",
    "in conclusion",
    "without further ado",
    "at the end of the day",
    "let's dive in",
    "dive in",
    "revolutionize",
    "harness the power of",
    "embark on a journey",
    "tapestry",
    "cutting-edge",
    "thanks for reading",
)

_WORD_RE = re.compile(r"\b\w+\b")
_H1_RE = re.compile(r"^#\s+(.+)$", re.M)
_H2_RE = re.compile(r"^##\s+(.+)$", re.M)
_BOLD_RE = re.compile(r"\*\*([^*]{8,120})\*\*")
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_CODE_FENCE_RE = re.compile(r"```.*?```", re.S)


def _slice(guide: str, start: str, end: str) -> str:
    i = guide.find(start)
    if i < 0:
        return ""
    j = guide.find(end, i + len(start)) if end else len(guide)
    if j < 0:
        j = len(guide)
    return guide[i:j].strip()


def compact_skills(guide: str) -> str:
    """Keep the enforceable sections of medium.md for later prompts."""
    text = (guide or "").strip()
    if not text:
        return ""
    parts = [
        _slice(text, "## 3. The", "## 4."),
        _slice(text, "### Banned Phrases", "## 6."),
        _slice(text, "## 9. Medium AI Content Policy", "## 11."),
    ]
    compact = "\n\n".join(p for p in parts if p)
    return compact or text[:6000]


def extract_banned_phrases(guide: str) -> list[str]:
    text = guide or ""
    start = text.lower().find("banned phrases")
    phrases: list[str] = []
    if start >= 0:
        end_markers = ("### CTA", "## 6.", "## 6 ")
        end = len(text)
        for marker in end_markers:
            idx = text.find(marker, start)
            if 0 <= idx < end:
                end = idx
        section = text[start:end]
        for line in section.splitlines():
            line = line.strip()
            if not line.startswith("-"):
                continue
            quoted = re.findall(r'"([^"]+)"', line)
            bits = quoted or [re.sub(r"^-\s*", "", line)]
            for bit in bits:
                for part in re.split(r"\s*/\s*", bit):
                    cleaned = re.sub(r"\s*\(.*?\)\s*", "", part).strip().strip('"').lower()
                    cleaned = re.sub(r"\s+", " ", cleaned)
                    if len(cleaned) >= 4:
                        phrases.append(cleaned)
    merged = []
    seen = set()
    for item in list(DEFAULT_BANNED) + phrases:
        if item not in seen:
            seen.add(item)
            merged.append(item)
    return merged


@dataclass
class SkillsCheck:
    check_id: str
    label: str
    passed: bool
    severity: str
    problem: str = ""
    suggested_fix: str = ""
    detail: str = ""


@dataclass
class SkillsAudit:
    checks: list[SkillsCheck] = field(default_factory=list)
    banned_hits: list[str] = field(default_factory=list)
    word_count: int = 0
    title: str = ""

    def as_dict(self) -> dict:
        return {
            "word_count": self.word_count,
            "title": self.title,
            "banned_hits": self.banned_hits,
            "passed": sum(1 for item in self.checks if item.passed),
            "failed": sum(1 for item in self.checks if not item.passed),
            "checks": [
                {
                    "id": item.check_id,
                    "label": item.label,
                    "passed": item.passed,
                    "severity": item.severity,
                    "detail": item.detail or item.problem,
                    "suggested_fix": item.suggested_fix,
                }
                for item in self.checks
            ],
        }


def _word_count(markdown: str) -> int:
    stripped = _CODE_FENCE_RE.sub(" ", markdown or "")
    return len(_WORD_RE.findall(stripped))


def _first_prose(markdown: str) -> str:
    body = markdown or ""
    body = _H1_RE.sub("", body, count=1)
    for para in re.split(r"\n\s*\n", body):
        text = para.strip()
        if not text or text.startswith(("#", "!", ">", "-", "*", "|")):
            continue
        if text.startswith("*") and text.endswith("*") and "\n" not in text:
            continue
        return text
    return ""


def _sentence_count(para: str) -> int:
    return len([part for part in re.split(r"[.!?]+", para) if part.strip()])


def lint_article(markdown: str, *, skills_rules: str = "", images: list | None = None) -> SkillsAudit:
    text = markdown or ""
    banned = extract_banned_phrases(skills_rules)
    words = _word_count(text)
    h1 = _H1_RE.search(text)
    title = (h1.group(1).strip() if h1 else "")
    audit = SkillsAudit(word_count=words, title=title)
    lower = text.lower()

    def add(check_id: str, label: str, passed: bool, severity: str, problem: str = "", fix: str = "", detail: str = ""):
        audit.checks.append(
            SkillsCheck(
                check_id=check_id,
                label=label,
                passed=passed,
                severity=severity,
                problem=problem,
                suggested_fix=fix,
                detail=detail,
            )
        )

    hits: list[str] = []
    for phrase in banned:
        if " " in phrase or "-" in phrase:
            found = phrase in lower
        else:
            found = re.search(rf"\b{re.escape(phrase)}\b", lower) is not None
        if found:
            hits.append(phrase)
    audit.banned_hits = hits
    add(
        "banned",
        "Zero banned AI-ism phrases",
        not hits,
        "major",
        problem=f"Banned house-skill phrases still in the draft: {', '.join(hits[:8])}" if hits else "",
        fix="Replace each banned phrase with plain wording. Never use delve, leverage, game-changer, in conclusion, or similar AI-isms.",
        detail=", ".join(hits) if hits else "Clean",
    )

    dashes = find_em_en_dash_violations(text)
    add(
        "dashes",
        "No em or en dashes",
        not dashes,
        "major",
        problem=f"{len(dashes)} em/en dash(es) remain" if dashes else "",
        fix="Replace em dashes with commas or periods, and en dashes with hyphens.",
        detail=str(len(dashes)),
    )

    add(
        "wordcount",
        "1,000–1,500 words (allow up to 1,800)",
        1000 <= words <= 1800,
        "major" if words < 1000 else "minor",
        problem=f"Word count is {words}. House skill wants 1,000–1,500 (hard fail under 1,000 or over 1,800).",
        fix="Expand with a worked example and source details if short. Cut repetition if long. Stay in the 1,000–1,500 band.",
        detail=str(words),
    )

    h2s = _H2_RE.findall(text)
    add(
        "h2",
        "H2 subheadings every 200–300 words",
        bool(h2s) and (words < 400 or words / max(len(h2s), 1) <= 400),
        "major",
        problem="Missing scannable H2s (need a subheading about every 200–300 words)." if not h2s else f"{len(h2s)} H2s for {words} words is too sparse.",
        fix="Add H2s a skimmer can follow. One heading about every 250 words.",
        detail=f"{len(h2s)} H2s",
    )

    long_paras = 0
    for para in re.split(r"\n\s*\n", text):
        stripped = para.strip()
        if not stripped or stripped.startswith(("#", "!", "|", "-", "*", "```")):
            continue
        if _sentence_count(stripped) > 3:
            long_paras += 1
    add(
        "paragraphs",
        "Max 3 sentences per paragraph",
        long_paras < 3,
        "minor",
        problem=f"{long_paras} paragraph(s) have more than 3 sentences." if long_paras else "",
        fix="Break long paragraphs. Mobile Medium readers need white space.",
        detail=str(long_paras),
    )

    goldens = _BOLD_RE.findall(text)
    add(
        "golden",
        "At least 3 bold golden sentences",
        len(goldens) >= 3,
        "minor",
        problem=f"Only {len(goldens)} bold takeaway(s). House skill wants at least 3 highlightable golden sentences.",
        fix="Bold three short, punchy takeaways a reader would highlight.",
        detail=str(len(goldens)),
    )

    lede = _first_prose(text)
    fluff = bool(re.match(r"^(in today'?s|have you ever|in the world of|imagine if)\b", lede, re.I))
    add(
        "lede",
        "First sentence states the problem",
        bool(lede) and not fluff,
        "major",
        problem="Opening is fluff or missing. First sentence must state the pain, not 'In today's world'.",
        fix="Rewrite the lede so sentence one names a specific problem, number, or scene.",
        detail=(lede[:140] + "…") if len(lede) > 140 else lede,
    )

    disclosure = DISCLOSURE_NEEDLE in lower
    add(
        "disclosure",
        "AI disclosure at the bottom",
        disclosure,
        "critical",
        problem="Missing Medium AI-assistance disclosure. Undisclosed AI content is suppressed.",
        fix=f'Add this italic line at the bottom: *{DISCLOSURE_TEXT}*',
        detail="present" if disclosure else "missing",
    )

    add(
        "title_len",
        "Title under 60 characters",
        bool(title) and len(title) <= 60,
        "minor",
        problem=f"Title is {len(title)} characters. Medium SEO title should stay under 60.",
        fix="Shorten the H1. Keyword first, then the promise.",
        detail=f"{len(title)} chars" if title else "no H1",
    )

    thanks = "thanks for reading" in lower
    last = text.strip()[-500:].lower()
    has_cta = ("?" in last) or ("comment" in last) or ("follow" in last) or ("what would" in last)
    add(
        "cta",
        "CTA that drives comments (not 'Thanks for reading!')",
        has_cta and not thanks,
        "minor",
        problem="Closing is missing a comment-driving CTA, or uses 'Thanks for reading!'.",
        fix="End with a specific question or request for a war story. Never 'Thanks for reading!'.",
        detail="ok" if has_cta and not thanks else "weak close",
    )

    empty_alts = [m.group(2) for m in _IMG_RE.finditer(text) if not (m.group(1) or "").strip()]
    image_count = len(_IMG_RE.findall(text)) + (len(images or []) if not _IMG_RE.search(text) else 0)
    add(
        "alt",
        "Images have descriptive alt text",
        not empty_alts,
        "minor",
        problem=f"{len(empty_alts)} Markdown image(s) have empty alt text." if empty_alts else "",
        fix="Put a concrete description inside the square brackets of every ![alt](url).",
        detail=f"{image_count} images",
    )

    return audit


def apply_deterministic_fixes(markdown: str) -> str:
    """Fixes the house skill can enforce without another LLM call."""
    text = strip_em_en_dashes(markdown or "")
    if DISCLOSURE_NEEDLE not in text.lower():
        text = text.rstrip() + f"\n\n*{DISCLOSURE_TEXT}*\n"
    return text
