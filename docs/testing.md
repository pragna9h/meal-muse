# MealMuse Testing

This document tracks how MealMuse is validated throughout development.

Testing is treated as part of the engineering process rather than something added only after implementation. During development, tests are used not only to verify correctness but also to expose assumptions in the architecture, identify data-quality problems, and guide design changes.

---

# Testing Strategy

MealMuse currently uses three levels of testing:

```text
Incremental Development Tests
        ↓
Manual End-to-End API Tests
        ↓
Automated Regression Tests
```

## 1. Incremental Development Tests

Small command-line tests and smoke-test scripts are executed while individual components are being built.

These tests answer questions such as:

- Can the model be imported?
- Can the OpenAI client connect?
- Can one recipe be parsed?
- Can the complete corpus be processed?
- Does caching work?
- Does candidate retrieval return sensible recipes?
- Are hard constraints actually enforced?
- Does ranking prefer stronger ingredient matches?

These tests provide fast feedback before components are connected to the full application.

## 2. Manual End-to-End API Tests

After the recommendation pipeline was connected to `POST /chat`, realistic natural-language requests were tested through FastAPI's Swagger interface.

These tests validate the complete path:

```text
Natural-Language Request
        ↓
Intent Extraction
        ↓
Clarification Policy
        ↓
Candidate Retrieval
        ↓
Hard-Constraint Filtering
        ↓
Ranking
        ↓
Recommendation Service
        ↓
Structured API Response
```

## 3. Automated Regression Tests

Important deterministic behaviors are preserved as Pytest tests under:

```text
backend/tests/
```

These tests protect previously working behavior as MealMuse evolves.

---

# Day 1 — Initial Recommendation Pipeline

The objective of Day 1 testing was to validate the first complete MealMuse vertical slice incrementally rather than building the entire pipeline and testing it only at the end.

---

# 1. OpenAI Connectivity

## Test: OpenAI API Connection

### Purpose

Verify that:

- environment configuration loads correctly
- the OpenAI API key is accessible to the application
- the OpenAI Python client works
- the configured model can successfully respond

### Files / Components Tested

```text
.env
backend/app/config/settings.py
backend/app/services/llm.py
test_openai_connection.py
```

### Test Script

```text
test_openai_connection.py
```

### Run With

```bash
python test_openai_connection.py
```

### Expected Behavior

A successful response should be returned without authentication, configuration, SDK, or model errors.

### Observed Result

```text
MealMuse connection successful
```

### Status

**PASS**

---

# 2. Structured Intent Extraction

## Test: Basic Intent Extraction

### Purpose

Verify that MealMuse can convert a natural-language meal request into the structured `ParsedIntent` model.

### Files / Components Tested

```text
backend/app/agents/intent.py
backend/app/models/chat.py
backend/app/services/llm.py
test_intent_agent.py
```

### Test Script

```text
test_intent_agent.py
```

### Input

```text
I have chicken, spinach and rice.
Give me a high-protein dinner under 30 minutes.
```

### Expected Extraction

```text
ingredients_available:
- chicken
- spinach
- rice

meal_type:
- dinner

nutrition_goals:
- high protein

max_prep_minutes:
- 30
```

Fields not supplied by the user should remain empty or `null`.

### Result

**PASS**

The intent extractor correctly identified the ingredients, meal type, nutrition goal, and time constraint without inventing unrelated constraints.

---

## Test: Complex Multi-Constraint Intent

### Purpose

Verify that the intent extraction layer can represent several independent preferences and constraints from one natural-language request.

### Input

```text
I have chicken breast, rice, spinach, Greek yogurt and onions.
Dinner for 2, high protein, under 500 calories per serving,
ready in 30 minutes. No peanuts. I prefer something spicy
and Indian-inspired. I only have a stovetop and microwave.
```

### Expected Extraction

The structured intent should capture:

```text
ingredients_available:
- chicken breast
- rice
- spinach
- greek yogurt
- onions

ingredients_excluded:
- peanuts

meal_type:
- dinner

servings:
- 2

nutrition_goals:
- high protein
- under 500 calories per serving

max_prep_minutes:
- 30

taste_preferences:
- spicy

cuisine_preferences:
- Indian

equipment_available:
- stovetop
- microwave
```

### Result

**PASS**

This test also confirmed deterministic ingredient normalization such as:

```text
Greek yogurt
        ↓
greek yogurt
```

