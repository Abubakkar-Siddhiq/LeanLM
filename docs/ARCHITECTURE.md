# Routiq Architecture

## 1. What Routiq Is

Routiq is an **AI gateway** — a FastAPI service that sits between a user and LLM providers. It does three things:

- **Model router**: every incoming prompt is classified by complexity (low/medium/high) and task type, then dispatched to a cost-appropriate model.
- **Conversation engine**: manages multi-turn conversations with PostgreSQL persistence, semantic retrieval, and lazy summarization.
- **Usage analytics layer**: logs every LLM call with token counts, latency, and cost estimates, exposed via dashboard-friendly API endpoints.

It is currently a **single-provider** system backed by Groq, designed so additional providers can be added without changing the orchestration layer.

## 2. Current Request Flow

```
User prompt (POST /api/chat)
│
├─ 1. ChatService.chat()
│   ├─ _validate_prompt()          → 400 if empty
│   ├─ _get_or_create_conversation() → find by UUID or create
│   ├─ _save_user_message()        → persist + compute embedding
│   ├─ _get_conversation_messages() → fetch full chat history
│   ├─ retrieve_relevant_messages() → semantic search (cosine sim)
│   ├─ prompt_builder.build()      → system + summary + relevant + history
│   ├─ classifier.classify()       → LLM-based complexity & task type
│   ├─ model_selector.select()     → pick model from routing config
│   ├─ _generate_with_fallbacks()  → try primary, then fallback chain
│   │   ├─ primary model call
│   │   ├─ fallback model 1 (if primary fails)
│   │   ├─ fallback model 2 (if all fail → 502)
│   ├─ _save_assistant_message()   → persist response
│   │
│   ├─ usage_logger.log_usage()    → write LLMUsageLog row
│   ├─ _schedule_summarization_if_needed()
│   │   └─ background task: Summarizer.run_summarization()
│   │
│   └─ return response + routing metadata + usage info
```

## 3. Main Components

### ChatService (`src/api/chat/services.py`)

The orchestration hub. Owns the full chat lifecycle — validation, persistence, context assembly, model invocation (with fallback), usage logging, and summarization scheduling.

### ChatPromptBuilder (`src/services/prompt_builder.py`)

Assembles the `messages` list sent to the LLM. Build order:
1. System prompt (from `Prompts.system_prompt()`)
2. Conversation summary (if available)
3. Relevant past messages (from semantic retrieval)
4. Current chat history

### IntentClassifier (`src/services/routing.py`)

Uses an LLM call to `llama-3.1-8b-instant` to classify every user prompt into a structured `ClassificationResult` with `task_type`, `complexity`, `confidence`, and `reason`. Falls back to a safe default if the LLM JSON response is malformed.

### ModelSelector (`src/services/routing.py`)

Decides which model to call based on the classified `task_type` and `complexity`. Uses `ROUTING_RULES` for exact matches, `DEFAULT_MODEL_BY_COMPLEXITY` as fallback. Also builds the `fallback_models` chain by removing the primary model from `FALLBACK_MODEL_BY_COMPLEXITY`.

### GroqProvider (`src/providers/groq.py`)

The only provider currently implemented. Wraps the **sync** Groq SDK inside an `async` method. Returns a normalized `LLMResponse` with content, token counts, latency, and raw response dump.

### UsageTracker (`src/services/usage_tracker.py`)

Placeholder for cost estimation. Currently returns `0.0` for cost and uses word-splitting for token estimates.

### UsageLogger (`src/services/usage_logger.py`)

Creates and persists `LLMUsageLog` records after every successful chat completion.

### Usage Analytics API (`src/api/usage/`)

Four read-only endpoints that query `LLMUsageLog`:
- `GET /api/usage/summary` — aggregate stats
- `GET /api/usage/by-model` — breakdown by provider/model
- `GET /api/usage/by-task-type` — breakdown by task type
- `GET /api/usage/recent` — last N calls with full metadata

### Summarizer (`src/memory/summarizer.py`)

Triggered in background when a conversation has 15+ new messages and 20+ total messages. Summarizes the oldest messages (keeping the latest 10), appends to `conversation.summary`, and deletes the compressed messages.

## 4. Important Schemas

### ClassificationResult (`src/schemas/classification.py`)

```python
task_type: Literal["coding","debugging","reasoning","simple_qa","summarization","extraction","writing"]
complexity: Literal["low","medium","high"]
reason: str
confidence: float
```

Output of the IntentClassifier. Informs the routing decision. `reason` explains the classification logic; `confidence` estimates certainty.

### RouteDecision (`src/schemas/routing.py`)

