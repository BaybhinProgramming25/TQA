"""Build a FAISS index locally from a transcript PDF without needing the full backend running."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

os.environ["DATA_DIR"] = str(BACKEND_DIR / "data")

from helpers.getchunks import parse_pdf
from rag import init_db


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a FAISS index from a transcript PDF.")
    parser.add_argument("--pdf", required=True, help="Path to the transcript PDF.")
    parser.add_argument("--index_key", required=True, help="Index key in the format <email>_<filename>")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set in backend/.env")
        return 1

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF not found at '{pdf_path}'")
        return 1

    print(f"Parsing transcript: {pdf_path.name}")
    pdf_bytes = pdf_path.read_bytes()
    chunks = parse_pdf(pdf_bytes)
    print(f"Found {len(chunks)} chunks")

    print(f"Building FAISS index for key: {args.index_key}")
    init_db(chunks, args.index_key, api_key)
    print(f"Index saved to {BACKEND_DIR / 'data' / f'faiss_index_{args.index_key}'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
