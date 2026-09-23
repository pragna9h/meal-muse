# MealMuse

**Production-grade agentic AI meal discovery system built with React, FastAPI, PostgreSQL, pgvector, OpenAI, Docker, and Google Cloud.**

#### ✅ Try [MealMuse](https://mealmuse-frontend-y4ymgnrpwq-uw.a.run.app/) Live

MealMuse turns natural-language meal requests into grounded recipe recommendations and direct recipe search results.

Instead of allowing an LLM to generate recipe facts or make final recommendation decisions, MealMuse uses AI for **natural-language interpretation and tool selection**, while deterministic application code controls **retrieval, constraints, ranking, recipe data, and known actions**.

The system operates over a corpus of **50,514 recipes with precomputed vector embeddings** and is deployed as a full-stack application on Google Cloud Platform.

---

## What MealMuse Does

MealMuse supports two primary natural-language workflows.

### Meal Recommendation

Users can describe the ingredients they have along with preferences or constraints:

```text
"Chicken, tomatoes, rice. Give me something spicy and Indian."
```

MealMuse:

1. interprets the request using OpenAI tool calling
2. extracts structured constraints and preferences
3. retrieves candidates using PostgreSQL + pgvector
4. applies deterministic hard constraints
5. ranks valid recipes using deterministic signals
6. returns the Top 5 recommendations

### Direct Recipe Search

Users can also search for a specific dish:

```text
"How do I make chicken tikka masala?"
```

MealMuse routes the request to a dedicated recipe-search workflow combining recipe-name matching with semantic retrieval.

Selecting a result uses its known `recipe_id` to retrieve complete recipe details directly from PostgreSQL without making another LLM call.

---

## System Architecture

```text
                         User
                           |
                           v
                 React + TypeScript
                           |
                           v
                    FastAPI API
                           |
                           v
                  Chat Orchestrator
                           |
                           v
                 OpenAI Tool Calling
                           |
               +-----------+-----------+
               |                       |
               v                       v
        recommend_meals          search_recipe
               |                       |
               v                       v
        Structured Arguments     Structured Arguments
               |                       |
               +-----------+-----------+
                           |
                           v
                     ParsedIntent
                           |
                           v
              Deterministic Application
                       Policies
                           |
              +------------+------------+
              |                         |
              v                         v
      Meal Recommendation        Recipe Search
              |                         |
              v                         v
        Hybrid Retrieval       Name + Semantic
              |                   Retrieval
              |                         |
              +------------+------------+
                           |
                           v
                 PostgreSQL + pgvector
                           |
                           v
                    Recipe Results
```

A central engineering principle is:

> **Use AI where interpretation is required. Use deterministic code where behavior must be predictable.**

The LLM selects an application capability and extracts structured arguments. It does not directly query the database, enforce hard constraints, rank recipes, or generate recipe facts.

For the detailed architecture and engineering decisions, see [`docs/architecture.md`](docs/architecture.md).

---

## Hybrid Retrieval

MealMuse combines two retrieval strategies.

**Structured PostgreSQL retrieval** handles explicit signals such as:

- available ingredients
- required or excluded ingredients
- cuisine
- meal type
- equipment
- time constraints

**Semantic pgvector retrieval** improves discovery for natural-language concepts and preferences.

```text
Structured Retrieval
        +
Semantic Retrieval
        |
        v
Merge + Deduplicate
        |
        v
Full Recipe Hydration
        |
        v
Hard-Constraint Filtering
        |
        v
Deterministic Ranking
        |
        v
Top Recommendations
```

Hybrid retrieval improves candidate recall while deterministic filtering prevents semantically similar recipes from overriding explicit user requirements.

---

## Agentic Orchestration

MealMuse exposes two AI-callable application tools:

```text
recommend_meals
search_recipe
```

The orchestration layer coordinates:

- tool selection
- structured argument extraction
- Pydantic validation
- `ParsedIntent` construction
- deterministic clarification
- application-tool execution
- result handling
- response construction

Application outcomes explicitly distinguish successful results, clarification requirements, no-result states, and infrastructure failures.

This keeps AI reasoning behind controlled application boundaries instead of allowing the model to directly control system behavior.

---

## Recipe Data

MealMuse operates over:

```text
50,514 recipes
50,514 precomputed embeddings
1536 dimensions per embedding
```

Recipe data is normalized and stored in PostgreSQL, including ingredients, instructions, timing, servings, cuisines, categories, cooking methods, equipment, nutrition, ratings, and source information.

