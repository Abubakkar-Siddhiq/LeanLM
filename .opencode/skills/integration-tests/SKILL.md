---
name: integration-tests
description: Write and run integration tests for Routiq covering the full request cycle through FastAPI, services, DB, and external providers with testcontainers and real Groq API
---

## What I do

I write integration tests that exercise Routiq's full stack — FastAPI endpoints through service orchestration, database persistence, and real external provider calls (Groq API). Tests use `testcontainers` for PostgreSQL (via `tc.postgres()`) and inject real Groq API keys from the environment. These tests validate that components wire together correctly and that the system behaves correctly end-to-end.

## Test layout

- `/tests/integration/test_chat_flow.py` — Full chat lifecycle
- `/tests/integration/test_conversation_flow.py` — Conversation CRUD lifecycle
- `/tests/integration/test_summarization.py` — Background summarization end-to-end

Place a shared `conftest.py` at `/tests/integration/conftest.py` managing the PostgreSQL container lifecycle and app setup.

## Database setup

Use `testcontainers` to spin up a disposable PostgreSQL instance:

```python
# tests/integration/conftest.py
import os
import pytest
from testcontainers.postgres import PostgresContainer
from sqlmodel import SQLModel, Session, create_engine
from fastapi.testclient import TestClient
from main import app
from db.session import get_session, engine as app_engine

@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        os.environ["DATABASE_URL"] = pg.get_connection_url()
        # Reinitialize the app engine with the test DB URL
        from db.session import engine
        # Force-recreate engine (if your session module caches it)
        yield
```

If the engine is cached at module import time, restructure `db/session.py` to support runtime engine replacement, or monkeypatch `settings.DATABASE_URL` before importing the app.

## conftest.py approach

1. Start PostgreSQL container at session scope
2. Set `DATABASE_URL` env var to the container's connection string before any code imports settings
3. Create all tables via `SQLModel.metadata.create_all`
4. Create `TestClient` with the real app (no dependency overrides for DB — it connects to the real PG)
5. Mock `GroqProvider.generate` by default to avoid real API calls (unless testing provider integration specifically)
6. Provide cleanup fixtures that truncate all tables between tests

## Fixture structure

```python
@pytest.fixture(scope="session")
def db_engine(postgres_container):
    from db.session import engine as app_engine
    # The engine should already point to the test PG via env var
    SQLModel.metadata.create_all(app_engine)
    yield app_engine
    SQLModel.metadata.drop_all(app_engine)

@pytest.fixture(autouse=True)
def clean_tables(db_engine):
    yield
    for table in reversed(SQLModel.metadata.sorted_tables):
        db_engine.execute(table.delete())

@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session

@pytest.fixture
def client(db_engine):
    from db.session import get_session
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
```

## Test cases: `test_chat_flow.py`

### Full chat roundtrip
- Send `POST /api/chat` with a simple prompt (e.g., "What is 2+2?")
- Verify 200 and that the response contains real LLM output
- Verify a `Conversation` row and two `Message` rows (user + assistant) exist in the database
- Verify `conversation.message_count == 2`

### Multi-turn conversation
- Send 3 sequential messages with the same `conversation_id`
- After each, verify `message_count` increments correctly (2, 4, 6)
- Verify all 6 messages are retrievable via `GET /api/conversations/{id}`

### Intent classification integration
- For a simple prompt, verify `intent` is `"low"` and `confidence` is at least `"low"`
- For a complex prompt (e.g., "Design a microservice architecture for an e-commerce platform"), verify `intent` is `"high"` or `"medium"`

### Empty conversation — retry
- Send prompt with conversation_id after a previous conversation completed
- Verify the assistant continues the conversation contextually

## Test cases: `test_conversation_flow.py`

### List after inserts
- Run 2 chat sessions (different conversation_ids)
- `GET /api/conversations` returns both, ordered by creation time descending

### Get with messages
- Run a chat session with 2 user prompts
- `GET /api/conversations/{id}` returns the conversation with all 4 messages (2 user + 2 assistant)

### Delete cascade
- Conversations without direct delete endpoint — verify by checking no orphan messages after conversation removal via session.delete

## Test cases: `test_summarization.py`

### Should summarize
- Insert a conversation with `message_count = 30` and `last_summarized_at_count = 5` (15+ new messages)
- Run `should_summarize` directly (unit-test-style but with real DB)
- Verify it returns True

### Background summarization run
- Create a conversation with 25 messages
- Mock `GroqProvider.generate` to return a fake summary
- Call `Summarizer.run_summarization` with a real DB session
- Verify `conversation.summary` is updated
- Verify `conversation.last_summarized_at_count` equals `conversation.message_count`
- Verify old messages (beyond the last 10) are deleted
- Verify remaining 10 messages are intact

## Running tests

```powershell
cd src
pytest tests/integration/ -v --tb=short
```

## Prerequisites

- Docker Desktop running (for testcontainers)
- `GROQ_API_KEY` set in `.env` or environment
- Python packages: `pytest`, `pytest-asyncio`, `testcontainers[postgresql]`, `httpx`
