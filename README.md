# Pluma

A free, offline reviewer-generator for students. Upload a lesson document and get a deck of fill-in-the-blank flashcards built from its factual sentences.

## Description

Pluma turns a lesson file into study questions. It extracts the text, picks the sentences that state factual claims, and generates a cloze (fill-in-the-blank) question from each one that has a concept worth blanking. The result is a set of flashcards you can review and prune.

Everything runs locally. Question generation is rule-based: there are no LLM API calls and no generated content that cannot be traced back to the source. Every answer is a term taken word-for-word from the original sentence, so a student can verify any answer against the material. Question quality is a relative judgment, the pipeline prefers the most specific, least generic concept available in a sentence and declines to make a card at all when only weak options exist, rather than an attempt to measure "importance" absolutely.

### Features

- Accepts text-based PDF and PPTX files.
- Runs a deterministic pipeline: extract, clean, split, analyze, score, generate, validate, dedupe, store, serve.
- Produces cloze questions with word-for-word traceable answers.
- Picks the most specific blankable concept: candidates are ranked by kind and rarity, and diagram labels (e.g. `Process A`, `R1`) or concept fragments are never blanked.
- Validates each question structurally (word length, ambiguous blanks, answer leakage, bare-pronoun subjects, fragment answers) before serving it.
- Removes near-duplicate cards within a deck while still allowing the same answer to appear in genuinely different questions.
- Persists everything to a local SQLite database with versioned migrations.
- Exposes a small HTTP API for creating reviewers, listing them, fetching questions, and discarding bad ones manually.

### What it is not

- No OCR. Scanned PDFs are unsupported and are rejected explicitly.
- No generative AI, paraphrasing, or LLM calls anywhere in the pipeline.
- No accounts, no cloud, no Docker setup — the API and database run on your machine.

## How it works

The pipeline stages are isolated services in the backend:

1. **Extract** — converts the uploaded file to Markdown text.
2. **Clean** — strips Markdown syntax and formatting noise before anything else sees the text.
3. **Split** — breaks the cleaned text into sentences.
4. **Analyze** — runs each sentence through spaCy for part-of-speech tags, dependency parsing, named entities, and noun chunks, and surfaces the spans worth blanking (entities, phrases, nouns) with their structural checks already applied.
5. **Score** — decides which sentences are worth turning into a question and rejects fragments, labels, equations, and boilerplate before Generate ever sees them.
6. **Generate** — ranks the candidate spans of each kept sentence by kind and rarity (using an offline word-frequency table as a genericness signal) and blanks the best one. If a sentence's only candidates are generic or diagram labels, no question is produced — an omitted card beats a weak one.
7. **Validate** — rejects questions that are structurally unsound: too short or too long, ambiguous or leaking answers, a bare-pronoun subject, or an answer that fragments a larger concept span.
8. **Dedupe** — compares each card's surface against earlier cards in the same document and hides near-duplicates, so duplicated slide content does not appear twice while the same answer in different questions is kept.
9. **Store** — persists the kept sentences and every generated question with its validation result and duplicate status.
10. **Serve** — the API returns the valid, non-discarded questions as a flashcard deck.

The backend is FastAPI, with spaCy for language analysis, MarkItDown for extraction, `wordfreq` for offline frequency-based candidate ranking, and SQLite accessed through the SQLAlchemy ORM with Alembic migrations. A SvelteKit frontend is planned but not yet built; the API and its interactive documentation are currently the way to use the application.

## Requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/) for dependency management

## Installation

```bash
uv sync
```

This installs the backend dependencies, including the spaCy English model.

## Usage

Run everything from the repository root. The backend imports the `core` package, so launching from inside `core/` does not work.

First create the database schema:

```bash
uv run alembic -c core/alembic.ini upgrade head
```

Then start the API server:

```bash
uv run fastapi dev core/main.py
```

The interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### API

All responses use the `{ "detail": "..." }` shape for errors.

#### Create a reviewer from a file

```bash
curl -X POST http://127.0.0.1:8000/reviewers \
  -F "file=@lesson.pdf"
```

Returns `201 Created` with the reviewer and its deck. A valid upload that happens to yield no questions still creates the reviewer, with an empty `questions` list.

```json
{
  "id": 1,
  "filename": "lesson.pdf",
  "created_at": "2026-08-31T12:33:18",
  "questions": [
    {
      "id": 1,
      "sentence_id": 1,
      "sentence_text": "Ribosomes synthesize proteins.",
      "text": "Ribosomes synthesize _____.",
      "answer": "proteins",
      "reason": "noun",
      "is_valid": true,
      "discarded": false
    }
  ]
}
```

#### List reviewers

```bash
curl http://127.0.0.1:8000/reviewers
```

Returns a list of reviewer summaries, each with the count of servable questions.

#### Get a reviewer's questions

```bash
curl http://127.0.0.1:8000/reviewers/1/questions
```

Returns only questions that passed validation and have not been discarded, in document order. Returns `404` if the reviewer does not exist.

#### Discard or restore a question

```bash
curl -X PATCH http://127.0.0.1:8000/questions/1 \
  -H "Content-Type: application/json" \
  -d '{"discarded": true}'
```

Discarded questions are hidden from the reviewer's deck. Setting `discarded` back to `false` restores them.

## Testing

From the repository root:

```bash
uv run pytest
```

Tests use isolated in-memory databases and do not require a running server or an external database.

## Roadmap

Current status: the full V1 pipeline is implemented from extraction through serving.

Planned and deferred work:

- User interface for uploading lessons, listing reviewers, and flipping flashcards.
- Manual question discard in the UI (the API supports it today).
- OCR / scanned PDF support.
- Multi-module input and cross-module statistics.
- Multiple-choice questions and distractor generation.
- WH-question generation.

## Contributing

Contributions are welcome. The project follows a strict tests-first workflow: write the tests for a change before the implementation, keep commits atomic, and run the full suite before finishing. Read `AGENTS.md` at the repository root before making changes, since it documents the architecture decisions and scope that the project intentionally keeps.
