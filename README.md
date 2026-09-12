# MealMuse

MealMuse is a full-stack AI-powered meal discovery application that helps users:

- decide what to cook from available ingredients, constraints, and preferences, or
- directly find recipes when they already know the dish they want.

MealMuse combines a React + TypeScript frontend with a FastAPI backend, agentic
tool-based orchestration, hybrid PostgreSQL + pgvector retrieval, and
deterministic filtering and ranking.

The project is being built as a production-grade Agentic AI system with a clear
engineering boundary: AI handles natural-language interpretation and capability
selection, while deterministic application code controls recipe facts,
constraints, retrieval, ranking, and known actions.

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
React + TypeScript Frontend
 ↓
FastAPI
 ↓
POST /chat
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
                 ↓
        Frontend Result Cards
```

A central design principle is:

> **Use AI where interpretation is required. Use deterministic code where
> behavior must be predictable.**

The LLM determines which application capability is appropriate and extracts
structured arguments. The backend remains responsible for validation,
clarification policy, retrieval, hard constraints, ranking, and database
operations.

For detailed design decisions, see [`docs/architecture.md`](docs/architecture.md).

## Frontend

MealMuse includes a React + TypeScript interface for both supported V1 workflows.

The frontend provides:

- natural-language request input
- Top 5 meal recommendation cards
- Top 3 direct recipe-search results
- recipe ratings and key metadata
- ingredient previews
- full recipe-detail selection
- clarification responses
- no-results handling
- backend/network failure handling
- animated loading state
- prompt clearing and request-state reset

The frontend remains a presentation and interaction layer. Recommendation logic, recipe retrieval, constraint enforcement, ranking, and recipe facts remain in the backend.

Recipe-card selection uses the known `recipe_id` to retrieve complete recipe details directly rather than invoking the orchestration layer again.

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

### Frontend

- React 19
- TypeScript
- Vite
- ESLint

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

### Production Roadmap

- GitHub Actions CI/CD
- GCP deployment
- structured logging and observability
- production health/readiness checks
- load and failure testing

Additional infrastructure will only be introduced when it solves a concrete
MealMuse production requirement.

---

## Testing

MealMuse is validated across backend unit/regression tests, integration tests,
frontend static validation, production builds, and manual full-stack testing.

Current Day 4 validation:

```text
Backend test suite             27 / 27 PASS
Frontend ESLint                     PASS
Frontend production build           PASS
Full-stack browser validation        PASS
```

Current coverage includes:

- recipe loading and normalization
- hard-constraint filtering
- deterministic ranking
- structured and semantic retrieval
- hybrid retrieval and deduplication
- multi-intent behavior
- AI tool selection and argument validation
- chat orchestration
- clarification
- no-results handling
- tool-execution failure handling
- recommendation UI flow
- direct recipe-search UI flow
- deterministic recipe-detail selection
- loading and error states
- frontend/backend integration

The recommendation, direct recipe-search, clarification, no-results, failure, and recipe-detail workflows have also been validated through the completed React frontend.

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

### Phase IV — React + TypeScript Frontend

- [x] React + TypeScript application
- [x] Natural-language request interface
- [x] Recommendation cards
- [x] Direct recipe-search results
- [x] Recipe-detail view
- [x] Deterministic recipe-detail API path
- [x] Clarification state
- [x] No-results state
- [x] Failure state
- [x] Loading state
- [x] Frontend/backend integration
- [x] Frontend lint validation
- [x] Production frontend build
- [x] Full-stack browser validation

### Next — Production Hardening & Deployment

- [ ] structured application logging
- [ ] production error handling
- [ ] request tracing and latency measurement
- [ ] production environment configuration
- [ ] production CORS configuration
- [ ] application containerization
- [ ] health and readiness checks
- [ ] GitHub Actions CI
- [ ] integration and failure testing
- [ ] GCP deployment
- [ ] production observability
- [ ] load testing
- [ ] production validation

---

## Running MealMuse

### 1. Start PostgreSQL + pgvector

From the project root:

```bash
docker compose up -d
```

### 2. Start the FastAPI backend

Activate the Python environment and run:

```bash
python -m uvicorn backend.app.main:app --reload
```

The API is avilable at: `http://127.0.0.1:8000`

Swagger documentation: `http://127.0.0.1:8000/docs`

### 3. Start the React frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL reported by Vite: `http://localhost:5173`

### 4. Run backend tests

```bash
python -m pytest -v
```

### 5. Validate the frontend

```bash
cd frontend
npm run lint
npm run build
```

---

## Goal

Build MealMuse into a **production-grade Agentic AI system** that demonstrates the engineering required to move an AI application from natural-language understanding through retrieval and deterministic application logic to a tested, observable, and publicly deployed full-stack product.
