# Business Requirements Document (BRD)

## Project Name

**AI Assistant — AI Application Development Learning Project**

## Document Purpose

This document defines the requirements for building a small but production-style AI Chat Application.

The primary objective is **not only to build the application**, but also to use the application as a learning project for understanding AI Application Development.

The developer/AI coding assistant must therefore explain the architecture, implementation decisions, code, API communication, debugging approach, and AI integration while developing the application.

---

# 1. Project Objective

Build a web-based AI Assistant where users can:

1. Create a conversation.
2. Send messages to an AI model.
3. Receive AI-generated responses.
4. View conversation history.
5. Continue previous conversations.
6. Delete conversations.
7. Handle loading and error states.
8. Persist conversations and messages in PostgreSQL.

The application should provide a clean foundation that can later be extended into:

- AI Document Summarizer
- Document Q&A
- RAG
- Vector Search
- Tool Calling
- AI Agents
- AI Evaluation
- Domain-specific AI Assistant

---

# 2. Primary Learning Objective

The developer must build the application in a way that teaches the following concepts:

```text
Frontend
   ↓
React
   ↓
HTTP / REST API
   ↓
FastAPI
   ↓
Service Layer
   ↓
LLM API
   ↓
FastAPI
   ↓
Database
   ↓
React
```

The learner must understand:

- How React calls a backend API.
- How FastAPI receives the request.
- How request validation works.
- How FastAPI calls an external AI API.
- How the AI response is processed.
- How data is stored in PostgreSQL.
- How the backend sends a response to React.
- How React updates the UI.
- How authentication/API keys are handled.
- How to debug the complete request flow.
- How AI-specific errors differ from normal API errors.

---

# 3. Target Users

## Primary User

A developer who wants to learn how to build AI-powered applications.

## Secondary User

A normal application user who wants to communicate with an AI assistant.

---

# 4. Scope

## Phase 1 — MVP

The first version must contain:

### Frontend

- Login page
- Chat page
- Conversation sidebar
- New conversation
- Message input
- Send button
- User messages
- AI messages
- Loading indicator
- Error display
- Conversation history
- Delete conversation
- Responsive UI

### Backend

- Authentication
- User API
- Conversation API
- Message API
- AI/LLM service
- Request validation
- Error handling
- Database persistence
- Logging

### Database

Store:

- Users
- Conversations
- Messages

### AI

Integrate one LLM provider through the backend.

The exact provider/model should be configurable through environment variables rather than hard-coded.

---

# 5. Out of Scope for Phase 1

Do NOT implement these in the first version:

- RAG
- Vector database
- Document upload
- Embeddings
- AI agents
- Tool calling
- Web search
- Fine-tuning
- Multi-agent systems
- Voice
- Image generation
- Complex role/permission systems
- Microservices
- Kubernetes

These will be introduced in later learning phases.

---

# 6. High-Level Architecture

The application should follow this architecture:

```text
                    ┌─────────────────────┐
                    │       User          │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │   React Frontend    │
                    └──────────┬──────────┘
                               │
                         HTTP / REST
                               │
                               ↓
                    ┌─────────────────────┐
                    │    FastAPI API      │
                    └──────────┬──────────┘
                               │
                     ┌─────────┴─────────┐
                     │                   │
                     ↓                   ↓
            ┌────────────────┐   ┌────────────────┐
            │  PostgreSQL    │   │   AI Service   │
            │                │   │                │
            │ Users          │   │ LLM API        │
            │ Conversations  │   │                │
            │ Messages       │   │                │
            └────────────────┘   └───────┬────────┘
                                         │
                                         ↓
                                  ┌──────────────┐
                                  │  LLM Model   │
                                  └──────────────┘
```

---

# 7. Technology Requirements

## Frontend

Use:

- React
- TypeScript
- Modern React patterns
- React Hooks
- Fetch API or Axios
- CSS or an appropriate styling solution

Do not introduce unnecessary frontend frameworks unless there is a clear reason.

---

## Backend

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- Appropriate AI SDK/API client

Backend should follow a clean separation of responsibilities.