---

# 3. Recipe Model Validation

## Test: Recipe Model Import

### Purpose

Verify that the `Recipe`, `Ingredient`, and `Nutrition` Pydantic models can be imported successfully after defining the recipe-domain schema.

### Files / Components Tested

```text
backend/app/models/recipe.py
```

### Command-Line Test

```bash
python -c "from backend.app.models.recipe import Recipe, Ingredient, Nutrition; print('Recipe models imported successfully')"
```

### Expected Output

```text
Recipe models imported successfully
```

### Result

**PASS**

### Issue Encountered During Development

The first attempt produced a Pydantic error related to a field validator referencing an incorrect/nonexistent field.

The problem occurred while an older version of the model remained alongside the updated implementation.

After removing the obsolete model code and retaining the intended schema, the import succeeded.

This was verified before continuing with dataset ingestion.

---

## Test: Recipe Schema Inspection

### Purpose

Verify that the final `Recipe` model exposes the expected fields.

### Command-Line Test

```bash
python -c "from backend.app.models.recipe import Recipe; print(Recipe.model_json_schema()['properties'].keys())"
```

### Observed Schema

The model exposed fields including:

```text
recipe_id
name
description
ingredients
ingredients_raw
normalized_ingredients
instructions
prep_time_minutes
cook_time_minutes
total_time_minutes
servings
serving_description
categories
cuisines
cooking_methods
equipment
nutrition
rating_value
rating_count
source_url
```

### Status

**PASS**

---

# 4. Recipe Dataset Processing

## Test: Single Recipe Parsing

### Purpose

Before processing the complete dataset, validate that one raw recipe row can be converted into the internal MealMuse `Recipe` representation.

### Files / Components Tested

```text
backend/app/services/recipe_loader.py
backend/app/models/recipe.py
data/raw/
```

### Run With

```bash
python -m backend.app.services.recipe_loader
```

### Initial Result

**FAIL**

The first execution produced:

```text
IndexError: list index out of range
```

The failure originated while extracting a numeric nutrition value.

The parsing code assumed that converting a raw nutrition field to a string and splitting it would always produce a usable first element.

The real dataset contained missing/empty values that violated this assumption.

### Resolution

The nutrition parsing logic was made tolerant of missing and malformed values instead of assuming every field contained a valid number.

### Retest

The first recipe was successfully transformed.

Example:

```text
recipe_id: recipe_000001
name: Pineapple Glaze for Ham
```

The resulting object included:

- structured ingredients
- raw ingredient descriptions
- normalized ingredients
- instructions
- preparation/cooking time
- servings
- categories
- cuisines
- cooking methods
- equipment
- nutrition
- ratings
- source URL

### Status

**PASS AFTER FIX**

---

# 5. Complete Corpus Processing

## Test: Process All Recipe Rows

### Purpose

Validate that the parsing logic works across the complete source corpus rather than only on a single example.

### Files / Components Tested

```text
backend/app/services/recipe_loader.py
backend/app/models/recipe.py
data/raw/
```

### Run With

```bash
python -m backend.app.services.recipe_loader
```

### Observed Output

```text
Successfully loaded: 50514
Failed to load: 0
```

### Status

**PASS**

All **50,514 recipes** were successfully transformed into validated MealMuse recipe objects.

---

## Test: Generate Processed Recipe Corpus

### Purpose

Persist the validated recipe representation so runtime code does not need to repeatedly process the raw source dataset.

### Run With

```bash
python -m backend.app.services.recipe_loader
```

### Observed Output

```text
Successfully loaded: 50514
Failed to load: 0
Saved processed recipes to: data\processed\recipes.json
```

### Generated Artifact

```text
data/processed/recipes.json
```

### Status

**PASS**

The generated corpus is excluded from Git because it can be reproduced by the processing pipeline.

---

# 6. Runtime Recipe Store

## Test: Load Processed Corpus

### Purpose

Verify that the processed recipe corpus can be loaded at runtime and deserialized into `Recipe` objects.

### Files / Components Tested

```text
backend/app/services/recipe_store.py
backend/app/models/recipe.py
data/processed/recipes.json
```

### Command-Line Test

```bash
python -c "from backend.app.services.recipe_store import load_recipes; recipes = load_recipes(); print(len(recipes)); print(recipes[0].name)"
```

### Observed Output

```text
50514
Pineapple Glaze for Ham
```

