# Routiq Architecture

## 1. What Routiq Is

Routiq is an **AI gateway** — a FastAPI service that sits between a user and LLM providers. It does three things:

- **Model router**: every incoming prompt is classified by complexity (low/medium/high) and task type, then dispatched to a cost-appropriate model from any configured provider.
- **Conversation engine**: manages multi-turn conversations with PostgreSQL persistence, semantic retrieval, and lazy summarization.
- **Usage analytics layer**: logs every LLM call with token counts, latency, and cost estimates, exposed via dashboard-friendly API endpoints.

Routiq supports **four providers** (Groq, OpenAI, Anthropic, Google) through a common adapter pattern, with provider availability-aware routing and Fernet-encrypted BYOK key storage.

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
│   ├─ BYOK or env provider availability
│   │   ├─ ProviderKeyService.get_available_providers()  → BYOK active keys
│   │   └─ fallback: ProviderFactory.available_providers() → env keys
│   ├─ model_selector.select(available_providers) → pick model from routing config
│   │   └─ filters ROUTING_RULES to available providers only
│   ├─ _generate_with_fallbacks()  → try primary, then same-provider fallback chain
│   │   ├─ resolve provider per model via MODEL_TO_PROVIDER + ProviderFactory
│   │   ├─ primary model call (from selected provider)
│   │   ├─ fallback model (same provider, if primary fails)
│   │   ├─ all fail → 502
│   ├─ _save_assistant_message()   → persist response
│   │
│   ├─ usage_logger.log_usage()    → write LLMUsageLog row
│   ├─ _schedule_summarization_if_needed()
│   │   └─ background task: Summarizer.run_summarization()
│   │
│   └─ return response + routing metadata + usage info + available_providers
```

## 3. Main Components

### ChatService (`src/api/chat/services.py`)

The orchestration hub. Owns the full chat lifecycle — validation, persistence, context assembly, provider resolution, model invocation (with BYOK key resolution and fallback), usage logging, and summarization scheduling.

### ChatPromptBuilder (`src/services/prompt_builder.py`)

Assembles the `messages` list sent to the LLM. Build order:
1. System prompt (from `Prompts.system_prompt()`)
2. Conversation summary (if available)
3. Relevant past messages (from semantic retrieval)
4. Current chat history

### IntentClassifier (`src/services/routing.py`)

Uses an LLM call to `CLASSIFIER_MODEL` (default `llama-3.1-8b-instant` via Groq) to classify every user prompt into a structured `ClassificationResult` with `task_type`, `complexity`, `confidence`, and `reason`. Falls back to a safe default if the LLM JSON response is malformed.

### ModelSelector (`src/services/routing.py`)

Decides which model to call based on the classified `task_type` and `complexity`. Uses `ROUTING_RULES` for exact matches, `DEFAULT_MODEL_BY_COMPLEXITY` as fallback. When `available_providers` is provided, filters rules to only those whose provider is available, and limits fallback chains to same-provider models. Raises `ValueError` if no configured model is available.

### ProviderFactory (`src/providers/__init__.py`)

Factory and registry for all provider adapters. Lazy-imports each provider module on first request. Provides `available_providers()` which checks env-sourced API keys (`GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`). This is used as a fallback when no BYOK keys are stored. Respects `ALLOW_ENV_PROVIDER_FALLBACK` setting — returns `[]` when `false` (production mode, BYOK-only).

**Provider availability priority at runtime:**
1. BYOK active stored keys (from `ProviderKeyService.get_available_providers(session)`)
2. Env-configured keys (from `ProviderFactory.available_providers()`) — local development fallback

When executing a provider call, BYOK keys are preferred: `ProviderKeyService.get_decrypted_api_key()` is called for the selected provider. If a BYOK key exists, it's passed as `api_key` to the provider's `generate()` method. If no BYOK key exists, the provider falls back to its env-configured client (via `api_key=None`).

### Provider Adapters (`src/providers/`)

| Provider | File | SDK | Async |
|---|---|---|---|
| Groq | `groq.py` | `groq` (sync) | Blocks event loop |
| OpenAI | `openai.py` | `openai` (AsyncOpenAI) | Native async |
| Anthropic | `anthropic.py` | `anthropic` (AsyncAnthropic) | Native async |
| Google | `google.py` | `google-generativeai` (sync) | Wrapped in `run_in_executor` |

All adapters implement `generate(model, messages, api_key=None) → LLMResponse` and resolve API keys inside `generate()`:

1. BYOK `api_key` param (if provided)
2. Env key fallback (only when `settings.ALLOW_ENV_PROVIDER_FALLBACK=True`)
3. `ValueError` if no key resolved

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

### ProviderKeyService (`src/api/providers/services.py`)

Manages BYOK provider keys. Stores API keys encrypted (Fernet) in the `ProviderKey` table. Provides CRUD operations and internal `get_decrypted_api_key()` for future routing use.

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
provider: str            # resolved from ROUTING_RULES (one of: groq, openai, anthropic, google)
model: str               # primary model to call
task_type: str           # passed through from classification
complexity: str          # passed through from classification
classifier_reason: str   # from ClassificationResult.reason
routing_reason: str      # from ROUTING_RULES config (why this model was chosen)
confidence: float
fallback_models: list[str]   # same-provider ordered fallback chain, primary excluded
fallback_used: bool          # set at runtime if fallback triggered
fallback_model: str | None   # which fallback succeeded
fallback_error: str | None   # original error from primary call
```

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

