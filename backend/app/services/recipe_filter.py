from backend.app.models.chat import ParsedIntent
from backend.app.models.recipe import Recipe

from backend.app.services.recipe_time import (
    get_effective_total_time,
)


def ingredient_matches(
    requested_ingredient: str,
    recipe_ingredients: list[str],
) -> bool:
    """
    Check whether a requested ingredient appears in a recipe.

    Supports simple cases such as:
        "chicken" -> "chicken breast"
        "peanut"  -> "peanut butter"

    More sophisticated ingredient normalization will come later.
    """
    requested = requested_ingredient.strip().lower()

    for recipe_ingredient in recipe_ingredients:
        candidate = recipe_ingredient.strip().lower()

        if (
            requested == candidate
            or requested in candidate
            or candidate in requested
        ):
            return True

    return False


def violates_excluded_ingredients(
    recipe: Recipe,
    excluded_ingredients: list[str],
) -> bool:
    for excluded in excluded_ingredients:
        if ingredient_matches(
            excluded,
            recipe.normalized_ingredients,
        ):
            return True

    return False


def missing_required_ingredients(
    recipe: Recipe,
    required_ingredients: list[str],
) -> bool:
    for required in required_ingredients:
        if not ingredient_matches(
            required,
            recipe.normalized_ingredients,
        ):
            return True

    return False


def exceeds_time_limit(
    recipe: Recipe,
    max_prep_minutes: int | None,
    ) -> bool:
    if max_prep_minutes is None:
        return False

    effective_time = get_effective_total_time(
        recipe
    )

    if effective_time is None:
        return True

    return effective_time > max_prep_minutes


def requires_unavailable_equipment(
    recipe: Recipe,
    equipment_available: list[str],
) -> bool:
    if not equipment_available:
        return False

    if not recipe.equipment:
        return False

    available = {
        item.strip().lower()
        for item in equipment_available
    }

    required = {
        item.strip().lower()
        for item in recipe.equipment
    }

    return not required.issubset(available)


def recipe_passes_hard_constraints(
    recipe: Recipe,
    parsed_intent: ParsedIntent,
) -> bool:
    excluded = (
        parsed_intent.ingredients_excluded
        + parsed_intent.allergies
    )

    if violates_excluded_ingredients(
        recipe,
        excluded,
    ):
        return False

    if missing_required_ingredients(
        recipe,
        parsed_intent.ingredients_required,
    ):
        return False

    if exceeds_time_limit(
        recipe,
        parsed_intent.max_prep_minutes,
    ):
        return False

    if requires_unavailable_equipment(
        recipe,
        parsed_intent.equipment_available,
    ):
        return False

    return True


def filter_recipes(
    recipes: list[Recipe],
    parsed_intent: ParsedIntent,
) -> list[Recipe]:
    return [
        recipe
        for recipe in recipes
        if recipe_passes_hard_constraints(
            recipe,
            parsed_intent,
        )
    ]