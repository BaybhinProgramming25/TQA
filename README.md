# TQA — Transcript Q&A

A RAG-powered web application that lets Stony Brook CS students upload their academic transcripts and ask natural language questions about their records. Answers are grounded in the transcript content via semantic search and streamed back in real time.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) + Uvicorn |
| Database | MySQL + SQLAlchemy |
| Vector Store | FAISS |
| Embeddings | OpenAI `text-embedding-3-large` |
| LLM | OpenAI `gpt-4o-mini` |
| RAG Framework | LangChain |
| Auth | JWT + bcrypt |
| Infrastructure | Docker + Docker Compose |

## Features

- Upload a PDF transcript — parsed and indexed automatically into a FAISS vector store
- Ask natural language questions with streaming responses — "What's my cumulative GPA?", "What is this class about", "What classes did I take this semester?"
- Conversation memory — follow-up questions work naturally
- Smart routing — general questions bypass the RAG pipeline entirely
- Source citations — each answer links back to the page in the transcript it came from
- Export transcript to a formatted Excel (.xlsx) file
- Clear chat history per document
- RAGAS evaluation harness with 86% faithfulness and 61% answer relevancy across 50 test queries

## Architecture

```
Browser → Frontend container (React)
                        → /api/* → Backend container (FastAPI)
                        → MySQL (users, documents, messages)
                        → FAISS index (vector embeddings)
```

### RAG Pipeline

1. User uploads a PDF transcript
2. Backend parses it into structured chunks (semester, course, student level)
3. Chunks are embedded via OpenAI and saved to a FAISS index on disk
4. On each query, a classifier determines if the question is transcript-related
5. If yes — FAISS retrieves the top matching chunk, context is passed to Claude Sonnet
6. Answer streams back token by token via SSE with a source page citation

## Setup

### Prerequisites

- Docker + Docker Compose
- OpenAI API key

### Environment Variables

Create a `backend/.env` file:

```env
JWT_SECRET_KEY=your-secret-key

OPENAI_API_KEY=sk-...

MYSQL_ROOT_PASSWORD=yourpassword
MYSQL_DATABASE=yourdbname
MYSQL_USER=yourusername
MYSQL_PASSWORD=yourpassword

DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@tqa-mysql:3306/${MYSQL_DATABASE}
FRONTEND_URL=https://yourdomain.com

UPLOADS_DIR=/uploads
DATA_DIR=/app/data
```

### Running Locally

```bash
docker compose up -d --build
```

The frontend will be available at `http://localhost:8080` and the backend at `http://localhost:3000`.

## Evaluation

The testing harness uses RAGAS to evaluate the RAG pipeline on 50 generated test queries.

```bash
# Build the FAISS index locally
python testing/build_index.py --pdf path/to/transcript.pdf --index_key email@example.com_transcript.pdf

# Generate test question/chunk pairs
python testing/generate_pairs.py --pdf path/to/transcript.pdf --count {count_amount <= 56} --seed {seed_value}

# Run RAGAS evaluation
python testing/evaluate.py --index_key email@example.com_transcript.pdf
```

Results are saved to `testing/results.json`.