SQLModel table recording every LLM call. Columns: `id`, `conversation_id`, `user_message_id`, `assistant_message_id`, `provider`, `model`, `task_type`, `complexity`, `classifier_reason`, `routing_reason`, `confidence`, `input_tokens`, `output_tokens`, `total_tokens`, `estimated_cost`, `latency_ms`, `created_at`.

### ProviderKey (`src/db/provider_keys.py`)

SQLModel table for BYOK key storage. Columns: `id`, `provider_name` (unique), `encrypted_api_key`, `is_active`, `created_at`, `updated_at`.

### Schemas (`src/api/providers/schemas.py`)

- `ProviderKeyCreate` — `provider_name`, `api_key` (input only, never exposed)
- `ProviderKeyResponse` — `id`, `provider_name`, `is_active`, `created_at`, `updated_at` (no key data)
- `ProviderKeyValidateResponse` — `provider_name`, `valid`, `message`
- `ProviderAvailabilityResponse` — `available_providers: list[str]`

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
├── providers/
│   ├── schemas.py           # Request/response schemas for BYOK endpoints
│   ├── services.py          # ProviderKeyService (CRUD + encrypt + decrypt)
│   └── views.py             # CRUD + validate + available endpoints
└── usage/
    ├── schemas.py           # Response schemas for analytics endpoints
    ├── services.py          # UsageAnalytics (SQL aggregate queries)
    └── views.py             # GET /api/usage/summary, /by-model, /by-task-type, /recent
```

All routes are registered in `src/main.py` under the `/api` prefix.

## 6. Config Files

### `src/config/models.py`

```python
CLASSIFIER_MODEL = "llama-3.1-8b-instant"
LOW_MODEL        = "llama-3.1-8b-instant"
MEDIUM_MODEL     = "qwen/qwen3-32b"
HIGH_MODEL       = "openai/gpt-oss-120b"
```

Named constants for model identifiers. `CLASSIFIER_MODEL` is used by the IntentClassifier; the others are referenced by routing config.

### `src/config/routing.py`

Four data structures that control the entire routing logic:

- **`ROUTING_RULES`** — list of `{provider, task_types, complexities, model, reason}` tuples. Each rule now includes a `provider` field (groq, openai, etc.) so routing can filter by provider availability.
- **`DEFAULT_MODEL_BY_COMPLEXITY`** — fallback when no `ROUTING_RULES` match the intent.
- **`MODEL_TO_PROVIDER`** — maps every known model identifier to its provider name. Used by `ModelSelector` to find same-provider fallbacks and by `_generate_with_fallbacks` to resolve which `ProviderFactory` to call.
- **`FALLBACK_MODEL_BY_COMPLEXITY`** — ordered lists of models across all providers. `ModelSelector` filters these to same-provider models at routing time.

### `src/config/prompts.py`

- `Prompts.intent_detection(prompt)` — the full classification prompt sent to the LLM classifier. Defines task types, complexity tiers, classification rules, and few-shot examples.
- `Prompts.system_prompt()` — the system prompt used for actual chat responses.

### `src/config/settings.py`

Loads from `.env` via `pydantic-settings`. Fields: `DATABASE_URL`, `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `PROVIDER_KEY_ENCRYPTION_SECRET`, `HF_TOKEN`. All API key fields default to `""`.

**Provider key fallback:** `ALLOW_ENV_PROVIDER_FALLBACK` (default `True`) controls whether providers fall back to env-configured keys when no BYOK key is provided. Set to `false` in production when BYOK is required.

**Provider key priority:**
1. BYOK stored key (passed as `api_key` to `generate()`)
2. Env key fallback — only when `ALLOW_ENV_PROVIDER_FALLBACK=true`
3. `ValueError` if neither is available

## 7. Design Patterns Used

