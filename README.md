# Reference Fixer

A CLI tool that checks whether authors from your **reference list** are actually cited in your **research paper**. It extracts author surnames from a references PDF, scans a discussion PDF for mentions, and reports which references are used and how many times.

## Installation

```bash
pip install -e .
```

## Usage

```bash
reference-fixer <REFERENCES_PDF> <DISCUSSION_PDF>
```

**Example:**
```bash
reference-fixer references.pdf chapter2_discussion.pdf
```

### Options

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Show the raw text of each parsed reference |
| `-h, --help` | Show help message |

## Output

The tool prints a table like:

```
                   Reference Citation Check
+---+----------------+------+-------------+----------+--------+
| # | First Author   | Year | All Authors | Mentions | Status |
+---+----------------+------+-------------+----------+--------+
| 1 | Smith          | 2020 | Smith, ...  |    3     |[+] Used|
| 2 | Johnson        | 2019 | Johnson,... |    0     |[-] Missing|
+---+----------------+------+-------------+----------+--------+

  Total references:       10
  Cited in discussion:     8
  NOT cited (missing):     2  <-- These references may not have been discussed.
```

## How It Works

1. **PDF Extraction** — Extracts text from both PDFs using PyMuPDF
2. **Reference Parsing** — Splits the reference text into individual APA-style entries and extracts author surnames
3. **Discussion Scanning** — Searches the discussion text for each first author's surname using word-boundary matching
4. **Report** — Displays a colour-coded table with mention counts and a summary

## Requirements

- Python >= 3.9
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF text extraction
- [Rich](https://rich.readthedocs.io/) — Terminal formatting

## Notes

- The parser targets **APA-style references** (the most common format in academic RRLs)
- Author matching uses **case-insensitive word-boundary regex** to avoid false positives
- Only the **first author's surname** is checked against the discussion text
