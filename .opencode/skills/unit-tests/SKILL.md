---
name: unit-tests
description: Write and run unit tests for Routiq covering models, providers, services, memory, and config in isolation with mocked dependencies
---

## What I do

I write unit tests that verify individual Routiq components in isolation. All external dependencies (DB, Groq API, tiktoken) must be mocked. Tests use pytest with pytest-mock, run against an in-memory SQLite SQLModel engine, and avoid any real network or database calls.

## Test layout

- `/tests/unit/models/` — SQLModel table definitions
- `/tests/unit/providers/` — GroqProvider
- `/tests/unit/memory/` — ContextBuilder, Summarizer
- `/tests/unit/config/` — Prompts, Settings
- `/tests/unit/api/chat/` — ChatService
- `/tests/unit/api/conversation/` — ConversationService

Place a `conftest.py` at `/tests/unit/` (and/or sub-packages) with shared fixtures.

## Testing patterns by module

### `src/db/models.py`
- Create `Conversation` and `Message` instances with valid/edge-case field values
- Verify UUIDs are auto-generated, timestamps are UTC, relationships work
- Use an in-memory SQLite engine (`sqlite:///:memory:`) with `SQLModel.metadata.create_all`

### `src/providers/groq.py` (GroqProvider)
- Mock the module-level `groq.Groq` client entirely — never hit the real API
- Mock `client.chat.completions.create` return value to simulate API responses
- Test `generate(model, messages)` returns expected content string
- Verify the mock was called with correct `model` and `messages` args

### `src/config/prompts.py` (Prompts)
- Test `intent_detection(prompt)` returns expected template for known prompt types (greeting, technical, complex)
- Test `system_prompt()` returns non-empty string
- Don't test the LLM output — only that the static method returns a string containing expected keywords

### `src/config/settings.py` (Settings)
- Test that `Settings` loads from env with `pydantic_settings`
- Override `DATABASE_URL` and `GROQ_API_KEY` via monkeypatch on `os.environ`
- Verify `settings.DATABASE_URL` and `settings.GROQ_API_KEY` match overrides

### `src/memory/context_builder.py` (ContextBuilder)
- Mock `tiktoken.get_encoding` to return a deterministic tokenizer stub
- Test `count(text)` returns expected token count
- Test `score_message(msg)` returns correct scores for different message types (user vs assistant, code blocks, questions, long messages, keyword messages)
- Test `build(system_prompt, summary, messages)`:
  - Always includes system prompt first
  - Includes summary when provided
  - Evicts low-scored messages when token budget exceeded
  - Preserves original message order after scoring
  - Does not exceed max_tokens

### `src/memory/summarizer.py` (Summarizer)
- Mock `GroqProvider.generate` — test that `summarize` calls provider with correct prompt
- Test `should_summarize(conversation, messages, context_tokens)` with:
  - Below threshold returns False
  - Above thresholds returns True
  - Edge case at exact boundary values
- Test `run_summarization` with a mocked session:
  - Verify it fetches conversation and messages
  - Calls `summarize` on old messages (keeps last 10)
  - Updates `conversation.summary` and `last_summarized_at_count`
  - Deletes old messages
  - Calls `session.commit` at the end

### `src/api/chat/services.py` (ChatService)
- Mock `GroqProvider`, `ContextBuilder`, `Summarizer`, and the DB session entirely
- Test `find_intent(prompt)` — mock `llm_provider.generate` to return a valid JSON string, verify parsed dict
- Test `select_model(complexity)` — returns correct model for each tier
- Test `chat(payload, session)` — the full orchestration:
  - New conversation: mocks `session.refresh`, verifies `Conversation()` is created
  - Existing conversation: verifies `session.get` is called
  - Empty prompt raises `HTTPException(400)`
  - Invalid conversation_id raises `HTTPException(404)`
  - Verifies intent detection is called and response is parsed
  - Verifies correct model is selected based on intent
  - Verifies assistant response is saved to DB
  - Verifies `message_count` is incremented by 2
  - Verifies the return dict has all expected keys
- Test summarization trigger condition (when should_summarize returns True, background task is added)

### `src/api/conversation/services.py` (ConversationService)
- Mock the DB session
- Test `get_conversations` returns list ordered by `created_at.desc()`
- Test `get_conversation_messages` returns conversation with messages
- Test `get_conversation_messages` returns None for missing conversation

## Shared fixtures (`conftest.py`)

```python
# tests/unit/conftest.py
import pytest
from sqlmodel import SQLModel, Session, create_engine

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def db_session(in_memory_db):
    with Session(in_memory_db) as session:
        yield session
```

## Running tests

```powershell
cd src
pytest tests/unit/ -v --tb=short
```
