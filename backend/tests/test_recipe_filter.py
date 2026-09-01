from backend.app.models.chat import ParsedIntent
from backend.app.models.recipe import Recipe
from backend.app.services.recipe_filter import (
    filter_recipes,
)


def make_recipe(
    recipe_id: str,
    ingredients: list[str],
    total_time: int | None = None,
) -> Recipe:
    return Recipe(
        recipe_id=recipe_id,
        name=recipe_id,
        normalized_ingredients=ingredients,
        total_time_minutes=total_time,
    )


def test_excluded_ingredient_is_filtered():
    recipes = [
        make_recipe(
            "safe_recipe",
            ["chicken", "rice"],
        ),
        make_recipe(
            "peanut_recipe",
            ["chicken", "peanut butter"],
        ),
    ]

    intent = ParsedIntent(
        ingredients_excluded=["peanut"]
    )

    filtered = filter_recipes(
        recipes,
        intent,
    )

    assert len(filtered) == 1
    assert filtered[0].recipe_id == "safe_recipe"


def test_required_ingredient_is_enforced():
    recipes = [
        make_recipe(
            "with_spinach",
            ["chicken", "spinach"],
        ),
        make_recipe(
            "without_spinach",
            ["chicken", "rice"],
        ),
    ]

    intent = ParsedIntent(
        ingredients_required=["spinach"]
    )

    filtered = filter_recipes(
        recipes,
        intent,
    )

    assert len(filtered) == 1
    assert filtered[0].recipe_id == "with_spinach"