### Status

**PASS**

---

## Test: Recipe Store Caching

### Purpose

Verify that repeated calls to `load_recipes()` reuse the loaded collection rather than repeatedly deserializing all 50,514 recipes.

### Files / Components Tested

```text
backend/app/services/recipe_store.py
```

### Command-Line Test

```bash
python -c "from backend.app.services.recipe_store import load_recipes; a = load_recipes(); b = load_recipes(); print(a is b)"
```

### Observed Output

```text
True
```

### Status

**PASS**

The same cached collection was reused.

---

# 7. Candidate Recipe Retrieval

## Test: Ingredient-Based Candidate Search

### Purpose

Verify that candidate generation returns recipes plausibly related to the ingredients supplied by the user.

### Files / Components Tested

```text
backend/app/services/recipe_search.py
backend/app/services/recipe_store.py
backend/app/models/chat.py
```

### Command-Line Test

```bash
python -c "from backend.app.models.chat import ParsedIntent; from backend.app.services.recipe_search import search_recipe_candidates; intent = ParsedIntent(ingredients_available=['chicken','spinach','rice']); recipes = search_recipe_candidates(intent, limit=10); [print(r.name) for r in recipes]"
```

### Observed Output

```text
Chicken and Tortellini Florentine Soup
Make-Ahead Chicken Divan Casserole
Peppers Stuffed with Spinach and Ground Chicken
Hearty Chicken and Rice Soup
Rouxless Gumbo
Methi Murgh (Fenugreek Chicken)
Creamy Tomato-Chicken Pasta
Honey Chicken and Rice Casserole
Chicken and Spinach Alfredo Lasagna
Torta di Riso
```

### Status

**PASS**

The candidate stage returned recipes related to one or more available ingredients.

This validated the separation between:

```text
Candidate Retrieval
        ↓
"What recipes might be relevant?"

Final Ranking
        ↓
"Which candidates best satisfy this request?"
```

---

# 8. Hard-Constraint Filtering

## Test: Maximum Time Constraint

### Purpose

Verify that recipes violating an explicit maximum-time constraint are removed before ranking.

### Files / Components Tested

```text
backend/app/services/recipe_search.py
backend/app/services/recipe_filter.py
backend/app/services/recipe_time.py
backend/app/models/chat.py
```

### Test Intent

```text
ingredients_available:
- chicken
- spinach
- rice

max_prep_minutes:
- 30
```

### Observed Output

```text
Candidates: 200
After filtering: 41
```

Example filtered recipes included:

```text
Spinach Salad with Chicken, Avocado, and Goat Cheese -> 20 min
Lemon BBQ Chicken Salad -> 30 min
Chicken Salad Spread -> 5 min
Jason's Salmon Florentine -> 25 min
Strawberry and Spinach Salad with Honey-Poppy Seed Dressing -> 15 min
Date and Spinach Salad -> 10 min
Mushroom Spinach Omelet -> 30 min
The Best Spinach Salad -> 25 min
Chicken Caesar Salad on a Stick -> 10 min
```

### Status

**PASS**

---

## Test: Excluded Ingredient Constraint

### Purpose

Verify that excluded ingredients are treated as hard constraints rather than simply lowering recommendation score.

### Files / Components Tested

```text
backend/app/services/recipe_search.py
backend/app/services/recipe_filter.py
backend/app/models/chat.py
```

### Command-Line Test

```bash
python -c "from backend.app.models.chat import ParsedIntent; from backend.app.services.recipe_search import search_recipe_candidates; from backend.app.services.recipe_filter import filter_recipes; intent = ParsedIntent(ingredients_available=['chicken','rice'], ingredients_excluded=['peanut']); candidates = search_recipe_candidates(intent, limit=200); filtered = filter_recipes(candidates, intent); print('Candidates:', len(candidates)); print('Filtered:', len(filtered)); print('Peanut recipes remaining:', sum(1 for r in filtered if any('peanut' in i for i in r.normalized_ingredients)))"
```

### Observed Output

```text
Candidates: 200
Filtered: 196
Peanut recipes remaining: 0
```

### Status

**PASS**

No recipe containing the excluded ingredient remained after filtering.

---

## Test: Required Ingredient Constraint

### Purpose

Verify that a recipe missing an explicitly required ingredient cannot proceed to ranking.

### Files / Components Tested

