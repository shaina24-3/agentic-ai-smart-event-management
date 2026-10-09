# Agentic AI Smart Event Management System — Backend

A production-ready, zero-API-key FastAPI backend engineered for intelligent event coordination. The system incorporates an autonomous agent loop, local Retrieval-Augmented Generation (RAG), strict Role-Based Access Control (RBAC), and automated audit logging over a 10-table relational schema.

---

## Architecture Overview

```
[ Client / Frontend ]
          │
          ▼  (REST API / JWT Auth)
┌────────────────────────────────────────────────────────┐
│                     FastAPI App                        │
│  ├── /api/auth       (JWT Token, Hash, RBAC)           │
│  ├── /api/venues     (CRUD & Capacity Validation)      │
│  ├── /api/events     (Scheduling & Slot Management)    │
│  ├── /api/registrations (Atomic Event Booking)         │
│  ├── /api/chat       (Autonomous Agent Engine)         │
│  └── /api/audit-logs (Security & Traceability)         │
└────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌──────────────────┐           ┌──────────────────┐
│   Agent Engine   │           │   Local RAG Engine│
│ ├── Intent Route │           │ ├── Document Store│
│ ├── Tool Runner  │           │ └── Overlap/TFIDF │
│ └── Session Tracing          └──────────────────┘
          │                              │
          └──────────────┬───────────────┘
                         ▼
        ┌──────────────────────────────────┐
        │       SQLAlchemy ORM Layer       │
        │   (PostgreSQL / MySQL / SQLite)  │
        └──────────────────────────────────┘

```

---

## Core Features

* **Zero External API Cost:** Autonomous agent processing and RAG pipeline run entirely on deterministic logic and local Python text processing without requiring paid LLM provider keys.
* **Relational Integrity (10 Tables):** Tracks users, venues, events, registrations, agent sessions, agent runs, tool execution logs, knowledge documents, knowledge chunks, and security audit trails.
* **Fail-Safe Multi-Database Support:** Operates seamlessly on cloud PostgreSQL or MySQL via `DATABASE_URL` and defaults gracefully to a zero-config local SQLite database (`event_system.db`).
* **Autonomous Tool Calling:** The agent dynamically decides when to query the schedule, register attendees, cancel registrations, or retrieve internal FAQ knowledge.
* **Audit Logging:** Automatically logs IP addresses, actions, user IDs, and target resources for critical operations.

---

## Database Schema Design

| Table Name | Primary Role |
| --- | --- |
| `users` | User credentials, roles (`ADMIN`, `ORGANIZER`, `ATTENDEE`), and timestamps |
| `venues` | Physical or virtual locations with strict seating capacities |
| `events` | Event schedule, assigned venue, capacity, and current lifecycle status |
| `registrations` | Unique mapping between attendees and events (`user_id`, `event_id`) |
| `agent_sessions` | Tracks multi-turn conversational threads for users |
| `agent_runs` | Individual user prompts, detected intents, final replies, and latency metrics |
| `tool_calls` | Detailed telemetry of tool executions (`tool_name`, `input`, `output`, `latency_ms`) |
| `knowledge_documents` | Document registry for internal campus/event rulebooks |
| `knowledge_chunks` | Token/word-window chunks of documents for RAG retrieval |
| `audit_logs` | Immutable audit trail capturing operations, IP addresses, and state changes |

---

## Project Structure

```text
.
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── database.py       # Engine binding, connection args, and DB sessions
│   ├── models.py         # 10 relational SQLAlchemy database models
│   ├── schemas.py        # Pydantic request/response validation contracts
│   ├── auth.py           # JWT generation, PassLib hashing, RBAC & audit helper
│   ├── tools.py          # Deterministic tools invoked by the agent
│   ├── rag.py            # Local document ingestion and semantic/keyword scoring
│   ├── agent.py          # Intent routing, execution loop, and state logging
│   └── main.py           # FastAPI endpoints, CORS, and startup seeds
└── event_system.db       # Auto-generated SQLite instance (when local)

```

---

## Environment Configuration

Create a `.env` file in the project root (optional for local SQLite execution):

```env
# Database Connection (Defaults to sqlite:///./event_system.db if omitted)
DATABASE_URL=sqlite:///./event_system.db

# JWT Security Secret
JWT_SECRET=your_super_secret_jwt_key_here

# Server Settings
PORT=8000

```

---

## Local Development & Setup

### 1. Clone & Set Up Environment

```bash
git clone <your-repository-url>
cd <repository-directory>

# From the repository root, enter the backend directory first:
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### 2. Run the Application

On Windows, start the backend from the repository's `backend` directory with:

```powershell
.\run_backend.bat
```

This launcher changes to the `backend` directory and starts Uvicorn with the complete ASGI target `app.main:app`. If starting Uvicorn manually, run it from the `backend` directory and use `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`; `app.main:` is incomplete and prevents Uvicorn from loading the application.

The API will be accessible at `[http://127.0.0.1:8000](http://127.0.0.1:8000)`, matching the frontend's default API URL. Interactive OpenAPI documentation is available at `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`.

---

## API Endpoints Summary

### Authentication (`/api/auth`)

* `POST /api/auth/register` — Create a new attendee account.
* `POST /api/auth/login` — Authenticate and receive a Bearer JWT.
* `GET /api/auth/me` — Inspect profile of the authenticated user.

### Events & Venues

* `GET /api/events` — List all scheduled events.
* `POST /api/events` — Create an event (Admin/Organizer only).
* `GET /api/venues` — List available venues and capacities.
* `POST /api/venues` — Register a new venue (Admin only).

### Registrations

* `POST /api/registrations` — Register for an event slot.
* `DELETE /api/registrations/{event_id}` — Cancel an existing booking.
* `GET /api/registrations/my` — List all bookings for the logged-in user.

### Intelligent Agent (`/api/chat`)

* `POST /api/chat` — Submit a natural language prompt. The agent detects the intent (`REGISTRATION`, `CANCELLATION`, `SEARCH_EVENTS`, `RAG_KNOWLEDGE`), executes the respective tool, updates the database, and returns the response with full telemetry.

### Security & Audit (`/api/audit-logs`)

* `GET /api/audit-logs` — Read system-wide audit logs with client IP tracking (Admin only).

---

## Cloud Deployment (Render)

This repository is optimized for one-click deployment on Render's Python runtime.

### Web Service Settings

1. **Environment:** `Python 3`
2. **Build Command:**
```bash
pip install -r requirements.txt

```


3. **Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000

```


4. **Environment Variables:**
* `PYTHON_VERSION`: `3.11.8` (or `3.10.x`)
* `JWT_SECRET`: `[Set your random secure string]`
* `DATABASE_URL`: *(Leave empty to use automatic local SQLite, or paste an external PostgreSQL/MySQL URL)*



---

## License

This project is licensed under the MIT License. Available for academic, demonstration, and production extension purposes.

---
Live Demo
---
Backend Link -> https://agentic-ai-smart-event-management-2.onrender.com/docs
