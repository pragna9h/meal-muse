from backend.app.models.chat import ParsedIntent
from backend.app.models.tool_arguments import MealRecommendationToolArguments
from backend.app.services.recommendation_service import recommend_meals


def build_recommendation_intent(
    arguments: MealRecommendationToolArguments,
) -> ParsedIntent:
    return ParsedIntent(
        intent="meal_recommendation",
        **arguments.model_dump(),
    )


def execute_recommendation_tool(
    parsed_intent: ParsedIntent,
):
    return recommend_meals(parsed_intent)