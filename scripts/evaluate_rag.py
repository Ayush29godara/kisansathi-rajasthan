#!/usr/bin/env python3
"""
RAG Evaluation Pipeline: Gemini-Alone vs Gemini+RAG Knowledge Base.

Runs a side-by-side benchmark comparing ungrounded LLM responses against
RAG-retrieved grounded responses for human scoring and accuracy evaluation.

Usage:
    python scripts/evaluate_rag.py --eval-file data/rag_eval_questions.csv --output data/rag_evaluation_results.csv
"""

import os
import sys
import csv
import asyncio
import argparse
import logging
from typing import List, Dict, Any

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

import httpx
from services.intent import classify_intent
from services.rag import retrieve_relevant_chunks
from services.llm import generate_grounded_answer
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_rag")

settings = get_settings()

GEMINI_GENERATE_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)


async def call_gemini_alone(question: str, language: str) -> str:
    """Generate answer using Gemini alone without any RAG context."""
    if not settings.GEMINI_API_KEY or settings.ENVIRONMENT == "test":
        return (
            f"[Baseline Ungrounded Response ({language})]: General advice regarding: {question}"
        )

    prompt = (
        f"You are an agricultural advisor. Answer this question in {'Hindi' if language == 'hi' else 'English'}:\n"
        f"{question}"
    )

    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GEMINI_GENERATE_ENDPOINT,
                json=request_body,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts).strip()
    except Exception as exc:
        return f"[Gemini Error: {str(exc)[:100]}]"


async def evaluate_single_question(item: Dict[str, str]) -> Dict[str, Any]:
    """Run intent classification, Gemini-alone, and Gemini+RAG for one question."""
    question = item.get("question", "").strip()
    language = item.get("language", "hi").strip()
    expected_intent = item.get("expected_intent", "general").strip()

    detected_intent = classify_intent(question)

    # 1. Gemini Alone (ungrounded)
    alone_task = asyncio.create_task(call_gemini_alone(question, language))

    # 2. Gemini + RAG (grounded)
    sources = await retrieve_relevant_chunks(question, limit=4)
    rag_answer = await generate_grounded_answer(
        question=question,
        sources=sources,
        language=language,
    )

    alone_answer = await alone_task

    sources_summary = "; ".join([f"[{s.doc_title} | {s.source}]" for s in sources])

    return {
        "question": question,
        "language": language,
        "expected_intent": expected_intent,
        "detected_intent": detected_intent,
        "gemini_alone_answer": alone_answer,
        "gemini_rag_answer": rag_answer,
        "sources_used": sources_summary,
        "num_sources": len(sources),
    }


async def run_evaluation(eval_file: str, output_file: str) -> None:
    """Read questions CSV, run benchmark, write comparison CSV, and report metrics."""
    if not os.path.exists(eval_file):
        logger.error("Evaluation question file '%s' not found.", eval_file)
        sys.exit(1)

    questions: List[Dict[str, str]] = []
    with open(eval_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("question"):
                questions.append(row)

    logger.info("Loaded %d questions from %s", len(questions), eval_file)
    logger.info("Executing Gemini-Alone vs Gemini+RAG side-by-side benchmark...")

    results: List[Dict[str, Any]] = []
    for idx, q_item in enumerate(questions, start=1):
        logger.info("  [%d/%d] Processing: %s", idx, len(questions), q_item["question"][:50])
        res = await evaluate_single_question(q_item)
        results.append(res)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    # Write output CSV
    fieldnames = [
        "question",
        "language",
        "expected_intent",
        "detected_intent",
        "gemini_alone_answer",
        "gemini_rag_answer",
        "sources_used",
        "num_sources",
    ]
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info("Saved side-by-side evaluation outputs to: %s", output_file)

    # Compute summary metrics
    total = len(results)
    intent_matches = sum(1 for r in results if r["detected_intent"] == r["expected_intent"])
    citations_present = sum(1 for r in results if r["num_sources"] > 0)
    kvk_fallback_count = sum(
        1
        for r in results
        if "KVK" in r["gemini_rag_answer"]
        or "कृषि विज्ञान केंद्र" in r["gemini_rag_answer"]
    )

    print("\n" + "=" * 60)
    print("           RAG EVALUATION BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Total Questions Evaluated       : {total}")
    print(f"Intent Classification Accuracy  : {(intent_matches / total) * 100:.1f}% ({intent_matches}/{total})")
    print(f"RAG Grounding Citation Rate     : {(citations_present / total) * 100:.1f}% ({citations_present}/{total})")
    print(f"Safety KVK Fallback Invocations : {kvk_fallback_count} time(s)")
    print(f"Detailed output stored at       : {output_file}")
    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG Grounding vs Unassisted LLM")
    parser.add_argument(
        "--eval-file",
        type=str,
        default="data/rag_eval_questions.csv",
        help="Path to input questions CSV",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/rag_evaluation_results.csv",
        help="Path to save evaluation output CSV",
    )
    args = parser.parse_args()

    asyncio.run(run_evaluation(args.eval_file, args.output))


if __name__ == "__main__":
    main()
