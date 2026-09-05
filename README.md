# MealMuse

MealMuse is an ingredient-aware meal recommendation system that helps users decide what to cook based on the ingredients they already have, along with their preferences and constraints.

The project is being built as an end-to-end **Agentic AI system**, combining LLM-based intent understanding with deterministic retrieval, filtering, and ranking.

## Current Features

- Natural-language meal requests
- Structured intent extraction using an LLM
- Ingredient-aware recipe retrieval
- Hard-constraint filtering
  - Required ingredients
  - Excluded ingredients
  - Time constraints
- Deterministic recipe ranking
- Top-5 meal recommendations
- Nutrition and recipe metadata
- Clarification handling for underspecified requests
- FastAPI backend with structured request/response models
- Automated unit and API tests
- Recipe processing pipeline for 50K+ recipes

## Current Recommendation Pipeline

```text
User Request
     ↓
FastAPI
     ↓
LLM Intent Extraction
     ↓
Structured Parsed Intent
     ↓
Candidate Recipe Retrieval
     ↓
Hard-Constraint Filtering
     ↓
Deterministic Ranking
     ↓
Top 5 Recommendations
```

## Development Journey

### Phase I — Building the First End-to-End Vertical Slice

The goal for Day 1 was not to build the complete production architecture immediately. Instead, the focus was to establish a working vertical slice that could take a natural-language request and return real, ranked meal recommendations.

This gave the project a functional baseline before introducing PostgreSQL, vector search, orchestration, caching, observability, and cloud infrastructure.

#### 1. Defining the Product Boundary

MealMuse initially had the potential to become a broad food assistant covering recipe search, meal planning, grocery assistance, nutrition, and recommendations.

For V1, the scope was deliberately narrowed to one core problem:

> **"I have these ingredients. What should I cook?"**

MealMuse therefore became an **ingredient-aware meal recommendation advisor** rather than a generic food chatbot.

The primary input remains natural language, while the data model also supports constraints and preferences such as:

- available ingredients
- required ingredients
- excluded ingredients
- meal type
- dietary preferences and allergies
- cuisine preferences
- nutrition goals
- maximum preparation time
- servings
- taste preferences
- available equipment
- budget and skill level
- substitution preference

A key modeling decision was separating:

```text
ingredients_available
ingredients_required
ingredients_excluded
```

rather than treating every ingredient mentioned by the user identically.

#### 2. Establishing the Backend

The backend was created using **Python 3.12 and FastAPI**.

Initial API functionality included:

```text
GET  /health
POST /chat
GET  /docs
```

Pydantic models were introduced to create explicit contracts between natural-language understanding, recommendation logic, and the API response.

The `/chat` endpoint became the entry point for the recommendation pipeline.

#### 3. Adding Structured LLM Intent Extraction

The OpenAI API was integrated behind a dedicated LLM service rather than calling the model directly throughout the application.

The intent extraction component converts requests such as:

```text
"I have chicken, spinach and rice.
Give me a high-protein dinner under 30 minutes."
```

into structured data representing ingredients, constraints, and preferences.

An important architectural principle emerged here:

> **Use the LLM for semantic understanding, but use deterministic application code for rules that must behave predictably.**

For example, ingredient normalization is enforced by Pydantic validators rather than depending on the model to always return consistently formatted strings.

#### 4. Building the Recipe Data Pipeline

The initial recipe dataset contained **50,514 recipes** with useful information including:

- ingredients
- instructions
- preparation and cooking times
- servings
- cuisine/category information
- cooking methods
- nutrition
- ratings
- source URLs

The raw dataset was not suitable for direct application use, so a processing layer was built to transform each source row into a validated `Recipe` model.

This required parsing nested ingredient structures, nutrition fields, instructions, metadata, and inconsistent or missing values.

After resolving parsing issues discovered during implementation:

```text
Successfully loaded: 50514
Failed to load: 0
```

The processed corpus is generated locally as `recipes.json`.

Raw and generated datasets are intentionally excluded from Git because the processed dataset can be reproduced from the ingestion pipeline.

#### 5. Separating Recipe Loading from Runtime Access

Rather than repeatedly parsing the entire dataset for every recommendation request, a runtime recipe store was introduced.

The processed recipes are loaded once and cached for reuse:

```text
Processed Recipe Corpus
        ↓
Recipe Store
        ↓
Recommendation Pipeline
```

This provided a simple runtime architecture for the first vertical slice while leaving the storage layer replaceable.

The long-term architecture will replace this local store with PostgreSQL and pgvector.

#### 6. Candidate Retrieval

The next layer introduced candidate retrieval.

Instead of attempting to rank all 50K+ recipes for every request, MealMuse first retrieves a smaller set of recipes that are plausibly relevant to the user's available ingredients.

This established an important separation:

```text
Retrieval
    ↓
"What recipes might be relevant?"

Ranking
    ↓
"Which of those recipes are best?"
```

This distinction will become more important when semantic/vector retrieval is introduced.

#### 7. Hard-Constraint Filtering

Candidate recipes then pass through deterministic filtering.

Hard constraints such as:

```text
excluded ingredients
required ingredients
maximum time
```

