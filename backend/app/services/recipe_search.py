from backend.app.models.chat import ParsedIntent
from backend.app.models.recipe import Recipe
from backend.app.services.recipe_store import load_recipes


def ingredient_overlap_score(
    recipe: Recipe,
    available_ingredients: list[str],
) -> float:
    if not available_ingredients:
        return 0.0

    recipe_ingredients = set(recipe.normalized_ingredients)
    user_ingredients = set(available_ingredients)

    matched_ingredients = recipe_ingredients.intersection(
        user_ingredients
    )

    return len(matched_ingredients) / len(user_ingredients)


def search_recipe_candidates(
    parsed_intent: ParsedIntent,
    limit: int = 200,
) -> list[Recipe]:
    recipes = load_recipes()

    available_ingredients = (
        parsed_intent.ingredients_available
    )

    if not available_ingredients:
        return recipes[:limit]

    scored_recipes: list[tuple[float, Recipe]] = []

    for recipe in recipes:
        score = ingredient_overlap_score(
            recipe,
            available_ingredients,
        )

        if score > 0:
            scored_recipes.append(
                (score, recipe)
            )

    scored_recipes.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        recipe
        for _, recipe in scored_recipes[:limit]
    ]