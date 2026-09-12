# MealMuse Architecture

This document describes the architecture of MealMuse, the responsibilities of its major components, and the engineering decisions behind them.

The architecture will evolve as MealMuse moves from the recommendation foundation toward agentic orchestration, production deployment, and observability.

---

# 1. Current System Architecture

MealMuse currently supports two end-to-end natural-language workflows through a React and TypeScript frontend backed by FastAPI, PostgreSQL, and pgvector:

- ingredient-aware meal recommendation
- direct recipe search

The application also supports deterministic recipe-detail retrieval when a user selects a result card.

```text
User
  ↓
React + TypeScript Frontend
  ↓
POST /chat
  ↓
FastAPI API Layer
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
Tool Arguments                 Tool Arguments
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
Hybrid Retrieval             Recipe Name + Semantic Search
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
       Frontend Result Rendering
                  ↓
     Recommendation / Recipe Cards
                  ↓
         User Selects Recipe
                  ↓
      GET /recipes/{recipe_id}
                  ↓
       Deterministic DB Lookup
                  ↓
          Recipe Detail View
```

---

# 2. Architectural Principles

MealMuse follows several principles intended to keep AI reasoning separate from deterministic application behavior.

## LLMs Interpret Semantics

The LLM is used where natural-language understanding is valuable.

Examples include:

- available ingredients
- required or excluded ingredients
- cuisine preferences
- taste preferences
- nutrition goals
- meal type
- time constraints
- equipment
- clarification signals

The LLM selects one of MealMuse's application tools and extracts structured tool arguments from the user's natural-language request.

The backend validates those arguments with Pydantic and converts them into `ParsedIntent`.

The LLM therefore handles semantic interpretation and capability selection, while deterministic backend code retains control over application behavior.

## Databases Provide Recipe Facts

Recipe facts come from the recipe corpus stored in PostgreSQL.

The LLM does not invent:

- recipe names
- ingredients
- cooking times
- nutrition values
- ratings
- source URLs

## Deterministic Code Enforces Product Rules

Hard constraints and predictable application behavior are implemented in backend code.

Examples include:

- excluded ingredients
- required ingredients
- maximum cooking time
- clarification requirements
- deterministic recipe ranking

This prevents probabilistic LLM behavior from overriding explicit user constraints.

---

# 3. Request Understanding

The public recommendation endpoint accepts natural language:

```json
{
  "message": "I have chicken and rice. I want a spicy dinner under 30 minutes."
}
```

The orchestration layer sends the request to the OpenAI model with MealMuse's available tool definitions.

The model selects exactly one application capability:

- `recommend_meals`
- `search_recipe`

The returned tool arguments are validated with Pydantic and converted into `ParsedIntent`.

Example:

```text
ingredients_available = ["chicken", "rice"]
meal_type = "dinner"
taste_preferences = ["spicy"]
max_prep_minutes = 30
```

This structured representation becomes the contract between natural-language understanding and the deterministic recommendation system.

## Supported V1 Workflows

MealMuse V1 supports two primary natural-language workflows.

### Meal Recommendation

The user wants help deciding what to cook based on available ingredients,
constraints, or preferences.

Examples:

- "I have chicken and rice. What can I make?"
- "I want something spicy and high protein under 30 minutes."

Recommendation requests use the existing hybrid recommendation pipeline:

1. Tool selection and structured argument extraction
2. Structured and semantic candidate retrieval
3. Candidate merging and deduplication
4. Full recipe hydration
5. Deterministic hard-constraint filtering
6. Deterministic ranking
7. Top recommendation selection

### Direct Recipe Search

The user already knows the dish they want and asks MealMuse to find it.

Examples:

- "How do I make chicken tikka masala?"
- "Give me a lasagna recipe."
- "Show me how to make pad thai."

Direct recipe search uses a separate retrieval strategy because the retrieval objective differs from meal recommendation.

The search combines:

1. Deterministic recipe-name matching in PostgreSQL
2. Semantic retrieval using pgvector
3. Candidate merging and deduplication
4. Full Recipe hydration from PostgreSQL

Direct recipe search does not use the recommendation filtering and ranking pipeline.

---

# 4. Deterministic Clarification

MealMuse is specifically an ingredient-aware recommendation system.

