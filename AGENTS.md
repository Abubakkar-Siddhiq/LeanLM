# Routiq

LLM routing system — classifies prompt complexity (low/medium/high) and dispatches to different Groq-hosted models.

## Quick start

```powershell
docker compose up -d                          # start PostgreSQL
& "$env:VIRTUAL_ENV\Scripts\Activate.ps1"    # or: venv\Scripts\Activate
cd src; uvicorn main:app --reload            # working dir MUST be src/
```

## Known bugs (uncommitted work in `src/api/chat/services.py`)

The working tree has in-progress changes with several issues. Before the code runs, fix:

1. **Line 10** — stray `B` character, delete it.
2. **`Prompts.system`** — should be `Prompts.system_prompt()` (call the static method).
3. **`GroqProvider.generate` calls** — uses `prompt=...` but signature expects `messages: list`.
4. **`background_tasks` param** — added to `chat()` but (a) never used in body, (b) view calls `chat_service.chat(payload, session)` missing the argument.
5. **New `Conversation()` creation** — old code had `session.add()` + `session.commit()` before `session.refresh()`. Uncommitted change removed `session.add()`, causing a `DetachedInstanceError`.
6. **`run_summarization` buggy** — uses undefined `SessionLocal()` (should be `Session(engine)`) and `self.provider` (should be `self.llm_provider`).

## Structure

| Path | Role |
|---|---|
| `src/main.py` | FastAPI app entrypoint, includes `/api` routers |
| `src/api/chat/views.py` | Route: `POST /api/chat` |
| `src/api/chat/services.py` | Business logic: intent detection, model routing, message persistence |
| `src/api/chat/schema.py` | Pydantic request schema (`ChatRequest`) |
| `src/api/conversation/views.py` | Routes: `GET /api/conversations[/{id}]` |
| `src/api/conversation/services.py` | Query logic for conversations and their messages |
| `src/db/models.py` | SQLModel tables: `Conversation`, `Message` |
| `src/config/settings.py` | `DATABASE_URL`, `GROQ_API_KEY` from `.env` |
| `src/config/prompts.py` | Static prompt templates (`intent_detection`, `system_prompt`) |
| `src/providers/groq.py` | Groq API wrapper (module-level client init, sync SDK in async method) |
| `src/db/session.py` | SQLModel engine + session factory, auto-creates tables on startup |
| `src/memory/context_builder.py` | Token-aware context window with scoring/eviction |
| `src/memory/summarizer.py` | Background summarization trigger + LLM call |

## Architecture notes

- **Model routing**: `low` → `llama-3.1-8b-instant`, `medium` → `qwen/qwen3-32b`, `high` → `openai/gpt-oss-120b`
- **Intent classification** reuses `llama-3.1-8b-instant` regardless of prompt tier
- **DB**: PostgreSQL via docker-compose (bitnami image). Tables created automatically at startup via `SQLModel.metadata.create_all` (models must be imported before that call — currently works via transitive imports from both routers)
- **`GroqProvider.generate`** — uses the **sync** `groq` SDK inside an `async` method (blocks event loop). The `client` is instantiated at module level
- **`context_builder.py`** uses `tiktoken` for token counting; `cl100k_base` encoding
- **No logging** — uses bare `print()` statements
- **No tests** — zero test files, no pytest config, no CI
- **No lint/format config** — no `ruff.toml`, `.flake8`, `pyproject.toml`, or `Makefile`

## `.env` (required, gitignored)

```
GROQ_API_KEY=...
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/routiq
```

## Branch

Working on `develop`; `origin` at `https://github.com/Abubakkar-Siddhiq/routiq`.

To setup: `python -m venv venv`, `.\venv\Scripts\Activate.ps1`, `pip install -r requirements.txt`.
