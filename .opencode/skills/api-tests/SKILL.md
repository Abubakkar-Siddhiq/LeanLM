---
name: api-tests
description: Write and run API-level tests for LeanLM FastAPI endpoints using TestClient with mocked service layer and in-memory SQLite
---

## What I do

I test all FastAPI HTTP endpoints in LeanLM using `fastapi.testclient.TestClient`. Tests start a real FastAPI app instance with the same routers but override the `get_session` dependency with an in-memory SQLite session. Service-level dependencies (GroqProvider, ContextBuilder, Summarizer) are mocked at the view layer. No real network calls or PostgreSQL instance is needed.

## Test layout

- `/tests/api/test_chat.py` — `POST /api/chat`
- `/tests/api/test_conversation.py` — `GET /api/conversations`, `GET /api/conversations/{id}`

Place a shared `conftest.py` at `/tests/api/conftest.py` with the TestClient app factory and DB fixtures.

## General approach

1. Create a fresh FastAPI `TestClient` per test (or per module) with overridden `get_session` dependency
2. Mock `ChatService` (or its dependencies) at the integration seam — prefer dependency injection over monkeypatching
3. Use `httpx`'s `TestClient` as context manager (`with TestClient(app) as client:`)

## `conftest.py` template

```python
# tests/api/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from main import app
from db.session import get_session

@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    def override_get_session():
        yield db_session
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

## Test cases: `POST /api/chat`

### 200 — successful chat (no conversation_id)

- Send `{"prompt": "Hello"}`
- Verify 200 status
- Verify response contains `user_message_id`, `assistant_message_id`, `conversation_id`, `intent`, `reason`, `confidence`, `model`, `response`
- Verify `conversation_id` is a valid UUID

### 200 — successful chat (with conversation_id)

- First create a conversation via direct DB insert
- Send `{"prompt": "Follow up", "conversation_id": "<uuid>"}`
- Verify 200 and same `conversation_id` in response

### 400 — empty prompt

- Send `{"prompt": ""}` or `{"prompt": "   "}`
- Verify 400 status with `detail` field

### 400 — missing prompt

- Send `{}` (no prompt field)
- Verify 422 (Pydantic validation)

### 404 — invalid conversation_id

- Send `{"prompt": "Hello", "conversation_id": "00000000-0000-0000-0000-000000000000"}`
- Verify 404 with detail "Conversation not found"

### Intent classification response shapes

- Mock `ChatService.find_intent` or `GroqProvider.generate` to return a known JSON
- Verify each complexity level maps to the correct model in the response:
  - `{"complexity": "low", ...}` → model ends with `8b-instant`
  - `{"complexity": "medium", ...}` → model contains `qwen`
  - `{"complexity": "high", ...}` → model contains `gpt-oss`
- Verify `model` field in response matches expected value

## Test cases: `GET /api/conversations`

### 200 — empty list

- Verify 200 with `[]`

### 200 — returns conversations

- Insert 2-3 conversations via DB directly
- Verify response is a list ordered by `created_at` descending
- Verify each item has `id`, `summary`, `message_count`, `created_at`

## Test cases: `GET /api/conversations/{conversation_id}`

### 200 — returns conversation with messages

- Insert a conversation + 2 messages via DB
- Verify response has `conversation_id`, `created_at`, `messages` (array of 2)
- Each message has `id`, `role`, `content`, `created_at`

### 404 — conversation not found

- Request with nonexistent UUID
- Verify 404

### 422 — invalid UUID format

- Request with `"not-a-uuid"`
- Verify 422

## Running tests

```powershell
cd src
pytest tests/api/ -v --tb=short
```
