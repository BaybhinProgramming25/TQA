# TranscriptQA

A web application that lets Stony Brook CS students upload their academic transcripts and ask natural language questions about their records. The full transcript is supplied as context on every question, so answers are grounded in the document itself and streamed back in real time.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) + Uvicorn |
| Database | MySQL + SQLAlchemy |
| PDF Extraction | LangChain `PyPDFLoader` |
| LLM | OpenAI `gpt-4o-mini` |
| LLM Framework | LangChain |
| Auth | JWT + bcrypt |
| Infrastructure | Docker + Docker Compose |

## Features

- Upload a PDF transcript — text is extracted once at upload and stored
- Ask natural language questions with streaming responses — "What's my cumulative GPA?", "What is this class about", "What classes did I take this semester?"
- Conversation memory — follow-up questions work naturally
- Question rewriting — vague follow-ups ("what about that one?") are expanded into standalone questions before answering
- Smart routing — general chit-chat skips the transcript context entirely
- Clear chat history per document
- RAGAS evaluation harness measuring faithfulness and answer relevancy

## Architecture

```
Browser → Frontend container (React)
                        → /api/* → Backend container (FastAPI)
                        → MySQL (users, documents, messages, transcript text)
```

### Pipeline

1. User uploads a PDF transcript
2. Backend extracts the full text with `PyPDFLoader` and stores it on the document row
3. On each query, the question is rewritten against chat history into a standalone question
4. A classifier decides whether the question is transcript-related
5. If yes — the **entire** transcript is passed as context to `gpt-4o-mini`; if no, a plain chat prompt is used
6. The answer streams back token by token via SSE

There is no retrieval step. The transcript is small enough to fit in the model's
context window, so it is sent in full rather than chunked, embedded, and searched.
This trades token cost per question for the removal of retrieval as a failure mode.

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

DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@mysql:3306/${MYSQL_DATABASE}
FRONTEND_URL=https://yourdomain.com

UPLOADS_DIR=/uploads
```

### Running Locally

```bash
docker compose up -d --build
```

The frontend will be available at `http://localhost:8080` and the backend at `http://localhost:3000`.

## Evaluation

The testing harness uses RAGAS to score the pipeline on generated test questions.
`evaluate.py` drives the real pipeline (`query_stream`) rather than reimplementing
it, so the rewrite and classify steps are measured too.

The harness runs on the host, not in Docker. It needs the backend dependencies
plus `ragas`, which is not part of the backend runtime requirements, and reads
`OPENAI_API_KEY` from `backend/.env`:

```bash
pip install -r backend/requirements.txt
pip install ragas
```

```bash
# Generate test questions from a transcript
# --count must not exceed the number of chunks the transcript yields
python testing/generate_pairs.py --pdf path/to/transcript.pdf --count 50 --seed 42

# Run RAGAS evaluation
python testing/evaluate.py --pdf path/to/transcript.pdf
```

Results are saved to `testing/results.json`, including per-question rows so a low
average can be traced back to the answer that caused it.

`generate_pairs.py` splits the transcript into semester- and course-level chunks
and writes one question per sampled chunk, which keeps the question set spread
evenly across every semester. This is a test-authoring tool only — the
application itself never chunks anything, and `evaluate.py` reads only the
`question` field.

### Baseline

50 questions against a real transcript, `gpt-4o-mini`:

| Metric | Score |
|---|---|
| faithfulness | 0.91 |
| answer relevancy | 0.70 |

Not comparable to retrieval-based baselines: supplying the whole transcript as
context removes retrieval error as a failure mode, so faithfulness is measured
against an easier target than it would be under a retrieval pipeline. Question
generation is non-deterministic, so expect movement between runs.

### Interpreting the metrics

- **faithfulness** — are the answer's claims supported by the context. With the
  whole transcript in context this is an easier test than it was under retrieval,
  so scores are high and not comparable to retrieval-based baselines.
- **answer relevancy** — does the answer address the question. Scores here are
  held down by the question generator's prompt, which deliberately asks for vague,
  student-like phrasing; specific correct answers to vague questions score lower.

Question generation is non-deterministic, so numbers shift between runs. For a
stable baseline, generate a question set once and commit it.
