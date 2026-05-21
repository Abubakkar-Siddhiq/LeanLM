<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

<br />
<div align="center">
  <a href="https://github.com/Abubakkar-Siddhiq/routiq">
    <img width="80" height="80" alt="logo" src="https://github.com/user-attachments/assets/6fa1afd6-a56b-4ba9-9f47-1c58d13a2bce" />
  </a>
  
  <h3 align="center">Routiq</h3>

  <p align="center">
    Intelligent LLM routing and memory orchestration backend
    <br />
    <a href="docs/ARCHITECTURE.md"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="#quick-api-checks">View Demo</a>
    &middot;
    <a href="https://github.com/Abubakkar-Siddhiq/routiq/issues/new">Report Bug</a>
    &middot;
    <a href="https://github.com/Abubakkar-Siddhiq/routiq/issues/new">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#api-endpoints">API Endpoints</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

## About The Project

Routiq is an AI gateway that sits between your application and LLM providers. It classifies prompt complexity, routes requests to cost-efficient models across multiple providers, maintains conversational memory with rolling summaries, and logs usage for analytics.

**What it does:**

- **Smart routing** — every prompt is classified by complexity (low/medium/high) and task type, then dispatched to the most cost-effective model across Groq, OpenAI, Anthropic, or Google. Provider availability priority: BYOK stored keys → env-configured keys.
- **Fallback resilience** — if the primary model fails, same-provider fallback models are tried before giving up.
- **Provider-aware** — routing automatically adapts to which API keys you've configured. Missing a key? That provider's models are skipped.
- **Conversation memory** — multi-turn conversations with semantic retrieval (pgvector) and lazy background summarization.
- **BYOK** — bring your own API keys, encrypted with Fernet and stored in the database.
- **Usage analytics** — every LLM call is logged with tokens, latency, and cost estimates, exposed via dashboard-friendly endpoints.

### Built With

- [![FastAPI][FastAPI.com]][FastAPI-url]
- [![Python][Python.org]][Python-url]
- [![PostgreSQL][PostgreSQL.com]][PostgreSQL-url]
- [![SQLModel][SQLModel.com]][SQLModel-url]
- [![Groq][Groq.com]][Groq-url]

**LLM Providers:** Groq, OpenAI, Anthropic, Google Generative AI

**Supporting:** pgvector, sentence-transformers, tiktoken, cryptography (Fernet)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/Abubakkar-Siddhiq/routiq.git
   cd routiq
   ```
2. Create virtual environment
   ```sh
   python -m venv venv
   ```
3. Activate it
   ```sh
   # PowerShell:
   .\venv\Scripts\Activate.ps1
   # bash:
   source venv/bin/activate
   ```
4. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```
5. Copy environment file and fill in your API keys
   ```sh
   cp .env.example .env
   ```
6. Start PostgreSQL
   ```sh
   docker compose up -d
   ```
7. Start the FastAPI server
   ```sh
   cd src
   uvicorn main:app --reload
   ```
8. Open the API docs
   ```sh
   open http://localhost:8000/docs
   ```

### Running Tests

```sh
cd src
pytest ../tests/ -v
```

All 74+ unit tests run offline — no API keys needed.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

### Chat

```sh
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is a variable in programming?"}'
```

Returns routing metadata including which provider and model handled the request, fallback status, token usage, and available providers.

### Conversations

```sh
# List all conversations
curl "http://localhost:8000/api/conversations"

# Get conversation with messages (replace UUID)
curl "http://localhost:8000/api/conversations/<conversation-id>"
```

### Usage Analytics

```sh
curl "http://localhost:8000/api/usage/summary"
curl "http://localhost:8000/api/usage/by-model"
curl "http://localhost:8000/api/usage/by-task-type"
curl "http://localhost:8000/api/usage/recent"
```

### Provider Key Management (BYOK)

```sh
# Store an encrypted API key
curl -X POST "http://localhost:8000/api/providers" \
  -H "Content-Type: application/json" \
  -d '{"provider_name": "groq", "api_key": "gsk_your_key"}'

# List saved providers
curl "http://localhost:8000/api/providers"

# Check if a provider key is active
curl "http://localhost:8000/api/providers/groq/validate"

# Get active provider names
curl "http://localhost:8000/api/providers/available"

# Disable a provider key
curl -X DELETE "http://localhost:8000/api/providers/groq"
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a prompt, get an LLM response |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversations/{id}` | Get conversation with messages |
| `GET` | `/api/usage/summary` | Aggregate usage stats |
| `GET` | `/api/usage/by-model` | Usage breakdown by model |
| `GET` | `/api/usage/by-task-type` | Usage breakdown by task type |
| `GET` | `/api/usage/recent` | Recent LLM calls |
| `POST` | `/api/providers` | Store an encrypted provider key |
| `GET` | `/api/providers` | List saved providers |
| `DELETE` | `/api/providers/{name}` | Disable a provider key |
| `POST` | `/api/providers/{name}/validate` | Check if key is active |
| `GET` | `/api/providers/available` | Active provider names |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