A request such as:

```text
"I want something light."
```

does not provide sufficient ingredient context.

Although the LLM can identify `"light"` as a preference, application policy determines whether MealMuse has enough information to proceed.

```text
ParsedIntent
     ↓
Ingredients available or required?
     │
 ┌───┴───┐
 No      Yes
 ↓        ↓
Clarify  Retrieve
```

This keeps product-policy decisions deterministic.

---

# 5. Recipe Data Pipeline

The recipe dataset is processed before runtime.

```text
Raw Recipe Dataset
        ↓
Recipe Loader
        ↓
Pydantic Validation
        ↓
Recipe Objects
        ↓
Processed JSON
        ↓
PostgreSQL Ingestion
        ↓
recipes table
```

The processed JSON remains a reproducible intermediate artifact.

PostgreSQL is the runtime recipe store.

The application therefore does not need to repeatedly parse the raw dataset during normal API requests.

---

# 6. PostgreSQL Recipe Store

The `recipes` table stores structured recipe information including:

```text
recipe_id
name
description
ingredients
normalized ingredients
instructions
timing
servings
categories
cuisines
cooking methods
equipment
nutrition
ratings
source URL
search text
embedding
```

PostgreSQL serves two retrieval responsibilities:

```text
Structured recipe attributes
            +
Vector embeddings through pgvector
```

Keeping these in the same database allows structured and semantic retrieval to operate over the same recipe corpus.

---

# 7. Semantic Representation

Each recipe receives a compact `search_text` representation built from:

```text
name
normalized ingredients
categories
cuisines
cooking methods
```

Example:

```text
Pineapple Glaze for Ham |
pineapple maraschino cherries brown sugar |
dinner |
american |
microwave
```

Descriptions are intentionally excluded from the semantic representation because they can be missing or noisy.

The goal is to embed relatively stable attributes that describe what the recipe is and how it relates to a meal request.

---

# 8. Embeddings

MealMuse currently uses:

```text
OpenAI text-embedding-3-small
```

Recipe embeddings are stored as:

```text
VECTOR(1536)
```

inside PostgreSQL using pgvector.

Embedding generation is performed offline rather than during normal recommendation requests.

The ingestion process uses:

- batched API requests
- incremental database commits
- `embedding IS NULL` selection
- retry/backoff for rate limits

This makes corpus embedding generation resumable.

At request time, only the user's semantic query needs to be embedded.

---

# 9. Structured Retrieval

Structured retrieval uses explicit fields extracted into `ParsedIntent`.

Examples include:

```text
ingredients
cuisine
meal type
equipment
maximum time
```

PostgreSQL array fields use GIN indexes where appropriate.

For ingredient candidate retrieval, array overlap operations are used instead of scanning and unnesting every recipe ingredient list.

Conceptually:

```sql
normalized_ingredients && requested_ingredients
```

Structured retrieval is primarily responsible for efficiently identifying recipes related to explicit structured signals.

It is still candidate generation rather than the final recommendation decision.

---

# 10. Semantic Retrieval

Semantic retrieval handles similarity that cannot always be represented cleanly through exact structured comparisons.

Example:

```text
"quick high protein chicken dinner"
        ↓
OpenAI query embedding
        ↓
pgvector cosine-distance search
        ↓
Semantically similar recipes
```

pgvector cosine distance is calculated using:

```sql
embedding <=> query_embedding
```

Lower distance represents greater semantic similarity.

---

# 11. Why Hybrid Retrieval?

Structured and semantic retrieval solve different problems.

Structured retrieval is strong when the request contains explicit fields:

```text
chicken
rice
dinner
30 minutes
Indian
```

Semantic retrieval is useful for concepts such as:

```text
spicy
comforting
light
quick high-protein dinner
```

Using only structured retrieval can miss semantically relevant recipes.

Using only vector similarity can return recipes that are conceptually related but violate explicit requirements.

MealMuse therefore combines both:

```text
Structured Retrieval
        +
Semantic Retrieval
        ↓
Merge
        ↓
Deduplicate
        ↓
Hard Filtering
        ↓
Deterministic Ranking
```

Hybrid retrieval increases candidate recall while deterministic filtering protects correctness.

---

# 12. Repository Layer

Database access is isolated behind:

