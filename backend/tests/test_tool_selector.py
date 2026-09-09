import json
from types import SimpleNamespace

import pytest

from backend.app.models.tool_arguments import (
    MealRecommendationToolArguments,
    RecipeSearchToolArguments,
)
from backend.app.orchestration.exceptions import ToolSelectionError
from backend.app.orchestration.tool_selector import select_tool


def build_response(*function_calls):
    return SimpleNamespace(
        output=list(function_calls),
    )


def build_function_call(
    name: str,
    arguments: dict,
):
    return SimpleNamespace(
        type="function_call",
        name=name,
        arguments=json.dumps(arguments),
    )


def test_select_tool_returns_recommendation_arguments(monkeypatch):
    mock_response = build_response(
        build_function_call(
            name="recommend_meals",
            arguments={
                "ingredients_available": ["chicken", "rice"],
                "taste_preferences": ["spicy"],
                "max_prep_minutes": 30,
            },
        )
    )

    def mock_create(**kwargs):
        return mock_response

    monkeypatch.setattr(
        "backend.app.orchestration.tool_selector.client.responses.create",
        mock_create,
    )

    tool_name, arguments = select_tool(
        "I have chicken and rice. Something spicy under 30 minutes."
    )

    assert tool_name == "recommend_meals"
    assert isinstance(
        arguments,
        MealRecommendationToolArguments,
    )

    assert arguments.ingredients_available == [
        "chicken",
        "rice",
    ]
    assert arguments.taste_preferences == ["spicy"]
    assert arguments.max_prep_minutes == 30


def test_select_tool_returns_recipe_search_arguments(monkeypatch):
    mock_response = build_response(
        build_function_call(
            name="search_recipe",
            arguments={
                "recipe_query": "chicken tikka masala",
            },
        )
    )

    def mock_create(**kwargs):
        return mock_response

    monkeypatch.setattr(
        "backend.app.orchestration.tool_selector.client.responses.create",
        mock_create,
    )

    tool_name, arguments = select_tool(
        "How do I make chicken tikka masala?"
    )

    assert tool_name == "search_recipe"
    assert isinstance(
        arguments,
        RecipeSearchToolArguments,
    )
    assert arguments.recipe_query == "chicken tikka masala"


def test_select_tool_raises_error_for_invalid_json(monkeypatch):
    mock_response = build_response(
        SimpleNamespace(
            type="function_call",
            name="recommend_meals",
            arguments="{invalid-json",
        )
    )

    def mock_create(**kwargs):
        return mock_response

    monkeypatch.setattr(
        "backend.app.orchestration.tool_selector.client.responses.create",
        mock_create,
    )

    with pytest.raises(ToolSelectionError):
        select_tool(
            "I have chicken."
        )


def test_select_tool_raises_error_for_unsupported_tool(monkeypatch):
    mock_response = build_response(
        build_function_call(
            name="unknown_tool",
            arguments={},
        )
    )

    def mock_create(**kwargs):
        return mock_response

    monkeypatch.setattr(
        "backend.app.orchestration.tool_selector.client.responses.create",
        mock_create,
    )

    with pytest.raises(ToolSelectionError):
        select_tool(
            "Do something."
        )


def test_select_tool_raises_error_when_no_tool_is_returned(monkeypatch):
    mock_response = build_response()

    def mock_create(**kwargs):
        return mock_response

    monkeypatch.setattr(
        "backend.app.orchestration.tool_selector.client.responses.create",
        mock_create,
    )

    with pytest.raises(ToolSelectionError):
        select_tool(
            "I have chicken."
        )


def test_select_tool_raises_error_when_multiple_tools_are_returned(
    monkeypatch,
):
    mock_response = build_response(
        build_function_call(
            name="recommend_meals",
            arguments={
                "ingredients_available": ["chicken"],
            },
        ),
        build_function_call(
            name="search_recipe",
            arguments={
                "recipe_query": "chicken curry",
            },
        ),
    )

    def mock_create(**kwargs):
        return mock_response

    monkeypatch.setattr(
        "backend.app.orchestration.tool_selector.client.responses.create",
        mock_create,
    )

    with pytest.raises(ToolSelectionError):
        select_tool(
            "I have chicken. Also show me chicken curry."
        )