```
src/
├── api/                  # FastAPI route modules
│   ├── chat/             # POST /api/chat — main orchestrator
│   ├── conversation/     # GET /api/conversations — conversation CRUD
│   ├── providers/        # BYOK key management endpoints
│   └── usage/            # GET /api/usage/* — analytics dashboard
├── config/               # Configuration
│   ├── models.py         # Model name constants (CLASSIFIER_MODEL, LOW/MEDIUM/HIGH)
│   ├── prompts.py        # LLM prompt templates
│   ├── routing.py        # Routing rules + fallback chains + MODEL_TO_PROVIDER
│   └── settings.py       # Pydantic env settings (all API keys)
├── core/                 # Core utilities
│   └── security.py       # Fernet encrypt/decrypt for BYOK
├── db/                   # Database
│   ├── models.py         # Conversation, Message (SQLModel + pgvector)
│   ├── provider_keys.py  # ProviderKey model (encrypted key storage)
│   ├── session.py        # Engine, session factory, init_db()
│   └── usage.py          # LLMUsageLog model
├── memory/               # Context + summarization
│   ├── context_builder.py   # Token-aware context window
│   └── summarizer.py        # Background conversation summarization
├── providers/            # LLM provider adapters
│   ├── __init__.py       # ProviderFactory (lazy registry + available_providers)
│   ├── groq.py           # GroqProvider
│   ├── openai.py         # OpenAIProvider (AsyncOpenAI)
│   ├── anthropic.py      # AnthropicProvider (AsyncAnthropic)
│   └── google.py         # GoogleProvider (sync genai in executor)
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
└── unit/                 # 74 offline unit tests (no API keys needed)
```

## Environment Variables

See `.env.example` for all variables.

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes (for Groq) | Groq API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `OPENAI_API_KEY` | No | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |
| `GEMINI_API_KEY` | No | Google Gemini API key |
| `PROVIDER_KEY_ENCRYPTION_SECRET` | For BYOK | Fernet key for encrypting stored API keys |
| `HF_TOKEN` | No | Hugging Face token (embedder) |

Generate the encryption secret with:
```sh
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

See the [architecture docs](docs/ARCHITECTURE.md#10-next-roadmap) for the full roadmap.

High-level priorities:
- Wire BYOK into routing (replace env-based provider availability)
- Async provider overhaul (replace deprecated SDKs)
- Dynamic scoring router with latency-cost-quality tradeoffs
- OpenAI-compatible `/v1/chat/completions` endpoint with streaming
- Usage analytics dashboard

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

Contributions are welcome! Please open an issue first to discuss the change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: add AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Project Link: [https://github.com/Abubakkar-Siddhiq/routiq](https://github.com/Abubakkar-Siddhiq/routiq)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[contributors-shield]: https://img.shields.io/github/contributors/Abubakkar-Siddhiq/routiq.svg?style=for-the-badge
[contributors-url]: https://github.com/Abubakkar-Siddhiq/routiq/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Abubakkar-Siddhiq/routiq.svg?style=for-the-badge
[forks-url]: https://github.com/Abubakkar-Siddhiq/routiq/network/members
[stars-shield]: https://img.shields.io/github/stars/Abubakkar-Siddhiq/routiq.svg?style=for-the-badge
[stars-url]: https://github.com/Abubakkar-Siddhiq/routiq/stargazers
[issues-shield]: https://img.shields.io/github/issues/Abubakkar-Siddhiq/routiq.svg?style=for-the-badge
[issues-url]: https://github.com/Abubakkar-Siddhiq/routiq/issues
[FastAPI.com]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/
[Python.org]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://python.org/
[PostgreSQL.com]: https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white
[PostgreSQL-url]: https://postgresql.org/
[Groq.com]: https://img.shields.io/badge/Groq-000000?style=for-the-badge&logo=groq&logoColor=white
[Groq-url]: https://groq.com/
[SQLModel.com]: https://img.shields.io/badge/SQLModel-1a1a2e?style=for-the-badge&logo=python&logoColor=white
[SQLModel-url]: https://sqlmodel.tiangolo.com/
