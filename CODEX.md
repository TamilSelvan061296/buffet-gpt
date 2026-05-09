# CODEX.md

Working notes for Codex when continuing work in this repository.

## Project Snapshot

`buffet-gpt` is a Warren Buffett-style chatbot grounded in Berkshire Hathaway
shareholder letters from 1977-2024. The app has three main parts:

- A Python ingestion pipeline that loads HTML/PDF letters, chunks them, embeds
  them with Voyage AI, and stores vectors in local Qdrant storage.
- A FastAPI backend that builds a LangChain agent using Anthropic chat, a Qdrant
  retrieval tool, and SQLite-backed LangGraph checkpoints for sessions.
- A Vite/React frontend that streams `/chat` responses with server-sent events.

The repository is small and still early-stage. There is no formal test suite,
formatter, or linter configured.

## Important Files

- `pyproject.toml` - Python 3.12 project dependencies.
- `src/app/main.py` - FastAPI app, lifespan setup, `/chat`, `/health`, static
  frontend serving from `frontend/dist` when present.
- `src/app/agent.py` - Agent prompt, Voyage embeddings, local Qdrant connection,
  `retrieve_context` tool, Anthropic model selection.
- `src/app/schemas.py` - `ChatRequest` Pydantic schema.
- `src/scripts/main.py` - One-shot ingestion entrypoint.
- `src/scripts/data_ingestor.py` - HTML/PDF loaders and chunker.
- `src/scripts/embedder.py` - Voyage AI embedding wrapper.
- `src/scripts/buffet_vector_store.py` - Qdrant collection creation and upsert.
- `src/scripts/config.yaml` - Absolute local paths for corpus, Qdrant, sessions,
  and embedding config.
- `src/scripts/utils/scrape_letters.py` - Berkshire letter scraper.
- `frontend/src/App.jsx` - Single-page chat UI and SSE parsing.
- `frontend/src/App.css` - Current frontend styling.
- `frontend/vite.config.js` - Dev proxy for `/chat` and `/health`.
- `test/chat.py`, `test/query.py`, `test/loader.py` - Manual smoke scripts, not
  pytest tests.

## Local Data

- `src/buffet_sink/html/` contains 1977-1997 HTML letters.
- `src/buffet_sink/pdf/` contains 1998-2024 PDF letters.
- `qdrant_storage/` contains local Qdrant data for collection `buffet_letters`.
- `sessions.db` is configured as the LangGraph checkpoint database path, but it
  may not exist until the backend runs.

`src/scripts/config.yaml` currently uses absolute paths under:

```text
/home/tamil/work/skunkworks/buffet-gpt
```

If the repo is moved, backend and ingestion config will need path cleanup.

## Runtime Requirements

Expected external API credentials:

- `ANTHROPIC_API_KEY` for `ChatAnthropic`.
- `VOYAGE_API_KEY` for `VoyageAIEmbeddings`.

The backend currently hardcodes:

```python
ChatAnthropic(model="claude-haiku-4-5", max_tokens=512)
VoyageAIEmbeddings(model=config["embeddings"]["model"])
```

The embedding vector size in config is `1024`, which must match the selected
Voyage model output dimension for collection creation and querying.

## Run Commands

Backend dev server:

```bash
uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8765
```

Frontend dev server:

```bash
cd frontend
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

Run ingestion:

```bash
python src/scripts/main.py
```

Depending on the environment, prefer running Python commands through `uv run`
if dependencies are managed by uv.

## Current Behavior

### Backend

`src/app/main.py` loads config during FastAPI lifespan, creates an
`AsyncSqliteSaver`, builds the agent, and stores it at `app.state.agent`.

`POST /chat` accepts:

```json
{
  "session_id": "string",
  "message": "string"
}
```

It streams text chunks as SSE:

```text
data: "<json-encoded text chunk>"

event: end
data:
```

Tool chunks are skipped. Text is extracted from string content or Anthropic-style
text blocks.

### Agent

The agent prompt asks the model to:

- speak as Warren Buffett in first person;
- ground substantive claims in retrieved letters;
- admit when retrieval does not cover the question;
- mention letter years casually;
- keep responses short.

The retrieval tool runs `similarity_search(query, k=4)` over local Qdrant and
serializes each document as:

```text
(YEAR) CONTENT
```

### Frontend

The React app stores a persistent `session_id` in `localStorage`, posts messages
to `/chat`, reads the response body stream, parses SSE events, and appends
decoded text chunks to the answer.

Vite proxies `/chat` and `/health` to `http://127.0.0.1:8765`.

## Known Issues And Risks

- `README.md` is minimal and does not document setup.
- `CLAUDE.md` is stale: it describes older placeholder code and should not be
  treated as current architecture.
- `src/scripts/config.yaml` uses absolute paths, which hurts portability.
- `src/scripts/main.py` logs to `logs/app.log`, but the `logs/` directory may
  not exist before running.
- Ingestion is not idempotent; repeated runs can re-embed and upsert duplicate
  chunks with new UUIDs.
- Ingestion holds the full corpus and all vectors in memory. Acceptable for the
  current corpus, but it will not scale cleanly.
- `test/query.py` expects `test/config.yaml`, which does not appear to exist.
- `test/chat.py` posts to `localhost:8080`, while Vite config expects backend
  port `8765`.
- `src/app/main.py` prints every streamed chunk to stdout, which is noisy for a
  production server.
- The frontend title says `Chat Warren Buffet`; the conventional spelling of the
  surname is `Buffett`.
- Affiliate/product cards have placeholder `href="#"` links.
- There are no automated tests for ingestion, retrieval, streaming, or frontend
  parsing.

## Suggested Next Work

1. Make config portable by deriving repo-relative paths or supporting env vars.
2. Add a backend README section with exact setup and run commands.
3. Fix manual smoke scripts so ports and config paths match the app.
4. Add basic backend tests around `/health`, request validation, and SSE parsing
   with a stubbed agent.
5. Remove or gate noisy stream debug printing.
6. Make ingestion idempotent with content hashes or `(path, mtime, size)` state.
7. Add a small retrieval quality smoke test using known Buffett letter topics.
8. Improve frontend polish after confirming product direction and desired tone.

## Environment Notes From Initial Scan

- `git status --short` showed one untracked file: `Untitled.ipynb`.
- No user files were modified during analysis before this file was added.
- Shell sandboxing failed locally because `bubblewrap` was unavailable, so
  repository inspection required escalated command execution.
