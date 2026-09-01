from backend.app.models.chat import ParsedIntent
from backend.app.models.recipe import Recipe
from backend.app.services.recipe_ranker import (
    rank_recipes,
)


def test_recipe_with_more_matching_ingredients_ranks_higher():
    recipes = [
        Recipe(
            recipe_id="better_match",
            name="Better Match",
            normalized_ingredients=[
                "chicken",
                "spinach",
                "rice",
            ],
        ),
        Recipe(
            recipe_id="weaker_match",
            name="Weaker Match",
            normalized_ingredients=[
                "chicken",
            ],
        ),
    ]

    intent = ParsedIntent(
        ingredients_available=[
            "chicken",
            "spinach",
            "rice",
        ]
    )

    ranked = rank_recipes(
        recipes,
        intent,
    )

    assert ranked[0].recipe.recipe_id == "better_match"
    assert ranked[0].score > ranked[1].score