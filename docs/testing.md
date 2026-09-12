# MealMuse Testing

This document summarizes how MealMuse is validated across its API,
orchestration, retrieval, filtering, ranking, and database layers.

Testing is split into:

- backend unit and regression tests
- backend integration tests
- frontend static validation and production build validation
- manual full-stack end-to-end validation

---

# 1. Test Strategy

## Backend Unit and Regression Tests

Deterministic application behavior is tested with Pytest without requiring
live external services where possible.

Normal regression suite:

```bash
python -m pytest -v -m "not integration"

Current result:

```text
26 passed
1 deselected
```

## Backend Integration Tests

Tests that require PostgreSQL, pgvector, or live OpenAI calls are marked: `integration`

Run with :

```bash
python -m pytest -v -m integration
```

Current result:

```text
1 passed
26 deselected
```

## Complete Backend Suite
```bash
python -m pytest -v
```
Current Result:
```text
27 passed
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
- meal-recommendation response
- direct recipe-search response
- clarification response
- no-results response
- `ChatResponse` serialization through the orchestrator

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

The hybrid retrieval test is marked as integration test as it requires PostgreSQL, pgvector, and a live query embedding.

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

Day 2 — PostgreSQL + pgvector

Database ingestion                PASS (50,514 recipes)
Recipe embeddings                 PASS (50,514 recipes)
Structured retrieval              PASS
Semantic retrieval                PASS
Hybrid retrieval                  PASS

Day 3 — Agentic Orchestration

Tool selection                    PASS
Tool argument validation          PASS
Meal recommendation orchestration PASS
Recipe-search orchestration       PASS
Clarification handling            PASS
No-results handling               PASS
Tool failure handling             PASS
Manual Swagger validation         PASS

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

# 6. Planned Testing

The production-hardening and deployment phases will add validation for:

- structured application logging
- dependency and infrastructure failure handling
- request tracing and latency measurement
- production configuration
- health and readiness behavior
- containerized application startup
- frontend/backend integration in the containerized environment
- GitHub Actions CI
- production deployment
- observability
- load and performance testing
- production end-to-end validation

Additional infrastructure such as caching will only introduce corresponding tests if that infrastructure is actually added to MealMuse.
