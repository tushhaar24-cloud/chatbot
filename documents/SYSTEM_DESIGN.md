# System Design

Companion to [BRD.md](BRD.md). The BRD says *what* to build; this says *how the
pieces fit* and *which rules the code must obey*. Every milestone is checked
against this document before it is called done.

---

## 1. The one-sentence design

> A React client talks HTTP to a FastAPI server; inside that server, each request
> passes through exactly one chain of layers, and each layer is allowed to know
> about only the layer directly below it.

Everything below is a consequence of that sentence.

---

## 2. Physical architecture (processes on your machine)

```text
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│  Browser         │        │  Vite dev server │        │  Uvicorn         │
│  localhost:5173  │◄──────►│  (serves the JS) │        │  localhost:8010  │
└────────┬─────────┘        └──────────────────┘        └────────┬─────────┘
         │                                                        │
         │  HTTP/JSON  +  Authorization: Bearer <JWT>             │
         └────────────────────────────────────────────────────────┘
                                                                  │
                          ┌───────────────────────────────────────┴───┐
                          │                                           │
                          ▼                                           ▼
              ┌────────────────────┐                     ┌────────────────────┐
              │  PostgreSQL 18     │                     │  Groq API          │
              │  localhost:5432    │                     │  api.groq.com      │
              │  db: chatbot_app   │                     │  (over the network)│
              └────────────────────┘                     └────────────────────┘
```

Three processes, two external dependencies. The browser never talks to
PostgreSQL or to Groq — it only ever talks to FastAPI. That single rule is what
keeps the AI API key secret and the database unreachable from the internet.

---

## 3. Logical architecture (layers inside FastAPI)

```text
          HTTP request
               │
               ▼
     ┌───────────────────┐   HTTP only: status codes, headers, JSON.
     │  Route            │   Parses input, calls one service, maps
     │  api/routes/*.py  │   domain errors to HTTP responses.
     └─────────┬─────────┘   NO business logic. NO database queries.
               │
               ▼
     ┌───────────────────┐   Business rules: ownership, context limits,
     │  Service          │   orchestration, transaction boundaries.
     │  services/*.py    │   Knows nothing about HTTP.
     └────┬─────────┬────┘   Raises domain exceptions, never HTTPException.
          │         │
          ▼         ▼
 ┌────────────┐  ┌────────────────┐   Repository: the ONLY place that
 │ Repository │  │  AI Service    │   writes SQLAlchemy queries.
 │ repos/*.py │  │ ai_service.py  │   AI Service: the ONLY place that
 └─────┬──────┘  └───────┬────────┘   knows the LLM wire format.
       │                 │
       ▼                 ▼
 ┌────────────┐   ┌──────────────┐
 │  Model     │   │  Groq HTTP   │
 │ models/*.py│   │  API         │
 └─────┬──────┘   └──────────────┘
       ▼
 ┌────────────┐
 │ PostgreSQL │
 └────────────┘

Cross-cutting (used by any layer): core/config.py, core/security.py,
core/exceptions.py, schemas/*.py
```

### The dependency rule

**Dependencies point downward only.** A lower layer never imports a higher one.

| Layer | May import | May NOT import |
|---|---|---|
| Route | schemas, services, core | repositories, models directly |
| Service | repositories, ai_service, schemas, core, models | anything in `api/`, `fastapi` |
| Repository | models, core | services, routes |
| Model | core | everything else |
| AI Service | core, schemas | repositories, models, routes |

The practical test: **if you cannot unit-test a service without starting a web
server, the rule has been broken.**

### Why each boundary exists

| Boundary | What it buys you |
|---|---|
| Route ≠ Service | You can ask "did this fail before or after the service call?" and a stack trace answers it |
| Service ≠ Repository | Milestone 9 can test business rules with a fake repository, no database |
| Service ≠ AI Service | Swapping Groq → OpenAI → Claude touches one file |
| Schema ≠ Model | The API contract can stay stable while the tables change — and `password_hash` can never leak into a response |

---

## 4. Layer responsibilities in detail

### 4.1 Schemas (`app/schemas/`) — the API contract

Pydantic models describing what goes **in** and what comes **out**.

- `XxxCreate` — request body. Validation lives here (`EmailStr`, `min_length`).
- `XxxResponse` — response body. Only fields safe to expose.

**Rule: an ORM model is never returned from a route.** `User` has
`password_hash`; `UserResponse` does not. Return the ORM object once and you
have shipped a password hash to the browser.

### 4.2 Routes (`app/api/routes/`) — HTTP translation

A route function should read like a table of contents, roughly 3–8 lines:

```python
@router.post("/conversations", response_model=ConversationResponse, status_code=201)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return conversation_service.create(db, user=current_user, title=payload.title)
```

Its four jobs, and no fifth: declare the contract, resolve dependencies
(session, current user), call **one** service, return.

### 4.3 Services (`app/services/`) — business rules

