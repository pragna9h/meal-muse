# MealMuse Testing

This document summarizes how MealMuse is validated across its API,
orchestration, retrieval, filtering, ranking, frontend, infrastructure,
failure-handling, performance, and production deployment layers.

Testing is split into:

- backend unit and regression tests
- backend integration tests
- frontend static validation and production build validation
- manual full-stack end-to-end validation
- containerized runtime and dependency-failure validation
- continuous integration
- production observability and debugging validation
- load and performance testing
- final production regression

---

# 1. Test Strategy

## Backend Unit and Regression Tests

Deterministic application behavior is tested with Pytest without requiring
live external services where possible.

Pytest discovery is restricted to the automated test suite under
`backend/tests`. Manual OpenAI smoke-test scripts remain outside automated
test discovery.

CI-safe regression suite:

````bash
python -m pytest -v -m "not integration"

Current result:

```text
30 passed
2 deselected
````

## Backend Integration Tests

Tests requiring PostgreSQL, pgvector, or live OpenAI-dependent retrieval are
marked `integration`.

Run with:

```bash
python -m pytest -v -m integration
```

Current result:

```text
1 passed
26 deselected
```

## Complete Backend Suite

With PostgreSQL running and required external configuration available:

```bash
python -m pytest -v
```

Current Result:

```text
32 passed
```

## Frontend Validation

The React and TypeScript frontend is validated using ESLint:

```bash
cd frontend
npm run lint
```

Current result:

```text
PASS
No ESLint errors or warnings
```

The production frontend build is validated with:

```bash
npm run build
```

Current result:

```text
PASS
Vite production build completed successfully
```

## Manual Full Stack Validation

The complete application is manually validated with all runtime components running together:

```text
React + TypeScript
        ↓
FastAPI
        ↓
Chat Orchestrator
        ↓
Recommendation / Search Services
        ↓
PostgreSQL + pgvector
```

The frontend is exercised through the browser while the FastAPI backend and PostgreSQL/pgvector database are running locally.

FastAPI Swagger remains available for direct API inspection at:

```text
http://127.0.0.1:8000/docs
```

# 2. Automated Test Coverage

## API

`backend/tests/test_chat_api.py`

Validates:

- health endpoint
- readiness success
- readiness failure when PostgreSQL is unavailable
- meal-recommendation response
- direct recipe-search response
- clarification response
- no-results response
- tool-selection failure maps to HTTP 500
- tool-execution failure maps to HTTP 503
- request IDs are returned on successful and controlled failure responses
- `ChatResponse` serialization through the API boundary

## Recipe Detail

Recipe-detail retrieval validates the deterministic path used when a user selects a result card.

```text
Known recipe_id -> GET /recipes/{recipe_id} -> Recipe Repository -> PostgreSQL -> Full Recipe
```

This path intentionally bypasses the LLM and orchestration layer because the application already knows which recipe the user selected.

## Chat Orchestration

`backend/tests/test_chat_orchestrator.py`

Validates:

- meal recommendation success
- recipe-search success
- clarification
- recommendation no-results
- recipe-search no-results
- recommendation tool failure handling
- recipe-search tool failure handling

## Tool Selection

`backend/tests/test_tool_selector.py`

Mocks the OpenAI Responses API and validates:

- `recommend_meals` selection
- `search_recipe` selection
- tool-argument parsing
- invalid JSON handling
- unsupported tool handling
- zero tool calls
- multiple tool calls
- OpenAI request failure handling

## Intent Compatibility

`backend/tests/test_intent_routing.py`

Validates the two supported V1 request types: meal_recommendation, recipe_search

## Recipe Filtering

`backend/tests/test_recipe_filter.py`

Validates: excluded ingredients are rejected, required ingredients are enforced

## Recipe Loading

`backend/tests/test_recipe_loader.py`

Validates: zero-valued recipe times become unknown, valid positive times are preserved

## Recipe Ranking

`backend/tests/test_recipe_ranker.py`

Validates that stronger ingredient matches rank above weaker matches.

## Recipe Retrieval

`backend/tests/test_recipe_retrieval.py`

Validates:

- structured retrieval respects maximum-time constraints
- hybrid retrieval merges and deduplicates candidates

Both retrieval tests are marked as integration tests because they require external infrastructure. Hybrid retrieval additionally requires live query embedding generation.

---

# 3. Manual End-to-End Validation

## Meal Recommendation

Input:

```json
{ "message": "I have chicken and rice. I want spicy Indian dish" }
```

Validated:

```bash
result_state: success
intent: meal_recommendation
ingredients_available: chicken, rice
cuisine_preferences: Indian
taste_preferences: spicy
recommendations: populated
```

Status: PASS

## Direct Recipe Search

Input:

```json
{ "message": "How do I make paneer tikka masala?" }
```

Validated:

```bash
result_state: success
intent: recipe_search
recipe_query: paneer tikka masala
recommendations: []
recipes: populated
```

Status: PASS

## Clarification

Input:

```json
{ "message": "I want something healthy" }
```

Validated:

```bash
result_state: clarification_required
message: What ingredients do you have on hand?
needs_clarification: true
recommendations: []
recipes: []
```

Status: PASS

---

# Full-Stack Browser Validation

The completed React frontend was manually tested against the running FastAPI
backend and PostgreSQL/pgvector database.

### Meal Recommendation

Validated:

- natural-language request submission
- loading state
- Top 5 recommendation rendering
- recommendation metadata rendering
- result ordering
- recipe-card selection
- full recipe-detail retrieval

Status: PASS

### Direct Recipe Search

Validated:

- natural-language recipe-search request
- Top 3 recipe result rendering
- recipe rating display
- ingredient preview rendering
- recipe-card selection
- full recipe-detail retrieval
- source-link availability

Status: PASS

### Clarification

Validated:

- underspecified recommendation request
- clarification message rendering
- empty recommendation and recipe collections

Status: PASS

### No Results

Validated:

- valid request with no matching recipes
- no-results state renders without frontend failure

Status: PASS

### Failure Handling

Validated:

- backend/network failure is surfaced as an error state
- stale results are not presented as a successful response

Status: PASS

### Client Interaction

Validated:

- prompt clear control
- new request clears previous recipe-detail state
- loading indicator cycles while a request is active
- result cards remain interactive after successful responses

Status: PASS

## Containerized Runtime Validation

The complete production-oriented stack was validated through Docker Compose:

```text
Browser
   ↓