```text
backend/app/repositories/recipe_repository.py
```

The repository is responsible for operations such as:

```text
semantic_search()
structured_search()
get_recipes_by_ids()
```

Higher application layers therefore do not need to know:

- SQL syntax
- PostgreSQL table structure
- pgvector operators
- row-to-model conversion

Conceptually:

```text
Recommendation / Retrieval Logic
             ↓
      Recipe Repository
             ↓
     PostgreSQL + pgvector
```

This creates a clear database-access boundary.

---

# 13. Retrieval Layer

Hybrid candidate-generation strategy lives separately from database access:

```text
backend/app/retrieval/recipe_retriever.py
```

Its responsibility is to coordinate retrieval methods rather than execute raw SQL.

```text
recipe_retriever
      │
      ├── structured_search()
      │
      └── semantic_search()
                ↓
        recipe_repository
                ↓
        PostgreSQL / pgvector
```

Candidates are merged and deduplicated by `recipe_id`.

Retrieval-source metadata can identify candidates obtained through:

```text
structured
semantic
both
```

This information can later support debugging and observability.

---

# 14. Hard Filtering

Retrieval deliberately favors finding potentially relevant candidates.

It does not have final authority over explicit user constraints.

Candidates therefore pass through deterministic hard filtering before ranking.

Examples:

```text
Excluded ingredient
        ↓
Recipe rejected

Required ingredient missing
        ↓
Recipe rejected

Explicit maximum time violated
        ↓
Recipe rejected
```

A semantically excellent recipe cannot override a hard constraint.

---

# 15. Deterministic Ranking

After hard filtering, remaining candidates are ranked deterministically.

Ranking considers interpretable signals such as:

- available ingredient overlap
- missing ingredients
- preferences
- recipe metadata

The LLM does not directly choose the final Top 5.

This provides repeatable behavior and makes recommendation decisions easier to inspect and test.

---

# 16. Current Recommendation Flow

The current recommendation runtime path is:

```text
Natural Language
      ↓
Chat Orchestrator
      ↓
OpenAI Tool Calling
      ↓
recommend_meals
      ↓
Validated Tool Arguments
      ↓
ParsedIntent
      ↓
Deterministic Clarification
      ↓
Hybrid Candidate Retrieval
   ↙                    ↘
Structured             Semantic
PostgreSQL              pgvector
   ↘                    ↙
      Merge + Deduplicate
              ↓
        Recipe Repository
              ↓
         Recipe Objects
              ↓
        Hard Filtering
              ↓
    Deterministic Ranking
              ↓
           Top 5
              ↓
      MealRecommendation
              ↓
         ChatResponse
```

Direct recipe search follows the same orchestration boundary but executes search_recipe, which uses recipe-name and semantic retrieval rather than the recommendation filtering and ranking pipeline.

---

# 17. Current Technology Responsibilities

| Technology / Component          | Responsibility                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------- |
| React                           | User-facing interface and UI state rendering                                                |
| TypeScript                      | Typed frontend contracts and component development                                          |
| Vite                            | Frontend development and production build tooling                                           |
| FastAPI                         | HTTP API layer                                                                              |
| OpenAI language model           | Natural-language understanding and tool selection                                           |
| OpenAI `text-embedding-3-small` | Semantic query and recipe embeddings                                                        |
| Chat Orchestrator               | Coordinates tool selection, validation, clarification, execution, and response construction |
| OpenAI tool calling             | Exposes explicit meal-recommendation and recipe-search capabilities                         |
| Pydantic                        | API/domain validation and structured contracts                                              |
| PostgreSQL                      | Runtime recipe store and structured querying                                                |
| pgvector                        | Vector storage and semantic similarity search                                               |
| SQLAlchemy                      | Python/PostgreSQL connection and query execution                                            |
| Docker                          | Local PostgreSQL/pgvector environment                                                       |
| Pytest                          | Backend regression and integration testing                                                  |
| ESLint                          | Frontend code-quality validation                                                            |

Each component is intended to solve a specific MealMuse requirement rather than being included solely for technology breadth.

---

# 18. Engineering-Decision

## AI and Deterministic Application Boundaries

MealMuse uses AI where natural-language interpretation or reasoning is
useful and deterministic application logic where the required action is
already known.

