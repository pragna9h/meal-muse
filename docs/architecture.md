# MealMuse Architecture

This document describes the architecture of MealMuse, the responsibilities of its major components, and the engineering decisions behind them.

The architecture will evolve as MealMuse moves from the recommendation foundation toward agentic orchestration, production deployment, and observability.

---

# 1. Current System Architecture

At the end of Day 2, MealMuse supports an end-to-end ingredient-aware recommendation pipeline backed by PostgreSQL and hybrid retrieval.

```text
User
 ↓
FastAPI /chat
 ↓
OpenAI Intent Extraction
 ↓
ParsedIntent
 ↓
Deterministic Clarification Policy
 ↓
┌──────────────────────┬──────────────────────┐
│                      │                      │
Structured Retrieval   Semantic Retrieval
│                      │
PostgreSQL              OpenAI Embedding
│                      │
│                      ↓
│                   pgvector
│                      │
└───────────┬──────────┘
            ↓
      Merge + Deduplicate
            ↓
       Recipe Repository
            ↓
    Hard-Constraint Filtering
            ↓
    Deterministic Ranking
            ↓
       Top 5 Recommendations
            ↓
     Structured API Response
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

The LLM produces a structured `ParsedIntent` rather than directly selecting recipes.

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

The intent extraction layer converts this into `ParsedIntent`.

Example:

```text
ingredients_available = ["chicken", "rice"]
meal_type = "dinner"
taste_preferences = ["spicy"]
max_prep_minutes = 30
```

This structured representation becomes the contract between natural-language understanding and the deterministic recommendation system.

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

The complete Day 2 runtime path is:

```text
Natural Language
      ↓
OpenAI Intent Extraction
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
        FastAPI Response
```

---

# 17. Current Technology Responsibilities

| Technology / Component | Responsibility |
|---|---|
| FastAPI | HTTP API layer |
| OpenAI language model | Natural-language intent extraction |
| OpenAI `text-embedding-3-small` | Semantic query and recipe embeddings |
| Pydantic | API/domain validation and structured contracts |
| PostgreSQL | Runtime recipe store and structured querying |
| pgvector | Vector storage and semantic similarity search |
| SQLAlchemy | Python/PostgreSQL connection and query execution |
| Docker | Local PostgreSQL/pgvector environment |
| Pytest | Regression and integration testing |

Each component is intended to solve a specific MealMuse requirement rather than being included solely for technology breadth.

---

# 18. Architecture Evolution

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

---

# 19. Next Architectural Phase

The next phase introduces agentic orchestration and explicit tool boundaries.

Planned direction:

```text
User
 ↓
Agent Orchestrator
 ↓
Reason about required action
 ↓
Tool Calls
 ↓
Retrieval / Recipe Operations
 ↓
Deterministic Policies
 ↓
Response
```

The orchestrator will not replace deterministic filtering or database retrieval.

Instead, it will coordinate capabilities while preserving the existing separation between:

```text
LLM reasoning
tool execution
recipe facts
deterministic application policy
```

The architecture will be updated as those responsibilities are implemented and validated.