```text
backend/app/services/recipe_search.py
backend/app/services/recipe_filter.py
backend/app/models/chat.py
```

### Command-Line Test

```bash
python -c "from backend.app.models.chat import ParsedIntent; from backend.app.services.recipe_search import search_recipe_candidates; from backend.app.services.recipe_filter import filter_recipes; intent = ParsedIntent(ingredients_available=['chicken','spinach','rice'], ingredients_required=['spinach']); candidates = search_recipe_candidates(intent, limit=200); filtered = filter_recipes(candidates, intent); print('Candidates:', len(candidates)); print('Filtered:', len(filtered)); [print(r.name) for r in filtered[:10]]"
```

### Observed Output

```text
Candidates: 200
Filtered: 96
```

Example results included:

```text
Chicken and Tortellini Florentine Soup
Peppers Stuffed with Spinach and Ground Chicken
Methi Murgh (Fenugreek Chicken)
Creamy Tomato-Chicken Pasta
Chicken and Spinach Alfredo Lasagna
Torta di Riso
Chicken, Spinach, and Cheese Pasta Bake
Cream of Chicken and Gnocchi Soup
```

### Status

**PASS**

---

# 9. Deterministic Recipe Ranking

## Test: Ranking Relevant Candidates

### Purpose

Verify that recipes matching more of the user's available ingredients rank above weaker matches.

### Files / Components Tested

```text
backend/app/services/recipe_ranker.py
backend/app/services/recipe_filter.py
backend/app/services/recipe_search.py
backend/app/models/chat.py
```

### Test Intent

```text
ingredients_available:
- chicken
- spinach
- rice

meal_type:
- dinner

max_prep_minutes:
- 30
```

### Command-Line Test

The ranking pipeline was executed from the command line by:

1. creating a `ParsedIntent`
2. retrieving up to 200 candidates
3. applying hard filters
4. ranking the remaining recipes
5. printing score, recipe name, matched ingredients, and missing ingredients

### Observed Output

Top results included:

```text
60.4  -> Scrumptious Chicken Vegetable Stew
         matched: ['chicken', 'spinach']
         missing: ['rice']

59.92 -> Southwest Chicken Casserole
         matched: ['chicken', 'rice']
         missing: ['spinach']

59.8  -> Veggie Chicken Rice Casserole
         matched: ['chicken', 'rice']
         missing: ['spinach']

48.77 -> Bang Bang Sriracha Cocktail Meatballs
         matched: ['chicken', 'rice']
         missing: ['spinach']

48.76 -> Keto Creamy Spinach, Mushroom, and Tomato Risotto
         matched: ['spinach', 'rice']
         missing: ['chicken']
```

### Status

**PASS**

The test confirmed that ranking exposes interpretable signals:

```text
score
matched ingredients
missing ingredients
```

rather than returning an unexplained ordering.

---

# 10. Recommendation Service

## Test: Complete Recommendation Pipeline

### Purpose

Verify that retrieval, filtering, ranking, and response construction work together through `recommend_meals()`.

### Files / Components Tested

```text
backend/app/services/recommendation_service.py
backend/app/services/recipe_search.py
backend/app/services/recipe_filter.py
backend/app/services/recipe_ranker.py
backend/app/services/recipe_time.py
backend/app/models/chat.py
```

### Test Intent

```text
ingredients_available:
- chicken
- spinach
- rice

meal_type:
- dinner

max_prep_minutes:
- 30
```

### Initial Observed Result

The recommendation service returned structured Top-5 recommendations containing:

```text
recipe_id
name
score
total_time_minutes
calories
protein_g
matched_ingredients
missing_ingredients
reason
source_url
```

### Status

**PASS**, but testing exposed an important time-data issue described below.

---

# 11. Issue Discovered — Zero / Missing Recipe Times

## Problem Discovery

During recommendation-service testing, several high-ranking recipes appeared as:

```text
Scrumptious Chicken Vegetable Stew
total_time_minutes: 0

Southwest Chicken Casserole
total_time_minutes: 0

Veggie Chicken Rice Casserole
total_time_minutes: 0
```

The recommendation reason consequently produced output such as:

```text
Ready in about 0 minutes.
```

This was conceptually incorrect.

A source value of `0` did not necessarily mean that the recipe actually required zero minutes. It could indicate incomplete timing information.

---

## Architectural Problem

The application was effectively assuming:

```text
total_time_minutes = 0
        ↓
recipe takes zero minutes
```

