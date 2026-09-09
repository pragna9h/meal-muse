import json

from backend.app.config.settings import get_settings
from backend.app.models.tool_arguments import (
    MealRecommendationToolArguments,
    RecipeSearchToolArguments,
)
from backend.app.services.llm import client
from backend.app.tools.tool_definitions import MEALMUSE_TOOLS
from backend.app.orchestration.exceptions import ToolSelectionError


settings = get_settings()


TOOL_SELECTION_INSTRUCTIONS = """
You are the request-understanding layer for MealMuse.

You must choose exactly one MealMuse tool.

Use recommend_meals when the user wants help deciding what to cook or wants
meal recommendations based on ingredients, preferences, dietary constraints,
time, equipment, nutrition goals, or similar criteria.

Use search_recipe when the user already knows the specific dish or recipe they
want to find or learn how to make.

Extract only information explicitly stated or clearly implied by the user.
Do not invent ingredients, preferences, dietary restrictions, or constraints.

For recipe searches, place the dish name in recipe_query.
Do not treat words from the dish name as ingredients_available.
"""


def select_tool(message: str):
    response = client.responses.create(
        model=settings.openai_model,
        instructions=TOOL_SELECTION_INSTRUCTIONS,
        input=message,
        tools=MEALMUSE_TOOLS,
        tool_choice="required",
        parallel_tool_calls=False,
    )

    function_calls = [
        item
        for item in response.output
        if item.type == "function_call"
    ]

    if len(function_calls) != 1:
        raise ToolSelectionError(
            f"Expected exactly one tool call, received {len(function_calls)}."
        )

    tool_call = function_calls[0]

    try:
        arguments = json.loads(tool_call.arguments)

        if tool_call.name == "recommend_meals":
            return (
                tool_call.name,
                MealRecommendationToolArguments(**arguments),
            )

        if tool_call.name == "search_recipe":
            return (
                tool_call.name,
                RecipeSearchToolArguments(**arguments),
            )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ToolSelectionError(
            "MealMuse received invalid tool arguments."
        ) from exc
    raise ToolSelectionError(
        f"Unsupported MealMuse tool: {tool_call.name}"
    )