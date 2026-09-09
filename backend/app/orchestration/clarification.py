from backend.app.models.chat import ParsedIntent


def apply_clarification_policy(
    parsed_intent: ParsedIntent,
) -> ParsedIntent:
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