That assumption could allow unknown-time recipes to incorrectly satisfy a request such as:

```text
under 30 minutes
```

---

## Resolution

Recipe-time handling was separated into dedicated logic.

MealMuse now derives an effective recipe time using the available source fields.

Conceptually:

```text
Valid total_time_minutes?
        │
       YES
        ↓
Use total time

        │ NO
        ↓

Valid prep + cook time?
        │
       YES
        ↓
Use prep + cook

        │ NO
        ↓
Time is unknown
```

A recipe with unknown time is not treated as satisfying an explicit maximum-time constraint.

---

## Retest

The same recommendation request was executed again.

The previous zero-time recommendations disappeared from the constrained Top-5 results.

Updated recommendations included recipes with valid effective times such as:

```text
Bang Bang Sriracha Cocktail Meatballs -> 29 min
Keto Creamy Spinach, Mushroom, and Tomato Risotto -> 30 min
Spinach Salad with Chicken, Avocado, and Goat Cheese -> 20 min
Lemon BBQ Chicken Salad -> 30 min
Strawberry and Spinach Salad with Honey-Poppy Seed Dressing -> 15 min
```

### Status

**PASS AFTER FIX**

### Engineering Lesson

Real dataset behavior changed the implementation.

Instead of trusting a single source field blindly, MealMuse now explicitly models unknown timing data and derives usable timing information where possible.

---

# 12. End-to-End `/chat` API Testing

After the complete recommendation pipeline was connected to `POST /chat`, the system was manually tested through FastAPI Swagger.

Swagger endpoint:

```text
http://127.0.0.1:8000/docs
```

The following scenarios were tested.

| Scenario | Result |
|---|---|
| Basic ingredient recommendation | PASS |
| Time constraint | PASS |
| Excluded ingredient | PASS |
| Required ingredient | PASS |
| Cuisine preference | PASS |
| Nutrition preference | PASS |
| Multiple constraints together | PASS |
| Clarification | INITIAL FAIL → FIXED → PASS |
| Very minimal request | PASS |
| No matching constraints | PASS |

---

## API Test 1: Basic Ingredient Recommendation

### Input

```json
{
  "message": "I have chicken, spinach and rice. Give me dinner ideas."
}
```

### Validated

- available ingredients are extracted
- meal type is extracted
- real recipes are returned
- five recommendations are produced when sufficient candidates exist
- ingredient overlap influences ranking

### Status

**PASS**

---

## API Test 2: Time Constraint

### Input

```json
{
  "message": "I have chicken and rice. I need dinner in 20 minutes."
}
```

### Validated

- `max_prep_minutes` is extracted
- time is enforced as a hard constraint
- returned recipes have usable timing information
- unknown-time recipes do not incorrectly satisfy the constraint

### Status

**PASS**

---

## API Test 3: Excluded Ingredient

### Input

```json
{
  "message": "I have chicken and rice. No peanuts."
}
```

### Validated

- excluded ingredient is extracted
- recipes containing the excluded ingredient are removed before ranking

### Status

**PASS**

---

## API Test 4: Required Ingredient

### Input

```json
{
  "message": "I have chicken, spinach and rice. I definitely want to use spinach."
}
```

### Validated

- `spinach` is interpreted as required
- recipes without the required ingredient are removed

### Status

**PASS**

---

## API Test 5: Cuisine Preference

### Input

```json
{
  "message": "I have chicken and rice. I want something Indian-inspired."
}
```

### Validated

- cuisine preference is extracted
- cuisine preference participates in recommendation ranking
- ingredient relevance is still considered

### Status

**PASS**

---

## API Test 6: Nutrition Preference

### Input

```json
{
  "message": "I have chicken, spinach and rice. I want a high-protein dinner."
}
```

### Validated

- nutrition preference is extracted
- recommendation pipeline handles nutrition goals correctly

### Status

**PASS**

Nutrition-aware ranking will continue to become more sophisticated in later iterations.

---

## API Test 7: Multiple Constraints Together

### Input

```json
{
  "message": "I have chicken, spinach, rice and onions. Dinner for 2, under 30 minutes, no peanuts, and I prefer something spicy and Indian-inspired."
}
```

### Validated

A single request can carry multiple independent signals through the pipeline:

```text
available ingredients
servings
maximum time
excluded ingredient
cuisine preference
taste preference
```

