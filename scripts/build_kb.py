#!/usr/bin/env python3
"""
KisanSathi Knowledge Base Builder: Chunk agricultural documents, generate
Gemini embeddings (768-dim), and upsert into Supabase `kb_chunks` table.

Usage:
    python scripts/build_kb.py --input-dir data/kb_docs --language hi --dry-run
"""

import os
import sys
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *args, **kwargs):
        """Fallback progress generator when tqdm is not installed."""
        return iterable

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

EMBEDDING_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("build_kb")

# Devanagari Unicode range for language detection
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from a PDF file using PyPDF2."""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            logger.error("pypdf is required for PDF ingestion. Install with: pip install pypdf")
            sys.exit(1)

    reader = PdfReader(filepath)
    pages: List[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def extract_text_from_file(filepath: str) -> str:
    """Read plain text from .txt or .md files."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_document(filepath: str) -> str:
    """Dispatch to the correct reader based on file extension."""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext in (".txt", ".md"):
        return extract_text_from_file(filepath)
    else:
        logger.warning("Unsupported file type '%s', skipping: %s", ext, filepath)
        return ""


# ---------------------------------------------------------------------------
# Chunking (word-based, ~400 words per chunk, 100-word overlap)
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks based on word count.

    Args:
        text: Full document text.
        chunk_size: Target number of words per chunk.
        overlap: Number of overlapping words between consecutive chunks.

    Returns:
        List of text chunks.
    """
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start += chunk_size - overlap

    return chunks


# ---------------------------------------------------------------------------
# Language detection heuristic
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """
    Simple language heuristic: if >30% of characters are Devanagari, classify
    as Hindi ('hi'), otherwise English ('en').
    """
    if not text:
        return "en"
    total_chars = len(text.replace(" ", ""))
    if total_chars == 0:
        return "en"
    devanagari_count = len(_DEVANAGARI_RE.findall(text))
    return "hi" if (devanagari_count / total_chars) > 0.30 else "en"


# ---------------------------------------------------------------------------
# Document title extraction
# ---------------------------------------------------------------------------

def extract_doc_title(text: str, filename: str) -> str:
    """
    Extract the document title from the first non-empty line of text.
    Falls back to the filename stem if no suitable line is found.
    """
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            # Truncate very long first lines
            return stripped[:200]
    return Path(filename).stem


# ---------------------------------------------------------------------------
# Gemini embedding
# ---------------------------------------------------------------------------

def embed_text(text: str, client: httpx.Client) -> Optional[List[float]]:
    """
    Generate a 768-dim embedding for the given text via Gemini embedding API.

    Returns:
        List of 768 floats, or None on failure.
    """
    payload = {
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": 768,
    }
    api_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY
    try:
        resp = client.post(
            EMBEDDING_ENDPOINT,
            json=payload,
            headers={"x-goog-api-key": api_key},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["embedding"]["values"]
    except httpx.HTTPStatusError as exc:
        logger.error("Embedding API HTTP error %d: %s", exc.response.status_code, exc.response.text[:300])
        return None
    except Exception as exc:
        logger.error("Embedding failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Supabase insertion
# ---------------------------------------------------------------------------

def insert_chunk(
    row: Dict[str, Any],
    client: httpx.Client,
) -> bool:
    """
    Insert a single chunk row into the Supabase `kb_chunks` table via REST API.

    Returns:
        True on success, False on failure.
    """
    supabase_url = os.environ.get("SUPABASE_URL", "") or SUPABASE_URL
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or SUPABASE_SERVICE_ROLE_KEY
    url = f"{supabase_url}/rest/v1/kb_chunks"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    try:
        resp = client.post(url, json=row, headers=headers, timeout=15.0)
        resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as exc:
        logger.error("Supabase insert error %d: %s", exc.response.status_code, exc.response.text[:300])
        return False
    except Exception as exc:
        logger.error("Supabase insert failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the full knowledge-base build pipeline."""
    parser = argparse.ArgumentParser(
        description="KisanSathi Knowledge Base Ingestion Script"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/kb_docs",
        help="Directory containing agricultural texts or PDFs",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        choices=["hi", "en"],
        help="Override auto-detected language for all documents",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk without writing to Supabase or calling embedding API",
    )
    args = parser.parse_args()

    # ---- Validate input directory ----
    if not os.path.isdir(args.input_dir):
        logger.error("Input directory '%s' not found.", args.input_dir)
        logger.info("Create '%s' and supply verified agricultural manuals.", args.input_dir)
        logger.info("See data/kb_docs/README.md for file format instructions.")
        sys.exit(1)

    supported_exts = (".txt", ".md", ".pdf")
    files = sorted(
        f
        for f in os.listdir(args.input_dir)
        if f.lower().endswith(supported_exts) and not f.startswith(".") and f.lower() != "readme.md"
    )

    if not files:
        logger.error("No valid document files (%s) found in '%s'.", ", ".join(supported_exts), args.input_dir)
        sys.exit(1)

    # ---- Validate environment for non-dry-run ----
    if not args.dry_run:
        missing_vars: List[str] = []
        if not GEMINI_API_KEY:
            missing_vars.append("GEMINI_API_KEY")
        if not SUPABASE_URL:
            missing_vars.append("SUPABASE_URL")
        if not SUPABASE_SERVICE_ROLE_KEY:
            missing_vars.append("SUPABASE_SERVICE_ROLE_KEY")
        if missing_vars:
            logger.error(
                "Required environment variables missing: %s", ", ".join(missing_vars)
            )
            sys.exit(1)

    logger.info("Found %d document(s) to ingest from '%s'.", len(files), args.input_dir)

    total_chunks = 0
    total_inserted = 0
    total_failed = 0

    with httpx.Client() as client:
        for filename in tqdm(files, desc="Processing documents"):
            filepath = os.path.join(args.input_dir, filename)

            # 1. Extract text
            text = read_document(filepath)
            if not text.strip():
                logger.warning("Empty or unreadable file: %s — skipping.", filename)
                continue

            # 2. Detect metadata
            doc_title = extract_doc_title(text, filename)
            language = args.language or detect_language(text)

            # 3. Chunk
            chunks = chunk_text(text, chunk_size=400, overlap=100)
            total_chunks += len(chunks)
            logger.info(
                "  -> %s: %d chunks, language=%s, title='%s'",
                filename,
                len(chunks),
                language,
                doc_title[:60],
            )

            if args.dry_run:
                continue

            # 4. Embed & insert each chunk
            for chunk in tqdm(chunks, desc=f"  Embedding {filename}", leave=False):
                embedding = embed_text(chunk, client)
                if embedding is None:
                    total_failed += 1
                    continue

                row = {
                    "source": filename,
                    "doc_title": doc_title,
                    "chunk_text": chunk,
                    "embedding": embedding,
                    "language": language,
                }

                if insert_chunk(row, client):
                    total_inserted += 1
                else:
                    total_failed += 1

    # ---- Summary ----
    logger.info("=" * 60)
    logger.info("Total chunks extracted : %d", total_chunks)
    if args.dry_run:
        logger.info("Dry run enabled — no database records modified.")
    else:
        logger.info("Chunks inserted        : %d", total_inserted)
        logger.info("Chunks failed          : %d", total_failed)

    if total_failed > 0:
        logger.error("Some chunks failed to ingest. Check logs above.")
        sys.exit(1)

    logger.info("Knowledge base build complete.")


if __name__ == "__main__":
    main()
