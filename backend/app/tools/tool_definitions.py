MEAL_RECOMMENDATION_TOOL = {
    "type": "function",
    "name": "recommend_meals",
    "description": (
        "Use when the user wants help deciding what meal to make based on "
        "ingredients, preferences, dietary needs, time constraints, or other "
        "meal-planning criteria."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ingredients_available": {
                "type": "array",
                "items": {"type": "string"},
            },
            "ingredients_required": {
                "type": "array",
                "items": {"type": "string"},
            },
            "ingredients_excluded": {
                "type": "array",
                "items": {"type": "string"},
            },
            "meal_type": {
                "type": ["string", "null"],
            },
            "dietary_preferences": {
                "type": "array",
                "items": {"type": "string"},
            },
            "allergies": {
                "type": "array",
                "items": {"type": "string"},
            },
            "cuisine_preferences": {
                "type": "array",
                "items": {"type": "string"},
            },
            "nutrition_goals": {
                "type": "array",
                "items": {"type": "string"},
            },
            "max_prep_minutes": {
                "type": ["integer", "null"],
            },
            "servings": {
                "type": ["integer", "null"],
            },
            "taste_preferences": {
                "type": "array",
                "items": {"type": "string"},
            },
            "equipment_available": {
                "type": "array",
                "items": {"type": "string"},
            },
            "budget_level": {
                "type": ["string", "null"],
            },
            "skill_level": {
                "type": ["string", "null"],
            },
            "allow_substitutions": {
                "type": ["boolean", "null"],
            },
        },
        "additionalProperties": False,
    },
    "strict": False,
}


RECIPE_SEARCH_TOOL = {
    "type": "function",
    "name": "search_recipe",
    "description": (
        "Use when the user already knows the specific dish or recipe they "
        "want to find, such as chicken tikka masala, lasagna, or pad thai."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "recipe_query": {
                "type": ["string", "null"],
            },
        },
        "additionalProperties": False,
    },
    "strict": False,
}


MEALMUSE_TOOLS = [
    MEAL_RECOMMENDATION_TOOL,
    RECIPE_SEARCH_TOOL,
]