Hard constraints remain enforced while preferences influence recommendation quality.

### Status

**PASS**

---

# 13. Issue Discovered — Clarification Policy

## API Test 8: Underspecified Request

### Input

```json
{
  "message": "I want something light."
}
```

### Expected Behavior

Because MealMuse is an ingredient-aware recommendation system and the user supplied no ingredients, the system should request additional information rather than return arbitrary recipes.

---

## Initial Result

**FAIL**

The LLM produced approximately:

```json
{
  "ingredients_available": [],
  "ingredients_required": [],
  "ingredients_excluded": [],
  "taste_preferences": ["light"],
  "needs_clarification": false,
  "clarification_question": null
}
```

Because `needs_clarification` was false, the recommendation pipeline continued.

It returned unrelated recommendations including:

```text
Grandma's Lemon Meringue Pie
Old-Fashioned Coconut Cream Pie
Banana Cake
White Chocolate Raspberry Cheesecake
Marinade for Chicken
```

This exposed an architectural issue rather than simply a bad ranking result.

---

## Root Cause

The application trusted the LLM to make the final product-policy decision about whether sufficient information existed to recommend a meal.

The model correctly interpreted `"light"` as a preference, but MealMuse still lacked enough ingredient context for its intended recommendation workflow.

---

## Resolution

A deterministic clarification policy was added to the application layer.

The architecture became:

```text
LLM
 ↓
Understand user semantics
 ↓
ParsedIntent
 ↓
Deterministic application policy
 ↓
Enough information?
   │
   ├── No → clarification
   │
   └── Yes → recommendation pipeline
```

This separates two responsibilities:

> **The LLM interprets what the user said.**

> **Deterministic application logic decides whether MealMuse has enough information to proceed safely and usefully.**

---

## Retest

The same request was executed again:

```json
{
  "message": "I want something light."
}
```

### Observed Result

```text
needs_clarification: true
recommendations: []
```

A clarification question was returned asking the user for available ingredients.

### Status

**PASS AFTER FIX**

---

# 14. API Test 9: Very Minimal Request

### Input

```json
{
  "message": "I have eggs and potatoes."
}
```

### Purpose

Verify that MealMuse does not over-clarify.

A user should not be forced to provide every optional field before receiving recommendations.

### Validated

The available ingredients provide sufficient information to enter the recommendation pipeline even though fields such as:

```text
meal type
servings
cuisine
nutrition goal
taste
budget
equipment
```

may remain unspecified.

### Status

**PASS**

This test complements the clarification test:

```text
"I want something light."
        ↓
Insufficient ingredient context
        ↓
Clarify

"I have eggs and potatoes."
        ↓
Sufficient ingredient context
        ↓
Recommend
```

---

# 15. API Test 10: Highly Restrictive / No-Match Request

### Input

```json
{
  "message": "I have chicken and rice. I need it in 5 minutes and no dairy."
}
```

### Purpose

Verify that highly restrictive requests do not crash the application.

### Validated

- intent extraction succeeds
- hard constraints remain enforced
- the API remains stable
- small or empty result sets can be returned safely

### Status

**PASS**

Future failure-handling work will improve the user experience for empty result sets, for example by offering to relax a constraint rather than simply returning no recommendations.

---

# 16. Automated Regression Tests

After manual component and end-to-end validation, the most important deterministic behaviors were converted into automated Pytest tests.

## Test Directory

```text
backend/tests/
├── test_chat_api.py
├── test_recipe_filter.py
├── test_recipe_loader.py
└── test_recipe_ranker.py
```

---

## Automated Test: Health Endpoint

### File

```text
backend/tests/test_chat_api.py
```

### Test

```text
test_health_endpoint
```

### Purpose

Verify that the FastAPI application starts correctly and exposes a functioning health endpoint.

### Status

**PASS**

---

## Automated Test: Excluded Ingredient Filtering

### File

```text
backend/tests/test_recipe_filter.py
```

### Test

```text
test_excluded_ingredient_is_filtered
```

### Purpose

Protect the hard-constraint behavior that prevents excluded ingredients from appearing in valid recommendations.

### Status

**PASS**

---

## Automated Test: Required Ingredient Filtering

### File

```text
backend/tests/test_recipe_filter.py
```

### Test

```text
test_required_ingredient_is_enforced
```

### Purpose

Ensure recipes missing explicitly required ingredients are rejected.

### Status

