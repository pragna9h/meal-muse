# MealMuse

MealMuse is an AI-powered meal discovery application that helps users either:

- decide what to cook from ingredients, constraints, and preferences, or
- directly find recipes when they already know the dish they want.

The project is being built as a production-grade Agentic AI system combining
LLM-based request understanding and tool calling with deterministic retrieval,
filtering, ranking, and application policies.

## Core Workflows

### Meal Recommendation

Example:

```text
"I have chicken and rice. I want something spicy and Indian."
```

MealMuse interprets the request, retrieves relevant recipes using structured
PostgreSQL search and semantic pgvector search, applies hard constraints, and
deterministically ranks the remaining candidates.

### Direct Recipe Search

Example:

```text
"How do I make chicken tikka masala?"
```

MealMuse routes the request to a dedicated recipe-search workflow that combines
recipe-name matching with semantic retrieval and returns complete recipe data.

---

## Architecture

```text
User
 ↓
FastAPI /chat
 ↓
Chat Orchestrator
 ↓
OpenAI Tool Calling
 ↓
Tool Selection
 ├───────────────────────────────┐
 ↓                               ↓
recommend_meals               search_recipe
 ↓                               ↓
Tool Arguments                Tool Arguments
 └───────────────┬───────────────┘
                 ↓
            ParsedIntent
                 ↓
     Deterministic Clarification
                 ↓
 ┌───────────────┴───────────────┐
 ↓                               ↓
Meal Recommendation          Direct Recipe Search
 ↓                               ↓
Hybrid Retrieval             Name + Semantic Search
 ↓                               ↓
PostgreSQL + pgvector        PostgreSQL + pgvector
 ↓                               ↓
Full Recipe Hydration        Full Recipe Hydration
 ↓                               ↓
Hard Filtering               Recipe Results
 ↓
Deterministic Ranking
 ↓
Top 5 Recommendations
 └───────────────┬───────────────┘
                 ↓
            ChatResponse
```

A central design principle is:

> **Use AI where interpretation is required. Use deterministic code where
> behavior must be predictable.**

The LLM determines which application capability is appropriate and extracts
structured arguments. The backend remains responsible for validation,
clarification policy, retrieval, hard constraints, ranking, and database
operations.

For detailed design decisions, see [`docs/architecture.md`](docs/architecture.md).

---

## Agentic Orchestration

MealMuse currently exposes two AI-callable application tools:

```text
recommend_meals
search_recipe
```

The chat orchestrator coordinates:

1. request understanding and tool selection
2. tool-argument validation
3. `ParsedIntent` construction
4. deterministic clarification
5. application-tool execution
6. result handling
7. `ChatResponse` construction

The orchestrator intentionally does **not** perform SQL, vector retrieval,
recipe hydration, filtering, ranking, or nutrition calculations.

Those responsibilities remain in deterministic application layers.

---

## Retrieval Architecture

### Meal Recommendations

Recommendation retrieval combines two candidate sources:

```text
Structured PostgreSQL Retrieval
              +
Semantic pgvector Retrieval
              ↓
      Merge + Deduplicate
              ↓
       Recipe Hydration
              ↓
      Hard-Constraint Filter
              ↓
    Deterministic Ranking
              ↓
             Top 5
```

Structured retrieval handles explicit constraints and metadata, while semantic
retrieval improves discovery for natural-language preferences.

### Direct Recipe Search

```text
Recipe-Name Search
        +
Semantic pgvector Search
        ↓
Merge + Deduplicate
        ↓
Full Recipe Hydration
        ↓
Recipe Results
```

Direct recipe search intentionally bypasses recommendation filtering and
ranking because the user already knows what dish they want.

---

## Recipe Data

MealMuse uses a processed corpus of:

```text
50,514 recipes
```

The data pipeline normalizes and validates:

- ingredients
- instructions
- preparation and cooking times
- servings
- cuisine and category metadata
- cooking methods and equipment
- nutrition
- ratings
- source URLs

All 50,514 recipes are stored in PostgreSQL and have 1536-dimensional OpenAI
embeddings stored in pgvector.

Embedding generation is batched, resumable, and includes retry/backoff handling
for API rate limits.

---

## Deterministic Application Policies

MealMuse deliberately keeps several decisions outside the LLM.

