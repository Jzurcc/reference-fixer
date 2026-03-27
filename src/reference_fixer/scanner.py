"""Scan RRL discussion text for mentions of reference author surnames."""

from __future__ import annotations

import re
from dataclasses import dataclass

from reference_fixer.ref_parser import Reference


@dataclass
class MentionResult:
    """Result of scanning the discussion for a single reference."""

    reference: Reference
    first_author: str
    mention_count: int

    @property
    def mentioned(self) -> bool:
        return self.mention_count > 0


def _build_pattern(surname: str) -> re.Pattern[str]:
    """Build a word-boundary regex pattern for a surname.

    Handles surnames with hyphens, apostrophes, and accented characters.
    """
    # Escape any regex-special chars in the surname
    escaped = re.escape(surname)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def scan_mentions(
    discussion_text: str,
    references: list[Reference],
) -> list[MentionResult]:
    """Scan the discussion text for occurrences of each reference's first author.

    Args:
        discussion_text: The full text of the RRL discussion PDF.
        references: Parsed reference list.

    Returns:
        A list of MentionResult objects, one per reference, in the same order.
    """
    results: list[MentionResult] = []

    for ref in references:
        surname = ref.first_author
        if surname == "Unknown":
            results.append(MentionResult(reference=ref, first_author=surname, mention_count=0))
            continue

        pattern = _build_pattern(surname)
        matches = pattern.findall(discussion_text)
        count = len(matches)

        results.append(
            MentionResult(
                reference=ref,
                first_author=surname,
                mention_count=count,
            )
        )

    return results
