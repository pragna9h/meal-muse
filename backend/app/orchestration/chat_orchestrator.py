from backend.app.models.chat import ChatResponse
from backend.app.models.orchestration import ResultState
from backend.app.models.tool_arguments import (
    MealRecommendationToolArguments,
    RecipeSearchToolArguments,
)
from backend.app.orchestration.clarification import (
    apply_clarification_policy,
)
from backend.app.orchestration.tool_selector import select_tool
from backend.app.tools.recommendation_tool import (
    build_recommendation_intent,
    execute_recommendation_tool,
)
from backend.app.tools.recipe_search_tool import (
    build_recipe_search_intent,
    execute_recipe_search_tool,
)
from backend.app.orchestration.exceptions import ToolExecutionError


def orchestrate_chat(message: str) -> ChatResponse:
    tool_name, arguments = select_tool(message)

    if tool_name == "recommend_meals":
        if not isinstance(
            arguments,
            MealRecommendationToolArguments,
        ):
            raise TypeError(
                "Invalid arguments for recommendation tool."
            )

        parsed_intent = build_recommendation_intent(arguments)

    elif tool_name == "search_recipe":
        if not isinstance(
            arguments,
            RecipeSearchToolArguments,
        ):
            raise TypeError(
                "Invalid arguments for recipe-search tool."
            )

        parsed_intent = build_recipe_search_intent(arguments)

    else:
        raise ValueError(
            f"Unsupported MealMuse tool: {tool_name}"
        )

    parsed_intent = apply_clarification_policy(
        parsed_intent
    )

    if parsed_intent.needs_clarification:
        return ChatResponse(
            result_state=ResultState.CLARIFICATION_REQUIRED,
            message=parsed_intent.clarification_question,
            parsed_intent=parsed_intent,
            recommendations=[],
            recipes=[],
        )

    if tool_name == "recommend_meals":
        try:
            recommendations = execute_recommendation_tool(
                parsed_intent
            )
        except Exception as exc:
            raise ToolExecutionError(
                "Recommendation tool execution failed."
            ) from exc

        if not recommendations:
            return ChatResponse(
                result_state=ResultState.NO_RESULTS,
                message=(
                    "I couldn't find any recipes matching "
                    "those constraints."
                ),
                parsed_intent=parsed_intent,
                recommendations=[],
                recipes=[],
            )

        return ChatResponse(
            result_state=ResultState.SUCCESS,
            message=None,
            parsed_intent=parsed_intent,
            recommendations=recommendations,
            recipes=[],
        )

    try:
        recipes = execute_recipe_search_tool(
        parsed_intent
        )
    except Exception as exc:
        raise ToolExecutionError(
            "Recipe-search tool execution failed."
        ) from exc

    if not recipes:
        return ChatResponse(
            result_state=ResultState.NO_RESULTS,
            message=(
                "I couldn't find a recipe matching that dish."
            ),
            parsed_intent=parsed_intent,
            recommendations=[],
            recipes=[],
        )

    return ChatResponse(
        result_state=ResultState.SUCCESS,
        message=None,
        parsed_intent=parsed_intent,
        recommendations=[],
        recipes=recipes,
    )