### Hard Constraints

Explicit requirements are enforced before ranking, including:

- required ingredients
- excluded ingredients
- maximum preparation time

Unknown recipe times cannot satisfy explicit maximum-time constraints.

### Clarification

Meal recommendation requests without enough ingredient information return a
clarification request instead of arbitrary recommendations.

Example:

```text
User: "I want something healthy."

MealMuse:
"What ingredients do you have on hand?"
```

### Ranking

After filtering, valid recommendation candidates are ranked using deterministic
signals such as:

- ingredient coverage
- missing ingredients
- meal-type compatibility
- cuisine preference
- time suitability
- recipe metadata and ratings

This keeps recommendation behavior interpretable and testable.

---

## Tech Stack

### Backend & AI

- Python 3.12
- FastAPI
- Pydantic
- OpenAI Responses API
- OpenAI tool calling
- OpenAI embeddings

### Data & Retrieval

- PostgreSQL
- pgvector
- SQLAlchemy
- Psycopg
- PostgreSQL GIN indexes
- hybrid structured + semantic retrieval

### Infrastructure & Testing

- Docker
- Pytest

### Planned

- React + TypeScript
- CI/CD
- GCP
- Kubernetes
- OpenTelemetry
- Prometheus + Grafana
- Redis, if runtime caching requirements justify it

---

## Testing

MealMuse currently includes unit/regression, integration, and manual
end-to-end API validation.

```text
Regression suite       26 / 26 PASS
Integration suite       1 / 1  PASS
```

Current coverage includes:

- recipe loading
- hard-constraint filtering
- deterministic ranking
- structured and semantic retrieval
- hybrid retrieval and deduplication
- multi-intent behavior
- tool selection and argument validation
- chat orchestration
- clarification
- no-result handling
- tool-execution failure handling
- API response behavior

The current recommendation, direct recipe-search, and clarification workflows
have also been validated end-to-end through FastAPI Swagger.

For details, see [`docs/testing.md`](docs/testing.md).

---

## Project Status

🚧 **Active Development**

### Phase I — Recommendation Foundation

- [x] FastAPI backend
- [x] Recipe processing pipeline
- [x] 50,514-recipe corpus
- [x] Hard-constraint filtering
- [x] Deterministic ranking
- [x] Top-5 meal recommendations
- [x] Clarification policy

### Phase II — PostgreSQL + Hybrid Retrieval

- [x] Dockerized PostgreSQL + pgvector
- [x] 50,514 recipes stored in PostgreSQL
- [x] 50,514 recipe embeddings
- [x] Structured PostgreSQL retrieval
- [x] pgvector semantic retrieval
- [x] GIN indexes
- [x] Hybrid candidate retrieval
- [x] Retrieval deduplication
- [x] Direct recipe search
- [x] Full recipe hydration

### Phase III — Agentic Orchestration

- [x] OpenAI tool definitions
- [x] Tool selection
- [x] Pydantic tool-argument validation
- [x] Chat orchestrator
- [x] Recommendation tool
- [x] Recipe-search tool
- [x] Deterministic clarification
- [x] Explicit result states
- [x] Orchestration failure handling
- [x] Unit and end-to-end validation

### Next — Frontend

- [ ] React + TypeScript application
- [ ] Natural-language chat interface
- [ ] Recommendation cards
- [ ] Direct recipe-search results
- [ ] Recipe-detail view
- [ ] Clarification and error states
- [ ] Frontend/backend integration

### Production Roadmap

- [ ] Dockerize application services
- [ ] CI/CD
- [ ] structured logging and analytics
- [ ] rate limiting and production error handling
- [ ] GCP deployment
- [ ] Kubernetes
- [ ] OpenTelemetry
- [ ] Prometheus + Grafana
- [ ] load and failure testing
- [ ] production validation

---

## Running the Backend

Start PostgreSQL:

```bash
docker compose up -d
```

Start the API:

```bash
python -m uvicorn backend.app.main:app --reload
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

Run the regression suite:

```bash
python -m pytest -v -m "not integration"
```

Run integration tests:

```bash
python -m pytest -v -m integration
```

---

## Goal

Build MealMuse into a **production-grade Agentic AI system** while exploring
the engineering required to move an AI application from a working prototype
to a reliable, observable, tested, deployed product used by real users.