Semantic embeddings are generated using OpenAI `text-embedding-3-small` and stored with pgvector.

Embedding generation is performed offline using batching, incremental commits, resumability, and retry/backoff handling.

---

## Production Deployment

**Live application:** [MealMuse](https://mealmuse-frontend-y4ymgnrpwq-uw.a.run.app/) on Google Cloud Run

MealMuse is deployed on **Google Cloud Platform** using separate frontend and backend services.

```text
Browser
   |
   v
Cloud Run
React + Nginx
   |
   | /api/*
   v
Cloud Run
FastAPI
   |             |
   |             +--> OpenAI API
   |
   v
Cloud SQL
PostgreSQL + pgvector
```

Production infrastructure includes:

- **Cloud Run** — independently deployed frontend and backend services
- **Cloud SQL** — PostgreSQL 16 + pgvector
- **Artifact Registry** — frontend and backend container images
- **Cloud Build** — production Docker image builds
- **Secret Manager** — database and OpenAI credentials
- **IAM** — dedicated least-privilege backend service identity
- **GitHub Actions** — continuous integration

The production database contains the migrated 50,514-recipe corpus and its precomputed embeddings.

Production deployment remains manual for V1 by design. Automated CD is deferred until deployment frequency or team size justifies the additional infrastructure and permissions.

See [`docs/deployment.md`](docs/deployment.md) for deployment details.

---

## Production Engineering

MealMuse includes production-oriented safeguards and validation beyond the core AI workflow:

- health and database-readiness endpoints
- request IDs
- request latency logging
- bounded database connection timeouts
- controlled dependency-failure handling
- explicit HTTP failure semantics
- containerized local and production environments
- Nginx API reverse proxying
- runtime secret injection
- least-privilege cloud identity
- CI validation
- production observability and log inspection
- failure and recovery validation
- load and performance testing
- bottleneck analysis
- evidence-based optimization decisions
- final production regression validation

Performance changes are driven by measured behavior rather than optimization being added solely for technology breadth.

---

## Testing

MealMuse is validated across deterministic application logic, AI orchestration, retrieval, infrastructure, frontend behavior, and the deployed production system.

Coverage includes:

- recipe loading and normalization
- hard-constraint filtering
- deterministic ranking
- structured retrieval
- semantic retrieval
- hybrid retrieval and deduplication
- OpenAI tool selection
- tool-argument validation
- chat orchestration
- clarification
- no-results handling
- dependency and tool-execution failures
- deterministic recipe-detail retrieval
- frontend recommendation and search workflows
- frontend loading and failure states
- Docker Compose full-stack behavior
- database failure and recovery
- GitHub Actions CI
- Cloud Run / Cloud SQL integration
- production end-to-end workflows
- load and performance behavior
- final production regression

The backend test suite, frontend lint/build validation, containerized runtime validation, CI pipeline, and production regression have all been validated successfully.

See [`docs/testing.md`](docs/testing.md) for the complete test strategy and validation evidence.

---

## Tech Stack

### Frontend
- React 19
- TypeScript
- Vite
- Nginx
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

### Infrastructure & Cloud
- Docker
- Docker Compose
- Google Cloud Run
- Google Cloud SQL
- Google Artifact Registry
- Google Cloud Build
- Google Secret Manager
- Google Cloud IAM

### Testing & CI
- Pytest
- GitHub Actions
- frontend lint and production-build validation
- integration and production regression testing
- load and performance testing

---

## Running Locally

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

API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 3. Start the React frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL reported by Vite, typically:

```text
http://localhost:5173
```

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

## Engineering Documentation

Detailed engineering documentation is intentionally kept outside the README:

- [`docs/architecture.md`](docs/architecture.md) — architecture, orchestration, retrieval, AI boundaries, and engineering decisions
- [`docs/deployment.md`](docs/deployment.md) — GCP infrastructure and production deployment
- [`docs/testing.md`](docs/testing.md) — automated, integration, failure, performance, and production validation

---

## Current Status

**MealMuse V1 is complete and deployed.**

The system currently includes:

- full-stack React + FastAPI application
- agentic tool-based orchestration
- hybrid PostgreSQL + pgvector retrieval
- deterministic filtering and ranking
- 50,514-recipe production corpus
- Dockerized development and production environments
- GitHub Actions CI
- GCP production deployment
- production observability and failure validation
- load and performance validation
- final production regression testing

Potential V2 work includes persistent conversational state, multi-turn constraint merging, reference resolution, and additional application tools.
