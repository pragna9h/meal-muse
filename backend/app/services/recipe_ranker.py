from dataclasses import dataclass

from backend.app.models.chat import ParsedIntent
from backend.app.models.recipe import Recipe
from backend.app.services.recipe_filter import ingredient_matches

from backend.app.services.recipe_time import (
    get_effective_total_time,
)


@dataclass
class RankedRecipe:
    recipe: Recipe
    score: float
    matched_ingredients: list[str]
    missing_ingredients: list[str]


def calculate_ingredient_match(
    recipe: Recipe,
    parsed_intent: ParsedIntent,
) -> tuple[float, list[str], list[str]]:
    available = parsed_intent.ingredients_available

    if not available:
        return 0.0, [], []

    matched: list[str] = []
    missing: list[str] = []

    for ingredient in available:
        if ingredient_matches(
            ingredient,
            recipe.normalized_ingredients,
        ):
            matched.append(ingredient)
        else:
            missing.append(ingredient)

    coverage = len(matched) / len(available)

    return coverage, matched, missing


def meal_type_score(
    recipe: Recipe,
    parsed_intent: ParsedIntent,
) -> float:
    if not parsed_intent.meal_type:
        return 0.0

    requested = parsed_intent.meal_type.strip().lower()

    if requested in recipe.categories:
        return 1.0

    return 0.0


def cuisine_score(
    recipe: Recipe,
    parsed_intent: ParsedIntent,
) -> float:
    if not parsed_intent.cuisine_preferences:
        return 0.0

    requested_cuisines = {
        cuisine.strip().lower()
        for cuisine in parsed_intent.cuisine_preferences
    }

    recipe_cuisines = set(recipe.cuisines)

    if requested_cuisines.intersection(recipe_cuisines):
        return 1.0

    return 0.0


def time_score(
    recipe: Recipe,
    parsed_intent: ParsedIntent,
) -> float:
    max_minutes = parsed_intent.max_prep_minutes

    if max_minutes is None:
        return 0.0

    effective_time = get_effective_total_time(recipe)

    if effective_time is None:
        return 0.0

    if effective_time > max_minutes:
        return 0.0

    if max_minutes == 0:
        return 0.0

    remaining_fraction = (max_minutes - effective_time) / max_minutes

    return max(0.0, remaining_fraction)


def rating_score(recipe: Recipe) -> float:
    if recipe.rating_value is None:
        return 0.0

    normalized_rating = recipe.rating_value / 5.0

    rating_count = recipe.rating_count or 0

    if rating_count >= 1000:
        confidence = 1.0
    elif rating_count >= 100:
        confidence = 0.8
    elif rating_count >= 20:
        confidence = 0.6
    elif rating_count > 0:
        confidence = 0.4
    else:
        confidence = 0.2

    return normalized_rating * confidence


def score_recipe(
    recipe: Recipe,
    parsed_intent: ParsedIntent,
) -> RankedRecipe:
    (
        ingredient_coverage,
        matched_ingredients,
        missing_ingredients,
    ) = calculate_ingredient_match(
        recipe,
        parsed_intent,
    )

    meal_score = meal_type_score(
        recipe,
        parsed_intent,
    )

    cuisine = cuisine_score(
        recipe,
        parsed_intent,
    )

    time_fit = time_score(
        recipe,
        parsed_intent,
    )

    rating = rating_score(recipe)

    missing_penalty = 0.0

    if parsed_intent.ingredients_available:
        missing_penalty = (
            len(missing_ingredients)
            / len(parsed_intent.ingredients_available)
        )

    final_score = (
        ingredient_coverage * 60
        + meal_score * 10
        + cuisine * 10
        + time_fit * 10
        + rating * 10
        - missing_penalty * 15
    )

    return RankedRecipe(
        recipe=recipe,
        score=round(final_score, 2),
        matched_ingredients=matched_ingredients,
        missing_ingredients=missing_ingredients,
    )


def rank_recipes(
    recipes: list[Recipe],
    parsed_intent: ParsedIntent,
) -> list[RankedRecipe]:
    ranked = [
        score_recipe(recipe, parsed_intent)
        for recipe in recipes
    ]

    ranked.sort(
        key=lambda item: item.score,
        reverse=True,
    )

    return ranked