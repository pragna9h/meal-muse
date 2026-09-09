import pytest

from backend.app.models.chat import MealRecommendation
from backend.app.models.orchestration import ResultState
from backend.app.models.tool_arguments import (
    MealRecommendationToolArguments,
    RecipeSearchToolArguments,
)
from backend.app.orchestration.chat_orchestrator import orchestrate_chat
from backend.app.orchestration.exceptions import ToolExecutionError
from backend.app.models.recipe import Recipe


def test_orchestrator_returns_meal_recommendations(monkeypatch):
    def mock_select_tool(message: str):
        return (
            "recommend_meals",
            MealRecommendationToolArguments(
                ingredients_available=["chicken", "rice"],
                taste_preferences=["spicy"],
            ),
        )

    def mock_execute_recommendation_tool(parsed_intent):
        return [
            MealRecommendation(
                recipe_id="recipe_1",
                name="Spicy Chicken Rice Bowl",
                score=1.0,
                reason="Matches available ingredients and spicy preference.",
            )
        ]

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.execute_recommendation_tool",
        mock_execute_recommendation_tool,
    )

    response = orchestrate_chat(
        "I have chicken and rice. Something spicy."
    )

    assert response.result_state == ResultState.SUCCESS
    assert response.message is None
    assert response.parsed_intent.intent == "meal_recommendation"
    assert response.parsed_intent.ingredients_available == [
        "chicken",
        "rice",
    ]
    assert len(response.recommendations) == 1
    assert response.recommendations[0].name == "Spicy Chicken Rice Bowl"
    assert response.recipes == []


def test_orchestrator_returns_recipe_search_results(monkeypatch):
    def mock_select_tool(message: str):
        return (
            "search_recipe",
            RecipeSearchToolArguments(
                recipe_query="chicken tikka masala",
            ),
        )

    recipe = Recipe(
        recipe_id="recipe_1",
        name="Chicken Tikka Masala",
        ingredients=[],
        ingredients_raw=[],
        normalized_ingredients=[],
        instructions=[],
        categories=[],
        cuisines=[],
        cooking_methods=[],
        equipment=[],
    )

    def mock_execute_recipe_search_tool(parsed_intent):
        return [recipe]

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.execute_recipe_search_tool",
        mock_execute_recipe_search_tool,
    )

    response = orchestrate_chat(
        "How do I make chicken tikka masala?"
    )

    assert response.result_state == ResultState.SUCCESS
    assert response.message is None
    assert response.parsed_intent.intent == "recipe_search"
    assert response.parsed_intent.recipe_query == "chicken tikka masala"
    assert response.recommendations == []
    assert len(response.recipes) == 1
    assert response.recipes[0].name == "Chicken Tikka Masala"


def test_orchestrator_returns_clarification(monkeypatch):
    def mock_select_tool(message: str):
        return (
            "recommend_meals",
            MealRecommendationToolArguments(),
        )

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.select_tool",
        mock_select_tool,
    )

    response = orchestrate_chat(
        "I want something healthy."
    )

    assert response.result_state == ResultState.CLARIFICATION_REQUIRED
    assert response.message == "What ingredients do you have on hand?"
    assert response.parsed_intent.needs_clarification is True
    assert response.recommendations == []
    assert response.recipes == []


def test_orchestrator_returns_no_results_for_recommendation(monkeypatch):
    def mock_select_tool(message: str):
        return (
            "recommend_meals",
            MealRecommendationToolArguments(
                ingredients_available=["dragonfruit"],
            ),
        )

    def mock_execute_recommendation_tool(parsed_intent):
        return []

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.execute_recommendation_tool",
        mock_execute_recommendation_tool,
    )

    response = orchestrate_chat(
        "I only have dragonfruit."
    )

    assert response.result_state == ResultState.NO_RESULTS
    assert response.message == (
        "I couldn't find any recipes matching those constraints."
    )
    assert response.recommendations == []
    assert response.recipes == []


def test_orchestrator_returns_no_results_for_recipe_search(monkeypatch):
    def mock_select_tool(message: str):
        return (
            "search_recipe",
            RecipeSearchToolArguments(
                recipe_query="nonexistent dish",
            ),
        )

    def mock_execute_recipe_search_tool(parsed_intent):
        return []

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.execute_recipe_search_tool",
        mock_execute_recipe_search_tool,
    )

    response = orchestrate_chat(
        "How do I make nonexistent dish?"
    )

    assert response.result_state == ResultState.NO_RESULTS
    assert response.message == (
        "I couldn't find a recipe matching that dish."
    )
    assert response.recommendations == []
    assert response.recipes == []


def test_orchestrator_raises_tool_execution_error_for_recommendation(
    monkeypatch,
):
    def mock_select_tool(message: str):
        return (
            "recommend_meals",
            MealRecommendationToolArguments(
                ingredients_available=["chicken"],
            ),
        )

    def mock_execute_recommendation_tool(parsed_intent):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.execute_recommendation_tool",
        mock_execute_recommendation_tool,
    )

    with pytest.raises(ToolExecutionError):
        orchestrate_chat(
            "I have chicken."
        )


def test_orchestrator_raises_tool_execution_error_for_recipe_search(
    monkeypatch,
):
    def mock_select_tool(message: str):
        return (
            "search_recipe",
            RecipeSearchToolArguments(
                recipe_query="pad thai",
            ),
        )

    def mock_execute_recipe_search_tool(parsed_intent):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.select_tool",
        mock_select_tool,
    )

    monkeypatch.setattr(
        "backend.app.orchestration.chat_orchestrator.execute_recipe_search_tool",
        mock_execute_recipe_search_tool,
    )

    with pytest.raises(ToolExecutionError):
        orchestrate_chat(
            "How do I make pad thai?"
        )