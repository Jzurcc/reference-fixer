"""Extract in-text and narrative APA citations from discussion text."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Citation:
    """A single citation found in the discussion text."""

    author: str       # Primary author surname
    year: str         # e.g. "2025"
    style: str        # "parenthetical" or "narrative"
    raw: str          # The original matched text

    def __hash__(self) -> int:
        return hash((self.author.lower(), self.year))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Citation):
            return NotImplemented
        return self.author.lower() == other.author.lower() and self.year == other.year


# ── Name building blocks ─────────────────────────────────────────────────
_NAME = r"[A-Z][A-Za-z\u00C0-\u024F\'\-]+"
_YEAR = r"(?:19|20)\d{2}[a-z]?"

# ── Parenthetical patterns ───────────────────────────────────────────────
# Matches the CONTENT inside parentheses: "(Author, 2025)" or grouped
# "(Author, 2025; Author2 & Author3, 2024)"
#
# Single author:          Author, 2025
# Two authors:            Author1 & Author2, 2025
# Three+ authors:         Author et al., 2025
_PAREN_SINGLE = rf"({_NAME})\s*,\s*({_YEAR})"
_PAREN_TWO    = rf"({_NAME})\s*&\s*{_NAME}\s*,\s*({_YEAR})"
_PAREN_ETAL   = rf"({_NAME})\s+et\s+al\.\s*,\s*({_YEAR})"

# We match the full parenthesised block and then parse inside it
_PAREN_BLOCK = re.compile(r"\(([^)]+)\)")

# ── Narrative patterns ───────────────────────────────────────────────────
# Author (2025)
_NARR_SINGLE = re.compile(
    rf"\b({_NAME})\s+\(({_YEAR})\)", re.UNICODE
)
# Author1 and Author2 (2025)
_NARR_TWO = re.compile(
    rf"\b({_NAME})\s+and\s+{_NAME}\s+\(({_YEAR})\)", re.UNICODE
)
# Author et al. (2025)
_NARR_ETAL = re.compile(
    rf"\b({_NAME})\s+et\s+al\.\s+\(({_YEAR})\)", re.UNICODE
)


def _parse_paren_block(block: str) -> list[Citation]:
    """Parse citations from the inside of a parenthesised block.

    Handles semicolon-separated groups like:
        "Author, 2025; Author2 et al., 2024"
    """
    citations: list[Citation] = []
    # Split by semicolons to handle grouped citations
    parts = block.split(";")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Try et al. first (most specific)
        m = re.search(_PAREN_ETAL, part)
        if m:
            citations.append(Citation(
                author=m.group(1), year=m.group(2),
                style="parenthetical", raw=f"({part.strip()})",
            ))
            continue

        # Try two-author
        m = re.search(_PAREN_TWO, part)
        if m:
            citations.append(Citation(
                author=m.group(1), year=m.group(2),
                style="parenthetical", raw=f"({part.strip()})",
            ))
            continue

        # Try single author
        m = re.search(_PAREN_SINGLE, part)
        if m:
            citations.append(Citation(
                author=m.group(1), year=m.group(2),
                style="parenthetical", raw=f"({part.strip()})",
            ))

    return citations


def extract_citations(text: str) -> list[Citation]:
    """Extract all APA-style citations from discussion text.

    Returns a deduplicated list of Citation objects.
    """
    seen: set[tuple[str, str]] = set()
    citations: list[Citation] = []

    def _add(c: Citation) -> None:
        key = (c.author.lower(), c.year)
        if key not in seen:
            seen.add(key)
            citations.append(c)

    # 1. Narrative citations (must run BEFORE parenthetical to avoid
    #    the year-in-parens being consumed by the block parser)
    for pattern, style_note in [
        (_NARR_ETAL, "narrative"),
        (_NARR_TWO, "narrative"),
        (_NARR_SINGLE, "narrative"),
    ]:
        for m in pattern.finditer(text):
            _add(Citation(
                author=m.group(1), year=m.group(2),
                style=style_note, raw=m.group(0),
            ))

    # 2. Parenthetical citations
    for m in _PAREN_BLOCK.finditer(text):
        block = m.group(1)
        for c in _parse_paren_block(block):
            _add(c)

    return citations


def extract_all_citations_with_freq(text: str) -> list[tuple[str, str, int]]:
    """Extract all citations WITH frequency (not deduplicated).

    Returns a list of (author, year, count) tuples sorted descending by count.
    """
    freq: Counter[tuple[str, str]] = Counter()

    # Count narrative citations
    for pattern in [_NARR_ETAL, _NARR_TWO, _NARR_SINGLE]:
        for m in pattern.finditer(text):
            key = (m.group(1), m.group(2))
            freq[key] += 1

    # Count parenthetical citations
    for m in _PAREN_BLOCK.finditer(text):
        block = m.group(1)
        for c in _parse_paren_block(block):
            key = (c.author, c.year)
            freq[key] += 1

    # Sort descending by frequency
    return [(author, year, count) for (author, year), count in freq.most_common()]


@dataclass
class ParenGroup:
    """A full parenthetical group, e.g. (Author, 2025; Author2, 2024)."""

    raw: str                    # The full matched parenthetical text
    citations: list[Citation]   # Individual citations parsed from this group
    count: int = 0              # Number of citations in this group


def extract_paren_groups(text: str) -> list[ParenGroup]:
    """Extract full parenthetical blocks and rank by number of citations inside.

    Returns a list of ParenGroup sorted descending by citation count.
    """
    groups: list[ParenGroup] = []

    for m in _PAREN_BLOCK.finditer(text):
        block = m.group(1)
        citations = _parse_paren_block(block)
        if citations:
            groups.append(ParenGroup(
                raw=f"({block})",
                citations=citations,
                count=len(citations),
            ))

    # Sort descending by number of citations in the group
    groups.sort(key=lambda g: g.count, reverse=True)
    return groups
