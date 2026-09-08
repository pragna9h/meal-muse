from backend.app.models.recipe import Recipe
from backend.app.repositories.recipe_repository import (
    get_recipes_by_ids,
)
from backend.app.retrieval.recipe_search import search_recipes


def find_recipes(
    recipe_query: str,
    limit: int = 5,
) -> list[Recipe]:
    candidates = search_recipes(
        recipe_query=recipe_query,
        limit=limit,
    )

    recipe_ids = [
        candidate["recipe_id"]
        for candidate in candidates
    ]

    return get_recipes_by_ids(recipe_ids)