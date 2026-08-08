"""Parse PDFs and split them into overlapping text chunks.

Each chunk keeps track of which document and which page it came from, so
retrieval can always cite an accurate (document_name, page_number) pair.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from pypdf import PdfReader


@dataclass
class Chunk:
    doc_name: str
    page_number: int  # 1-indexed, matches what a human sees in a PDF viewer
    chunk_index: int  # index of this chunk within the page (for a stable id)
    text: str


def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping character-based chunks.

    Character-based (not token-based) chunking is used deliberately to keep
    the pipeline dependency-light and predictable; chunk_size/overlap are
    tunable via environment variables.
    """
    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap  # step forward, keeping overlap
    return chunks


def load_pdfs(pdf_dir: str, chunk_size: int, chunk_overlap: int) -> List[Chunk]:
    """Read every PDF in pdf_dir and return a flat list of Chunk objects.

    Raises FileNotFoundError if the directory doesn't exist, and skips
    (with a warning) any PDF that fails to parse, so one corrupt file
    doesn't take down the whole ingestion run.
    """
    directory = Path(pdf_dir)
    if not directory.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    pdf_paths = sorted(directory.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in: {pdf_dir}")

    all_chunks: List[Chunk] = []

    for pdf_path in pdf_paths:
        try:
            reader = PdfReader(str(pdf_path))
        except Exception as exc:  # noqa: BLE001 - we want to continue on any parse error
            print(f"[WARN] Could not open {pdf_path.name}: {exc}")
            continue

        doc_name = pdf_path.name

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] Could not extract text from {doc_name} page {page_idx}: {exc}")
                continue

            if not page_text.strip():
                continue  # blank / image-only page, nothing to index

            page_chunks = _split_text(page_text, chunk_size, chunk_overlap)
            for i, chunk_text in enumerate(page_chunks):
                all_chunks.append(
                    Chunk(
                        doc_name=doc_name,
                        page_number=page_idx,
                        chunk_index=i,
                        text=chunk_text,
                    )
                )

        print(f"[OK] Parsed {doc_name}: {len(reader.pages)} pages")

    if not all_chunks:
        raise ValueError("No extractable text found in any supplied PDF.")

    return all_chunks
