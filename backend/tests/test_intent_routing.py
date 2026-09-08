from backend.app.models.chat import ParsedIntent


def test_meal_recommendation_intent():
    parsed_intent = ParsedIntent(
        intent="meal_recommendation",
        ingredients_available=["chicken", "rice"],
    )

    assert parsed_intent.intent == "meal_recommendation"
    assert parsed_intent.recipe_query is None


def test_recipe_search_intent():
    parsed_intent = ParsedIntent(
        intent="recipe_search",
        recipe_query="chicken tikka masala",
    )

    assert parsed_intent.intent == "recipe_search"
    assert parsed_intent.recipe_query == "chicken tikka masala"