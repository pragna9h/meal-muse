from backend.app.repositories.recipe_repository import (
    search_recipes_by_name,
    semantic_search,
)


DEFAULT_RECIPE_SEARCH_LIMIT = 10


def search_recipes(
    recipe_query: str,
    limit: int = DEFAULT_RECIPE_SEARCH_LIMIT,
) -> list[dict]:
    name_matches = search_recipes_by_name(
        recipe_query=recipe_query,
        limit=limit,
    )

    semantic_matches = semantic_search(
        query=recipe_query,
        limit=limit,
    )

    merged: dict[str, dict] = {}

    for recipe in name_matches:
        recipe_id = recipe["recipe_id"]

        merged[recipe_id] = {
            **recipe,
            "retrieval_source": "name",
        }

    for recipe in semantic_matches:
        recipe_id = recipe["recipe_id"]

        if recipe_id in merged:
            merged[recipe_id]["retrieval_source"] = "both"
        else:
            merged[recipe_id] = {
                **recipe,
                "retrieval_source": "semantic",
            }

    return list(merged.values())[:limit]