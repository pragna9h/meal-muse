from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.chat import (
    ChatResponse,
    MealRecommendation,
    ParsedIntent,
)
from backend.app.models.orchestration import ResultState


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200


def test_chat_returns_meal_recommendation(monkeypatch):
    def mock_orchestrate_chat(message: str):
        return ChatResponse(
            result_state=ResultState.SUCCESS,
            message=None,
            parsed_intent=ParsedIntent(
                intent="meal_recommendation",
                ingredients_available=["chicken", "rice"],
            ),
            recommendations=[
                MealRecommendation(
                    recipe_id="recipe_1",
                    name="Chicken Rice Bowl",
                    score=1.0,
                    reason="Matches available ingredients.",
                )
            ],
            recipes=[],
        )

    monkeypatch.setattr(
        "backend.app.api.chat.orchestrate_chat",
        mock_orchestrate_chat,
    )

    response = client.post(
        "/chat",
        json={
            "message": "I have chicken and rice. What can I make?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["result_state"] == "success"
    assert data["message"] is None
    assert data["parsed_intent"]["intent"] == "meal_recommendation"
    assert data["parsed_intent"]["recipe_query"] is None
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["name"] == "Chicken Rice Bowl"
    assert data["recipes"] == []


def test_chat_returns_recipe_search(monkeypatch):
    def mock_orchestrate_chat(message: str):
        return ChatResponse(
            result_state=ResultState.SUCCESS,
            message=None,
            parsed_intent=ParsedIntent(
                intent="recipe_search",
                recipe_query="chicken tikka masala",
            ),
            recommendations=[],
            recipes=[],
        )

    monkeypatch.setattr(
        "backend.app.api.chat.orchestrate_chat",
        mock_orchestrate_chat,
    )

    response = client.post(
        "/chat",
        json={
            "message": "How do I make chicken tikka masala?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["result_state"] == "success"
    assert data["message"] is None
    assert data["parsed_intent"]["intent"] == "recipe_search"
    assert data["parsed_intent"]["recipe_query"] == "chicken tikka masala"
    assert data["recommendations"] == []
    assert data["recipes"] == []


def test_chat_returns_clarification(monkeypatch):
    def mock_orchestrate_chat(message: str):
        return ChatResponse(
            result_state=ResultState.CLARIFICATION_REQUIRED,
            message="What ingredients do you have on hand?",
            parsed_intent=ParsedIntent(
                intent="meal_recommendation",
                ingredients_available=[],
                ingredients_required=[],
                needs_clarification=True,
                clarification_question=(
                    "What ingredients do you have on hand?"
                ),
            ),
            recommendations=[],
            recipes=[],
        )

    monkeypatch.setattr(
        "backend.app.api.chat.orchestrate_chat",
        mock_orchestrate_chat,
    )

    response = client.post(
        "/chat",
        json={
            "message": "I want something good to eat."
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["result_state"] == "clarification_required"
    assert data["message"] == "What ingredients do you have on hand?"
    assert data["parsed_intent"]["needs_clarification"] is True
    assert data["parsed_intent"]["clarification_question"] == (
        "What ingredients do you have on hand?"
    )
    assert data["recommendations"] == []
    assert data["recipes"] == []


def test_chat_returns_no_results(monkeypatch):
    def mock_orchestrate_chat(message: str):
        return ChatResponse(
            result_state=ResultState.NO_RESULTS,
            message=(
                "I couldn't find any recipes matching those constraints."
            ),
            parsed_intent=ParsedIntent(
                intent="meal_recommendation",
                ingredients_available=["dragonfruit"],
            ),
            recommendations=[],
            recipes=[],
        )

    monkeypatch.setattr(
        "backend.app.api.chat.orchestrate_chat",
        mock_orchestrate_chat,
    )

    response = client.post(
        "/chat",
        json={
            "message": "I only have dragonfruit."
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["result_state"] == "no_results"
    assert data["recommendations"] == []
    assert data["recipes"] == []