| Pattern | Where | Why |
|---|---|---|
| **Service Layer** | `ChatService`, `ConversationService`, `ProviderKeyService`, `UsageAnalytics` | Business logic lives in service classes, not in route handlers. Views are thin wrappers. |
| **Adapter Pattern** | `GroqProvider`, `OpenAIProvider`, `AnthropicProvider`, `GoogleProvider` | Wraps third-party SDKs behind a uniform `generate(model, messages) → LLMResponse` interface. |
| **Factory Pattern** | `ProviderFactory` | Lazy provider instantiation and registry. Decouples provider construction from consumption. |
| **Strategy Pattern** | `ModelSelector`, `IntentClassifier` | Routing and classification strategies can be swapped without changing callers. |
| **DTO/Schema Pattern** | `ClassificationResult`, `RouteDecision`, `LLMResponse` | Explicit data contracts between layers. No raw dicts. |
| **Builder Pattern** | `ChatPromptBuilder.build()` | Assembles a complex `messages` list from multiple sources (system prompt, summary, relevant messages, history). |
| **Chain of Responsibility (ish)** | `_generate_with_fallbacks()` | Tries a chain of models in order until one succeeds or all fail. |
| **Configuration-Driven Routing** | `ROUTING_RULES` | Routing decisions are declarative data, not hard-coded if/else chains. |
| **Dependency Injection (manual)** | `ChatService.__init__` | Dependencies (provider, classifier, selector, logger) are instantiated in the constructor. |

## 8. What Is Done

- Chat orchestration (validate → persist → classify → route → generate → respond)
- Prompt context assembly (system + summary + relevant + history)
- Intent classification (LLM-based, with safe fallback)
- Task type classification (7 types: coding, debugging, reasoning, simple_qa, summarization, extraction, writing)
- Routing decision (config-driven ROUTING_RULES + complexity fallback)
- Provider response normalization (LLMResponse schema)
- Multi-provider support (Groq, OpenAI, Anthropic, Google adapters)
- Provider availability-aware routing (env API key checks, ModelSelector filtering)
- Same-provider fallback chains (filtered to available providers)
- ProviderFactory with lazy initialization (no module-level crashes)
- Fallback routing (ordered chain per complexity tier, runtime safety net)
- Usage logging (LLMUsageLog table with per-call metadata)
- Usage analytics API (summary, by-model, by-task-type, recent)
- BYOK provider key management (Fernet-encrypted storage, CRUD API, soft-delete)
- Encryption utility (Fernet encrypt/decrypt with config error handling)
- Provider key CRUD API (create, list, delete, validate, available)
- Summarizer model separation (dedicated summarizer prompt)
- Background summarization (FastAPI BackgroundTasks)
- Semantic retrieval (sentence-transformers embeddings, pgvector cosine distance)
- Conversation CRUD (create, list, detail with messages)
- Token-aware context window (tiktoken-based scoring and eviction)
- Offline unit tests (74 tests, no API keys needed)

## 9. Current Limitations

- **Sync SDK in async context**: `GroqProvider` and `GoogleProvider` use sync SDKs, blocking the event loop. OpenAI and Anthropic use native async.
- **No real cost estimation**: `UsageTracker.estimate_cost` returns `0.0` always.
- **No streaming**: all responses are fully buffered.
- **No OpenAI-compatible `/v1/chat/completions` endpoint**: the API is custom.
- **Background summarization**: uses `BackgroundTasks` (in-process), not a queue. A crash during summarization loses the task.
- **No auth**: all endpoints are public.
- **No Alembic migrations**: tables are auto-created via `SQLModel.metadata.create_all`, which does not alter existing tables.
- **Fallback fields not persisted**: `fallback_used`, `fallback_model`, `fallback_error` are returned in the API response but not stored in `LLMUsageLog`.
- **BYOK not wired into routing**: routing still uses env-based provider availability. ProviderKeyService exists but is not yet consumed by ChatService (TODO in `providers/__init__.py`).
- **No lint/format config**: no ruff, flake8, or pyproject.toml.

## 10. Next Roadmap

### Phase 1: Stabilize Current API
- Add real cost tables per model
- Persist fallback fields to LLMUsageLog
- Add request validation and error standardization
- Set up ruff + formatting

### Phase 2: Wire BYOK into Routing
- Replace env-based `ProviderFactory.available_providers()` with `ProviderKeyService.get_available_providers()`
- Add user_id to ProviderKey model when auth is implemented
- Real provider API key validation (test connectivity)

### Phase 3: Async Provider Overhaul
- Replace sync `GroqProvider` with native async SDK
- Replace deprecated `google-generativeai` with `google.genai`
- Add provider health checks

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
ChatService         — coordinates everything. One method orchestrates the full flow.
Classifier          — asks an LLM "what kind of request is this?" Returns task_type + complexity.
ModelSelector       — maps (task_type, complexity) → model + fallback chain. Filters by available providers.
ProviderFactory     — lazy registry of provider adapters. Checks env keys for availability.
Provider Adapters   — Groq, OpenAI, Anthropic, Google. All implement generate() → LLMResponse.
UsageLogger         — writes a row to LLMUsageLog for every completed request.
Usage Analytics     — reads LLMUsageLog. Dashboard backend. Read-only.
ProviderKeyService  — manages encrypted API keys in DB. CRUD + internal decryption.
Summarizer          — compresses old messages in the background when conversations get long.
```

**Data flow**: Request → Schema → Service → Schema → Provider → Schema → Response.

**Key principle**: every layer communicates through explicit schemas (Pydantic models), not raw dicts or unstructured data.
