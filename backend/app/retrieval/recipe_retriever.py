from backend.app.models.chat import ParsedIntent
from backend.app.repositories.recipe_repository import (semantic_search, structured_search)

SEMANTIC_LIMIT = 50
STRUCTURED_LIMIT = 50


def build_semantic_query(intent: ParsedIntent) -> str:
    parts = [
        *intent.ingredients_available,
        *intent.ingredients_required,
        *intent.cuisine_preferences,
        *intent.taste_preferences,
        *intent.nutrition_goals,
    ]

    if intent.meal_type:
        parts.append(intent.meal_type)

    return " ".join(parts)


def hybrid_retrieve(intent: ParsedIntent) -> list[dict]:
    semantic_query = build_semantic_query(intent)

    semantic_candidates = semantic_search(
        semantic_query,
        limit=SEMANTIC_LIMIT,
    )

    structured_candidates = structured_search(
        intent,
        limit=STRUCTURED_LIMIT,
    )

    candidates_by_id = {}

    for candidate in structured_candidates:
        recipe_id = candidate["recipe_id"]
        candidate["retrieval_source"] = "structured"
        candidates_by_id[recipe_id] = candidate

    for candidate in semantic_candidates:
        recipe_id = candidate["recipe_id"]

        if recipe_id in candidates_by_id:
            candidates_by_id[recipe_id]["distance"] = candidate["distance"]
            candidates_by_id[recipe_id]["retrieval_source"] = "both"
        else:
            candidate["retrieval_source"] = "semantic"
            candidates_by_id[recipe_id] = candidate

    return list(candidates_by_id.values())