Where "a user may only see their own conversations" and "send at most N
previous messages to the model" live. Services own the **transaction
boundary**: a service method either commits a coherent unit of work or rolls
it back. Repositories do not commit.

Services raise **domain exceptions** (`ConversationNotFound`), never
`HTTPException` — that would make the service untestable outside HTTP and leak
web concerns into business logic.

### 4.4 Repositories (`app/repositories/`) — data access

Every `select()`, `db.add()`, `db.delete()` lives here. Repositories take a
`Session` as an argument; they never create one. They return ORM objects or
`None`. They contain no ownership comparison — that is a business rule.

### 4.5 AI Service (`app/services/ai_service.py`) — the provider boundary

The only module that knows:

- the URL `/chat/completions`
- the header `Authorization: Bearer ...`
- the body shape `{"model", "messages", "temperature", "max_tokens"}`
- where the reply hides: `choices[0].message.content`

It accepts a plain list of `{"role", "content"}` dicts and returns plain text
plus usage metadata. It converts provider failures into **our** exception types
so that nothing above it ever catches an `httpx` error.

---

## 5. Request lifecycle — the trace to memorise

`POST /api/conversations/{id}/messages` with `{"message": "What is FastAPI?"}`

```text
 1  MessageInput.tsx        user hits Send; local state -> sending
 2  chatApi.ts              sendMessage(conversationId, text)
 3  api.ts                  fetch(POST, + Content-Type, + Authorization: Bearer)
 ─────────────────────────── network ───────────────────────────
 4  CORSMiddleware          origin http://localhost:5173 allowed?
 5  FastAPI router          match path -> chat.send_message
 6  Depends(get_db)         open a Session for this request
 7  Depends(get_current_user)  decode JWT -> load User   (401 if bad)
 8  Pydantic                validate body -> MessageCreate  (422 if bad)
 9  chat_service.send_message(db, user, conversation_id, text)
10    conversation_repo.get(db, conversation_id)
11    if none OR conversation.user_id != user.id -> ConversationNotFound (404)
12    message_repo.create(db, role="user", content=text)   <- saved BEFORE the LLM
13    message_repo.list_recent(db, conversation_id, limit=N)
14    build [system prompt] + [history] + [new message]
15    ai_service.complete(messages)  ──────────► Groq  (timeout, retries here)
16    message_repo.create(db, role="assistant", content=reply)
17    conversation_repo.touch(db, conversation)    updated_at = now()
18    db.commit()
19  route returns MessageResponse -> JSON, 201
 ─────────────────────────── network ───────────────────────────
20  api.ts                  response.ok? else throw ApiError
21  useChat hook            append assistant message, sending -> idle
22  MessageList.tsx         re-render
```

**Step 12 before step 15 is deliberate.** Persist the user message *before*
calling the LLM, so a timeout at step 15 never loses what they typed.

**Step 11 returns 404, not 403.** A 403 would confirm the conversation exists.
Same response for "no such conversation" and "not yours".

---

## 6. Data model

```text
users                   conversations             messages
─────                   ─────────────             ────────
id           uuid PK    id          uuid PK       id              uuid PK
email        UNIQUE ◄───user_id     FK CASCADE ◄──conversation_id FK CASCADE
password_hash           title                     role   CHECK(user|assistant)
created_at              created_at                content TEXT
updated_at              updated_at                created_at
```

Design decisions and their reasons:

| Decision | Reason |
|---|---|
| UUID primary keys | IDs appear in URLs; sequential ints leak volume and invite probing |
| `email UNIQUE` | the service-layer duplicate check has a race; only the index is safe |
| CASCADE on both FKs | FR-08 must hold even for deletes that bypass the ORM |
| index on `messages.conversation_id` | the hottest query in the app filters on it |
| `role` CHECK, not ENUM | `system` / `tool` roles arrive later; CHECK is a one-line change |
| `content` as TEXT | AI replies have no sensible length cap |
| messages have no `updated_at` | messages are immutable; editing history silently changes model input |

Ownership chain: `messages → conversations → users`. Authorisation always
walks it — there is no direct `message.user_id` shortcut to get out of sync.

---

## 7. API contract

| Method | Path | Auth | Success | Notes |
|---|---|---|---|---|
| POST | `/api/auth/register` | — | 201 | 409 if email taken |
| POST | `/api/auth/login` | — | 200 | returns JWT; 401 on bad credentials |
| GET | `/api/conversations` | yes | 200 | only the caller's, newest first |
| POST | `/api/conversations` | yes | 201 | title defaults to "New Conversation" |
| GET | `/api/conversations/{id}` | yes | 200 | includes messages; 404 if not yours |
| DELETE | `/api/conversations/{id}` | yes | 204 | cascades to messages |
| POST | `/api/conversations/{id}/messages` | yes | 201 | the AI call |

Conventions: plural nouns, no verbs in paths; `201` for creation, `204` for
delete; all errors as `{"detail": "..."}` so the frontend has one shape to parse.

---

## 8. Error model