**PASS**

---

## Automated Test: Zero-Time Normalization

### File

```text
backend/tests/test_recipe_loader.py
```

### Test

```text
test_zero_time_becomes_none
```

### Purpose

Protect the fix introduced after discovering that zero-valued recipe times could actually represent missing timing information.

### Status

**PASS**

---

## Automated Test: Positive Recipe Time

### File

```text
backend/tests/test_recipe_loader.py
```

### Test

```text
test_positive_time_is_preserved
```

### Purpose

Verify that valid positive recipe times are preserved while invalid zero-time values are normalized.

### Status

**PASS**

---

## Automated Test: Ingredient-Based Ranking

### File

```text
backend/tests/test_recipe_ranker.py
```

### Test

```text
test_recipe_with_more_matching_ingredients_ranks_higher
```

### Purpose

Verify that a recipe matching more of the user's available ingredients ranks above an otherwise weaker ingredient match.

### Status

**PASS**

---

# 17. Complete Automated Test Run

### Command

On the current Windows development environment, tests are run using:

```bash
python -m pytest -v
```

rather than invoking `pytest.exe` directly.

### Observed Result

```text
collected 6 items

backend/tests/test_chat_api.py::test_health_endpoint PASSED
backend/tests/test_recipe_filter.py::test_excluded_ingredient_is_filtered PASSED
backend/tests/test_recipe_filter.py::test_required_ingredient_is_enforced PASSED
backend/tests/test_recipe_loader.py::test_zero_time_becomes_none PASSED
backend/tests/test_recipe_loader.py::test_positive_time_is_preserved PASSED
backend/tests/test_recipe_ranker.py::test_recipe_with_more_matching_ingredients_ranks_higher PASSED

6 passed
```

### Status

**PASS — 6/6**

---

# 18. Development Testing Progression

Day 1 intentionally used different testing techniques at different stages.

```text
Component being developed
        ↓
Small command-line test
        ↓
Component behaves correctly
        ↓
Connect to next component
        ↓
Manual end-to-end API test
        ↓
Discover edge cases / architectural issues
        ↓
Fix + retest
        ↓
Preserve important behavior in Pytest
```

Examples:

```text
Recipe model
    ↓
Import/schema command

Recipe loader
    ↓
Single-row test
    ↓
50,514-row test

Recipe store
    ↓
Load test
    ↓
Cache identity test

Candidate retrieval
    ↓
CLI candidate inspection

Filtering
    ↓
CLI constraint tests

Ranking
    ↓
CLI score/match inspection

Complete pipeline
    ↓
Swagger scenarios

Critical deterministic behavior
    ↓
Pytest regression suite
```

---

# 19. Bugs / Issues Found Through Testing

Testing directly resulted in multiple implementation improvements.

| Issue | How It Was Discovered | Resolution | Final Status |
|---|---|---|---|
| Recipe model validator/schema problem | Model import smoke test | Removed obsolete/conflicting model code | PASS |
| Empty/malformed nutrition values caused parser failure | Single-recipe loader test | Made numeric parsing tolerant of missing values | PASS |
| `total_time_minutes = 0` treated as real time | Recommendation pipeline testing | Added effective-time resolution and unknown-time handling | PASS |
| Underspecified request returned arbitrary recipes | Swagger clarification test | Added deterministic clarification policy | PASS |
| Direct `pytest.exe` execution blocked by Windows environment | Automated test execution | Run tests using `python -m pytest -v` | PASS |

These failures were useful because they exposed assumptions that were not visible from static code inspection alone.

---

# 20. Day 1 Test Matrix

