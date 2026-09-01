from backend.app.models.chat import (
    MealRecommendation,
    ParsedIntent,
)
from backend.app.services.recipe_filter import filter_recipes
from backend.app.services.recipe_ranker import (
    RankedRecipe,
    rank_recipes,
)
from backend.app.services.recipe_search import (
    search_recipe_candidates,
)

from backend.app.services.recipe_time import (
    get_effective_total_time,
)

def build_recommendation_reason(
    ranked_recipe: RankedRecipe,
) -> str:
    recipe = ranked_recipe.recipe

    reasons: list[str] = []

    if ranked_recipe.matched_ingredients:
        matched = ", ".join(
            ranked_recipe.matched_ingredients
        )

        reasons.append(
            f"Uses ingredients you have: {matched}"
        )

    effective_time = get_effective_total_time(recipe)

    if effective_time is not None:
        reasons.append(f"Ready in about {effective_time} minutes")
    
    if recipe.nutrition.protein_g is not None:
        reasons.append(f"{recipe.nutrition.protein_g:g}g protein per serving")

    if not reasons:
        return "Strong overall match for your request."

    return ". ".join(reasons) + "."


def ranked_recipe_to_recommendation(
    ranked_recipe: RankedRecipe,
) -> MealRecommendation:
    recipe = ranked_recipe.recipe
    effective_time = get_effective_total_time(recipe)

    return MealRecommendation(
        recipe_id=recipe.recipe_id,
        name=recipe.name,
        score=ranked_recipe.score,
        total_time_minutes=effective_time,
        calories=recipe.nutrition.calories,
        protein_g=recipe.nutrition.protein_g,
        matched_ingredients=(
            ranked_recipe.matched_ingredients
        ),
        missing_ingredients=(
            ranked_recipe.missing_ingredients
        ),
        reason=build_recommendation_reason(
            ranked_recipe
        ),
        source_url=(
            str(recipe.source_url)
            if recipe.source_url
            else None
        ),
    )


def recommend_meals(
    parsed_intent: ParsedIntent,
    candidate_limit: int = 200,
    recommendation_limit: int = 5,
) -> list[MealRecommendation]:
    candidates = search_recipe_candidates(
        parsed_intent,
        limit=candidate_limit,
    )

    filtered = filter_recipes(
        candidates,
        parsed_intent,
    )

    ranked = rank_recipes(
        filtered,
        parsed_intent,
    )

    top_ranked = ranked[:recommendation_limit]

    return [
        ranked_recipe_to_recommendation(item)
        for item in top_ranked
    ]