# MealMuse Testing

This document summarizes how MealMuse is validated across its API,
orchestration, retrieval, filtering, ranking, and database layers.

Testing is split into:

- unit/regression tests
- integration tests
- manual end-to-end API validation

---

# 1. Test Strategy

## Unit and Regression Tests

Deterministic application behavior is tested with Pytest without requiring
live external services where possible.

Normal regression suite:

```bash
python -m pytest -v -m "not integration"
```

Current result:

```text
26 passed
1 deselected
```

## Integration Tests

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

## Manual End-to-End Tests

The complete applicastion flow is manually validated through FastAPI Swagger:

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
- `ChatResponse` serialization through the orchestrator`

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

Automated Suites

Regression suite                  PASS (26 / 26)
Integration suite                 PASS (1 / 1)

Overall status                    PASS
```

# Planned Testing

Future phases will add validation for:

- React frontend behavior
- frontend/backend integration
- recipe-detail selection
- structured logging
- analytics events
- rate limiting
- CI/CD
- Redis caching, if introduced
- observability
- load testing
- production deployment
- health/readiness behavior
