# Pluma

This file orients any AI coding agent (or human) working in this repo. Read this before making changes, especially before adding a feature or "fixing" something that looks incomplete — several things below are deliberate scope decisions, not oversights.

## What pluma is

A free, offline reviewer-generator for students. It takes a lesson document, extracts factual sentences, and turns them into flashcard-style study questions.

**Core design decision: pluma uses classical/rule-based NLP, not generative AI.** No LLM API calls anywhere in the question-generation services. This is intentional — it's the entire point of the project (a free alternative to paywalled AI-powered reviewer apps), not a temporary limitation to "upgrade" later. Every generated question's answer must be traceable, word-for-word, back to the source sentence. Do not introduce paraphrase-based or generative question creation into these services.

## Repo structure

```
pluma/
├── core/          FastAPI backend + NLP services
│   │
│   │── main.py
│   │── api/       route handlers (future — Serve stage)
│   │── services/  extract, clean, split, analyze, score, generate, validate, store
│   │── models/    SQLAlchemy ORM models (one file per model)
│   │── schemas/   future Pydantic API request/response schemas (added with Serve)
│   │── db/        session.py
│   │── alembic/   versioned database migrations
│   └── tests/
├── ui/
│   │── src/       SvelteKit frontend
│   └── tests/
├── AGENTS.md
└── README.md
```

## Development workflow

These rules govern _how_ work gets done in this repo, for every feature, in both `core/` and `ui/`. They apply regardless of which service stage or page is being built.

Dependency management uses **uv**, not pip/venv directly. Do not manually create a `.venv`, do not run `pip install`, and do not maintain a `requirements.txt` — uv manages the virtual environment and dependency resolution from `pyproject.toml` and `uv.lock`.

- Run `uv sync` to install/update dependencies before running anything in `core/`.
- Use `uv run <command>` to execute the server, scripts, or tests within that environment (e.g. `uv run pytest`, `uv run fastapi dev main.py`).
- When a feature genuinely needs a new dependency, add it with `uv add <package>` (or `uv add --dev <package>` for test/dev-only tools) so `pyproject.toml` and `uv.lock` stay in sync. Do not hand-edit the dependency list in `pyproject.toml`.
- `uv.lock` should be committed. Don't regenerate it wholesale for an unrelated change — if `uv sync` modifies the lockfile as a side effect of an unrelated feature, that's worth a second look, not an automatic commit.

### One feature at a time

- Do not implement multiple features, service stages, or UI pages in a single pass.
- A feature is not started until the previous one is working and its tests pass.
- If a task description spans more than one feature, implement the first one, stop, and confirm before continuing to the next. Do not silently keep going.

### Tests first, always

- Write tests before writing any implementation code — for every feature, in both `core/` and `ui/`. UI features need tests written before the component/logic exists too, not only backend logic.
- Test coverage for a feature should include:
  - The core/happy-path action the feature exists to perform.
  - Edge cases that could realistically occur given real input (e.g. empty file, malformed sentence, missing field).
- Do not write tests for scenarios that cannot occur or that don't add real confidence. Test count is not a goal — relevant coverage is.
- After tests are written, implement code and keep iterating until the tests pass.
- **Never edit a test to make it pass.** If a test seems wrong once implementation is underway, stop and ask rather than changing the test to fit the code. A test that gets quietly rewritten to match broken behavior defeats the entire point of writing it first.
- Before declaring a feature done, run the **full** test suite (`uv run pytest` for `core/`, the ui test command for `ui/`) — not just the tests written for this feature. A change to one service stage or component can break something elsewhere that wouldn't show up by running only the new tests.

### Commits

- Commits must be atomic: one logical change per commit. Don't bundle a bug fix with a new feature, or a refactor with new functionality, in the same commit.
  A commit should do one thing. That is, it should implement one feature, or one bugfix, or refactor one aspect of the codebase.
- Not every edit deserves its own commit. Trivial changes (formatting, typo fixes) don't need a standalone commit unless that edit is the entire scope of the change being made — fold them into the commit they're actually part of.
- Commit messages should state what changed and why, not just which files were touched.
- If possible, turn the commit into multiple non-breaking changes. So, for example, if you need foo to call bar.baz(), one commit implements and exposes baz but doesn't actually call it, (Explain why you're doing it, though!) and the second commit actually calls the function. In a pull request, these patches get submitted together, but they are separate commits.
  - Note: I (the project owner) don't typically do this at the time I'm writing code — I write the code I want and then rebase into multiple commits afterward. That's a description of my own habit, not an instruction to the agent. As an agent, aim to commit atomically as you go rather than writing everything first and restructuring history after — don't run interactive rebases on your own initiative.