Nginx / React
   ↓
/api reverse proxy
   ↓
FastAPI
   ↓
PostgreSQL + pgvector
```

Validated:

- PostgreSQL container health
- FastAPI container health
- frontend container startup
- backend-to-database Docker networking
- Nginx-to-FastAPI reverse proxy
- recommendation requests through the containerized stack
- direct recipe-search requests through the containerized stack
- deterministic recipe-detail retrieval through the containerized stack

Status: PASS

## Dependency Failure and Recovery

PostgreSQL was deliberately stopped while the backend remained running.

Validated:

```text
PostgreSQL available:
    /health -> 200
    /ready  -> 200

PostgreSQL unavailable:
    /health -> 200
    /ready  -> 503

PostgreSQL restored:
    /ready  -> 200
```

The initial failure exercise exposed that database connection attempts could wait too long when PostgreSQL was unavailable. A bounded database connection timeout was added, after which `/ready` returned its controlled HTTP 503 response promptly.

Status: PASS

## Continuous Integration Validation

GitHub Actions automatically validates pushes and pull requests targeting
`main`.

The CI pipeline contains two independent jobs.

### Backend Tests

```text
Python 3.12
    ↓
Install dependencies
    ↓
python -m pytest -m "not integration" -v
```

Current CI results:

```text
30 passed
2 deselected
PASS
```

# 4. Important behaviors protected by tests

MealMuse tests currently protect the following architectural guarantees:

- explicit hard constraints are enforced deterministically
- unknown recipe times do not incorrectly satisfy time limits
- hybrid retrieval does not return duplicate recipe IDs
- recommendation ranking remains deterministic
- direct recipe search remains separate from recommendation ranking
- clarification is enforced by backend policy
- exactly one AI tool call is accepted
- invalid tool output becomes a controlled orchestration error
- application no-results are distinct from infrastructure failures
- orchestration failures do not silently return successful HTTP 200 responses
- recipe-card selection uses deterministic recipe-detail retrieval
- known recipe IDs do not trigger unnecessary LLM calls
- frontend correctly distinguishes recommendation and recipe-search results
- frontend handles clarification, no-results, loading, and failure states
- new requests do not retain stale recipe-detail state
- frontend passes static lint validation
- frontend produces a valid production build

# 5. Current Test Status

```text
Day 1 — Recommendation Foundation

Recipe loading                    PASS
Filtering                         PASS
Ranking                           PASS
Clarification                     PASS
```

```text
Day 2 — PostgreSQL + pgvector

Database ingestion                PASS (50,514 recipes)
Recipe embeddings                 PASS (50,514 recipes)
Structured retrieval              PASS
Semantic retrieval                PASS
Hybrid retrieval                  PASS
```

```text
Day 3 — Agentic Orchestration

