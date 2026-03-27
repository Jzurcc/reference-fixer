"""Format and print the citation-check report using Rich, and export CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from reference_fixer.scanner import MentionResult
import re as _re

from reference_fixer.citation_extractor import Citation, ParenGroup


def print_report(results: list[MentionResult], console: Console | None = None) -> None:
    """Print a formatted table of citation check results.

    Args:
        results: The list of MentionResult objects from the scanner.
        console: Optional Rich console (defaults to stdout).
    """
    if console is None:
        console = Console()

    # ── Build the table ──────────────────────────────────────────────
    table = Table(
        title="Reference Citation Check",
        title_style="bold cyan",
        show_lines=True,
        header_style="bold magenta",
        border_style="bright_black",
        pad_edge=True,
    )

    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("First Author", style="bold white", min_width=16)
    table.add_column("Year", justify="center", style="cyan", width=8)
    table.add_column("All Authors", style="dim white", max_width=40, overflow="fold")
    table.add_column("Mentions", justify="center", width=10)
    table.add_column("Status", justify="center", width=12)

    cited = 0
    not_cited = 0

    for idx, result in enumerate(results, start=1):
        # Status badge
        if result.mentioned:
            status = Text("[+] Used", style="bold green")
            cited += 1
        else:
            status = Text("[-] Missing", style="bold red")
            not_cited += 1

        # Mention count styling
        if result.mention_count == 0:
            count_style = "bold red"
        elif result.mention_count <= 2:
            count_style = "yellow"
        else:
            count_style = "bold green"

        # All authors (joined)
        all_authors = ", ".join(result.reference.authors)

        table.add_row(
            str(idx),
            result.first_author,
            result.reference.year or "—",
            all_authors,
            Text(str(result.mention_count), style=count_style),
            status,
        )

    console.print()
    console.print(table)

    # ── Summary ──────────────────────────────────────────────────────
    console.print()
    total = len(results)
    console.print(f"  [bold]Total references:[/bold]  {total}")
    console.print(f"  [bold green]Cited in discussion:[/bold green]  {cited}")
    if not_cited > 0:
        console.print(
            f"  [bold red]NOT cited (missing):[/bold red]  {not_cited}  <-- These references may not be discussed."
        )
    else:
        console.print("  [bold green]All references are cited in the discussion![/bold green]")
    console.print()


def export_csvs(results: list[MentionResult], output_path: str | Path) -> tuple[Path, Path]:
    """Write two CSV files: the full table and the sorted rankings.

    Args:
        results: The list of MentionResult objects from the scanner.
        output_path: Path for the full table CSV file. The rankings CSV 
                     will be named 'rankings.csv' in the same directory.

    Returns:
        A tuple of (table_path, rankings_path).
    """
    output_path = Path(output_path)
    rankings_path = output_path.with_name("rankings.csv")

    # 1. Write the full table to output_path
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "First Author", "Year", "All Authors", "Mentions", "Status"])
        for idx, result in enumerate(results, start=1):
            status = "Used" if result.mentioned else "Missing"
            all_authors = ", ".join(result.reference.authors)
            year = result.reference.year or "n.d."
            writer.writerow([idx, result.first_author, year, all_authors, result.mention_count, status])

    # 2. Write the rankings to rankings.csv
    sorted_results = sorted(results, key=lambda r: r.mention_count)
    with open(rankings_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["first_author", "mentions"])
        for result in sorted_results:
            writer.writerow([result.first_author, result.mention_count])

    return output_path, rankings_path


def print_reverse_report(
    orphans: list[Citation],
    console: Console | None = None,
) -> None:
    """Print a table of citations found in the discussion but NOT in the references."""
    if console is None:
        console = Console()

    table = Table(
        title="Reverse Check: Citations NOT in References",
        title_style="bold yellow",
        show_lines=True,
        header_style="bold magenta",
        border_style="bright_black",
        pad_edge=True,
    )

    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Author", style="bold white", min_width=16)
    table.add_column("Year", justify="center", style="cyan", width=8)
    table.add_column("Style", justify="center", width=16)
    table.add_column("Raw Citation", style="dim white", max_width=50, overflow="fold")

    for idx, c in enumerate(orphans, start=1):
        table.add_row(
            str(idx),
            c.author,
            c.year,
            c.style,
            c.raw,
        )

    console.print()
    console.print(table)
    console.print()
    if orphans:
        console.print(
            f"  [bold yellow]Orphan citations:[/bold yellow] {len(orphans)}"
            "  <-- These are cited in the discussion but have NO matching reference."
        )
    else:
        console.print(
            "  [bold green]All discussion citations have a matching reference![/bold green]"
        )
    console.print()


def export_orphan_csv(
    orphans: list[Citation], output_path: str | Path
) -> Path:
    """Write orphan citations to a CSV file."""
    output_path = Path(output_path)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Author", "Year", "Style", "Raw Citation"])
        for idx, c in enumerate(orphans, start=1):
            raw_clean = _re.sub(r"\s+", " ", c.raw).strip()
            writer.writerow([idx, c.author, c.year, c.style, raw_clean])
    return output_path


def export_paren_groups_csv(
    groups: list[ParenGroup], output_path: str | Path
) -> Path:
    """Write parenthetical groups CSV ranked by number of citations."""
    output_path = Path(output_path)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Citations in Group", "Parenthetical Group"])
        for idx, g in enumerate(groups, start=1):
            raw_clean = _re.sub(r"\s+", " ", g.raw).strip()
            writer.writerow([idx, g.count, raw_clean])
    return output_path
