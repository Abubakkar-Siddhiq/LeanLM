# Routiq

Routiq is an intelligent LLM routing and memory orchestration backend built with FastAPI.

It dynamically classifies prompt complexity, routes requests to cost-efficient models, maintains conversational memory with rolling summaries, and optimizes long-running chats using lazy memory compression.

## Tech Stack

- FastAPI
- SQLModel
- PostgreSQL + pgvector
- Groq API
- Python 3.12
- sentence-transformers (all-MiniLM-L6-v2)

## Local Setup

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/Abubakkar-Siddhiq/routiq.git
cd routiq

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# PowerShell:
.\venv\Scripts\Activate.ps1
# bash:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment file and fill in values
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# 6. Start PostgreSQL
docker compose up -d

# 7. Start the FastAPI server
cd src
uvicorn main:app --reload

# 8. Open API docs
# http://localhost:8000/docs
```

### Running Tests

```bash
cd src
pytest ../tests/ -v
```

## Quick API Checks

Start the server then try these endpoints.

### Chat

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is a variable in programming?"}'
```

### Conversations

```bash
# List all conversations
curl "http://localhost:8000/api/conversations"

# Get conversation messages (replace UUID)
curl "http://localhost:8000/api/conversations/<conversation-id>"
```

### Usage Analytics

```bash
# Summary stats
curl "http://localhost:8000/api/usage/summary"

# Breakdown by model
curl "http://localhost:8000/api/usage/by-model"

# Breakdown by task type
curl "http://localhost:8000/api/usage/by-task-type"

# Recent requests
curl "http://localhost:8000/api/usage/recent"
```

## Project Structure

```
src/
├── api/                  # FastAPI route modules
│   ├── chat/             # POST /api/chat — main orchestrator
│   ├── conversation/     # GET /api/conversations — conversation CRUD
│   └── usage/            # GET /api/usage/* — analytics dashboard
├── config/               # Configuration
│   ├── models.py         # Model name constants
│   ├── prompts.py        # LLM prompt templates
│   ├── routing.py        # Routing rules + fallback chains
│   └── settings.py       # Pydantic env settings
├── db/                   # Database
│   ├── models.py         # Conversation, Message (SQLModel + pgvector)
│   ├── session.py        # Engine, session factory, init_db()
│   └── usage.py          # LLMUsageLog model
├── memory/               # Context + summarization
│   ├── context_builder.py   # Token-aware context window
│   └── summarizer.py        # Background conversation summarization
├── providers/            # LLM provider adapters
│   └── groq.py           # GroqProvider (only provider currently)
├── schemas/              # Shared Pydantic models
│   ├── classification.py # ClassificationResult
│   ├── llm.py            # LLMResponse
│   ├── routing.py        # RouteDecision
│   └── trace.py          # RequestTrace
├── services/             # Business logic
│   ├── embedder.py       # sentence-transformers embedding
│   ├── prompt_builder.py # Chat context assembly
│   ├── routing.py        # IntentClassifier + ModelSelector
│   ├── usage_logger.py   # LLMUsageLog writer
│   └── usage_tracker.py  # Cost estimation (placeholder)
└── main.py               # FastAPI app entrypoint

docs/
└── ARCHITECTURE.md       # Full architecture documentation

tests/
├── unit/                 # 42 offline unit tests (no API keys needed)
└── intent_eval.py        # Intent classifier evaluation script
```

## Environment Variables

See `.env.example` for all variables. Required:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM calls |
| `DATABASE_URL` | PostgreSQL connection string |

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a detailed breakdown of components, data flow, schemas, design patterns, and roadmap.