Suggested structure:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   └── chat.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── conversation.py
│   │   └── chat.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── message.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── conversation_service.py
│   │   └── ai_service.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── conversation_repository.py
│   │   └── message_repository.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── migrations/
│   │
│   └── core/
│       ├── config.py
│       └── security.py
│
└── tests/
```

The exact structure may be adjusted if the project requirements justify it, but responsibilities should remain separated.

---

# 8. Functional Requirements

## FR-01 — User Registration

The user should be able to create an account.

Input:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Backend should:

1. Validate the request.
2. Check whether the user already exists.
3. Hash the password.
4. Store the user.
5. Return an appropriate response.

Passwords must never be stored as plain text.

---

# 9. FR-02 — User Login

User should be able to log in.

Input:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Backend should authenticate the user and return an authentication token/session according to the selected authentication architecture.

The frontend must use the authentication mechanism when calling protected APIs.

---

# 10. FR-03 — Create Conversation

User can create a new conversation.

Example:

```text
New Conversation
```

Backend creates:

```text
conversation_id
user_id
title
created_at
updated_at
```

Initially the title can be:

```text
New Conversation
```

Later it may be generated automatically.

---

# 11. FR-04 — Send Chat Message

User enters:

```text
Explain what FastAPI is.
```

Frontend sends:

```http
POST /api/conversations/{conversation_id}/messages
```

Request:

```json
{
  "message": "Explain what FastAPI is."
}
```

Backend flow:

```text
Receive request
      ↓
Authenticate user
      ↓
Validate request
      ↓
Verify conversation ownership
      ↓
Save user message
      ↓
Retrieve conversation context
      ↓
Build AI request
      ↓
Call LLM
      ↓
Receive AI response
      ↓
Save AI message
      ↓
Return response
```

Response:

```json
{
  "message_id": "uuid",
  "role": "assistant",
  "content": "FastAPI is a Python web framework...",
  "created_at": "..."
}
```

---

# 12. FR-05 — Conversation Context

When a user sends multiple messages:

```text
User:
What is FastAPI?

AI:
FastAPI is...

User:
Why is it used?

AI:
It is commonly used...
```

The AI should receive appropriate conversation history so that the second question can be interpreted in context.

The backend should control how much conversation history is sent to the model.

Do not blindly send unlimited conversation history.

---

# 13. FR-06 — Conversation List

Frontend should display the user's previous conversations.

Example:

```text
Conversations

FastAPI explanation
React authentication
Python questions
AI architecture
```

API:

```http
GET /api/conversations
```

Only conversations belonging to the authenticated user should be returned.

---

# 14. FR-07 — Get Conversation

API:

```http
GET /api/conversations/{id}
```

Response should include the conversation and its messages.

Example:

```json
{
  "id": "conversation-id",
  "title": "FastAPI explanation",
  "messages": [
    {
      "role": "user",
      "content": "What is FastAPI?"
    },
    {
      "role": "assistant",
      "content": "FastAPI is..."
    }
  ]
}
```

---

# 15. FR-08 — Delete Conversation

User should be able to delete a conversation.

API:

```http
DELETE /api/conversations/{conversation_id}
```

Backend must verify that the authenticated user owns the conversation.

---

# 16. FR-09 — Loading State

While the AI request is processing:

```text
User message
       ↓
      ...
AI is thinking
```

The Send button should be handled appropriately to prevent accidental duplicate requests.

---

# 17. FR-10 — Error Handling

The application should handle:

### Frontend errors

- Network failure
- Backend unavailable
- Invalid response
- Request timeout

### Backend errors

- Validation error
- Authentication failure
- Database error
- AI API failure
- AI timeout
- Rate limiting
- Unexpected exception

The user should receive a useful error message without exposing internal implementation details or secrets.

---

# 18. Database Requirements

Use PostgreSQL.

## Users

Suggested fields:

```text
id
email
password_hash
created_at
updated_at
```

---

## Conversations

Suggested fields:

```text
id
user_id
title
created_at
updated_at
```

Relationship:

```text
User
  │
  └── has many Conversations
```

---

## Messages

Suggested fields:

```text
id
conversation_id
role
content
created_at
```

Relationship:

```text
Conversation
     │
     └── has many Messages
```

Roles:

```text
user
assistant
```

The schema can be extended later for system messages and tool messages.

---

# 19. API Requirements

Initial API design:

```text
POST   /api/auth/register
POST   /api/auth/login

GET    /api/conversations
POST   /api/conversations
GET    /api/conversations/{id}
DELETE /api/conversations/{id}

POST   /api/conversations/{id}/messages
```

Every protected endpoint must authenticate the user.

---

# 20. AI Service Architecture

Do not call the LLM directly from route functions.

Avoid:

```python
@app.post("/chat")
async def chat():
    # 100 lines of AI logic here
```

Instead:

```text
Route
  ↓
Service
  ↓
AI Service
  ↓
