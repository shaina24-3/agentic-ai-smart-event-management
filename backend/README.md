
# ⚙️ Smart Event Management — Backend Service & AI Agent

The core backend service for the **Agentic AI Smart Event Management System**. Built with **FastAPI**, **SQLAlchemy 2.0**, **LangGraph**, and **RAG (Retrieval-Augmented Generation)** to power both standard REST API clients and autonomous natural-language workflows.

---

## 📋 Table of Contents
- [Architecture & Design](#-architecture--design)
- [Directory Structure](#-directory-structure)
- [Requirements](#-requirements)
- [Local Setup & Installation](#-local-setup--installation)
- [Database & Dual-Mode Storage](#-database--dual-mode-storage)
- [API Endpoints Reference](#-api-endpoints-reference)
- [LangGraph Agent & Tools](#-langgraph-agent--tools)
- [RAG Policy Retrieval](#-rag-policy-retrieval)
- [Automated Testing](#-automated-testing)
- [Deployment](#-deployment)

---

## 🏛 Architecture & Design

The backend is built with a clean layered architecture ensuring loose coupling between the API, Agent, Service, and Data layers:

```
FastAPI Routers (app/api/)
      │
      ├──────────────────────────────┐
      ▼                              ▼
LangGraph Agent (app/agent/)   Business Services (app/services/)
      │                              │
      ▼                              ▼
Controlled Tools (app/tools/)  SQLAlchemy Models (app/models/)
      │                              │
      ▼                              ▼
RAG Retriever (app/rag/)       Database (SQLite / PostgreSQL)
```

1. **API Layer (`app/api/`)**: Validates HTTP payloads with Pydantic v2 and enforces JWT security/RBAC.
2. **Agent Layer (`app/agent/`)**: State machine compiled with LangGraph to orchestrate reasoning, tool calling, and multi-step execution.
3. **Tool Layer (`app/tools/`)**: Controlled Python functions wrapped for agent access (never allows the LLM direct database write access).
4. **Service Layer (`app/services/`)**: Encapsulates transactional business logic (capacity validation, duplicate booking prevention).
5. **Data Layer (`app/models/`, `app/db/`)**: SQLAlchemy 2.0 ORM models and session management.

---

## 📂 Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app definition & lifespan seed data
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & environment variables
│   │   ├── security.py          # bcrypt password hashing & JWT handling
│   │   └── logging.py           # Standardized application logging
│   ├── db/
│   │   ├── base.py              # Declarative base definition
│   │   └── session.py           # Database engine & sessionmaker
│   ├── models/                  # SQLAlchemy ORM database models
│   │   ├── user.py              # User model (ADMIN, USER)
│   │   ├── venue.py             # Venue model & capacities
│   │   ├── event.py             # Event model & status lifecycle
│   │   ├── registration.py      # Attendee registration model
│   │   └── agent_log.py         # Agent execution audit logging
│   ├── schemas/                 # Pydantic v2 request/response schemas
│   │   ├── user.py
│   │   ├── venue.py
│   │   ├── event.py
│   │   ├── registration.py
│   │   ├── chat.py
│   │   └── agent_log.py
│   ├── services/                # Business logic & domain layer
│   │   ├── auth_service.py
│   │   ├── venue_service.py
│   │   ├── event_service.py
│   │   ├── registration_service.py
│   │   └── observability_service.py
│   ├── tools/                   # Controlled business tools for the agent
│   │   ├── event_tools.py
│   │   ├── venue_tools.py
│   │   ├── registration_tools.py
│   │   └── rag_tools.py
│   ├── rag/                     # RAG document ingestion & vector search
│   │   ├── loader.py            # Markdown document loader (UTF-8/BOM-safe)
│   │   ├── chunker.py           # Section-aware markdown chunker
│   │   └── retriever.py         # Semantic similarity scoring engine
│   └── agent/                   # LangGraph workflow definition
│       ├── state.py             # AgentState schema
│       ├── prompts.py           # System prompts & operational rules
│       ├── nodes.py             # Router, tool execution & synthesizer nodes
│       └── graph.py             # Compiled StateGraph workflow
├── documents/                   # Policy & FAQ documents indexed by RAG
│   ├── cancellation_policy.md
│   ├── event_policy.md
│   ├── registration_policy.md
│   ├── venue_policy.md
│   └── faq.md
├── tests/                       # Complete Pytest test suite
│   ├── conftest.py              # In-memory test db & fixtures
│   ├── test_auth.py             # Auth & registration tests
│   ├── test_events.py           # Event lifecycle & venue conflict tests
│   ├── test_registrations.py    # Capacity & duplicate prevention tests
│   └── test_agent.py            # Multi-step agent & RAG tests
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container build configuration
└── .env.example                 # Environment template
```

---

## 📦 Requirements

* **Python**: 3.11 or higher
* **Pip** package manager

---

## 🚀 Local Setup & Installation

### 1. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Server
```bash
uvicorn app.main:app --reload --port 8000
```

Once running:
* **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🗄 Database & Dual-Mode Storage

The backend supports **dual database modes** configured via `DATABASE_URL`:

1. **Local Mode (Default)**: Uses SQLite (`event_mgmt.db`). Requires zero setup or external services. Tables and pre-seeded accounts are provisioned automatically on startup.
2. **Production Mode**: Set `DATABASE_URL` to a PostgreSQL instance with pgvector:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/event_management
   ```

### Pre-Seeded Default Accounts:
* **Admin**: `admin@eventagent.io` | Password: `admin123`
* **User**: `user@eventagent.io` | Password: `user123`

---

## 📡 API Endpoints Reference

### 1. Authentication (`/api/auth`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `POST` | `/api/auth/register` | Register a new user | ❌ |
| `POST` | `/api/auth/login` | Log in and receive JWT token | ❌ |
| `GET` | `/api/auth/me` | Get current user's profile | ✅ |

### 2. Venues (`/api/venues`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `GET` | `/api/venues` | List all venues & capacities | ❌ |
| `POST` | `/api/venues` | Create a new venue | ✅ (Admin) |
| `GET` | `/api/venues/{id}` | Get venue details | ❌ |

### 3. Events (`/api/events`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `GET` | `/api/events` | List/search events with filters (`query`, `date`, `venue_id`, `available_only`) | ❌ |
| `POST` | `/api/events` | Create new event with venue check | ✅ (Admin) |
| `GET` | `/api/events/{id}` | Get single event details & seats | ❌ |
| `PUT` | `/api/events/{id}` | Update event details | ✅ (Admin) |
| `DELETE`| `/api/events/{id}` | Cancel event | ✅ (Admin) |

### 4. Registrations (`/api`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `POST` | `/api/events/{id}/register` | Register current user for event | ✅ |
| `DELETE`| `/api/events/{id}/register` | Cancel registration & free seat | ✅ |
| `GET` | `/api/registrations/me` | List user's registered passes | ✅ |
| `GET` | `/api/events/{id}/registrations` | View attendee roster | ✅ (Admin) |

### 5. AI Agent & Observability (`/api`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `POST` | `/api/chat` | Conversational agent interface | Optional |
| `GET` | `/api/observability/runs` | Inspect agent execution logs & latency | ✅ |

---

## 🤖 LangGraph Agent & Tools

The agent uses a compiled **LangGraph `StateGraph`**:

```
           ┌───────────────┐
           │  router_node  │
           └───────┬───────┘
                   │
                   ▼
        ┌───────────────────────┐
        │  tool_execution_node  │
        └──────────┬────────────┘
                   │
                   ▼
        ┌───────────────────────┐
        │    synthesis_node     │
        └──────────┬────────────┘
                   │
                   ▼
                 [END]
```

### Supported Intent Routes:
* `SEARCH_EVENT`: Discovers events by topic, date, or seat availability.
* `MULTI_STEP_SEARCH_AND_REGISTER`: Executes compound goals (e.g. *"Find an AI workshop and register me"*).
* `REGISTER_EVENT`: Books a seat with capacity validation.
* `CANCEL_REGISTRATION`: Releases a participant's seat.
* `CHECK_VENUE`: Checks physical venue schedules for scheduling conflicts.
* `POLICY_RAG`: Answers questions grounded in organizational guidelines.

---

## 🔍 RAG Policy Retrieval

The RAG system indexes documents in `documents/` on startup:
* `cancellation_policy.md` — Refund rules, cancellation windows.
* `event_policy.md` — Minimum advance notice, capacity limits.
* `registration_policy.md` — Limits per user, pass transferability.
* `venue_policy.md` — Venue specifications and facilities.
* `faq.md` — Common user questions.

Uses section-aware chunking with header context inheritance and ranked term-density similarity scoring.

---

## 🧪 Automated Testing

Run the full automated test suite using `pytest`:

```bash
pytest -v
```

### Test Coverage Summary:
* `tests/test_auth.py`: User registration, duplicate email rejection, JWT login, and profile lookup.
* `tests/test_events.py`: Event creation, venue double-booking prevention, capacity limits, and filtering.
* `tests/test_registrations.py`: Registration confirmation, duplicate prevention, and seat release.
* `tests/test_agent.py`: Search intent routing, multi-step execution, RAG policy retrieval, and observability audit records.

---

## ☁️ Deployment

### Deploying to Render.com (Zero Environment Variables Needed)
1. Push this backend repository to GitHub.
2. In Render, create a **New Web Service** linked to your repo.
3. Set the following:
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Leave the **Environment Variables** section empty (the backend runs with safe built-in defaults).
5. Click **Deploy Web Service**.

### Docker Deployment
```bash
docker build -t smart-event-backend .
docker run -p 8000:8000 smart-event-backend
```
Live Deploy Demo
---
link-> https://agentic-ai-smart-event-management-6.onrender.com/docs