- An exception is made for unit tests. If you implement a feature, add the unit tests that test your feature to the same commit. This keeps the CI from breaking needlessly.
- Explain what you're doing and why. If you're the creator of the project and are working on a personal project, "because I said so" is just fine. If you're implementing some subtle functionality on some weird device driver bug in the Linux kernel, you might need multiple paragraphs explaining the bug and how your approach solves it.
- Do not list the changes, make sure explanations are in paragraph form

## Tech stack

- **Backend:** FastAPI (Python). Chosen specifically because the NLP tooling (spaCy, MarkItDown) is Python-native — backend and services run in the same process, no cross-language calls.
- **Dependency management:** uv (see "Development workflow" above for commands and rules — don't fall back to pip or manual venvs).
- **NLP:** spaCy (`en_core_web_sm`) for sentence structure, POS tagging, and NER. Extraction via `markitdown`.
- **Frontend:** SvelteKit. Chosen over React because the UI is CRUD-shaped (upload, list, flashcard flip), not state-heavy enough to need a large component ecosystem.
- **Storage:** SQLite via SQLAlchemy ORM, with Alembic for versioned migrations and Pydantic for API request/response schemas at the API boundary only. Don't introduce Postgres or any other DB engine without an explicit reason tied to actual multi-user concurrency needs.

## Coding guidelines

- Keep the codebase simple and consistent with the project's current scope. Prefer straightforward implementations over abstractions that are not yet justified by the application.
- Do not introduce a dependency when the standard library or an existing dependency already solves the problem adequately. Any new dependency must have a clear reason and should not expand the NLP services without a corresponding test demonstrating the problem it solves. **SQLAlchemy and Alembic are explicit exceptions — the project's intentional persistence stack (ORM plus versioned migrations).** The exception does not extend to NLP/scoring logic, where the test-justifying-dependency rule still applies.
- Do not refactor unrelated code while implementing a feature. Make the smallest coherent change that completes the requested work.
- Before modifying code, inspect the existing implementation and follow its established patterns unless there is a concrete reason to change them.
- Do not assume a library, configuration file, utility, or architectural layer exists. Verify it in the repository first.
- Keep functions and modules focused on a single responsibility. Do not create layers, wrappers, repositories, services, or abstractions purely for architectural appearance — introduce them only when they provide a meaningful separation of responsibility.
- Use clear names instead of comments that explain poorly named code. Comments should explain why something is done when the reason is not obvious from the implementation, not restate what the code already says.
- Do not silently swallow exceptions. Handle expected errors explicitly and allow unexpected errors to remain visible during development.

### FastAPI

- FastAPI is responsible for API routing, request validation, application logic, database access, and returning data to the frontend.
- Keep route handlers thin. A route handler should primarily receive and validate the request, call the appropriate application logic, and return the response. Do not put substantial business logic directly inside route functions.
- Use Pydantic schemas for API request and response data. Do not expose database models directly as API responses.
- Use FastAPI dependency injection for shared concerns such as database sessions and request-level dependencies.
- Use explicit response models and appropriate HTTP status codes. Do not return 200 OK for every operation when another status code more accurately represents the result.
- Use 201 for successful resource creation and 204 when an operation succeeds without returning a response body. Use 400, 401, 403, and 404 appropriately when applicable.
- API errors should have a predictable response structure so the SvelteKit frontend can handle them consistently.
- Do not expose stack traces, database errors, internal implementation details, or sensitive information through API responses.
- Keep the NLP services independent from HTTP concerns. Service stages should not depend on FastAPI request objects, response objects, or HTTP-specific exceptions. The API layer should call the services and translate their results into API responses.
- Keep database access separate from the NLP services. The services should be independently testable without requiring a running server or external database. Store tests intentionally use isolated in-memory SQLite; the NLP services never touch the database.

### SvelteKit SPA frontend

- SvelteKit is used as a client-side SPA. The frontend is responsible for presentation, user interaction, client-side state, routing, and communicating with the FastAPI API.
- Do not put backend business logic or NLP logic in Svelte components. All reviewer generation and validation decisions belong to the FastAPI backend.
- Keep API communication separate from presentation code. Do not scatter complex or repeated fetch() implementations throughout components.
- Do not create every directory preemptively. Add a module only when the application has a real need for it.
- Components should primarily handle presentation and user interaction. Move reusable API calls, complex state logic, and reusable behavior into appropriate modules.
- Keep components reasonably focused. Extract a component when it has an independent responsibility or becomes difficult to understand, not simply because it reaches an arbitrary line count.
- Use TypeScript throughout the frontend. Avoid any. When a value is genuinely unknown, use unknown and narrow it appropriately.
- Define types for API contracts, component props, and important application state. Do not duplicate the same API response shape in multiple components.

### API communication

- Treat the FastAPI API as the contract between core/ and ui/.
- Centralize the API base URL rather than hardcoding it throughout the frontend.
- Do not hardcode environment-specific URLs in components.
- Use a small API client abstraction for repeated concerns such as constructing requests, parsing JSON, and handling non-success responses. Do not build a large API framework around fetch() unless the application actually requires one.
- Frontend API calls should explicitly handle loading, success, empty, and error states where those states are relevant to the UI.
- Do not silently ignore failed requests. Show an appropriate user-facing error state and preserve enough information for development debugging.
- When an API response changes, update the backend schema, frontend type, API client, and affected UI together.
- Avoid breaking API changes unless they are intentional and all consumers are updated.

### State management

- Prefer local Svelte state when state is only relevant to one component or page.
- Use shared state only when multiple unrelated components genuinely need the same state.
- Do not introduce a state-management library unless the application's actual complexity justifies it.
- Do not duplicate server state unnecessarily in multiple frontend stores.
- The backend remains the source of truth for persisted reviewer data. Frontend state should represent what the user currently needs to interact with the application.

## Pipeline stages (in order)

Each stage should stay isolated and independently testable. Don't collapse stages together.

1. **Extract** — `markitdown` converts the uploaded file to Markdown text.
2. **Clean** — strip Markdown syntax (headings, bullets, bold/italic markers, table pipes) before anything downstream sees the text. Headings are useful signal _before_ stripping (skip lines starting with `#` as likely non-sentence filler) — don't discard that signal, just don't let raw syntax reach spaCy.
3. **Split** — break cleaned text into sentences.
4. **Analyze** — run each sentence through spaCy: POS tags, dependency parse, named entities.
5. **Score** — rule-based filter for which sentences are worth turning into a question (contains a named entity or clear factual claim; reject boilerplate/filler).
6. **Generate** — cloze (fill-in-the-blank) question generation ONLY for V1. Do not implement WH-question rewriting (do-support / verb tense transformation is unsolved here) or MCQ distractor generation until V1's cloze services are validated.
7. **Validate** — reject a generated question if any of these fail:
   - the blanked term does not reappear elsewhere in the same sentence (answer-leakage check)
   - the sentence's subject is a bare pronoun with no clear referent
   - sentence word count is below ~5–6 or above ~25–30
   - the blanked term appears more than once in the sentence (ambiguous blank)
8. **Store** — persist sentence + question + validation result to SQLite via SQLAlchemy. Persists the sentences the caller supplies (Score-kept ones, per orchestration) and every generated question with its validation result; it does not filter, score, or validate.
9. **Serve** — API returns questions to the frontend for flashcard mode.

## V1 scope — do not exceed without explicit instruction

**In scope:**

- File formats: **PDF and PPTX only.** PDF extraction is **text-based PDFs only** — no OCR, no scanned-document support.
- Single module (single uploaded file) as input. No cross-module/multi-module aggregation yet.
- One question type: cloze / fill-in-the-blank.
- One study mode: flashcard (identification mode can reuse the same question objects later; don't build it as a separate generation path).
- A manual "discard this question" action in the UI — this is intentional quality control given imperfect automated validation, not a stopgap.

**Explicitly deferred — do not build unless asked:**

- OCR / scanned PDF support
- Multi-module input and cross-module statistics
- MCQ generation and distractor sourcing (WordNet/embeddings)
- WH-question generation
- User accounts / auth
- Docker

## PDF handling detail

After extraction, check output length against page count. If it's suspiciously short (rough heuristic: well under ~50 characters per page), treat it as a likely-scanned PDF and return a clear error to the user ("this looks like a scanned PDF, which isn't supported yet") instead of silently producing empty or near-empty results.

## Testing conventions

See "Development workflow" above for the general test-first rules. Specific to this pipeline of services:

- Validation (step 7) needs one test case per rejection rule, using a real example sentence — not a placeholder string.
- Maintain a small hand-labeled regression set (real sentences with expected good/bad question outcomes) under `core/tests/`. Run it after any change to scoring, generation, or validation logic — this is how "did this change help or hurt" gets answered, not by eyeballing.
- Don't add new dependencies to the services (new NLP libraries, scoring methods) without a corresponding test showing the specific problem it solves.

## Running locally

Run everything from the repository root, not from `core/` — the backend imports the `core` package, so launching from inside `core/` fails to import it. The database lives at `core/pluma.db`, resolved from the repository layout so it does not depend on the current working directory; both the application and Alembic always target that same file.

```bash
uv sync
uv run alembic -c core/alembic.ini upgrade head   # create/migrate core/pluma.db
uv run fastapi dev core/main.py                   # launch from the repo root

cd ui
npm run dev
```