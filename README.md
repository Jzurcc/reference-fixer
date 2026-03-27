# RefFixer

A CLI tool that checks whether every entry in your **reference list** is cited somewhere in your paper, and conversely, whether every **in-text citation** in the paper actually has a corresponding reference — all in a single run. While originally designed for RRL chapters, it works on any section of a research paper.

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
reference-fixer references.pdf research_paper.pdf
```

A Windows batch launcher with guided prompts is also available:
```bat
run.bat
```

### Options

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Show all parsed references and their extracted authors |
| `-o, --output` | Set the output CSV filename (default: `output.csv`) |
| `-h, --help` | Show help message |

## Output Files

Each run generates four CSV files in the current directory:

| File | Contents |
|------|----------|
| `output.csv` | Full forward-check table (reference → mention count → status) |
| `rankings.csv` | First-author surnames sorted by mention frequency (ascending) |
| `orphans.csv` | Citations found in the paper with **no matching reference** |
| `paren_groups.csv` | All parenthetical citation groups ranked by number of entries |

## How It Works

### 1. PDF Text Extraction
Both PDFs are extracted page-by-page using **PyMuPDF**. Page headers and footers injected mid-text (e.g. `References 43`) are automatically stripped before processing to prevent them from corrupting the parser.

### 2. Reference Parsing — Backtracking Author Extraction
The reference parser uses a **year-anchored backtracking algorithm** tuned for **APA 7th edition** format:
- It first locates all `(Year)` anchors in the extracted text.
- For each anchor, it backtracks through the preceding text until it hits the last digit of the previous reference (e.g., a DOI or page number). This precisely marks where the current reference's author block begins.
- It then scans forward using a strict regex pattern (`Surname, I.`) to extract only valid APA-formatted author names — ignoring article titles, journal names, and other non-author text.
- Multi-author entries using `&` or `and` are split with **word-boundary matching** so names like `Fernandes` and `Pandey` are never accidentally severed mid-name.

### 3. Forward Check — Discussion Scanning
For each parsed reference, the tool searches the full paper text for the **first author's surname** using a case-insensitive `\bSurname\b` word-boundary regex. This avoids false positives (e.g., matching "Smith" inside "Blacksmith"). Mention counts are tallied and colour-coded in the report.

### 4. Reverse Check — Citation Extraction
The paper text is scanned for all **APA in-text citation formats**:

- **Parenthetical**: `(Author, 2025)`, `(A & B, 2025)`, `(A et al., 2025)`, and semicolon-grouped `(A, 2025; B, 2024)`
- **Narrative**: `Author (2025)`, `A and B (2025)`, `A et al. (2025)`

Each extracted citation is cross-referenced against the parsed reference list. Any citation whose `(author, year)` pair has no matching reference is flagged as an **orphan** and exported to `orphans.csv`.

### 5. Grouped Parenthetical Analysis
All parenthetical blocks from the paper are collected and ranked by the number of citations they contain, exported to `paren_groups.csv`. This helps identify sections that may have too many or too few supporting references.

## Requirements

- Python >= 3.9
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF text extraction
- [Rich](https://rich.readthedocs.io/) — Terminal table formatting

## Notes

- Targets **APA 7th edition** reference and in-text citation formatting
- Works on any chapter or section of a research paper, not just the RRL
- The author extraction regex exclusively accepts `Word, L.` patterns — numbers, titles, and non-name fragments are automatically rejected