LLM Provider
```

Example:

```python
@router.post(...)
async def send_message(...):
    return await chat_service.send_message(...)
```

Then:

```text
chat_service
      ↓
ai_service
      ↓
LLM provider
```

This separation will make it easier to replace the model/provider later.

---

# 21. AI Configuration

AI configuration must come from environment variables.

Example:

```text
AI_API_KEY=
AI_MODEL=
AI_TEMPERATURE=
AI_MAX_TOKENS=
```

Do not hard-code secrets in source code.

Do not expose the AI API key to React.

Architecture:

```text
React
  ↓
FastAPI
  ↓
AI API key
  ↓
LLM Provider
```

---

# 22. Prompt Requirements

The AI service should use a system instruction.

Example concept:

```text
You are a helpful AI assistant.

Answer questions clearly and accurately.

If you are uncertain, state the uncertainty instead of
inventing information.
```

The exact prompt should be configurable and easy to modify.

Do not scatter prompt strings throughout the application.

---

# 23. AI Request Structure

The AI service should conceptually construct:

```text
System instruction
       +
Conversation history
       +
Current user message
       ↓
LLM
```

Example:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant."
    },
    {
      "role": "user",
      "content": "What is FastAPI?"
    },
    {
      "role": "assistant",
      "content": "FastAPI is..."
    },
    {
      "role": "user",
      "content": "Why is it useful?"
    }
  ]
}
```

The exact API format depends on the selected LLM provider.

---

# 24. Security Requirements

The application must:

- Hash passwords.
- Protect authenticated endpoints.
- Never expose AI API keys to the frontend.
- Validate user input.
- Validate conversation ownership.
- Prevent users from accessing another user's conversations.
- Avoid logging secrets.
- Avoid returning stack traces to users.
- Store secrets in environment variables.
- Apply appropriate CORS configuration.
- Validate AI output where structured data is expected.

---

# 25. Logging

Backend should log useful diagnostic information.

Example:

```text
Request received
Conversation ID
User ID
AI request started
AI request completed
AI request duration
Database operation status
```

Do NOT log:

- Passwords
- API keys
- Authentication tokens
- Sensitive secrets

If message content is logged, explain the privacy implications and make logging configurable.

---

# 26. Observability Requirements

For AI requests, capture useful metrics such as:

```text
Model
Request duration
Response duration
Token usage if available
Error status
Retry count
```

The first version does not need a complete observability platform.

Structured application logging is sufficient.

---

# 27. Frontend Requirements

Suggested structure:

```text
src/
│
├── components/
│   ├── Chat/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageInput.tsx
│   │   └── MessageBubble.tsx
│   │
│   └── Conversation/
│       ├── ConversationList.tsx
│       └── ConversationItem.tsx
│
├── pages/
│   ├── Login.tsx
│   └── Chat.tsx
│
├── services/
│   ├── api.ts
│   ├── authApi.ts
│   ├── conversationApi.ts
│   └── chatApi.ts
│
├── hooks/
│
├── types/
│
└── utils/
```

Again, this structure can be modified if a better project-specific organization is justified.

---

# 28. Frontend API Communication

Create a clear API layer.

Avoid putting API calls directly into every UI component.

Prefer:

```text
Component
   ↓
Hook / API function
   ↓
API client
   ↓
FastAPI
```

Example conceptual flow:

```text
MessageInput
     ↓
sendMessage()
     ↓
chatApi.ts
     ↓
POST /api/conversations/{id}/messages
     ↓
FastAPI
```

This is an important learning requirement.

---

# 29. UI Requirements

The chat interface should include:

### Sidebar

```text
+ New Chat

Previous conversations
----------------------
FastAPI explanation
Python questions
AI concepts
```

### Main chat area

```text
User:
What is an API?

AI:
An API is...
```

### Input area

```text
┌──────────────────────────────┐
│ Type your message...         │
└───────────────────────┬──────┘
                        │
                      Send
```

---

# 30. Non-Functional Requirements

## Performance

The application should provide clear loading feedback while waiting for AI responses.

## Maintainability

Frontend, backend, database, and AI logic should have clear boundaries.

## Extensibility

The architecture must allow future addition of:

```text
RAG
Embeddings
Vector DB
Tool Calling
Agents
```

without rewriting the entire application.

## Security

Secrets must never be exposed to the frontend.

## Reliability

AI failures should not crash the entire application.

---

# 31. Testing Requirements

Implement basic tests for:

### Backend

- Registration
- Login
- Conversation creation
- Conversation retrieval
- Conversation ownership
- Message creation
- Validation errors
- AI service failure