```python
provider: str            # currently always "groq"
model: str               # primary model to call
task_type: str           # passed through from classification
complexity: str          # passed through from classification
classifier_reason: str   # from ClassificationResult.reason
routing_reason: str      # from ROUTING_RULES config (why this model was chosen)
confidence: float
fallback_models: list[str]   # ordered fallback chain, primary excluded
fallback_used: bool          # set at runtime if fallback triggered
fallback_model: str | None   # which fallback succeeded
fallback_error: str | None   # original error from primary call
```

Input to provider execution. Contains everything needed to call a model and handle fallback.

### LLMResponse (`src/schemas/llm.py`)

```python
content: str
provider: str
model: str
input_tokens: int | None
output_tokens: int | None
total_tokens: int | None
latency_ms: float | None
raw: dict | None
```

Normalized output from any provider. Ensures all providers speak the same contract. `raw` holds the full provider response for debugging.

### RequestTrace (`src/schemas/trace.py`)

```python
provider: str
model: str
complexity: str
classifier_reason: str
confidence: float
prompt_tokens_estimate: int | None
input_tokens: int | None
output_tokens: int | None
total_tokens: int | None
latency_ms: float | None
```

Snapshot of routing metadata included in every API response for observability.

### LLMUsageLog (`src/db/usage.py`)

SQLModel table recording every LLM call. Used by the Usage Analytics API. Columns: `id`, `conversation_id`, `user_message_id`, `assistant_message_id`, `provider`, `model`, `task_type`, `complexity`, `classifier_reason`, `routing_reason`, `confidence`, `input_tokens`, `output_tokens`, `total_tokens`, `estimated_cost`, `latency_ms`, `created_at`.

### Usage Analytics Response Schemas (`src/api/usage/schemas.py`)

- `UsageSummaryResponse` — totals and averages
- `UsageByModelItem` — per-model aggregates
- `UsageByTaskTypeItem` — per-task-type aggregates
- `RecentUsageItem` — full row for dashboard list

## 5. API Modules

```
src/api/
├── chat/
│   ├── __init__.py          # re-exports router
│   ├── schema.py            # ChatRequest (prompt + optional conversation_id)
│   ├── services.py          # ChatService (orchestration + fallback)
│   └── views.py             # POST /api/chat
├── conversation/
│   ├── __init__.py
│   ├── services.py          # ConversationService (list + detail queries)
│   └── views.py             # GET /api/conversations, GET /api/conversations/{id}
└── usage/
    ├── schemas.py           # Response schemas for analytics endpoints
    ├── services.py          # UsageAnalytics (SQL aggregate queries)
    └── views.py             # GET /api/usage/summary, /by-model, /by-task-type, /recent
```

All routes are registered in `src/main.py` under the `/api` prefix.

## 6. Config Files

### `src/config/models.py`

```python
LOW_MODEL    = "llama-3.1-8b-instant"
MEDIUM_MODEL = "qwen/qwen3-32b"
HIGH_MODEL   = "openai/gpt-oss-120b"
```

Named constants for model identifiers. Used by other config modules.

### `src/config/routing.py`

Three data structures that control the entire routing logic:

- **`ROUTING_RULES`** — list of `{task_types, complexities, model, reason}` tuples. Matched in order. Each rule maps a (task_type, complexity) pair to a specific model with a human-readable routing reason.
- **`DEFAULT_MODEL_BY_COMPLEXITY`** — fallback when no `ROUTING_RULES` match the intent.
- **`FALLBACK_MODEL_BY_COMPLEXITY`** — ordered lists of models to try if the primary model call fails. Primary model is filtered out at runtime.

### `src/config/prompts.py`

- `Prompts.intent_detection(prompt)` — the full classification prompt sent to the LLM classifier. Defines task types, complexity tiers, classification rules, and few-shot examples.
- `Prompts.system_prompt()` — the system prompt used for actual chat responses.

### `src/config/settings.py`

Loads `GROQ_API_KEY`, `DATABASE_URL`, and `HF_TOKEN` from `.env` via `pydantic-settings`.

## 7. Design Patterns Used