are enforced before ranking.

This prevents ranking from accidentally promoting a recipe that violates an explicit user requirement.

For example:

```text
User: "No peanuts"
        ↓
Candidate retrieval
        ↓
Remove every recipe containing peanuts
        ↓
Rank only valid recipes
```

This also established a broader design principle for MealMuse:

> **Hard constraints are enforced deterministically; preferences influence ranking.**

#### 8. Discovering and Fixing the Recipe-Time Problem

During end-to-end testing, some highly ranked recipes appeared with:

```text
total_time_minutes = 0
```

Treating `0` as a genuine cooking time caused recipes with incomplete source data to incorrectly satisfy strict time constraints.

The time model was therefore changed.

MealMuse now derives an effective recipe time using available timing information rather than blindly trusting `total_time_minutes`.

Conceptually:

```text
valid total time
      ↓
use it

otherwise
      ↓
prep time + cook time

otherwise
      ↓
time unknown
```

Unknown-time recipes are not allowed to satisfy explicit maximum-time constraints.

This was an example of the implementation changing after observing real dataset behavior rather than designing solely from assumptions.

#### 9. Deterministic Ranking

After filtering, remaining candidates are scored and ranked.

The first ranking implementation considers signals such as:

- available ingredient coverage
- missing ingredients
- meal-type compatibility
- cuisine preference
- recipe metadata
- ratings
- time suitability

The ranking layer also records why a recipe matched, allowing the API to return information such as:

```text
matched ingredients
missing ingredients
score
time
nutrition
recommendation reason
source URL
```

The current algorithm is intentionally deterministic and interpretable.

Future iterations will combine this with semantic retrieval and richer ranking signals.

#### 10. Building the Recommendation Service

Retrieval, filtering, and ranking were then composed into a single recommendation service:

```text
ParsedIntent
     ↓
Candidate Retrieval
     ↓
Hard-Constraint Filtering
     ↓
Ranking
     ↓
Top 5
     ↓
MealRecommendation
```

This replaced the placeholder response originally used while constructing the API.

At this point, `/chat` became a complete working recommendation endpoint.

#### 11. Fixing Underspecified Requests

End-to-end testing uncovered another important issue.

A request such as:

```text
"I want something light."
```

was initially interpreted as:

```text
taste_preferences = ["light"]
needs_clarification = false
```

Because no ingredients were provided, the retrieval/ranking pipeline still returned recipes — including unrelated results such as desserts.

Rather than trying to compensate inside the ranking algorithm, a deterministic clarification policy was introduced.

MealMuse now recognizes when there is insufficient information for a meaningful ingredient-aware recommendation and returns a clarification request instead of arbitrary recipes.

This reinforced the separation between:

```text
LLM
→ understands what the user said

Application policy
→ decides whether the system has enough information to proceed
```

#### 12. Testing the Complete Pipeline

For the complete Day 1 validation history — including command-line smoke tests, API test scenarios, failures discovered during development, fixes, retests, and the automated regression suite — see [`docs/testing.md`](docs/testing.md).

#### Day 1 Outcome

By the end of Day 1, MealMuse had progressed from an empty backend structure to a working recommendation system:

```text
Natural-Language Request
          ↓
       FastAPI
          ↓
Structured LLM Intent Extraction
          ↓
   Clarification Policy
          ↓
 Candidate Recipe Retrieval
          ↓
 Hard-Constraint Filtering
          ↓
 Deterministic Ranking
          ↓
   Top 5 Recommendations
          ↓
 Structured API Response
```

The first milestone was committed only after the full vertical slice was working and both manual and automated tests passed.

The architecture is intentionally evolutionary: the local recipe store and deterministic retrieval provide a working baseline that can now be measured and progressively replaced with production-oriented components.

---

## Tech Stack

### Current

- Python 3.12
- FastAPI
- Pydantic
- OpenAI API
- Pytest

### Planned

- React + TypeScript
- PostgreSQL + pgvector
- Redis
- Agent orchestration
- Docker + Kubernetes
- GCP
- CI/CD
- OpenTelemetry
- Prometheus + Grafana

## Project Status

🚧 **Active development**

### Completed

**Phase I — Initial Recommendation Pipeline**

- [x] FastAPI backend
- [x] Structured LLM intent extraction
- [x] 50K+ recipe processing pipeline
- [x] Runtime recipe store
- [x] Candidate retrieval
- [x] Hard-constraint filtering
- [x] Deterministic ranking
- [x] Top-5 recommendations
- [x] Clarification handling
- [x] Initial automated tests

### Next

**Phase II — Production Retrieval Layer**

```text
PostgreSQL
    +
 pgvector
    ↓
Embeddings
    ↓
Hybrid Retrieval
    ↓
Improved Ranking
```

Later phases will introduce agent orchestration, React + TypeScript, authentication, Redis, integration testing, failure handling, structured logging, tracing, rate limiting, Docker/Kubernetes, CI/CD, observability, GCP deployment, load testing, and architecture documentation.

## Goal

Build MealMuse into a **production-grade Agentic AI system** while exploring the engineering required to take an AI application from an initial working vertical slice to a reliable, observable, tested, scalable, and deployed product.