### Frontend

- Login
- Conversation selection
- Message sending
- Loading state
- Error state

The AI model itself should be mocked in automated backend tests.

Tests should not make real AI API calls by default.

---

# 32. Error Scenarios to Test

The developer must deliberately test:

```text
Frontend
   ↓
Backend unavailable

Backend
   ↓
Invalid request

Backend
   ↓
Unauthenticated request

Backend
   ↓
Unauthorized conversation

Backend
   ↓
Database unavailable

Backend
   ↓
AI API unavailable

Backend
   ↓
AI timeout

Backend
   ↓
AI rate limit

Backend
   ↓
Unexpected AI response
```

The learner should understand how each failure appears in:

```text
Browser
 ↓
Network tab
 ↓
FastAPI logs
 ↓
AI service
```

---

# 33. Debugging Requirements

Debugging is a core learning objective.

For every major feature, document:

```text
1. What request is sent?
2. Which endpoint receives it?
3. What request body is sent?
4. What headers are sent?
5. What authentication is used?
6. What response is returned?
7. What status code is returned?
8. What happens in the FastAPI route?
9. What service is called?
10. What database operation occurs?
11. What AI request is sent?
12. What AI response is received?
13. How does the response reach React?
```

The learner should use:

```text
Chrome DevTools
Network tab
Console
FastAPI logs
Python debugger
Postman/HTTP client
PostgreSQL tools
```

---

# 34. Learning Mode — Critical Requirement

The application is being built specifically as a learning project.

Therefore, the AI coding assistant must NOT simply generate the complete application without explanation.

For each implementation step:

### Step 1 — Explain the requirement

Explain:

```text
What are we building?
Why do we need it?
Where does it fit in the architecture?
```

### Step 2 — Show the design

Explain:

```text
Frontend
 ↓
API
 ↓
Backend
 ↓
Service
 ↓
Database / AI
```

### Step 3 — Implement

Provide the code.

### Step 4 — Explain the code

For important functions explain:

- Input
- Output
- Responsibility
- Why this approach is used
- Alternatives
- Common mistakes

### Step 5 — Run

Tell the learner how to run it.

### Step 6 — Test

Provide test scenarios.

### Step 7 — Debug

Explain how to investigate failures.

---

# 35. Teaching Rules for the AI Coding Assistant

When developing this project, follow these rules.

## Rule 1

Do not make large unexplained changes.

Implement the application incrementally.

## Rule 2

Before modifying multiple files, explain which files will change and why.

## Rule 3

For every API endpoint explain:

```text
HTTP method
URL
Request
Headers
Authentication
Response
Status codes
```

## Rule 4

For every database operation explain:

```text
Model
Table
Relationship
Query
Transaction
```

## Rule 5

For every AI call explain:

```text
Model
Prompt
Messages
Parameters
Input
Output
Token usage
Errors
```

## Rule 6

When debugging, don't immediately change code.

First identify:

```text
Expected behavior
Actual behavior
Difference
Failure layer
Root cause
Fix
```

## Rule 7

Prefer simple implementations over unnecessary abstractions.

## Rule 8

Do not introduce an AI framework unless there is a clear learning or architectural reason.

First understand the underlying LLM API.

---

# 36. Development Milestones

The project should be implemented in these milestones.

## Milestone 1 — Project Setup

Build:

```text
React
+
FastAPI
+
PostgreSQL
```

Verify:

```text
React → FastAPI → React
```

---

## Milestone 2 — Database

Implement:

```text
Users
Conversations
Messages
```

Verify database connectivity and migrations.

---

## Milestone 3 — Authentication

Implement:

```text
Register
Login
Protected API
```

Verify authentication using browser/API tools.

---

## Milestone 4 — Conversation APIs

Implement:

```text
Create conversation
List conversations
Get conversation
Delete conversation
```

---

## Milestone 5 — Basic Chat Without AI

Before integrating AI, verify:

```text
React
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
FastAPI
 ↓
React
```

Store user messages and return a temporary/mock assistant response.

This milestone is important because it isolates normal application/API problems from AI problems.

---

## Milestone 6 — Integrate LLM

Replace the mock assistant response with an actual LLM.

Flow:

```text
React
 ↓
FastAPI
 ↓
AI Service
 ↓
LLM
 ↓
AI Service
 ↓
FastAPI
 ↓
React
```

---

## Milestone 7 — Conversation Context

Send previous messages as appropriate context to the model.

Implement reasonable context limits.

---

