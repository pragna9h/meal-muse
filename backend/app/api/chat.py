from fastapi import APIRouter

from backend.app.agents.intent import extract_intent
from backend.app.models.chat import (
    ChatRequest,
    ChatResponse,
)
from backend.app.services.recommendation_service import (
    recommend_meals,
)
from backend.app.services.recipe_search_service import find_recipes


router = APIRouter()


def apply_clarification_policy(parsed_intent):
    if parsed_intent.intent == "meal_recommendation":
        has_ingredients = bool(
            parsed_intent.ingredients_available
            or parsed_intent.ingredients_required
        )

        if not has_ingredients:
            parsed_intent.needs_clarification = True

            if not parsed_intent.clarification_question:
                parsed_intent.clarification_question = (
                    "What ingredients do you have on hand?"
                )

    elif parsed_intent.intent == "recipe_search":
        if not parsed_intent.recipe_query:
            parsed_intent.needs_clarification = True

            if not parsed_intent.clarification_question:
                parsed_intent.clarification_question = (
                    "Which recipe or dish would you like me to find?"
                )

    return parsed_intent


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    parsed_intent = extract_intent(request.message)
    parsed_intent = apply_clarification_policy(parsed_intent)

    if parsed_intent.needs_clarification:
        return ChatResponse(
            parsed_intent=parsed_intent,
            recommendations=[],
            recipes=[],
        )

    if parsed_intent.intent == "meal_recommendation":
        recommendations = recommend_meals(parsed_intent)

        return ChatResponse(
            parsed_intent=parsed_intent,
            recommendations=recommendations,
            recipes=[],
        )

    if parsed_intent.intent == "recipe_search":
        recipes = find_recipes(
            recipe_query=parsed_intent.recipe_query,
            limit=5,
        )

        return ChatResponse(
            parsed_intent=parsed_intent,
            recommendations=[],
            recipes=recipes,
        )

    return ChatResponse(
        parsed_intent=parsed_intent,
        recommendations=[],
        recipes=[],
    )
    
