"""Generate question/chunk pairs from a transcript PDF for RAG evaluation."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
from helpers.getchunks import parse_pdf

OUTPUT_PATH = Path(__file__).parent / "prompt_pairs.jsonl"
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.2

QUESTION_GEN_TEMPLATE = """\
You are generating ONE realistic question to test a RAG assistant that answers questions about a student's academic transcript.

You will be given an excerpt from the transcript. The excerpt should be sufficient to answer the question, but the student asking the question has NOT read the excerpt — they're asking from memory or curiosity about their own record.

Write like a real student.

Output only one question (1-2 sentences).

Hard requirements

Distance from the excerpt: Write the question using the student's goal and situation, not the excerpt's vocabulary.

Do NOT mirror the excerpt's structure (e.g., don't say "what are the courses listed for semester X").

Messy realism: Include at least one realistic human trait:
missing detail, mild confusion, shorthand, or a practical constraint (timeline, GPA concern, registration deadline).

Not overly complete: Real students rarely include every parameter. Leave some ambiguity.

Still answerable: The question must be answerable from the excerpt alone. Do NOT use vague references like "that class" or "last semester" without enough detail to identify which one (e.g. include the subject name or the specific year). Ambiguity in tone is fine — ambiguity in identity is not.

Not trivia / not "this exact line": Avoid narrow phrasing that only makes sense if you saw the specific line.

No citations, no field labels, no direct quotes from the excerpt.

Length: Aim for 15-30 words; allow up to 40 if needed to sound natural. Never exceed 45.

"Human-ness" style guide

Prefer: "Did I pass...?", "What grade did I get in...?", "How many credits did I take...?",
"Which semester was my best?", "Do I have enough credits to...?", "What was my GPA when...?"

Use natural tone — a student messaging their advisor or searching their student portal.

Excerpt:

{chunk}
"""


@dataclass(frozen=True)
class Chunk:
    text: str
    chunk_type: str
    metadata: dict


def collect_chunks(pdf_path: Path) -> list[Chunk]:
    pdf_bytes = pdf_path.read_bytes()
    raw_chunks = parse_pdf(pdf_bytes)
    chunks = []
    for text, metadata in raw_chunks:
        chunks.append(Chunk(
            text=text,
            chunk_type=metadata.get("type", "unknown"),
            metadata=metadata,
        ))
    return chunks


def select_chunks(chunks: list[Chunk], count: int, seed: int | None) -> list[Chunk]:
    if count > len(chunks):
        raise ValueError(f"Requested {count} chunks, but only {len(chunks)} available.")
    return random.Random(seed).sample(chunks, count)


def generate_question(llm: ChatOpenAI, prompt: PromptTemplate, chunk_text: str) -> str:
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"chunk": chunk_text}).strip()


def write_pairs(path: Path, pairs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")


def main() -> int:
    load_dotenv(BACKEND_DIR / ".env")

    parser = argparse.ArgumentParser(
        description="Generate question/chunk pairs from a transcript PDF."
    )
    parser.add_argument("--pdf", required=True, help="Path to the transcript PDF file.")
    parser.add_argument(
        "--types",
        default="all",
        help="Comma-separated chunk types to include: semester, course, student, or 'all' (default).",
    )
    parser.add_argument("--count", type=int, default=50, help="Number of pairs to generate.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible sampling.")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSONL path.")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set in .env")
        return 1

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF not found at '{pdf_path}'")
        return 1

    print(f"Parsing transcript: {pdf_path.name}")
    chunks = collect_chunks(pdf_path)
    print(f"Found {len(chunks)} chunks total")

    if args.types.strip().lower() != "all":
        allowed = {t.strip() for t in args.types.split(",")}
        chunks = [c for c in chunks if c.chunk_type in allowed]
        print(f"Filtered to {len(chunks)} chunks of types: {allowed}")

    if not chunks:
        print("Error: No chunks matched the requested types.")
        return 1

    sampled = select_chunks(chunks, args.count, args.seed)
    print(f"Generating {len(sampled)} questions...")

    llm = ChatOpenAI(api_key=api_key, model=MODEL, temperature=TEMPERATURE)
    prompt = PromptTemplate.from_template(QUESTION_GEN_TEMPLATE)

    pairs: list[dict] = []
    for i, chunk in enumerate(sampled, 1):
        print(f"Generating Prompt #{i} (type={chunk.chunk_type})...")
        question = generate_question(llm, prompt, chunk.text)
        pairs.append({
            "question": question,
            "chunk": chunk.text,
            "chunk_type": chunk.chunk_type,
            "metadata": chunk.metadata,
        })

    output_path = Path(args.output)
    write_pairs(output_path, pairs)
    print(f"Saved {len(pairs)} pairs to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