One domain exception per failure mode, defined in `app/core/exceptions.py`,
mapped to HTTP **once** in a handler rather than in every route:

| Domain exception | HTTP | User sees | Logged |
|---|---|---|---|
| (Pydantic validation) | 422 | which field is wrong | no |
| `InvalidCredentials` | 401 | "Invalid email or password" | attempt, never the password |
| `EmailAlreadyRegistered` | 409 | "That email is already registered" | no |
| `ConversationNotFound` | 404 | "Conversation not found" | user id + conversation id |
| `AITimeout` | 504 | "The assistant took too long. Try again." | duration, model |
| `AIRateLimited` | 429 | "Busy right now. Try again shortly." | retry-after |
| `AIProviderError` | 502 | "The assistant is unavailable." | status + provider body |
| anything else | 500 | "Something went wrong." | full traceback |

Two standing rules: **the user never sees a stack trace or a provider message**,
and **the log always holds the real cause**. The failure that teaches this best:
a wrong database password returns HTTP 200 from `/api/health` with
`database: "unavailable"` — the browser sees success, the log holds the truth.

Frontend mirror ([api.ts](../frontend/src/services/api.ts)): `fetch()` rejects
only on network-level failure; an HTTP 500 **resolves normally**. So the client
needs both a `try/catch` and an `if (!response.ok)`.

---

## 9. Security model

| Requirement | Where it is enforced |
|---|---|
| Passwords never stored plain | `core/security.py` hashes on registration |
| Protected endpoints | `Depends(get_current_user)` on every route but auth |
| Users cannot read others' data | ownership check in the **service**, not the route |
| AI key never reaches the browser | key lives in `backend/.env`; only `ai_service` reads it |
| No secrets in git | `.env` gitignored; `.env.example` documents the shape |
| No secrets in logs | log ids and durations, never tokens, keys or passwords |
| Only our frontend may call the API | CORS allowlist from `CORS_ORIGINS` |

`frontend/.env` is **public** — everything in it ships in the JS bundle. It may
contain only `VITE_API_BASE_URL`.

---

## 10. Frontend design

```text
Component          rendering + local UI state only
    │
    ▼
Hook               orchestration: loading / error / data for one feature
    │
    ▼
Feature API        conversationApi.ts, chatApi.ts — endpoint shapes
    │
    ▼
api.ts             the ONLY fetch() in the app: base URL, auth header,
                   error normalisation
```

**Rule: no component calls `fetch` directly.** That single wrapper is where the
`Authorization` header gets attached in Milestone 3 — one edit instead of ten.

Every async operation carries the same three states — `loading`, `data`,
`error` — established in Milestone 1's health button and reused for chat.
`setLoading(false)` always goes in `finally`, or the spinner never stops on
failure.

---

## 11. Configuration

All configuration enters through `app/core/config.py`. **No other module reads
`os.environ`.** A missing required variable fails at startup, not at 2am in a
request handler.

```text
backend/.env          secret   database credentials, AI_API_KEY    gitignored
backend/.env.example  —        documents the shape                 committed
frontend/.env         public   VITE_API_BASE_URL only              gitignored
```

---

## 12. Milestone map

| Milestone | Layers it fills in | Status |
|---|---|---|
| 1 Setup | process wiring, config, `api.ts`, CORS | done |
| 2 Database | models + schema management | done |
| 3 Auth | `core/security`, `schemas/auth`, `repositories/user`, `services/auth`, `routes/auth`, `get_current_user` | done |
| 4 Conversation APIs | conversation repository + service + routes | next |
| 5 Chat without AI | message repository, `chat_service` with a **mock** reply | |
| 6 LLM | `ai_service` replaces the mock — one file changes | |
| 7 Context | history window inside `chat_service` | |
| 8 Errors | `core/exceptions` + handlers, frontend error states | |
| 9 Tests | fake repositories, mocked AI | |
| 10 Docs | this file + API + runbook | |

Milestone 5 returning a fake AI reply is the most valuable idea in the plan: it
proves the entire pipeline works **before** the network and a third party can
be blamed. When the mock works and the real call does not, the bug is provably
in `ai_service`.

---

## 13. The rules, as a checklist

Every milestone is reviewed against these:

1. No business logic in a route.
2. No SQL outside a repository.
   *Known exception:* `GET /api/health` in `main.py` runs `SELECT 1` inline.
   A liveness probe is infrastructure, not business logic, and giving it a
   repository would add a layer that exists only to be mocked. This is the
   only place in the codebase allowed to break rule 2, and it is written down
   here so it stays a decision rather than becoming a precedent.
3. No `HTTPException` raised by a service.
4. No ORM model returned from a route — always a response schema.
5. No provider-specific code outside `ai_service.py`.
6. No `fetch()` outside `api.ts`.
7. No `os.environ` outside `config.py`.
8. No secret in `frontend/`, in git, or in a log line.
9. Ownership checked on every request that names a resource id.
10. Every new failure mode gets a domain exception and a user-safe message.
