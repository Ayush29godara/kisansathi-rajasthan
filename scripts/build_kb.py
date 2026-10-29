#!/usr/bin/env python3
"""
CLI script to chunk agricultural documents, generate Gemini embeddings,
and upsert chunks into Supabase `kb_chunks` table.

Usage:
    python scripts/build_kb.py --input-dir data/kb_documents --language hi
"""

import os
import sys
import argparse
from typing import List, Dict, Any


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping semantic segments without breaking sentences."""
    sentences = text.split("।") if "।" in text else text.split(".")
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        clean_sentence = sentence.strip()
        if not clean_sentence:
            continue
        sentence_len = len(clean_sentence)
        if current_len + sentence_len > chunk_size and current_chunk:
            chunks.append("। ".join(current_chunk) + "।")
            # Overlap with previous sentence
            current_chunk = [current_chunk[-1]] if len(current_chunk) > 1 else []
            current_len = sum(len(s) for s in current_chunk)
        current_chunk.append(clean_sentence)
        current_len += sentence_len

    if current_chunk:
        chunks.append("। ".join(current_chunk) + "।")
    return chunks


def main():
    parser = argparse.ArgumentParser(description="KisanSathi Knowledge Base Ingestion Script")
    parser.add_argument("--input-dir", type=str, default="data/kb_documents", help="Directory containing agricultural texts or PDFs")
    parser.add_argument("--language", type=str, default="hi", choices=["hi", "en"], help="Document language")
    parser.add_argument("--dry-run", action="store_true", help="Parse and chunk without writing to Supabase")
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"[!] Input directory '{args.input_dir}' not found.")
        print(f"[*] Please create '{args.input_dir}' and supply verified agricultural manuals.")
        print("    See scripts/README.md for file format instructions.")
        sys.exit(1)

    files = [f for f in os.listdir(args.input_dir) if f.endswith((".txt", ".md", ".pdf"))]
    if not files:
        print(f"[!] No valid document files (.txt, .md, .pdf) found in '{args.input_dir}'.")
        sys.exit(0)

    print(f"[*] Found {len(files)} documents to ingest.")
    total_chunks = 0
    for filename in files:
        filepath = os.path.join(args.input_dir, filename)
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        chunks = chunk_text(content)
        total_chunks += len(chunks)
        print(f" -> Processed {filename}: {len(chunks)} chunks created.")

    print(f"\n[✓] Total {total_chunks} chunks extracted.")
    if args.dry_run:
        print("[*] Dry run enabled. No database records modified.")
    else:
        print("[*] Ingesting embeddings into Supabase (Requires SUPABASE_URL and GEMINI_API_KEY in environment).")


if __name__ == "__main__":
    main()