| Layer | Test | Method | Status |
|---|---|---|---|
| Configuration | OpenAI connectivity | Smoke-test script | PASS |
| Intent | Basic structured extraction | Smoke-test script | PASS |
| Intent | Complex multi-constraint extraction | Smoke-test script | PASS |
| Models | Recipe model import | CLI | PASS |
| Models | Recipe schema | CLI | PASS |
| Data | Single recipe parsing | CLI/module | PASS after fix |
| Data | Complete 50K+ corpus | CLI/module | PASS |
| Data | Processed corpus generation | CLI/module | PASS |
| Store | Runtime recipe loading | CLI | PASS |
| Store | Runtime caching | CLI | PASS |
| Retrieval | Ingredient candidates | CLI | PASS |
| Filtering | Maximum time | CLI | PASS |
| Filtering | Excluded ingredient | CLI | PASS |
| Filtering | Required ingredient | CLI | PASS |
| Ranking | Ingredient relevance | CLI | PASS |
| Service | Top-5 recommendation pipeline | CLI | PASS |
| Edge Case | Missing/zero time | CLI | PASS after fix |
| API | Basic recommendation | Swagger | PASS |
| API | Time constraint | Swagger | PASS |
| API | Excluded ingredient | Swagger | PASS |
| API | Required ingredient | Swagger | PASS |
| API | Cuisine preference | Swagger | PASS |
| API | Nutrition preference | Swagger | PASS |
| API | Multiple constraints | Swagger | PASS |
| API | Clarification | Swagger | PASS after fix |
| API | Minimal usable request | Swagger | PASS |
| API | Restrictive/no-match request | Swagger | PASS |
| Regression | Automated suite | Pytest | 6/6 PASS |

---

# Day 1 Testing Outcome

By the end of Day 1, the complete initial MealMuse recommendation path had been exercised:

```text
Natural-Language Request
          ↓
       FastAPI
          ↓
   LLM Intent Extraction
          ↓
   Structured ParsedIntent
          ↓
 Deterministic Clarification
          ↓
   Candidate Retrieval
          ↓
 Hard-Constraint Filtering
          ↓
 Deterministic Ranking
          ↓
    Top-5 Selection
          ↓
 Structured Recommendation
          ↓
      API Response
```

Testing did more than confirm the implementation.

It changed the architecture.

Two particularly important examples were:

```text
Real recipe data contained incomplete timing
                    ↓
       Time handling redesigned
                    ↓
Effective time + explicit unknown-time behavior
```

and:

```text
LLM considered "I want something light" sufficient
                    ↓
       API returned arbitrary recipes
                    ↓
Clarification responsibility reconsidered
                    ↓
LLM semantics + deterministic application policy
```

This establishes the testing philosophy that will be used throughout the rest of MealMuse:

> **Build incrementally, test assumptions against real behavior, preserve important fixes as automated regression tests, and allow test results to influence the architecture.**

---

# Planned Testing — Upcoming Phases

As MealMuse evolves toward the production architecture, this document will be extended rather than replaced.

## PostgreSQL / pgvector

Planned validation includes:

- recipe database ingestion
- row-count and data-integrity checks
- SQL filtering
- database indexes
- embedding generation
- vector similarity retrieval
- hybrid retrieval
- retrieval latency
- retrieval relevance evaluation

## Agent Orchestration

Planned validation includes:

- workflow routing
- clarification branch
- retrieval branch
- tool invocation
- tool failures
- state transitions
- retries and fallbacks
- deterministic vs LLM-controlled decisions

## Frontend / Authentication

Planned validation includes:

- API contract integration
- form/input validation
- authentication
- authorization
- session behavior
- recommendation rendering
- recipe detail behavior

## Reliability

Planned validation includes:

- OpenAI timeout
- OpenAI failure
- database failure
- malformed data
- empty retrieval results
- rate limiting
- retry behavior
- fallback behavior
- cache availability/failure

## Redis / Caching

Planned validation includes:

- cache hits
- cache misses
- cache invalidation
- TTL behavior
- fallback when Redis is unavailable

## CI/CD

Planned validation includes:

- automated tests on push
- integration-test execution
- build validation
- container build
- deployment checks

## Observability

Planned validation includes:

- structured logs
- trace propagation
- request spans
- LLM latency
- database latency
- retrieval latency
- error metrics
- Prometheus metrics
- Grafana dashboards

## Performance / Load Testing

Planned validation includes:

- concurrent API requests
- throughput
- average latency
- p95 latency
- p99 latency
- error rate
- database bottlenecks
- LLM bottlenecks
- cache effectiveness
- behavior under sustained load

## Deployment

Planned validation includes:

- Docker container health
- Kubernetes readiness/liveness
- environment configuration
- secrets
- production database connectivity
- deployed API smoke tests
- frontend/backend connectivity
- rolling deployment behavior

---

# Current Test Status

```text
Day 1 Vertical Slice

Incremental component tests       PASS
Recipe corpus processing          PASS (50,514 / 50,514)
Manual API scenarios              PASS
Known Day 1 edge cases            PASS after fixes
Automated regression suite        PASS (6 / 6)

Overall Day 1 testing status:     PASS
```