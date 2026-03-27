"""PDF text extraction using PyMuPDF."""

from pathlib import Path

import fitz  # PyMuPDF


def extract_text(pdf_path: str | Path) -> str:
    """Extract all text from a PDF file, page by page.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        The full concatenated text of the PDF.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        RuntimeError: If the PDF cannot be opened or read.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise RuntimeError(f"Cannot open PDF: {pdf_path}") from exc

    pages: list[str] = []
    for page in doc:
        text = page.get_text("text")
        if text:
            pages.append(text)

    doc.close()
    return "\n".join(pages)
