"""CLI entry point for reference-fixer."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from reference_fixer.pdf_reader import extract_text
from reference_fixer.ref_parser import parse_references
from reference_fixer.report import (
    print_report, export_csvs, print_reverse_report,
    export_orphan_csv, export_paren_groups_csv,
)
from reference_fixer.scanner import scan_mentions
from reference_fixer.citation_extractor import (
    extract_citations, extract_paren_groups,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reference-fixer",
        description=(
            "Check whether authors from your reference list are actually "
            "cited in your RRL discussion."
        ),
    )
    parser.add_argument(
        "references",
        metavar="REFERENCES_PDF",
        help="Path to the PDF containing the reference list.",
    )
    parser.add_argument(
        "discussion",
        metavar="DISCUSSION_PDF",
        help="Path to the PDF containing the RRL discussion.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show the raw text of each parsed reference.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.csv",
        metavar="CSV_FILE",
        help="Path for the CSV output file (default: output.csv).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    console = Console()

    # ── Step 1: Extract text from PDFs ───────────────────────────────
    console.print("\n[bold cyan]>> Extracting text from PDFs...[/bold cyan]")
    try:
        ref_text = extract_text(args.references)
        disc_text = extract_text(args.discussion)
    except (FileNotFoundError, RuntimeError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)

    if not ref_text.strip():
        console.print("[bold red]Error:[/bold red] Reference PDF contains no extractable text.")
        sys.exit(1)
    if not disc_text.strip():
        console.print("[bold red]Error:[/bold red] Discussion PDF contains no extractable text.")
        sys.exit(1)

    # ── Step 2: Parse references ─────────────────────────────────────
    console.print("[bold cyan]>> Parsing references...[/bold cyan]")
    references = parse_references(ref_text)

    if not references:
        console.print("[bold red]Error:[/bold red] Could not detect any references in the PDF.")
        console.print("[dim]Tip: make sure the PDF contains APA-style references.[/dim]")
        sys.exit(1)

    console.print(f"   Found [bold]{len(references)}[/bold] references.")

    # ── (Optional) Verbose: show parsed references ───────────────────
    if args.verbose:
        console.print("\n[bold yellow]Parsed references:[/bold yellow]")
        for i, ref in enumerate(references, 1):
            authors = ", ".join(ref.authors)
            console.print(f"  {i:>3}. [{authors}] ({ref.year})")
            console.print(f"       [dim]{ref.raw[:120]}...[/dim]" if len(ref.raw) > 120 else f"       [dim]{ref.raw}[/dim]")

    # ── Step 3: Scan discussion for author mentions ──────────────────
    console.print("[bold cyan]>> Scanning discussion for author mentions...[/bold cyan]")
    results = scan_mentions(disc_text, references)

    # ── Step 4: Print report ─────────────────────────────────────────
    print_report(results, console=console)

    # ── Step 5: Write CSVs ───────────────────────────────────────────
    table_csv, rank_csv = export_csvs(results, args.output)
    console.print(f"  [bold cyan]Full table CSV written to:[/bold cyan] {table_csv}")
    console.print(f"  [bold cyan]Rankings CSV written to:[/bold cyan]   {rank_csv}")

    # ── Step 6: Reverse check — citations in discussion NOT in refs ──
    console.print("[bold cyan]>> Reverse check: finding orphan citations...[/bold cyan]")
    disc_citations = extract_citations(disc_text)
    console.print(f"   Found [bold]{len(disc_citations)}[/bold] unique citations in the discussion.")

    # Build a lookup set from parsed references: (lowercase surname, year)
    ref_keys: set[tuple[str, str]] = set()
    for ref in references:
        for author in ref.authors:
            ref_keys.add((author.lower(), ref.year))

    # Find orphans: citations whose (author, year) pair is not in references
    orphans = [
        c for c in disc_citations
        if (c.author.lower(), c.year) not in ref_keys
    ]

    print_reverse_report(orphans, console=console)

    orphan_csv = export_orphan_csv(orphans, "orphans.csv")
    console.print(f"  [bold cyan]Orphan citations CSV written to:[/bold cyan] {orphan_csv}")

    # ── Step 7: Parenthetical groups ─────────────────────────────────
    console.print("[bold cyan]>> Extracting parenthetical groups...[/bold cyan]")
    paren_groups = extract_paren_groups(disc_text)
    console.print(f"   Found [bold]{len(paren_groups)}[/bold] parenthetical groups.")

    paren_csv = export_paren_groups_csv(paren_groups, "paren_groups.csv")
    console.print(f"  [bold cyan]Parenthetical groups CSV written to:[/bold cyan] {paren_csv}")


if __name__ == "__main__":
    main()