Tool selection                    PASS
Tool argument validation          PASS
Meal recommendation orchestration PASS
Recipe-search orchestration       PASS
Clarification handling            PASS
No-results handling               PASS
Tool failure handling             PASS
Manual Swagger validation         PASS
```

```text
Day 4 — React + TypeScript Frontend

Frontend recommendation flow      PASS
Frontend recipe-search flow       PASS
Recipe-detail selection           PASS
Clarification UI                  PASS
No-results UI                     PASS
Failure UI                        PASS
Loading state                     PASS
Prompt clearing                   PASS
Frontend ESLint                   PASS
Frontend production build         PASS
Full-stack browser validation     PASS

Final Day 4 Validation

Backend test suite                PASS (27 / 27)
Frontend lint                     PASS
Frontend production build         PASS
Full-stack smoke tests            PASS

Overall status                    PASS
```


```text
Day 5 — Production Hardening + Docker + CI

Request ID middleware             PASS
Request latency logging           PASS
OpenAI dependency failure         PASS
Tool execution failure            PASS
Health endpoint                   PASS
Readiness endpoint                PASS
Database failure detection        PASS
Database recovery                 PASS
Bounded DB connection timeout     PASS
Backend Docker image              PASS
Frontend Docker image             PASS
Docker Compose full stack         PASS
Nginx API reverse proxy           PASS
Container dependency ordering     PASS
GitHub Actions backend CI         PASS
GitHub Actions frontend CI        PASS

Final Day 5 Validation

Backend complete suite             PASS (32 / 32)
Backend CI-safe suite              PASS (30 passed, 2 deselected)
Frontend lint                      PASS
Frontend production build          PASS
Containerized recommendation flow  PASS
Containerized recipe-search flow   PASS
Containerized recipe-detail flow   PASS
GitHub Actions CI                   PASS

Overall status                     PASS
```

```text
Day 6 — GCP Production Deployment

Cloud Run backend deployment          PASS
Cloud Run frontend deployment         PASS
Cloud SQL PostgreSQL connectivity     PASS
pgvector production retrieval         PASS
Production secret injection           PASS
Backend health endpoint               PASS
Backend readiness endpoint            PASS
Frontend-to-backend proxy             PASS
Production recommendation flow        PASS
Production recipe-search flow         PASS
Production recipe-detail flow         PASS
Production clarification handling     PASS
Production no-results handling        PASS
Migrated recipe corpus                PASS (50,514 recipes)
Migrated embeddings                   PASS (50,514 embeddings)

Final Day 6 Validation

Cloud Run frontend                    PASS
Cloud Run backend                     PASS
Cloud SQL                             PASS
OpenAI integration                    PASS
End-to-end production workflows       PASS

Overall status                        PASS
```

```text
Day 7 — Production Validation + Performance

Production observability baseline     PASS
Request ID correlation                PASS
Request latency visibility            PASS
Production log inspection             PASS
Failure/debugging validation          PASS
Dependency recovery validation        PASS
Load and performance testing          PASS
Bottleneck analysis                   PASS
Optimization decision review          PASS
Final backend regression              PASS
Final frontend regression             PASS
Final production E2E regression       PASS

Final Day 7 Validation

Health/readiness                      PASS
Meal recommendation                   PASS
Direct recipe search                  PASS
Recipe-detail retrieval               PASS
Clarification handling                PASS
Frontend result rendering             PASS
Production request logs               PASS

Overall status                        PASS
```

# 6. Production End-to-End Validation

The deployed GCP system was validated after deployment.

Validated production paths:

- Cloud Run backend `/health`
- Cloud Run backend `/ready`
- Cloud Run to Cloud SQL connectivity
- OpenAI tool selection
- OpenAI embedding generation
- pgvector hybrid retrieval
- meal recommendation flow
- direct recipe-search flow
- deterministic recipe-detail retrieval
- clarification handling
- graceful no-result handling
- React/Nginx frontend-to-backend proxying

The production recommendation flow successfully returned ranked recommendations from the migrated 50,514-recipe database.

Deployment testing also exposed and resolved environment-specific issues involving Cloud SQL configuration, database credential synchronization, and migrated-table permissions.

---

# 7. Production Observability and Debugging Validation

The deployed MealMuse system was inspected through production request and application logs to verify that runtime behavior can be traced during normal execution and failure scenarios.

Validated signals include:

- incoming HTTP requests
- request IDs
- response status
- request latency
- orchestration execution
- selected application workflow
- dependency failures
- Cloud Run runtime behavior

Request IDs allow application activity and controlled failures to be correlated across a request lifecycle.

Production log inspection was performed while exercising real recommendation and recipe-search workflows.

Status: PASS

## Failure and Recovery Validation

Failure testing verifies the distinction between valid product outcomes and infrastructure failures.

MealMuse treats:

```text
SUCCESS
CLARIFICATION_REQUIRED
NO_RESULTS
```

as valid application states.

Infrastructure or orchestration failures instead surface through controlled HTTP failure semantics.

The database readiness behavior was also validated:

```text
Database available
    /health -> 200
    /ready  -> 200