| Pattern | Where | Why |
|---|---|---|
| **Service Layer** | `ChatService`, `ConversationService`, `UsageAnalytics` | Business logic lives in service classes, not in route handlers. Views are thin wrappers. |
| **Adapter Pattern** | `GroqProvider` | Wraps a third-party SDK behind a uniform `generate(model, messages) → LLMResponse` interface. New providers implement the same contract. |
| **Strategy Pattern** | `ModelSelector`, `IntentClassifier` | Routing and classification strategies can be swapped without changing callers. |
| **DTO/Schema Pattern** | `ClassificationResult`, `RouteDecision`, `LLMResponse` | Explicit data contracts between layers. No raw dicts. |
| **Builder Pattern** | `ChatPromptBuilder.build()` | Assembles a complex `messages` list from multiple sources (system prompt, summary, relevant messages, history). |
| **Chain of Responsibility (ish)** | `_generate_with_fallbacks()` | Tries a chain of models in order until one succeeds or all fail. |
| **Configuration-Driven Routing** | `ROUTING_RULES` | Routing decisions are declarative data, not hard-coded if/else chains. |
| **Dependency Injection (manual)** | `ChatService.__init__` | Dependencies (provider, classifier, selector, logger) are instantiated in the constructor and could be swapped via parameters. Currently all wired at construction time. |

## 8. What Is Done

- Chat orchestration (validate → persist → classify → route → generate → respond)
- Prompt context assembly (system + summary + relevant + history)
- Intent classification (LLM-based, with safe fallback)
- Task type classification (7 types: coding, debugging, reasoning, simple_qa, summarization, extraction, writing)
- Routing decision (config-driven ROUTING_RULES + complexity fallback)
- Provider response normalization (LLMResponse schema)
- Fallback routing (ordered chain per complexity tier)
- Usage logging (LLMUsageLog table with per-call metadata)
- Usage analytics API (summary, by-model, by-task-type, recent)
- Summarizer model separation (dedicated summarizer prompt, model reuses llama)
- Background summarization (FastAPI BackgroundTasks)
- Semantic retrieval (sentence-transformers embeddings, pgvector cosine distance)
- Conversation CRUD (create, list, detail with messages)
- Token-aware context window (tiktoken-based scoring and eviction)
- Offline unit tests (42 tests, no API keys needed)

## 9. Current Limitations

- **Single provider**: only Groq is implemented. `openai/gpt-oss-120b` and `qwen/qwen3-32b` in the routing config are placeholders — they will fail at runtime in Groq.
- **Sync SDK in async context**: `GroqProvider` uses the sync Groq SDK inside an `async` method, blocking the event loop.
- **No real cost estimation**: `UsageTracker.estimate_cost` returns `0.0` always.
- **No provider key management / BYOK**: API key is hard-coded at module level from a single environment variable.
- **No streaming**: all responses are fully buffered.
- **No OpenAI-compatible `/v1/chat/completions` endpoint**: the API is custom.
- **Background summarization**: uses `BackgroundTasks` (in-process), not a queue. A crash during summarization loses the task.
- **No auth**: all endpoints are public.
- **No Alembic migrations**: tables are auto-created via `SQLModel.metadata.create_all`, which does not alter existing tables.
- **Fallback fields not persisted**: `fallback_used`, `fallback_model`, `fallback_error` are returned in the API response but not stored in `LLMUsageLog`.
- **No lint/format config**: no ruff, flake8, or pyproject.toml.

## 10. Next Roadmap

### Phase 1: Stabilize Current API
- Add real cost tables per model
- Persist fallback fields to LLMUsageLog
- Add request validation and error standardization
- Set up ruff + formatting

### Phase 2: Provider Key Management / BYOK
- Multi-tenant provider key storage in DB
- Key rotation and validation endpoints
- Per-request provider selection

### Phase 3: Multi-Provider Adapters
- OpenAI adapter
- Anthropic adapter
- Async-first provider interface
- Provider health checks

### Phase 4: Dynamic Scoring Router
- Replace ROUTING_RULES with a scoring/weight system
- Latency-cost-quality tradeoff configurable per tenant
- A/B testing between models

### Phase 5: OpenAI-Compatible Endpoint
- `/v1/chat/completions` proxy with routing headers
- Streaming support (SSE)
- Drop-in replacement for existing OpenAI clients

### Phase 6: Dashboard Polish
- Usage analytics charts and exports
- Real-time request tracing
- Cost alerts and budgets

## 11. Developer Mental Model

```
ChatService      — coordinates everything. One method orchestrates the full flow.
Classifier       — asks an LLM "what kind of request is this?" Returns task_type + complexity.
ModelSelector    — maps (task_type, complexity) → model + fallback chain. Pure config logic.
Provider         — makes the actual LLM call. Currently only Groq. Returns normalized response.
UsageLogger      — writes a row to LLMUsageLog for every completed request.
Usage Analytics  — reads LLMUsageLog. Dashboard backend. Read-only.
Summarizer       — compresses old messages in the background when conversations get long.
```

**Data flow**: Request → Schema → Service → Schema → Provider → Schema → Response.

**Key principle**: every layer communicates through explicit schemas (Pydantic models), not raw dicts or unstructured data.