For example, a natural-language request such as "How do I make chicken
tikka masala?" requires request understanding to distinguish recipe search
from recommendation.

In contrast, when a user clicks a recipe card, the application already
knows the recipe ID. Recipe-detail retrieval therefore uses a direct API
and database lookup rather than routing the operation through an LLM.

Hard constraints, recipe facts, filtering, calculations, and ranking also
remain deterministic. The LLM does not invent recipe facts or override
hard constraints.

This separation reduces unnecessary latency, API cost, failure surface,
and architectural complexity.

## Agentic Orchestration and Tool Boundaries

MealMuse exposes two AI-callable application tools:

- `recommend_meals`
- `search_recipe`

Tool selection replaces the earlier standalone intent-classification step. This avoids performing one LLM call to classify the request and another to decide which application capability should execute.

The orchestrator is responsible for:

1. request understanding and tool selection,
2. tool-argument validation,
3. `ParsedIntent` construction,
4. deterministic clarification policy,
5. application-tool execution,
6. result inspection,
7. `ChatResponse` construction.

The orchestrator does not perform SQL, vector search, recipe hydration, hard filtering, ranking, or nutrition calculations. Those responsibilities remain in their existing deterministic application layers.

MealMuse currently distinguishes the following product outcomes:

- `SUCCESS`
- `CLARIFICATION_REQUIRED`
- `NO_RESULTS`

Tool-selection failures are surfaced as HTTP 500 responses, while tool-execution or dependency failures are surfaced as HTTP 503 responses. Infrastructure failures therefore do not masquerade as successful HTTP 200 product responses.

## Deferred Conversational Capabilities

Persistent multi-turn recommendation state is intentionally outside the
MealMuse V1 scope.

Examples of deferred interactions include:

- "Make the previous recommendations spicier."
- "Now make them under 20 minutes."
- "Tell me more about the second one."

Supporting these interactions would require conversation state,
constraint merging, reference resolution, and state persistence.

These capabilities are candidates for a future MealMuse V2 rather than
being introduced without a current product requirement.

---

# 19. Architecture Evolution

## Day 1

The initial implementation established the recommendation vertical slice:

```text
Natural Language
      ↓
Intent Extraction
      ↓
JSON/In-Memory Candidate Search
      ↓
Hard Filtering
      ↓
Deterministic Ranking
      ↓
Top 5
```

This allowed the product behavior to be validated before introducing database infrastructure.

## Day 2

Runtime candidate generation moved to:

```text
PostgreSQL structured retrieval
             +
pgvector semantic retrieval
             ↓
       Hybrid Retrieval
```

The existing filtering and ranking layers were intentionally preserved.

This allowed the data/retrieval architecture to evolve without rewriting already validated recommendation behavior.

## Day 3

The request-understanding layer evolved from standalone structured intent
extraction into explicit tool-based orchestration.

```text
Natural Language
      ↓
OpenAI Tool Calling
      ↓
recommend_meals / search_recipe
      ↓
Validated Tool Arguments
      ↓
ParsedIntent
      ↓
Deterministic Application Policies
      ↓
Existing Service and Retrieval Layers
```

## Day 4

The application evolved from a backend-only system into a complete full-stack product.

A React and TypeScript frontend was introduced as the presentation layer while preserving the existing backend architecture.

```text
User
  ↓
React + TypeScript
  ↓
FastAPI
  ↓
Chat Orchestrator
  ↓
Application Tools
  ↓
Recommendation / Search Services
  ↓
PostgreSQL + pgvector
```

---

# 20. Next Architectural Phase

The next architectural phase focuses on production hardening and deployment rather than expanding MealMuse's product feature set.

Planned work includes:

- structured application logging,
- stronger dependency and infrastructure error handling,
- request tracing and latency measurement,
- production-safe environment configuration,
- production CORS configuration,
- backend and frontend containerization,
- health and readiness checks,
- GitHub Actions CI,
- integration testing,
- production deployment to GCP,
- runtime observability,
- load and failure testing,
- production validation.

The goal of the next phase is to evolve MealMuse from a complete local full-stack application into a reproducible, observable, and publicly deployable production system.

Persistent conversational state, constraint merging across turns, and reference resolution remain deferred to a future V2 unless a concrete product requirement justifies them.
