# 🛡️ AegisGateway

### Enterprise LLM API Gateway & Semantic Router

A high-throughput, resilient reverse proxy for enterprise LLM applications. AegisGateway provides **semantic caching, PII protection, provider failover, streaming, and token-level cost tracking** behind an OpenAI-compatible API.

Built to address common production challenges: **high token costs, provider outages, data privacy, and LLM latency.**

---

## ⚡ Architecture

```text
                         ┌──────────────┐
                         │  Client App  │
                         └──────┬───────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │    AegisGateway     │
                    │   FastAPI / Async   │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   ┌─────────────┐      ┌──────────────┐    ┌──────────────┐
   │ PII Shield  │      │ Semantic     │    │   Circuit    │
   │  Scrubber   │      │ Cache        │    │   Breaker    │
   └─────────────┘      └──────┬───────┘    └──────┬───────┘
                                │                    │
                         ┌──────┴──────┐      ┌─────┴──────┐
                         │ Redis +     │      │ LLM        │
                         │ PostgreSQL  │      │ Providers  │
                         │ + pgvector  │      │            │
                         └─────────────┘      └────────────┘
```

## 🧠 Core Engineering

### Semantic Caching

* Generates 384-dimensional embeddings using `sentence-transformers`.
* Checks Redis for exact matches before performing vector search.
* Uses PostgreSQL + `pgvector` for semantic similarity matching.
* Configurable similarity threshold to prevent incorrect cache hits.
* Reduces unnecessary upstream LLM calls and token costs.

### 🔐 PII Protection

* Async middleware inspects outgoing prompts before they reach external providers.
* Detects common PII such as emails, phone numbers, credit cards, and SSNs.
* Replaces sensitive values with safe placeholders such as `[EMAIL_REDACTED]`.

### 🔄 Circuit Breaker & Failover

* Tracks upstream provider health using Redis.
* Opens the circuit after repeated `5xx`/`429` failures.
* Automatically routes requests to a backup LLM provider.
* Prevents cascading failures and improves availability.

### ⚡ Async Streaming & Cost Tracking

* Proxies Server-Sent Events (SSE) using `httpx.AsyncClient`.
* Streams LLM responses chunk-by-chunk without blocking workers.
* Extracts token usage from provider responses.
* Persists usage data to PostgreSQL for cost attribution and billing analytics.

---

## 🛠️ Tech Stack

| Category       | Technology                    |
| -------------- | ----------------------------- |
| API            | FastAPI, Python 3.12, AsyncIO |
| Database       | PostgreSQL 15, pgvector       |
| Cache & State  | Redis 7                       |
| HTTP           | httpx                         |
| Embeddings     | sentence-transformers         |
| Infrastructure | Docker, Docker Compose        |
| LLM Providers  | OpenAI, Anthropic, Groq       |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/aegis-gateway.git
cd aegis-gateway
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aegis_db
REDIS_URL=redis://localhost:6379/0
UPSTREAM_API_KEY=your-api-key
```

### 4. Start infrastructure

```bash
docker compose up -d
```

### 5. Start the gateway

```bash
python -m uvicorn app.main:app --reload
```

The gateway will be available at:

```text
http://localhost:8000
```

---

## 📡 API Usage

AegisGateway exposes an OpenAI-compatible endpoint:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {
        "role": "user",
        "content": "What is the speed of light?"
      }
    ],
    "stream": false
  }'
```

---

## 🎯 Key Features

* ✅ OpenAI-compatible API
* ✅ Semantic response caching
* ✅ Redis exact-match caching
* ✅ PostgreSQL + pgvector similarity search
* ✅ PII redaction middleware
* ✅ Circuit breaker & provider failover
* ✅ Async SSE streaming
* ✅ Token usage tracking
* ✅ Team-level cost attribution
* ✅ Dockerized infrastructure

---

## 📌 Project Goal

AegisGateway is designed as a **production-oriented LLM infrastructure layer**, providing a single secure and resilient interface between applications and multiple LLM providers.
