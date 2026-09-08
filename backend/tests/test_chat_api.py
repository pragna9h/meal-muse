from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.chat import ParsedIntent


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200


def test_chat_routes_meal_recommendation(monkeypatch):
    parsed_intent = ParsedIntent(
        intent="meal_recommendation",
        ingredients_available=["chicken", "rice"],
        needs_clarification=False,
    )

    def mock_extract_intent(message: str):
        return parsed_intent

    def mock_recommend_meals(intent):
        return []

    monkeypatch.setattr(
        "backend.app.api.chat.extract_intent",
        mock_extract_intent,
    )

    monkeypatch.setattr(
        "backend.app.api.chat.recommend_meals",
        mock_recommend_meals,
    )

    response = client.post(
        "/chat",
        json={
            "message": "I have chicken and rice. What can I make?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["parsed_intent"]["intent"] == "meal_recommendation"
    assert data["parsed_intent"]["recipe_query"] is None
    assert data["recommendations"] == []
    assert data["recipes"] == []


def test_chat_routes_recipe_search(monkeypatch):
    parsed_intent = ParsedIntent(
        intent="recipe_search",
        recipe_query="chicken tikka masala",
        needs_clarification=False,
    )

    def mock_extract_intent(message: str):
        return parsed_intent

    def mock_find_recipes(recipe_query: str, limit: int = 5):
        return []

    monkeypatch.setattr(
        "backend.app.api.chat.extract_intent",
        mock_extract_intent,
    )

    monkeypatch.setattr(
        "backend.app.api.chat.find_recipes",
        mock_find_recipes,
    )

    response = client.post(
        "/chat",
        json={
            "message": "How do I make chicken tikka masala?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["parsed_intent"]["intent"] == "recipe_search"
    assert data["parsed_intent"]["recipe_query"] == "chicken tikka masala"
    assert data["recommendations"] == []
    assert data["recipes"] == []


def test_chat_returns_clarification(monkeypatch):
    parsed_intent = ParsedIntent(
        intent="meal_recommendation",
        ingredients_available=[],
        ingredients_required=[],
        needs_clarification=False,
    )

    def mock_extract_intent(message: str):
        return parsed_intent

    monkeypatch.setattr(
        "backend.app.api.chat.extract_intent",
        mock_extract_intent,
    )

    response = client.post(
        "/chat",
        json={
            "message": "I want something good to eat."
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["parsed_intent"]["needs_clarification"] is True
    assert data["parsed_intent"]["clarification_question"] == (
        "What ingredients do you have on hand?"
    )
    assert data["recommendations"] == []
    assert data["recipes"] == []