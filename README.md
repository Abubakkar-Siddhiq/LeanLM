# Routiq

Routiq is an intelligent LLM routing and memory orchestration backend built with FastAPI.

It dynamically classifies prompt complexity, routes requests to cost-efficient models, maintains conversational memory with rolling summaries, and optimizes long-running chats using lazy memory compression.

## Features

- AI-powered intent classification
- Dynamic model routing
- PostgreSQL conversation storage
- Context-aware chat memory
- Lazy memory + rolling summaries
- Smart context trimming
- Async background summarization
- UUID-based conversations
- FastAPI + SQLModel architecture

## Tech Stack

- FastAPI
- SQLModel
- PostgreSQL
- Groq API
- Python 3.12

## Architecture

```text
User
  ↓
Intent Classifier
  ↓
Model Router
  ↓
Context Builder
  ↓
LLM Provider
  ↓
Lazy Memory System
```

## Running Locally

```bash
docker compose up -d

uvicorn main:app --reload
```

## Environment Variables

```env
GROQ_API_KEY=your_api_key
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/routiq
```

## Planned Features

- Streaming responses
- Embeddings + vector memory
- Semantic retrieval
- RAG pipelines
- Tool calling
- Agent workflows
- Frontend UI
- Cost analytics
