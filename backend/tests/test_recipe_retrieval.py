from backend.app.models.chat import ParsedIntent
from backend.app.retrieval.recipe_retriever import hybrid_retrieve
from backend.app.repositories.recipe_repository import structured_search

import pytest

def test_structured_search_respects_time_limit():
    intent = ParsedIntent(
        ingredients_available=["chicken"],
        meal_type="dinner",
        max_prep_minutes=30,
    )

    results = structured_search(intent, limit=20)

    assert results

    for recipe in results:
        prep = recipe["prep_time_minutes"]
        cook = recipe["cook_time_minutes"]
        total = recipe["total_time_minutes"]

        if prep is not None and prep > 0 and cook is not None and cook > 0:
            effective_time = prep + cook
        else:
            effective_time = total

        assert effective_time is not None
        assert effective_time <= 30


@pytest.mark.integration
def test_hybrid_retrieval_deduplicates_candidates():
    intent = ParsedIntent(
        ingredients_available=["chicken", "rice"],
        meal_type="dinner",
        taste_preferences=["spicy"],
        max_prep_minutes=30,
    )

    results = hybrid_retrieve(intent)

    recipe_ids = [
        recipe["recipe_id"]
        for recipe in results
    ]

    assert len(recipe_ids) == len(set(recipe_ids))