Database unavailable
    /health -> 200
    /ready  -> 503

Database restored
    /ready  -> 200
```

This verifies that process health remains distinct from dependency readiness.

Status: PASS

---

# 8. Load and Performance Testing

The deployed backend was exercised under repeated and concurrent requests to establish production behavior under load.

The goal was not to optimize for an artificial benchmark. The goal was to:

1. establish a performance baseline
2. observe request behavior under concurrency
3. inspect production logs
4. identify the dominant request-path costs
5. determine whether an additional optimization layer was justified

The measured production request path includes:

```text
Client
   ↓
Cloud Run Backend
   ↓
OpenAI Tool Selection
   ↓
Query Embedding Generation
   ↓
PostgreSQL / pgvector Retrieval
   ↓
Deterministic Filtering
   ↓
Deterministic Ranking
   ↓
Response
```

Both MealMuse workflows were exercised:

- meal recommendation
- direct recipe search

Validated:

- successful responses under repeated requests
- successful responses under concurrent requests
- production request logging during load
- request ID generation during concurrent execution
- continued database and retrieval availability
- no regression in response correctness

Status: PASS

---

# 9. Bottleneck Analysis and Optimization Decision

Performance analysis was based on observed production behavior rather than assuming that every production system requires additional caching or infrastructure.

The request path was separated conceptually into:

```text
Network / Cloud Run
        +
LLM Tool Selection
        +
Embedding Generation
        +
Database / pgvector Retrieval
        +
Deterministic Filtering and Ranking
```

The purpose of the analysis was to determine which stages materially contribute to end-to-end latency and whether an additional optimization layer would solve a demonstrated problem.

MealMuse follows the optimization rule:

> Measure first. Optimize only when evidence justifies the additional complexity.

No caching layer or additional distributed infrastructure was introduced solely to increase the number of technologies in the architecture.

Potential optimizations remain available if future usage demonstrates a need, including:

- caching repeated retrieval results
- caching reusable query embeddings where appropriate
- tuning retrieval candidate limits
- database/index tuning
- Cloud Run scaling configuration
- reducing unnecessary external dependency calls

For V1, the measured system behavior did not justify adding another architectural layer solely for portfolio breadth.

Status: PASS

---

# 10. Final Production Regression

After the final frontend correction and redeployment, MealMuse underwent a complete production regression.

The final deployed path validated was:

```text
Browser
   ↓
Cloud Run React/Nginx Frontend
   ↓
/api reverse proxy
   ↓
Cloud Run FastAPI Backend
   ↓
Chat Orchestrator
   ↓
OpenAI Tool Selection
   ↓
Application Service
   ↓
PostgreSQL + pgvector
   ↓
Deterministic Filtering / Ranking
   ↓
API Response
   ↓
React UI
```

## Backend Regression

Validated:

- `/health`
- `/ready`
- meal-recommendation workflow
- direct recipe-search workflow
- clarification behavior
- deterministic recipe-detail retrieval

Responses were checked for correct result states, intent routing, populated result collections, and recipe-detail data.

Status: PASS

## Frontend Regression

Validated in the deployed Cloud Run frontend:

- meal-recommendation rendering
- direct recipe-search rendering
- recipe-card interaction
- deterministic recipe-detail loading
- source links
- layout behavior
- single document-level vertical scrolling
- absence of the previously observed duplicate recipe-search scrollbar

Status: PASS

## Production Logs

Production backend logs were inspected after the regression run.

Validated:

- successful `/chat` requests
- successful `/recipes/{recipe_id}` requests
- request IDs
- request timing information
- expected orchestration activity
- absence of unexplained regression failures during the validation run

Status: PASS

## Final V1 Validation Status

```text
Automated backend tests              PASS
Backend integration tests            PASS
Frontend lint                        PASS
Frontend production build            PASS
Local full-stack validation           PASS
Containerized full-stack validation   PASS
Failure and recovery validation       PASS
GitHub Actions CI                     PASS
GCP production deployment             PASS
Production observability              PASS
Load/performance validation           PASS
Bottleneck analysis                   PASS
Final production regression           PASS

MEALMUSE V1                          PASS
```