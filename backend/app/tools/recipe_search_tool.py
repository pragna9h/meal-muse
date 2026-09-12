from backend.app.models.chat import ParsedIntent
from backend.app.models.tool_arguments import RecipeSearchToolArguments
from backend.app.services.recipe_search_service import find_recipes


def build_recipe_search_intent(
    arguments: RecipeSearchToolArguments,
) -> ParsedIntent:
    return ParsedIntent(
        intent="recipe_search",
        recipe_query=arguments.recipe_query,
    )


def execute_recipe_search_tool(
    parsed_intent: ParsedIntent,
    limit: int = 3,
):
    return find_recipes(
        recipe_query=parsed_intent.recipe_query,
        limit=limit,
    )