## Milestone 8 — Error Handling

Test:

```text
AI timeout
AI API error
Invalid request
Authentication error
Database error
Network error
```

---

## Milestone 9 — Testing

Add backend and frontend tests.

Mock external AI calls.

---

## Milestone 10 — Documentation

Document:

```text
Architecture
API endpoints
Database schema
AI integration
Environment configuration
Running locally
Debugging
Known limitations
```

---

# 37. Future Roadmap

After the MVP is understood, extend the same project.

## Version 2 — AI Document Summarizer

Add:

```text
PDF upload
 ↓
Text extraction
 ↓
LLM
 ↓
Summary
```

---

## Version 3 — RAG

Add:

```text
Documents
 ↓
Chunking
 ↓
Embeddings
 ↓
pgvector
 ↓
Retrieval
 ↓
LLM
```

---

## Version 4 — AI Database Assistant

Add controlled tools:

```text
LLM
 ↓
Tool calling
 ↓
PostgreSQL
 ↓
Result
 ↓
LLM
```

---

## Version 5 — AI Agent

Add:

```text
LLM
+
Tools
+
State
+
Workflow
```

---

# 38. Acceptance Criteria

The MVP is considered complete when:

### Frontend

- User can register/login.
- User can create a conversation.
- User can send a message.
- User can see AI responses.
- User can view previous conversations.
- User can switch conversations.
- User can delete conversations.
- Loading states work.
- Errors are displayed appropriately.

### Backend

- APIs are implemented.
- Requests are validated.
- Authentication works.
- Authorization is enforced.
- Database persistence works.
- AI integration works.
- AI errors are handled.
- Secrets are protected.

### Database

- Users are persisted.
- Conversations are persisted.
- Messages are persisted.
- Relationships work correctly.

### AI

- Backend successfully communicates with the configured LLM.
- Conversation context is supplied appropriately.
- AI failures are handled.
- AI API keys are not exposed to the frontend.

### Learning

The learner can explain:

```text
How React calls FastAPI
How FastAPI validates a request
How authentication works
How FastAPI calls the LLM
How prompts are constructed
How the LLM response is processed
How messages are stored
How the response returns to React
How to debug a failed API request
How to debug an AI request
```

---

# 39. Definition of Done

The feature is not considered complete merely because the UI works.

For each feature, the learner must be able to explain:

```text
WHAT
What did we build?

WHY
Why did we build it this way?

HOW
How does it work?

FLOW
How does data move through the system?

DEBUG
How would I debug it?

TRADE-OFF
What alternatives exist?

FAILURE
What happens if it fails?
```

---

# 40. Final Learning Architecture

After completing the first version, the learner should understand this architecture:

```text
                         USER
                           │
                           ↓
                    ┌─────────────┐
                    │   React     │
                    │  Frontend   │
                    └──────┬──────┘
                           │
                       HTTP/REST
                           │
                           ↓
                    ┌─────────────┐
                    │   FastAPI   │
                    │     API     │
                    └──────┬──────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
                ↓          ↓          ↓
           PostgreSQL   Services   AI Service
                                      │
                                      ↓
                                  LLM API
                                      │
                                      ↓
                                  AI Model
```

This architecture will later evolve into:

```text
                         AI APPLICATION
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
           React            FastAPI          PostgreSQL
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                   LLM        RAG       Tools
                    │          │          │
                    │       Vector DB    APIs
                    │          │          │
                    └──────────┼──────────┘
                               │
                             Agents
```

---

# 41. Instructions to the AI Coding Assistant

When this BRD is provided, do the following:

1. First analyze the requirements.
2. Do not immediately write the entire application.
3. Propose the architecture.
4. Explain the folder structure.
5. Explain the database design.
6. Explain the API design.
7. Explain the AI integration design.
8. Identify assumptions and ask only essential questions.
9. Break development into milestones.
10. Start with Milestone 1.
11. After each milestone, explain what was implemented.
12. Explain important code line-by-line when requested.
13. Explain frontend/backend communication.
14. Explain how to test every API.
15. Explain how to debug failures.
16. Never hide architectural decisions.
17. Avoid unnecessary frameworks and dependencies.
18. Keep the application simple enough for a developer learning AI Application Development.
19. Do not implement RAG, embeddings, vector databases, agents, or tool calling until the basic AI chat application is understood.
20. After the MVP is complete, propose the next learning milestone rather than prematurely adding advanced AI functionality.

The goal is:

**Build the application + understand how it works + learn how to debug it + progressively evolve it into a production-style AI application.**
