## Custom Learning Chatbot — Refined Implementation Specification

### Project Overview

A highly responsive, scalable learning chatbot integrated with a Flutter client. Persistence leverages Firebase (Auth & Firestore), with the OpenAI API for question generation and evaluation.

**Key Features:**

- **User Profiles & Topics:** Persisted in Firestore under `/users/{uid}` and `/topics/{topicId}`.
- **Question Bank:** Each topic maintains a pool of 20 pre-generated questions (multiple choice, short answer, explanation); regenerated automatically upon full exhaustion.
- **Spaced-Repetition (FSRS):** Review scheduling via an open-source FSRS Python package.
- **Stateless API:** Firebase Auth JWTs for identity; endpoints maintain no in-memory session state.
- **Session Management:** Firestore-backed sessions, with in-memory caching on each server instance for ultra-low-latency reads of topics and active sessions.

---

### Architecture Principles

1. **Stateless Endpoints:** All requests include a valid JWT; services remain stateless.
2. **Idempotent Operations:** Write endpoints require an `Idempotency-Key` header to guard against duplicate processing.
3. **Instrumentation Hooks:** Insert placeholders for metrics (`metrics.increment(...)`) and structured logging.
4. **Firebase-First Persistence:** Firestore is the single source of truth for sessions, topics, questions, and FSRS state.
5. **In-Memory Caching:** On startup or first access, servers load current topics (and optionally sessions) into a TTL-based in-memory cache; fallback to Firestore on cache miss.

---

### High-Level Flow

1. **User Authentication:** Client obtains a Firebase Auth JWT.
2. **Topic Retrieval:** Server serves topic list from its in-memory cache; missing entries trigger Firestore reads and cache population.
3. **Automatic Question Regeneration:** When a topic’s questionBank is empty (or fully reviewed), the backend enqueues a regeneration task via `POST /topics/{topicId}/generate-questions` inside a Firestore transaction (guarded by a `regenerating` flag).
4. **Session Lifecycle:**
   - **Start:** `POST /sessions/start` creates `/sessions/{sessionId}` in Firestore, selecting question IDs from the topic’s bank.
   - **Fetch Current Question:** `GET /sessions/{sessionId}` returns the next question and FSRS parameters.
   - **Respond / Skip:** `POST /sessions/{sessionId}/respond` and `/skip` evaluate (via OpenAI) or bypass a question, update FSRS fields, and increment `questionIndex` in Firestore.
   - **End:** `POST /sessions/{sessionId}/end` finalizes review, updates the topic’s FSRS state, and archives the session.

---

### Data Models

```python
class Topic(BaseModel):
    id: str
    ownerUid: str
    name: str
    description: str
    questionBank: List[str]          # IDs of available questions
    fsrsParams: FSRSParams           # current spaced-repetition state
    regenerating: bool = False       # lock for auto-regeneration

class Question(BaseModel):
    id: str
    topicId: str
    text: str
    type: Literal['multiple_choice','short_answer','explanation']
    difficulty: int
    metadata: Dict[str, Any]

class Session(BaseModel):
    id: str
    userUid: str
    topicId: str
    questionIndex: int               # next question pointer
    questionIds: List[str]           # fixed list at session start
    responses: List[Response]
    startedAt: datetime
    nextReviewAt: Optional[datetime]

class FSRSParams(BaseModel):
    ease: float                      # e.g. starting at 2.5
    interval: int                    # days until next review
    repetition: int                  # number of successful reps

class Response(BaseModel):
    questionId: str
    answer: str
    score: int                        # 0–5 grading
    timestamp: datetime
```

---

### API Contract

```
POST   /api/v1/sessions/start              → { sessionId }
GET    /api/v1/sessions/{sessionId}        → { Session }
POST   /api/v1/sessions/{sessionId}/respond → { updated Session }
POST   /api/v1/sessions/{sessionId}/skip    → { updated Session }
POST   /api/v1/sessions/{sessionId}/end     → { reviewSchedule }

GET    /api/v1/topics/{userUid}            → [ Topic ]
POST   /api/v1/topics/{topicId}/generate-questions → { generatedCount }
```

**Required Headers:**

- `Authorization: Bearer <Firebase-ID-Token>`
- `Idempotency-Key: <UUID>`

---

### Implementation Phases

**Phase 1: Setup & Configuration**

- Initialize FastAPI skeleton, enable CORS, auth middleware.
- Add dependencies in `requirements.txt`:
  ```
  fastapi
  firebase-admin
  openai
  pydantic
  fsrs             # install via pip install fsrs
  ```
- Configure `app/config.py` for Firebase credentials & OpenAI key.
- Build Pydantic schemas and Firestore repository placeholders.
- Implement in-memory cache module under `infrastructure/cache/`.

**Phase 2: Core Functionality**

- **Firestore Repositories:** Topic, Question, Session CRUD.
- **Cache Layer:** Load and refresh topic cache with TTL.
- **Question Generation Pipeline:**
  - OpenAI generator → refiner loop with retry/backoff.
  - Guard regeneration via Firestore transaction on `regenerating` flag.
  - Batch-create 20 Question docs per topic.
- **FSRS Integration:**
  - Import and configure FSRS package (`from fsrs import FSRS`).
  - Initialize default FSRSParams (ease=2.5, interval=1, repetition=0).
  - Compute next `ease`, `interval`, and `repetition` on each review.

**Phase 3: API Layer**

- Implement route handlers in `api/v1/endpoints/`:
  - Map Pydantic models to repos/services.
  - Enforce idempotency via Firestore transactions.
- Validate input/output schemas; add automatic OpenAPI docs.

**Phase 4: Testing & Observability**

- Unit tests for services, FSRS logic, and repo methods.
- End-to-end tests: topic generation → session flow → review.
- Integrate basic metrics (`metrics.increment`) and structured logs.
- Expose health-check endpoint `/healthz`.

---

### Implementation Patterns

#### In-Memory Topic Cache

```python
class TopicCache:
    def __init__(self, ttl_seconds=300):
        self._cache = {}      # key: userUid → List[Topic]
        self._expires = {}    # key → timestamp

    def get_topics(self, userUid):
        now = time.time()
        if userUid in self._cache and self._expires[userUid] > now:
            return self._cache[userUid]
        topics = topic_repo.list(userUid)
        self._cache[userUid] = topics
        self._expires[userUid] = now + ttl_seconds
        return topics
```

#### Question Regeneration Lock

```python
def regenerate_if_needed(topicId):
    def txn_fn(txn):
        topic_ref = firestore.client().document(f"topics/{topicId}")
        snapshot = topic_ref.get(txn=txn)
        topic = Topic.parse_obj(snapshot.to_dict())
        if not topic.questionBank and not topic.regenerating:
            txn.update(topic_ref, {'regenerating': True})
            return True
        return False
    if firestore.client().transaction().run(txn_fn):
        # enqueue or run generation pipeline
        generate_questions(topicId)
```

---
