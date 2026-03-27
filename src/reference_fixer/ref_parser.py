"""Parse reference list text into structured entries with author names."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Reference:
    """A single bibliographic reference."""

    authors: list[str]  # List of author surnames
    year: str
    raw: str  # The original raw text of this reference entry

    @property
    def first_author(self) -> str:
        """Return the first author's surname, or 'Unknown' if empty."""
        return self.authors[0] if self.authors else "Unknown"


# Matches a year in parentheses like (2020) or (2020, January) or (n.d.)
_YEAR_PATTERN = re.compile(r"\(((?:19|20)\d{2}[a-z]?|n\.d\.)\)")

# Matches the start of an author: Capitalized word, comma, optional space, Capital letter, period.
# Includes hyphens and accented characters, ensuring NO NUMBERS are matched.
# Example: "Edge, D.", "Abdelghafour, M. A. M."
_AUTHOR_START_PATTERN = re.compile(r"([A-Z][A-Za-z\u00C0-\u024F\'\-]+,\s*(?:[A-Z]\.\s*-?)+)")


def _extract_authors_from_block(author_block: str) -> list[str]:
    """Extract individual author surnames from an author block string."""
    surnames: list[str] = []

    # Clean up trailing content before year
    author_block = author_block.split("(")[0].strip(" .,;")

    # Remove "..." or "…" (used when truncating author lists)
    author_block = re.sub(r"[…\.\.\.]", "", author_block)

    # Split by "&" 
    parts = re.split(r"\s*(?:&)\s*", author_block, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Split on ", " but only where the next token is a capital letter
        # followed by a comma or period (start of new author or initial).
        # We split by detecting "Surname,"
        author_chunks = re.split(r",\s*(?=[A-Z][A-Za-z\u00C0-\u024F\'\-]+,)", part)

        for chunk in author_chunks:
            chunk = chunk.strip().rstrip(",. ")
            if not chunk:
                continue
                
            comma_idx = chunk.find(",")
            if comma_idx > 0:
                surname = chunk[:comma_idx].strip()
            else:
                surname = chunk.split()[0] if chunk.split() else chunk

            surname = surname.strip(" .,;()[]")
            
            # Additional safety: guarantee no numbers in surname
            if len(surname) >= 2 and not any(char.isdigit() for char in surname):
                surnames.append(surname)

    return surnames


def parse_references(text: str) -> list[Reference]:
    """Parse raw reference-list text into structured Reference objects.

    Uses backtracking from the (Year) anchor to the last number of the 
    previous reference, then finds the first author strict pattern.
    """
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text.strip())
    
    # Strip injected page headers/footers like "References 243" that break autor lists
    text = re.sub(r"References\s+\d+\s*", "", text, flags=re.IGNORECASE)
    
    # We find all years, which act as strict anchors for the end of the author blocks
    years = list(_YEAR_PATTERN.finditer(text))
    
    references: list[Reference] = []
    
    for i in range(len(years)):
        chunk_start = 0 if i == 0 else years[i - 1].end()
        chunk = text[chunk_start:years[i].start()]
        
        last_num_idx = -1
        if i > 0:
            # Backtrack to find the last number from the previous reference's tail
            # This correctly bypasses URLs, page numbers, and list numbers
            for j in range(len(chunk) - 1, -1, -1):
                if chunk[j].isdigit():
                    last_num_idx = j
                    break
                    
        search_region = chunk[last_num_idx + 1:]
        
        match = _AUTHOR_START_PATTERN.search(search_region)
        is_fallback = False
        if not match:
            # Fallback if no strict author pattern found after number
            match = _AUTHOR_START_PATTERN.search(chunk)
            is_fallback = True
            
        if match:
            # We found the start of the author list!
            if not is_fallback:
                start_author_idx = last_num_idx + 1 + match.start()
            else:
                start_author_idx = match.start()
                
            # The author block is everything from `start_author_idx` up to the year!
            author_block = chunk[start_author_idx:].strip()
            
            # Now we extract individual surnames from this author block
            surnames = _extract_authors_from_block(author_block)
            year_str = years[i].group(1)
            raw_entry = author_block + " " + years[i].group(0)
            
            if surnames:
                references.append(Reference(authors=surnames, year=year_str, raw=raw_entry))

    return references
